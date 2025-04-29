from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.utils.push_notification_auth import PushNotificationSenderAuth
from agents.news.task_manager import AgentTaskManager
from agents.news.news_agent import NewsAgent
import click
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host, port):
    """Starts the News Agent server."""
    try:
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id="new_summary",
            name="News Summary Tool",
            description="Helps with news summaries and catcategorization of news.",
            tags=["news summary"],
            examples=["News summary"],
        )
        agent_card = AgentCard(
            name="News Agent",
            description="Helps generate news summaries. This agent only generates news summaries. Do not use this agent for anything other than generating news summaries.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=NewsAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=NewsAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=NewsAgent(), notification_sender_auth=notification_sender_auth),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json", notification_sender_auth.handle_jwks_endpoint, methods=["GET"]
        )

        logger.info(f"Starting server on {host}:{port}")
        server.start()
 
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
