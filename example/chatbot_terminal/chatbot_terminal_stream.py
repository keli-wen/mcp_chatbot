import argparse
import asyncio
import logging
import os
import sys

import colorama

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

# Configure logging to write to file instead of stdout
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
)

from mcp_chatbot import Configuration, MCPClient  # noqa: E402
from mcp_chatbot.chat import ChatSession  # noqa: E402
from mcp_chatbot.llm import LLMProvider, create_llm_client  # noqa: E402
from mcp_chatbot.utils import StreamPrinter  # noqa: E402


async def main(
    llm_provider: LLMProvider = "openai", show_workflow: bool = True
) -> None:
    """Initialize and run the streaming chat session with specified LLM provider.

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
                    print("\nExiting...")
                    break

                # Create a printer for this conversation turn
                printer = StreamPrinter()

                # Process message and get streaming response
                async for result in chat_session.send_message_stream(
                    user_input,
                    show_workflow=False,  # Don't show workflow in logs during chat
                ):
                    # Handle different types of results
                    if isinstance(result, tuple):
                        status, content = result

                        # Handle different status types
                        if status == "status" and printer.current_status != content:
                            printer.print_status(content)
                        elif status == "tool_processing":
                            printer.print_tool_processing(content)
                        elif status == "tool_results":
                            printer.print_tool_results(content)
                        elif status == "response":
                            printer.print_response_chunk(content)
                        elif status == "error":
                            printer.print_error(content)
                    else:
                        # Direct string output (backwards compatibility)
                        printer.print_direct(result)

                # End with a newline
                print()

                # Now we can safely display the workflow trace after
                # the response is complete
                if show_workflow:
                    print(
                        f"\n{colorama.Fore.WHITE}"
                        f"{chat_session.workflow_tracer.render_tree_workflow()}"
                        f"{colorama.Style.RESET_ALL}"
                    )

            except KeyboardInterrupt:
                print("\nExiting...")
                break
    finally:
        # Clean up resources
        await chat_session.cleanup_clients()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Streaming MCP Chatbot")
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
