from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage
from typing import Annotated, Any, Dict, AsyncIterable, Literal, TypedDict
from pydantic import BaseModel

import json

memory = MemorySaver()

from tool_call_helper import extract_tool_cals
from model import init_llm, get_exchange_rate

class GraphState(TypedDict):
    messages: any
    structured_response: dict

def query(state: GraphState):
    llm = init_llm()
    
    request = state["messages"]
    res = llm.invoke(request)

    structured_response = ResponseFormat(message=res.content, status="completed")

    return {"messages": [AIMessage(content=res.content)], "structured_response": structured_response}

tools = [get_exchange_rate]
tools_names = {t.name: t for t in tools}

class State(TypedDict):
  messages: any

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

def execute_tool_node(state: GraphState):
    messages = state["messages"]
    
    tool_call = extract_tool_cals(messages[0].content)[0]

    res = tools_names[tool_call["name"]].invoke(tool_call["arguments"])
    structured_response = ResponseFormat(message=json.dumps(res), status="completed")
    return {"messages": [ToolMessage(artifact=res, content=res, tool_call_id="esdads")], "structured_response": structured_response}
    
class CurrencyAgent:

    SYSTEM_INSTRUCTION = (
        "You are a specialized assistant for currency conversions. "
        "Your sole purpose is to use the 'get_exchange_rate' tool to answer questions about currency exchange rates. "
        "If the user asks about anything other than currency conversion or exchange rates, "
        "politely state that you cannot help with that topic and can only assist with currency-related queries. "
        "Do not attempt to answer unrelated questions or use tools for other purposes."
        "Set response status to input_required if the user needs to provide more information."
        "Set response status to error if there is an error while processing the request."
        "Set response status to completed if the request is complete."
    )
     
    def __init__(self):
        graph_builder=StateGraph(State)
        graph_builder.add_node("query", query)
        graph_builder.add_node("forex", execute_tool_node)
        graph_builder.add_edge(START,"query")
        graph_builder.add_edge("query","forex")
        graph_builder.add_edge("forex",END)

        self.graph = graph_builder.compile(checkpointer=memory)

    def invoke(self, query, sessionId) -> str:
        config = {"configurable": {"thread_id": sessionId}}
        print(f"THE sessionID is {sessionId}")
        self.graph.invoke({"messages": [("user", query)]}, config)        
        return self.get_agent_response(config)
      
    # async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
    #     inputs = {"messages": [("user", query)]}
    #     config = {"configurable": {"thread_id": sessionId}}

    #     for item in self.graph.stream(inputs, config, stream_mode="values"):
    #         message = item["messages"][-1]
          
    #         if (
    #             isinstance(message, AIMessage)
    #             #and message.tool_calls
    #             #and len(message.tool_calls) > 0
    #         ):
    #             yield {
    #                 "is_task_complete": False,
    #                 "require_user_input": False,
    #                 "content": "Looking up the exchange rates...",
    #             }
    #         elif isinstance(message, ToolMessage):
    #             yield {
    #                 "is_task_complete": False,
    #                 "require_user_input": False,
    #                 "content": "Processing the exchange rates..",
    #             }            
        
    #     yield self.get_agent_response(config)

        
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

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
