import json
import logging
import re
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

import colorama

from ..llm.oai import OpenAIClient as LLMClient
from ..mcp import MCPClient
from ..utils import WorkflowEventType, WorkflowTracer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

SYSTEM_MESSAGE = (
    "You are a helpful assistant with access to these tools:\n\n"
    "{tools_description}\n\n"
    "Choose the appropriate tool based on the user's question. "
    "If no tool is needed, reply directly.\n\n"
    "IMPORTANT: When you need to use a tool, you must respond with "
    "the exact JSON object format below:\n"
    "{{\n"
    '    "tool": "tool-name",\n'
    '    "arguments": {{\n'
    '        "argument-name": "value"\n'
    "    }}\n"
    "}}\n\n"
    "After receiving tool responses:\n"
    "1. Transform the raw data into a natural, conversational response\n"
    "2. Keep responses concise but informative\n"
    "3. Focus on the most relevant information\n"
    "4. Use appropriate context from the user's question\n"
    "5. Avoid simply repeating the raw data\n\n"
    "Please use only the tools that are explicitly defined above."
)


@dataclass
class ToolCall:
    """Represents a single tool call data structure."""

    tool: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None

    def is_successful(self) -> bool:
        """Check if the tool call is successful."""
        return self.error is None and self.result is not None

    def to_description(self, for_display: bool = False, max_length: int = 200) -> str:
        """Format the tool call to a description string.

        Args:
            for_display: Whether to format for display
            max_length: Maximum length of the formatted string

        Returns:
            A formatted string
        """
        base_description = (
            f"Tool Name: {self.tool}\n"
            f"- Arguments: {json.dumps(self.arguments, indent=2)}\n"
        )
        final_description = base_description
        if self.is_successful():
            result_str = (
                str(self.result)[:max_length] if for_display else str(self.result)
            )
            final_description += f"- Tool call result: {result_str}\n"
        else:
            error_str = str(self.error)[:max_length] if for_display else str(self.error)
            final_description += f"- Tool call error: {error_str}\n"
        return final_description


class ChatSession:
    """Orchestrates the interaction between user, LLM, and tools."""

    def __init__(self, clients: List[MCPClient], llm_client: LLMClient) -> None:
        """Initialize ChatSession.

        Args:
            clients: List of MCP clients
            llm_client: LLM client
        """
        self.clients: List[MCPClient] = clients
        self.llm_client: LLMClient = llm_client
        self.messages: List[Dict[str, str]] = []
        self._is_initialized: bool = False

    async def cleanup_clients(self) -> None:
        """Clean up all client resources."""
        for client in reversed(self.clients):
            try:
                await client.cleanup()
            except Exception as e:
                logging.warning(f"Warning during cleanup of client {client.name}: {e}")

    async def initialize(self) -> bool:
        """Initialize MCP clients and prepare system message.

        Returns:
            True if initialization is successful, False otherwise.
        """
        try:
            if self._is_initialized:
                return True

            # Initialize all MCP clients
            self.tool_client_map = {}
            for client in self.clients:
                try:
                    await client.initialize()
                    tools = await client.list_tools()
                    for tool in tools:
                        if tool.name in self.tool_client_map:
                            logging.warning(
                                f"Tool {tool.name} already exists in "
                                f"{self.tool_client_map[tool.name].name}"
                            )
                        self.tool_client_map[tool.name] = client
                except Exception as e:
                    logging.error(f"Failed to initialize client: {e}")
                    await self.cleanup_clients()
                    return False

            # Collect all available tools
            all_tools = []
            for client in self.clients:
                tools = await client.list_tools()
                all_tools.extend(tools)

            # Format tool descriptions and create system message
            tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
            system_message = SYSTEM_MESSAGE.format(tools_description=tools_description)

            self.messages = [{"role": "system", "content": system_message}]
            self._is_initialized = True
            return True
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            await self.cleanup_clients()
            return False

    def _extract_tool_calls(self, llm_response: str) -> List[Dict[str, Any]]:
        """Extract tool call JSON objects from LLM response.

        Handles multiple cases:
        1. Response contains only one JSON object
        2. Response contains multiple JSON objects
        3. Response contains JSON objects and additional text

        Args:
            llm_response: LLM response text

        Returns:
            List of extracted tool call objects
        """
        # Try to parse the entire response as JSON
        try:
            tool_call = json.loads(llm_response)
            if (
                isinstance(tool_call, dict)
                and "tool" in tool_call
                and "arguments" in tool_call
            ):
                return [tool_call]
        except json.JSONDecodeError:
            pass

        # Try to extract all JSON objects from the response
        tool_calls = []
        # Regex pattern to match JSON objects
        json_pattern = r"({[^{}]*({[^{}]*})*[^{}]*})"
        json_matches = re.finditer(json_pattern, llm_response)

        for match in json_matches:
            try:
                json_obj = json.loads(match.group(0))
                if (
                    isinstance(json_obj, dict)
                    and "tool" in json_obj
                    and "arguments" in json_obj
                ):
                    tool_calls.append(json_obj)
            except json.JSONDecodeError:
                continue

        return tool_calls

    async def _execute_tool_call(self, tool_call_data: Dict[str, Any]) -> ToolCall:
        """Execute a single tool call.

        Args:
            tool_call_data: A dictionary containing 'tool' and 'arguments'

        Returns:
            A ToolCall object containing the execution result
        """
        tool_name = tool_call_data["tool"]
        arguments = tool_call_data["arguments"]

        tool_call = ToolCall(tool=tool_name, arguments=arguments)

        # Find the client directly from the tool client map.
        if tool_name in self.tool_client_map:
            client = self.tool_client_map[tool_name]
            try:
                result = await client.execute_tool(tool_name, arguments)
                tool_call.result = result
                return tool_call
            except Exception as e:
                error_msg = f"Error executing tool: {str(e)}"
                logging.error(error_msg)
                tool_call.error = error_msg
                return tool_call

        # No client found to execute this tool
        tool_call.error = f"No server found with tool: {tool_name}"
        return tool_call

    async def process_tool_calls(
        self,
        llm_response: str,
        tool_call_data_list: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[ToolCall], bool]:
        """Process all tool calls in the response.

        Args:
            llm_response: The response text from the LLM
            tool_call_data_list: A list of tool call data, if provided, the tool calls
                will be executed in the order of the list.
                (without extracting from the response)

        Returns:
            A list of ToolCall objects and a boolean indicating
                if any tools were executed
        """
        if tool_call_data_list is None:
            tool_call_data_list = self._extract_tool_calls(llm_response)

        if not tool_call_data_list:
            return [], False

        tool_calls = []
        for tool_call_data in tool_call_data_list:
            tool_call = await self._execute_tool_call(tool_call_data)
            tool_calls.append(tool_call)

        return tool_calls, True

    def _format_tool_results(
        self,
        tool_calls: List[ToolCall],
        for_display: bool = False,
        max_length: int = 200,
    ) -> str:
        """Format tool call results as a prompt text.

        Args:
            tool_calls: A list of ToolCall objects
            for_display: Whether to format for display
            max_length: Maximum length of the formatted string

        Returns:
            A formatted tool result text
        """
        results = []
        for i, call in enumerate(tool_calls, 1):
            result_text = f"Tool Call {i}:\n"
            result_text += call.to_description(for_display, max_length)
            results.append(result_text)

        return "Tool execution results:\n\n" + "\n".join(results)

    async def send_message(
        self,
        user_message: str,
        auto_process_tools: bool = True,
        show_workflow: bool = False,
        max_iterations: int = 10,
    ) -> str:
        """Send message and get response, optionally auto-process tool calls.

        Args:
            user_message: The user's message
            auto_process_tools: Whether to auto-process tool calls
            show_workflow: Whether to show the workflow
            max_iterations: Maximum number of tool iterations (default: 10)

        Returns:
            The final response text
        """
        if not self._is_initialized:
            success = await self.initialize()
            if not success:
                return "Failed to initialize chat session"

        # Initialize the workflow tracer
        self.workflow_tracer = WorkflowTracer()

        # Record user query
        self.workflow_tracer.add_event(
            WorkflowEventType.USER_QUERY,
            user_message[:50] if len(user_message) > 50 else user_message,
        )

        self.messages.append({"role": "user", "content": user_message})

        # Record LLM thinking
        self.workflow_tracer.add_event(
            WorkflowEventType.LLM_THINKING, "LLM is processing your query..."
        )

        # Get LLM response
        llm_response = self.llm_client.get_response(self.messages)

        # Record LLM response
        self.workflow_tracer.add_event(
            WorkflowEventType.LLM_RESPONSE,
            llm_response[:50] if len(llm_response) > 50 else llm_response,
        )

        self.messages.append({"role": "assistant", "content": llm_response})
        logging.info(
            f"\n{colorama.Fore.YELLOW}"
            f"[Debug] LLM Response: "
            f"{llm_response}{colorama.Style.RESET_ALL}"
        )

        if not auto_process_tools:
            # Record final response
            self.workflow_tracer.add_event(
                WorkflowEventType.FINAL_RESPONSE,
                "Direct response without tool processing",
            )
            # Output formatted workflow
            if show_workflow:
                print(self.workflow_tracer.render_tree_workflow())
            return llm_response

        # Automatically process tool calls
        tool_iteration = 0
        while tool_iteration < max_iterations:
            tool_iteration += 1
            tool_calls, has_tools = await self.process_tool_calls(llm_response)

            if not has_tools:
                # Record final response
                self.workflow_tracer.add_event(
                    WorkflowEventType.FINAL_RESPONSE,
                    f"Final response after {tool_iteration - 1} tool iterations",
                )
                # Output formatted workflow
                if show_workflow:
                    print(self.workflow_tracer.render_tree_workflow())
                return llm_response

            # Record tool calls
            for i, tool_call in enumerate(tool_calls):
                # Record tool call request
                self.workflow_tracer.add_event(
                    WorkflowEventType.TOOL_CALL,
                    f"Call {i + 1}: {tool_call.tool}",
                    {"tool_name": tool_call.tool, "arguments": tool_call.arguments},
                )

                # Record tool execution
                self.workflow_tracer.add_event(
                    WorkflowEventType.TOOL_EXECUTION, f"Executing {tool_call.tool}..."
                )

                # Record tool result
                success = tool_call.is_successful()
                self.workflow_tracer.add_event(
                    WorkflowEventType.TOOL_RESULT,
                    "Success" if success else f"Error: {tool_call.error}",
                    {
                        "success": success,
                        "result": str(tool_call.result)[:100] if success else None,
                    },
                )

            # Format tool results and add to message history
            tool_results = self._format_tool_results(tool_calls)
            self.messages.append({"role": "user", "content": tool_results})
            tool_result_formatted = self._format_tool_results(
                tool_calls, for_display=True
            )
            logging.info(
                f"\n{colorama.Fore.MAGENTA}"
                f"[Debug] Tool Results: "
                f"{tool_result_formatted}{colorama.Style.RESET_ALL}"
            )

            # Record LLM thinking again
            self.workflow_tracer.add_event(
                WorkflowEventType.LLM_THINKING,
                f"LLM processing tool results (iteration {tool_iteration})...",
            )

            # Get next response
            llm_response = self.llm_client.get_response(self.messages)

            # Record LLM response
            self.workflow_tracer.add_event(
                WorkflowEventType.LLM_RESPONSE,
                llm_response[:50] if len(llm_response) > 50 else llm_response,
            )

            self.messages.append({"role": "assistant", "content": llm_response})
            logging.info(
                f"\n{colorama.Fore.YELLOW}"
                f"[Debug] LLM Response: "
                f"{llm_response}{colorama.Style.RESET_ALL}"
            )

            # Check if next response still contains tool calls
            next_tool_calls = self._extract_tool_calls(llm_response)
            if not next_tool_calls:
                # Record final response
                self.workflow_tracer.add_event(
                    WorkflowEventType.FINAL_RESPONSE,
                    f"Final response after {tool_iteration} tool iterations",
                )
                # Output formatted workflow
                if show_workflow:
                    print(self.workflow_tracer.render_tree_workflow())
                return llm_response

    async def send_message_stream(
        self,
        user_message: str,
        auto_process_tools: bool = True,
        show_workflow: bool = False,
        max_iterations: int = 10,
    ) -> AsyncGenerator[Union[str, Tuple[str, str]], None]:
        """Send message and get streaming response, with optional tool processing.

        Args:
            user_message: The user's message
            auto_process_tools: Whether to auto-process tool calls
            show_workflow: Whether to show the workflow
            max_iterations: Maximum number of tool iterations (default: 10)

        Yields:
            Response text chunks or tuples of (status, text_chunk)
        """
        if not self._is_initialized:
            success = await self.initialize()
            if not success:
                yield ("error", "Failed to initialize chat session")
                return

        # Initialize the workflow tracer
        self.workflow_tracer = WorkflowTracer()

        # Record user query
        self.workflow_tracer.add_event(
            WorkflowEventType.USER_QUERY,
            user_message[:50] if len(user_message) > 50 else user_message,
        )

        self.messages.append({"role": "user", "content": user_message})

        # Record LLM thinking
        self.workflow_tracer.add_event(
            WorkflowEventType.LLM_THINKING, "LLM is processing your query..."
        )

        #### Get initial response stream ####
        yield ("status", "Thinking...")
        response_chunks = []
        for chunk in self.llm_client.get_stream_response(self.messages):
            response_chunks.append(chunk)
            yield ("response", chunk)
        #####################################

        llm_response = "".join(response_chunks)

        # Record LLM response
        self.workflow_tracer.add_event(
            WorkflowEventType.LLM_RESPONSE,
            llm_response[:50] if len(llm_response) > 50 else llm_response,
        )

        self.messages.append({"role": "assistant", "content": llm_response})

        if not auto_process_tools:
            # Record final response
            self.workflow_tracer.add_event(
                WorkflowEventType.FINAL_RESPONSE,
                "Direct response without tool processing",
            )
            if show_workflow:
                print(self.workflow_tracer.render_tree_workflow())
            return

        # Process tool calls
        iteration = 0
        while iteration < max_iterations:
            # Extract tool call data
            tool_call_data_list = self._extract_tool_calls(llm_response)

            if not tool_call_data_list:
                # No tool calls, return final result
                self.workflow_tracer.add_event(
                    WorkflowEventType.FINAL_RESPONSE,
                    f"Final response after {iteration} tool iterations",
                )
                if show_workflow:
                    print(self.workflow_tracer.render_tree_workflow())
                return

            # Process each tool call separately, and pass detailed information to the UI
            tool_calls = []
            for idx, tool_call_data in enumerate(tool_call_data_list):
                tool_name = tool_call_data["tool"]
                arguments = tool_call_data["arguments"]

                # Pass tool name and arguments to the UI
                yield ("tool_call", tool_name)
                yield ("tool_arguments", json.dumps(arguments))

                # Record tool call request
                self.workflow_tracer.add_event(
                    WorkflowEventType.TOOL_CALL,
                    f"Call {idx + 1}: {tool_name}",
                    {"tool_name": tool_name, "arguments": arguments},
                )

                # Pass tool execution status to the UI
                yield ("tool_execution", f"Executing {tool_name}...")

                # Record tool execution
                self.workflow_tracer.add_event(
                    WorkflowEventType.TOOL_EXECUTION, f"Executing {tool_name}..."
                )

                # Execute tool call
                tool_call = await self._execute_tool_call(tool_call_data)
                tool_calls.append(tool_call)

                # Record tool result
                success = tool_call.is_successful()
                self.workflow_tracer.add_event(
                    WorkflowEventType.TOOL_RESULT,
                    "Success" if success else f"Error: {tool_call.error}",
                    {
                        "success": success,
                        "result": str(tool_call.result)[:100] if success else None,
                    },
                )

                # Pass tool result status to the UI
                yield (
                    "tool_results",
                    json.dumps(
                        {
                            "success": success,
                            "result": str(tool_call.result)
                            if success
                            else str(tool_call.error),
                        }
                    ),
                )

            # Format tool results and add to message history
            tool_results = self._format_tool_results(tool_calls)
            self.messages.append({"role": "system", "content": tool_results})

            # Record LLM thinking
            self.workflow_tracer.add_event(
                WorkflowEventType.LLM_THINKING,
                f"LLM processing tool results (iteration {iteration + 1})...",
            )

            # Get next response stream
            yield ("status", "Processing results...")
            response_chunks = []
            for chunk in self.llm_client.get_stream_response(self.messages):
                response_chunks.append(chunk)
                yield ("response", chunk)

            llm_response = "".join(response_chunks)

            # Record LLM response
            self.workflow_tracer.add_event(
                WorkflowEventType.LLM_RESPONSE,
                llm_response[:50] if len(llm_response) > 50 else llm_response,
            )

            self.messages.append({"role": "assistant", "content": llm_response})

            # Check if next response still contains tool calls
            next_tool_calls = self._extract_tool_calls(llm_response)
            if not next_tool_calls:
                # Record final response
                self.workflow_tracer.add_event(
                    WorkflowEventType.FINAL_RESPONSE,
                    f"Final response after {iteration + 1} tool iterations",
                )
                if show_workflow:
                    print(self.workflow_tracer.render_tree_workflow())
                return

            iteration += 1
