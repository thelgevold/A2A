from model import init_llm
from A2A.samples.python.common.types import SendTaskResponse
   
class GenericAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def invoke(self, query, sessionId) -> str:
        
        llm = init_llm()

        response = llm.invoke(query)

        task_result = {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response.content
                }

        return SendTaskResponse(id=sessionId, result=task_result)