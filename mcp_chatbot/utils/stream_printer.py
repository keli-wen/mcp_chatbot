from typing import List, Optional

import colorama


class StreamPrinter:
    """A helper class for managing streaming terminal output."""

    def __init__(self):
        """Initialize the stream printer."""
        self.current_status: Optional[str] = None
        self.response_text: List[str] = []
        self.has_printed_prefix = False

    def print_assistant_prefix(self):
        """Print the assistant prefix."""
        print(f"{colorama.Fore.BLUE}Assistant: {colorama.Style.RESET_ALL}", end="")
        self.has_printed_prefix = True

    def print_status(self, status: str):
        """Print a status message with the ability to clear it later.

        Args:
            status: The status message to display
        """
        # If the prefix has been printed, print a newline and reset the flag
        if self.has_printed_prefix:
            print()
            self.has_printed_prefix = False

        # Clear previous status if it exists
        if self.current_status:
            print("\r" + " " * len(self.current_status), end="\r")

        # Print new status information
        self.current_status = status
        print(f"{colorama.Fore.YELLOW}{status}{colorama.Style.RESET_ALL}", end="\r")

    def print_tool_processing(self, message: str):
        """Print a tool processing message.

        Args:
            message: The tool processing message
        """
        # If the prefix has been printed, print a newline and reset the flag
        if self.has_printed_prefix:
            print()
            self.has_printed_prefix = False

        # Clear previous status if it exists
        if self.current_status:
            print("\r" + " " * len(self.current_status), end="\r")
            self.current_status = None

        print(f"{colorama.Fore.MAGENTA}{message}{colorama.Style.RESET_ALL}")

    def print_tool_results(self, results: str):
        """Print formatted tool results.

        Args:
            results: The tool results to display
        """
        formatted_results = results.replace("\n", "\n  ")
        print(f"{colorama.Fore.CYAN}  {formatted_results}{colorama.Style.RESET_ALL}")

    def print_response_chunk(self, chunk: str):
        """Print a response chunk from the LLM.

        Args:
            chunk: The response text chunk
        """
        # If the prefix has been printed, print a newline and reset the flag
        if not self.has_printed_prefix:
            self.print_assistant_prefix()

        # Clear status information
        if self.current_status:
            self.current_status = None

        self.response_text.append(chunk)
        print(chunk, end="", flush=True)

    def print_error(self, error: str):
        """Print an error message.

        Args:
            error: The error message
        """
        # If the prefix has been printed, print a newline and reset the flag
        if self.has_printed_prefix:
            print()
            self.has_printed_prefix = False

        print(f"{colorama.Fore.RED}{error}{colorama.Style.RESET_ALL}")

    def print_direct(self, text: str):
        """Print direct text (for backward compatibility).

        Args:
            text: The text to print
        """
        # If the prefix has been printed, print a newline and reset the flag
        if not self.has_printed_prefix:
            self.print_assistant_prefix()

        self.response_text.append(text)
        print(text, end="", flush=True)
