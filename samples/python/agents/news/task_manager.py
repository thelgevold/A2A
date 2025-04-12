from common.server.task_manager import InMemoryTaskManager
from news_agent import NewsAgent
from common.utils.push_notification_auth import PushNotificationSenderAuth
from common.types import (
    SendTaskRequest,
    TaskSendParams,
    Message,
    TaskStatus,
    Artifact,
    TextPart,
    TaskState,
    SendTaskResponse,
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    Task,
    TaskIdParams,
    PushNotificationConfig,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    TaskPushNotificationConfig,
    TaskNotFoundError,
    InvalidParamsError,
)

import logging

import traceback

logger = logging.getLogger(__name__)

class AgentTaskManager(InMemoryTaskManager):
     def __init__(self, agent: NewsAgent, notification_sender_auth: PushNotificationSenderAuth):
        super().__init__()
        self.agent = agent

     async def on_send_task(self, request):
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)

        await self.upsert_task(request.params)
        task = await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), None
        )

        try:
            agent_response = self.agent.invoke(query, task_send_params.sessionId)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            traceback.print_exc()
            raise ValueError(f"Error invoking agent: {e}")
        return await self._process_agent_response(
            request, agent_response
        )

     async def on_send_task_subscribe(self, request):
        raise NotImplementedError
     
     async def _process_agent_response(
        self, request: SendTaskRequest, agent_response: dict
    ) -> SendTaskResponse:
        """Processes the agent's response and updates the task store."""
        
        task_send_params: TaskSendParams = request.params
        task_id = task_send_params.id
        history_length = task_send_params.historyLength
        task_status = None

        parts = [{"type": "text", "text": agent_response["content"]}]
        artifact = None
        if agent_response["require_user_input"]:
            task_status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message=Message(role="agent", parts=parts),
            )
        else:
            task_status = TaskStatus(state=TaskState.COMPLETED)
            artifact = Artifact(parts=parts)
        task = await self.update_store(
            task_id, task_status, None if artifact is None else [artifact]
        )
        task_result = self.append_task_history(task, history_length)
        #await self.send_task_notification(task)
        return SendTaskResponse(id=request.id, result=task_result)

     def _get_user_query(self, task_send_params: TaskSendParams) -> str:
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError("Only text parts are supported")
        return part.text

        