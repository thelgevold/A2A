from typing import Any, AsyncIterable, Dict, Literal
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage

from model import init_llm_with_tool_calling, init_llm
from nodes.rss_tools import get_rss_links, get_rss_feed
from nodes.url_tools import load_links
from state import GraphState
from tools.category_tools import get_article_categories
from dtos.news_context import NewsContext
from dtos.news_result import NewsResult

import json

tools = [get_article_categories]
tools_names = {t.name: t for t in tools}

memory = MemorySaver()

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class NewsAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        graph_builder=StateGraph(GraphState)
        graph_builder.add_node("get_rss_feed", get_rss_feed)
        graph_builder.add_node("get_rss_links", get_rss_links)
        graph_builder.add_node("load_links", load_links)
        graph_builder.add_node("generate_summary", generate_summary)
        graph_builder.add_node("execute_tools", execute_tools)
        graph_builder.add_node("get_categories", get_categories)

        graph_builder.add_edge(START, "get_rss_feed")  
        graph_builder.add_edge("get_rss_feed", "get_rss_links" )
        graph_builder.add_edge("get_rss_links", "load_links")
        graph_builder.add_edge("load_links", "generate_summary")
        graph_builder.add_edge("generate_summary", "get_categories")
        graph_builder.add_edge("get_categories", "execute_tools")
        graph_builder.add_edge("execute_tools", END)
        
        self.graph=graph_builder.compile(checkpointer=memory)

        print(self.graph.get_graph().draw_ascii())

    def invoke(self, query, sessionId) -> str:
        config = {"configurable": {"thread_id": sessionId}}

        news_ctx = NewsContext(rss_feed=query)
        self.graph.invoke({"data": news_ctx.rss_feed}, config)
      
        return self.get_agent_response(config=config)
    
    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
          
            if isinstance(message, AIMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": message.content,
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": message.content,
                }            
        
        yield self.get_agent_response(config)
    
    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)     
        structured_response = current_state.values.get('structured_response')
 
        if structured_response and isinstance(structured_response, ResponseFormat): 
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }
        
def generate_summary(state: GraphState):
    model = init_llm()

    articles = state["articles"]

    for article in articles:
        content = f"""
        Generate a two paragraph summary of the following text: {article["content"]}
        """

        request = [HumanMessage(content=content)]
        summary = model.invoke(request)
        article["summary"] = summary
        
    return {"articles": articles, "messages": [AIMessage(content="Completed getting article summaries from LLM")]}

def get_categories(state: GraphState):
    model = init_llm_with_tool_calling()

    articles = state["articles"]

    for article in articles:
        content= f"""You are an assistant who will use the tool called get_article_categories. Determine the categories that best describe this text: {article["summary"]}
        Use only categories from the following list: Real Estate, Politics, Sports, Immigration, Food, Entertainment, Business, Crime, Weather, Technology, Medicine, Science or Other. 
        You may select more than one category per text"""
        
        request = [SystemMessage(content=content)]
        categories = model.invoke(request)
        article["tool_call_raw"] = categories.content

    return {"tool": content, "messages": [ToolMessage(content="Completed getting tool calls from LLM", tool_call_id="567")]}

def parse_tool_call(article):
        start_index = article["tool_call_raw"].find("{")
        end_index = article["tool_call_raw"].rfind("}") + 1
        json_str = article["tool_call_raw"][start_index:end_index]

        data = json.loads(json_str)
        
        article["tool_name"] = data.get("name")
        categories = data.get("arguments", {}).get("article_categories")
        article["tool_argument"] = {"article_categories": categories}

def execute_tools(state: GraphState):
    articles = state["articles"]
   
    for article in articles:
        parse_tool_call(article)

        article["tool_result"] = tools_names[article["tool_name"]].invoke(article["tool_argument"])
              
    res = [NewsResult(r).to_dict() for r in articles]    
    res_json = json.dumps(res)  
    structured_response = ResponseFormat(message=res_json, status="completed")       

    return {"messages": [ToolMessage(artifact=res, content="Completed calling tools to categorize articles", tool_call_id="123")], "structured_response": structured_response}


        
