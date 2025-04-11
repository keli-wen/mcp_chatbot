import argparse
import asyncio
import os
import sys
from typing import Any, Dict, List

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from mcp_chatbot import ChatSession, Configuration, MCPClient  # noqa: E402
from mcp_chatbot.llm import LLMProvider, create_llm_client  # noqa: E402


def parse_servers_config(config: Dict[str, Any]) -> List[MCPClient]:
    return [
        MCPClient(name, srv_config) for name, srv_config in config["mcpServers"].items()
    ]


async def main(llm_provider: LLMProvider = "openai") -> None:
    """Initialize and run the chat session."""
    config = Configuration()
    # You can change the config file to the one you want to use
    server_config = config.load_config("mcp_servers/servers_config.json")
    servers = parse_servers_config(server_config)
    llm_client = create_llm_client(llm_provider, config)
    chat_session = ChatSession(servers, llm_client)

    markdown_folder_path = os.getenv("MARKDOWN_FOLDER_PATH")
    result_folder_path = os.getenv("RESULT_FOLDER_PATH")

    if "/path/to/your" in markdown_folder_path or "/path/to/your" in result_folder_path:
        raise ValueError(
            "markdown_folder_path or result_folder_path can not contain /path/to/folder"
            " Please set the correct path in the .env file"
        )

    try:
        await chat_session.initialize()
        await chat_session.send_message(
            f"Please summarize the content of the {markdown_folder_path} folder "
            "in one sentence. (use Chinese) "
            f"and write the result in the {result_folder_path}/summary.md file.",
            show_workflow=True,
        )
    finally:
        await chat_session.cleanup_clients()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--llm",
        type=str,
        choices=["openai", "ollama"],
        default="openai",
        help="LLM provider to use (openai or ollama)",
    )
    args = parser.parse_args()

    asyncio.run(main(llm_provider=args.llm))
