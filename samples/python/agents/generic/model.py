from langchain_ollama import ChatOllama

model_llm_tools = None
model_llm = None


def init_llm(): 
    global model_llm

    if model_llm == None:
        model_llm = ChatOllama(model="qwen2.5", base_url = "http://localhost:11438", num_ctx=3000)
       
    return model_llm



