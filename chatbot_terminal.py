import asyncio

from mcp_chatbot import ChatSession, Configuration, Server
from mcp_chatbot.llm.oai import OpenAIClient as LLMClient


async def main() -> None:
    """Initialize and run the chat session."""
    config = Configuration()
    server_config = config.load_config("mcp_servers/servers_config.json")
    servers = [
        Server(name, srv_config)
        for name, srv_config in server_config["mcpServers"].items()
    ]
    llm_client = LLMClient(
        model_name=config.llm_model_name,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
    )
    chat_session = ChatSession(servers, llm_client)
    await chat_session.start()


if __name__ == "__main__":
    asyncio.run(main())
