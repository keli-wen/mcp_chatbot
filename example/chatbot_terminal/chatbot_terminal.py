import argparse
import asyncio
import logging

import colorama

from mcp_chatbot import ChatSession, Configuration, MCPClient
from mcp_chatbot.llm import LLMProvider, create_llm_client


async def main(
    llm_provider: LLMProvider = "openai", show_workflow: bool = True
) -> None:
    """Initialize and run the chat session with specified LLM provider.

    Args:
        llm_provider: Which LLM provider to use ("openai" or "ollama")
    """
    # Initialize colorama for colored terminal output
    colorama.init()

    # Load configuration and setup clients
    config = Configuration()
    server_config = config.load_config("mcp_servers/servers_config.json")
    clients = [
        MCPClient(name, srv_config)
        for name, srv_config in server_config["mcpServers"].items()
    ]

    # Create appropriate LLM client
    llm_client = create_llm_client(
        provider=llm_provider,
        config=config,
    )

    # Create chat session
    chat_session = ChatSession(clients, llm_client)

    # Initialize the session
    init_success = await chat_session.initialize()
    if not init_success:
        logging.error("Failed to initialize chat session")
        return

    try:
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input(
                    f"{colorama.Fore.GREEN}You: {colorama.Style.RESET_ALL}"
                ).strip()

                # Check for exit command
                if user_input.lower() in ["quit", "exit"]:
                    logging.info("\nExiting...")
                    break

                # Process message and get response
                response = await chat_session.send_message(
                    user_input,
                    show_workflow=show_workflow,
                )

                # Display response
                print(
                    f"{colorama.Fore.BLUE}"
                    f"Assistant: {colorama.Style.RESET_ALL}"
                    f"{response}"
                )

            except KeyboardInterrupt:
                logging.info("\nExiting...")
                break
    finally:
        # Clean up resources
        await chat_session.cleanup_clients()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MCP Chatbot")
    parser.add_argument(
        "--llm",
        type=str,
        choices=["openai", "ollama"],
        default="openai",
        help="LLM provider to use (openai or ollama)",
    )
    parser.add_argument(
        "--no-workflow",
        action="store_true",
        help="Do not show workflow",
    )
    args = parser.parse_args()

    asyncio.run(main(llm_provider=args.llm, show_workflow=not args.no_workflow))
