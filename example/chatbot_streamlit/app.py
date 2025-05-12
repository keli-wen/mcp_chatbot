import asyncio
import json
import os
import re
import sys
from contextlib import AsyncExitStack
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

if sys.platform == "win32":
    # The default event loop policy for Windows is SelectorEventLoop
    # which may cause the mcp loading error.
    # Change to WindowsSelectorEventLoopPolicy to fix.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

# Assuming these imports exist and work correctly
from mcp_chatbot import Configuration, MCPClient  # noqa: E402
from mcp_chatbot.chat import ChatSession  # noqa: E402
from mcp_chatbot.llm import create_llm_client  # noqa: E402
from mcp_chatbot.mcp.mcp_tool import MCPTool  # noqa: E402

# --- Streamlit Logo Configuration ---
st.logo(
    os.path.join(PROJECT_ROOT, "assets", "mcp_chatbot_logo.png"),
    size="large",
)

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="MCP Chatbot", layout="wide")
st.title("⚙️ MCP Chatbot - Interactive Agent")
st.caption(
    "A chatbot that uses the Model Context Protocol (MCP) to interact with tools."
)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "openai"

if "chatbot_config" not in st.session_state:
    st.session_state.chatbot_config = Configuration()

if "mcp_tools_cache" not in st.session_state:
    st.session_state.mcp_tools_cache = {}

# Add state for chat session and config tracking
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "session_config_hash" not in st.session_state:
    st.session_state.session_config_hash = None
if "active_mcp_clients" not in st.session_state:
    st.session_state.active_mcp_clients = []  # Track active clients outside stack
if "mcp_client_stack" not in st.session_state:
    st.session_state.mcp_client_stack = None  # Store the stack itself
if "history_messages" not in st.session_state:
    st.session_state.history_messages = []

# --- Constants ---
WORKFLOW_ICONS = {
    "USER_QUERY": "👤",
    "LLM_THINKING": "☁️",
    "LLM_RESPONSE": "💬",
    "TOOL_CALL": "🔧",
    "TOOL_EXECUTION": "⚡️",
    "TOOL_RESULT": "📊",
    "FINAL_STATUS": "✅",
    "ERROR": "❌",
}


# --- DataClass for Workflow Step ---
@dataclass
class WorkflowStep:
    """Workflow step class for tracking chatbot interactions."""

    type: str
    content: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


async def get_mcp_tools(force_refresh=False) -> Dict[str, List[MCPTool]]:
    """Get MCP tools from cache or by initializing clients."""
    if not force_refresh and st.session_state.mcp_tools_cache:
        return st.session_state.mcp_tools_cache

    tools_dict = {}
    config = st.session_state.chatbot_config
    server_config_path = os.path.join(
        PROJECT_ROOT, "mcp_servers", "servers_config.json"
    )
    if not os.path.exists(server_config_path):
        st.sidebar.warning("MCP Server config file not found. No tools loaded.")
        st.session_state.mcp_tools_cache = {}
        return {}

    try:
        server_config = config.load_config(server_config_path)
    except Exception as e:
        st.sidebar.error(f"Error loading MCP server config: {e}")
        st.session_state.mcp_tools_cache = {}
        return {}

    async with AsyncExitStack() as stack:
        if "mcpServers" not in server_config:
            st.sidebar.error(
                "Invalid MCP server config format: 'mcpServers' key missing."
            )
            st.session_state.mcp_tools_cache = {}
            return {}

        for name, srv_config in server_config["mcpServers"].items():
            try:
                client = MCPClient(name, srv_config)
                await stack.enter_async_context(client)
                tools = await client.list_tools()
                tools_dict[name] = tools
            except Exception as e:
                st.sidebar.error(f"Error fetching tools from {name}: {e}")

    st.session_state.mcp_tools_cache = tools_dict
    return tools_dict


def render_sidebar(mcp_tools: Optional[Dict[str, List[MCPTool]]] = None):
    """Render the sidebar with settings, MCP tools, and control buttons."""
    with st.sidebar:
        st.header("Settings")

        # --- Clear Chat Button ---
        if st.button("🧹 Clear Chat", use_container_width=True):
            # Clear chat history
            st.session_state.messages = []
            # Reset chat session state variables
            st.session_state.chat_session = None
            st.session_state.session_config_hash = None
            # Note: We don't explicitly close the AsyncExitStack here,
            # as it's difficult to do reliably from a synchronous button click
            # before rerun. The logic in process_chat handles cleanup when
            # a *new* session is created due to config change or None state.
            st.session_state.active_mcp_clients = []
            st.session_state.mcp_client_stack = None
            st.session_state.history_messages = []
            st.toast("Chat cleared!", icon="🧹")
            st.rerun()  # Rerun the app to reflect the cleared state

        llm_tab, mcp_tab = st.tabs(["LLM", "MCP"])
        with llm_tab:
            # LLM provider selection
            st.session_state.llm_provider = st.radio(
                "LLM Provider:",
                ["openai", "ollama"],
                index=["openai", "ollama"].index(st.session_state.llm_provider),
                key="llm_provider_radio",  # Add a key for stability
            )

            config = st.session_state.chatbot_config
            # Model selection based on provider
            if st.session_state.llm_provider == "openai":
                config._llm_model_name = st.text_input(
                    "OpenAI Model Name:",
                    value=config._llm_model_name or "gpt-3.5-turbo",
                    placeholder="e.g. gpt-4o",
                    key="openai_model_name",
                )
                config._llm_api_key = st.text_input(
                    "OpenAI API Key:",
                    value=config._llm_api_key or "",
                    type="password",
                    key="openai_api_key",
                )
                config._llm_base_url = st.text_input(
                    "OpenAI Base URL (optional):",
                    value=config._llm_base_url or "",
                    key="openai_base_url",
                )
            else:  # ollama
                config._ollama_model_name = st.text_input(
                    "Ollama Model Name:",
                    value=config._ollama_model_name or "llama3",
                    placeholder="e.g. llama3",
                    key="ollama_model_name",
                )
                config._ollama_base_url = st.text_input(
                    "Ollama Base URL:",
                    value=config._ollama_base_url or "http://localhost:11434",
                    key="ollama_base_url",
                )

        with mcp_tab:
            if st.button("🔄 Refresh Tools", use_container_width=True, type="primary"):
                st.session_state.mcp_tools_cache = {}
                # Also reset the session as tool changes might affect capabilities
                st.session_state.chat_session = None
                st.session_state.session_config_hash = None
                st.session_state.active_mcp_clients = []
                st.session_state.mcp_client_stack = None
                st.toast("Tools refreshed and session reset.", icon="🔄")
                st.rerun()

            if not mcp_tools:
                st.info("No MCP tools loaded or configured.")

            for client_name, client_tools in (mcp_tools or {}).items():
                with st.expander(f"Client: {client_name} ({len(client_tools)} tools)"):
                    if not client_tools:
                        st.write("No tools found for this client.")
                        continue
                    total_tools = len(client_tools)
                    for idx, tool in enumerate(client_tools):
                        st.markdown(f"**Tool {idx + 1}: `{tool.name}`**")
                        st.caption(f"{tool.description}")
                        # Use tool name in key for popover uniqueness
                        with st.popover("Schema"):
                            st.json(tool.input_schema)
                        if idx < total_tools - 1:
                            st.divider()

        # --- About Tabs ---
        en_about_tab, cn_about_tab = st.tabs(["About", "关于"])
        with en_about_tab:
            # st.markdown("### About") # Header inside tab might be too much
            st.info(
                "This chatbot uses the Model Context Protocol (MCP) for tool use. "
                "Configure LLM and MCP settings, then ask questions! "
                "Use the 'Clear Chat' button to reset the conversation."
            )
        with cn_about_tab:
            # st.markdown("### 关于")
            st.info(
                "这个聊天机器人使用模型上下文协议（MCP）进行工具使用。\n"
                "配置LLM和MCP设置，然后提出问题！使用 `Clear Chat` 按钮重置对话。"
            )


def extract_json_tool_calls(text: str) -> Tuple[List[Dict[str, Any]], str]:
    """Extract tool call JSON objects from text using robust pattern matching.

    Uses similar logic to ChatSession._extract_tool_calls but adapted for our needs.

    Args:
        text: Text possibly containing JSON tool calls

    Returns:
        Tuple of (list of extracted tool calls, cleaned text without JSON)
    """
    tool_calls = []
    cleaned_text = text
    json_parsed = False

    # Try to parse the entire text as a single JSON array of
    # tool calls or a single tool call object
    try:
        data = json.loads(text.strip())
        if isinstance(data, list):  # Check if it's a list of tool calls
            valid_tools = True
            for item in data:
                if not (
                    isinstance(item, dict) and "tool" in item and "arguments" in item
                ):
                    valid_tools = False
                    break
            if valid_tools:
                tool_calls.extend(data)
                json_parsed = True
        elif (
            isinstance(data, dict) and "tool" in data and "arguments" in data
        ):  # Check if it's a single tool call
            tool_calls.append(data)
            json_parsed = True

        if json_parsed:
            return (
                tool_calls,
                "",
            )  # Return empty string as cleaned text if parsing was successful

    except json.JSONDecodeError:
        pass  # Proceed to regex matching if direct parsing fails

    # Regex pattern to find potential JSON objects (might include tool calls)
    # This pattern tries to find JSON objects starting with '{' and ending with '}'
    json_pattern = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"
    matches = list(re.finditer(json_pattern, text))
    extracted_indices = set()

    for match in matches:
        start, end = match.span()
        # Avoid processing overlapping matches
        if any(
            start < prev_end and end > prev_start
            for prev_start, prev_end in extracted_indices
        ):
            continue

        json_str = match.group(0)
        try:
            obj = json.loads(json_str)
            # Check if the parsed object looks like a tool call
            if isinstance(obj, dict) and "tool" in obj and "arguments" in obj:
                tool_calls.append(obj)
                # Mark this region as extracted
                extracted_indices.add((start, end))
        except json.JSONDecodeError:
            # Ignore parts that are not valid JSON or not tool calls
            pass

    # Build the cleaned text by removing the extracted JSON parts
    if extracted_indices:
        cleaned_parts = []
        last_end = 0
        for start, end in sorted(list(extracted_indices)):
            cleaned_parts.append(text[last_end:start])
            last_end = end
        cleaned_parts.append(text[last_end:])
        cleaned_text = "".join(cleaned_parts).strip()
    else:
        # If no JSON tool calls were extracted via regex,
        # the original text is the cleaned text
        cleaned_text = text

    return tool_calls, cleaned_text


def render_workflow(steps: List[WorkflowStep], container=None):
    """Render workflow steps, placing each tool call sequence in its own expander."""
    if not steps:
        return

    target = container if container else st

    rendered_indices = set()

    # Iterate through steps to render them sequentially
    for i, step in enumerate(steps):
        if i in rendered_indices:
            continue

        step_type = step.type

        if step_type == "TOOL_CALL":
            # Start of a new tool call sequence
            tool_name = step.details.get("tool_name", "Unknown Tool")
            expander_title = f"{WORKFLOW_ICONS['TOOL_CALL']} Tool Call: {tool_name}"
            with target.expander(expander_title, expanded=False):
                # Display arguments
                arguments = step.details.get("arguments", {})
                st.write("**Arguments:**")
                if isinstance(arguments, str) and arguments == "Pending...":
                    st.write("Preparing arguments...")
                elif isinstance(arguments, dict):
                    if arguments:
                        for key, value in arguments.items():
                            st.write(f"- `{key}`: `{repr(value)}`")
                    else:
                        st.write("_No arguments_")
                else:
                    st.code(
                        str(arguments), language="json"
                    )  # Display as code block if not dict
                rendered_indices.add(i)

                # Look ahead for related execution and result steps for *this* tool call
                j = i + 1
                while j < len(steps):
                    next_step = steps[j]
                    # Associate based on sequence and type
                    if next_step.type == "TOOL_EXECUTION":
                        st.write(
                            f"**Status** {WORKFLOW_ICONS['TOOL_EXECUTION']}: "
                            f"{next_step.content}"
                        )
                        rendered_indices.add(j)
                    elif next_step.type == "TOOL_RESULT":
                        st.write(f"**Result** {WORKFLOW_ICONS['TOOL_RESULT']}:")
                        details = next_step.details
                        try:
                            # Success, tool execution completed.
                            details_dict = json.loads(details)
                            st.json(details_dict)
                        except json.JSONDecodeError:
                            # Error, tool execution failed.
                            result_str = str(details)
                            st.text(
                                result_str[:500]
                                + ("..." if len(result_str) > 500 else "")
                                or "_Empty result_"
                            )
                        rendered_indices.add(j)
                        break  # Stop looking ahead once result is found for this tool
                    elif (
                        next_step.type == "TOOL_CALL"
                        or next_step.type == "JSON_TOOL_CALL"
                    ):
                        # Stop if another tool call starts before finding the result
                        break
                    j += 1

        elif step_type == "JSON_TOOL_CALL":
            # Render LLM-generated tool calls in their own expander
            tool_name = step.details.get("tool_name", "Unknown")
            expander_title = (
                f"{WORKFLOW_ICONS['TOOL_CALL']} LLM Generated Tool Call: {tool_name}"
            )
            with target.expander(expander_title, expanded=False):
                st.write("**Arguments:**")
                arguments = step.details.get("arguments", {})
                if isinstance(arguments, dict):
                    if arguments:
                        for key, value in arguments.items():
                            st.write(f"- `{key}`: `{value}`")
                    else:
                        st.write("_No arguments_")
                else:
                    st.code(str(arguments), language="json")  # Display as code block
            rendered_indices.add(i)

        elif step_type == "ERROR":
            # Display errors directly, outside expanders
            target.error(f"{WORKFLOW_ICONS['ERROR']} {step.content}")
            rendered_indices.add(i)

        # Ignore other step types (USER_QUERY, LLM_THINKING, LLM_RESPONSE, FINAL_STATUS)
        # as they are handled elsewhere (status bar, main message area).


def get_config_hash(config: Configuration, provider: str) -> int:
    """Generate a hash based on relevant configuration settings."""
    relevant_config = {
        "provider": provider,
    }
    if provider == "openai":
        relevant_config.update(
            {
                "model": config._llm_model_name,
                "api_key": config._llm_api_key,
                "base_url": config._llm_base_url,
            }
        )
    else:  # ollama
        relevant_config.update(
            {
                "model": config._ollama_model_name,
                "base_url": config._ollama_base_url,
            }
        )
    # Hash the sorted representation for consistency
    return hash(json.dumps(relevant_config, sort_keys=True))


async def initialize_mcp_clients(
    config: Configuration, stack: AsyncExitStack
) -> List[MCPClient]:
    """Initializes MCP Clients based on config."""
    clients = []
    server_config_path = os.path.join(
        PROJECT_ROOT, "mcp_servers", "servers_config.json"
    )
    server_config = {}
    if os.path.exists(server_config_path):
        try:
            server_config = config.load_config(server_config_path)
        except Exception as e:
            st.warning(f"Failed to load MCP server config for client init: {e}")

    if server_config and "mcpServers" in server_config:
        for name, srv_config in server_config["mcpServers"].items():
            try:
                client = MCPClient(name, srv_config)
                # Enter the client's context into the provided stack
                await stack.enter_async_context(client)
                clients.append(client)
            except Exception as client_ex:
                st.error(f"Failed to initialize MCP client {name}: {client_ex}")
    return clients


async def process_chat(user_input: str):
    """Handles user input, interacts with the backend."""

    # 1. Add user message to state and display it
    # Use a copy for history to avoid potential modification issues if session resets
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Prepare for assistant response
    current_workflow_steps = []
    with st.chat_message("assistant"):
        status_placeholder = st.status("Processing...", expanded=False)
        workflow_display_container = st.empty()
        message_placeholder = st.empty()

    try:
        # Session and Client Management
        config = st.session_state.chatbot_config
        provider = st.session_state.llm_provider
        current_config_hash = get_config_hash(config, provider)

        # Check if config changed or session doesn't exist
        if (
            st.session_state.chat_session is None
            or current_config_hash != st.session_state.session_config_hash
        ):
            # st.toast(
            # "Configuration changed or first run, initializing new chat session."
            # )
            # If config changed, clear previous messages and reset state
            if (
                st.session_state.session_config_hash is not None
                and current_config_hash != st.session_state.session_config_hash
            ):
                st.session_state.messages = [
                    {"role": "user", "content": user_input}
                ]  # Keep only current input
                # Need to properly exit previous stack if it exists
                if st.session_state.mcp_client_stack:
                    await st.session_state.mcp_client_stack.__aexit__(None, None, None)
                    st.session_state.mcp_client_stack = None
                    st.session_state.active_mcp_clients = []

            # Create LLM Client
            llm_client = create_llm_client(provider=provider, config=config)
            if not llm_client:
                raise ValueError(
                    "LLM Client could not be created. Check configuration."
                )

            # Create and manage MCP Clients using
            # an AsyncExitStack stored in session state
            st.session_state.mcp_client_stack = AsyncExitStack()
            mcp_clients = await initialize_mcp_clients(
                config, st.session_state.mcp_client_stack
            )
            st.session_state.active_mcp_clients = mcp_clients  # Store references

            # Create new ChatSession
            # Pass the *active* clients.
            # ChatSession needs to handle these potentially changing.
            # Assuming ChatSession uses the clients passed at creation time.
            st.session_state.chat_session = ChatSession(
                st.session_state.active_mcp_clients, llm_client
            )
            await st.session_state.chat_session.initialize()
            # Keep the history messages from the new chat session.
            if not st.session_state.history_messages:
                # If the history messages are not set, we need to get the
                # system prompt from the chat session.
                st.session_state.history_messages = (
                    st.session_state.chat_session.messages
                )
            st.session_state.session_config_hash = current_config_hash
            # st.toast("New chat session initialized.", icon="🎈")  # User feedback
        else:
            # Ensure clients are available if session exists
            # (they should be in active_mcp_clients)
            # This part assumes the clients associated with the existing session
            # are still valid. If tool refresh happens, this might need adjustment.
            pass  # Use existing session

        if not st.session_state.chat_session:
            raise RuntimeError("Chat session could not be initialized.")

        chat_session = st.session_state.chat_session
        chat_session.messages = st.session_state.history_messages
        print("Chat session messages:", chat_session.messages)

        # Add user query to workflow steps
        current_workflow_steps.append(
            WorkflowStep(type="USER_QUERY", content=user_input)
        )
        with workflow_display_container.container():
            render_workflow([], container=st)  # Render empty initially

        tool_call_count = 0
        active_tool_name = None
        mcp_tool_calls_made = False

        # Initial thinking step (not added to workflow steps for display here)
        status_placeholder.update(
            label="🧠 Processing request...", state="running", expanded=False
        )

        # Stream response handling
        accumulated_response_content = ""  # Accumulate raw response content
        new_step_added = False  # Track if workflow needs rerender

        # Process streaming response using the persistent chat_session
        print("Now chat session messages:", chat_session.messages)
        async for result in chat_session.send_message_stream(
            user_input, show_workflow=True
        ):
            new_step_added = False  # Reset for this iteration
            if isinstance(result, tuple):
                status, content = result

                if status == "status":
                    status_placeholder.update(label=f"🧠 {content}", state="running")
                elif status == "tool_call":
                    mcp_tool_calls_made = True
                    tool_call_count += 1
                    active_tool_name = content
                    tool_call_step = WorkflowStep(
                        type="TOOL_CALL",
                        content=f"Initiating call to: {content}",
                        details={"tool_name": content, "arguments": "Pending..."},
                    )
                    current_workflow_steps.append(tool_call_step)
                    new_step_added = True
                    status_placeholder.update(
                        label=f"🔧 Calling tool: {content}", state="running"
                    )
                elif status == "tool_arguments":
                    if active_tool_name:
                        updated = False
                        for step in reversed(current_workflow_steps):
                            if (
                                step.type == "TOOL_CALL"
                                and step.details.get("tool_name") == active_tool_name
                                and step.details.get("arguments") == "Pending..."
                            ):
                                try:
                                    step.details["arguments"] = json.loads(content)
                                except json.JSONDecodeError:
                                    step.details["arguments"] = content
                                updated = True
                                break
                        if updated:
                            new_step_added = True
                elif status == "tool_execution":
                    current_workflow_steps.append(
                        WorkflowStep(type="TOOL_EXECUTION", content=content)
                    )
                    new_step_added = True
                    status_placeholder.update(label=f"⚡ {content}", state="running")
                elif status == "tool_results":
                    current_workflow_steps.append(
                        WorkflowStep(
                            type="TOOL_RESULT",
                            content="Received result.",
                            details=content,
                        )
                    )
                    new_step_added = True
                    status_placeholder.update(
                        label=f"🧠 Processing results from {active_tool_name}...",
                        state="running",
                    )
                    active_tool_name = None

                elif status == "response":
                    if isinstance(content, str):
                        accumulated_response_content += content
                        potential_json_tools, clean_response_so_far = (
                            extract_json_tool_calls(accumulated_response_content)
                        )
                        message_placeholder.markdown(clean_response_so_far + "▌")
                        status_placeholder.update(
                            label="💬 Streaming response...", state="running"
                        )

                elif status == "error":
                    error_content = str(content)
                    error_step = WorkflowStep(type="ERROR", content=error_content)
                    current_workflow_steps.append(error_step)
                    new_step_added = True
                    status_placeholder.update(
                        label=f"❌ Error: {error_content[:100]}...",
                        state="error",
                        expanded=True,
                    )
                    message_placeholder.error(f"An error occurred: {error_content}")
                    with workflow_display_container.container():
                        render_workflow(current_workflow_steps, container=st)
                    break  # Stop processing on error

            else:  # Handle non-tuple results (e.g., direct string) if necessary
                if isinstance(result, str):
                    accumulated_response_content += result
                    potential_json_tools, clean_response_so_far = (
                        extract_json_tool_calls(accumulated_response_content)
                    )
                    message_placeholder.markdown(clean_response_so_far + "▌")
                    status_placeholder.update(
                        label="💬 Streaming response...", state="running"
                    )

            # Re-render the workflow area if a new step was added
            if new_step_added:
                with workflow_display_container.container():
                    render_workflow(current_workflow_steps, container=st)

        # 3. Post-stream processing and final display

        json_tools, clean_response = extract_json_tool_calls(
            accumulated_response_content
        )
        final_display_content = clean_response.strip()

        json_tools_added = False
        for json_tool in json_tools:
            if not mcp_tool_calls_made:  # Heuristic: only add if no standard calls
                tool_name = json_tool.get("tool", "unknown_tool")
                tool_args = json_tool.get("arguments", {})
                json_step = WorkflowStep(
                    type="JSON_TOOL_CALL",
                    content=f"LLM generated tool call: {tool_name}",
                    details={"tool_name": tool_name, "arguments": tool_args},
                )
                current_workflow_steps.append(json_step)
                tool_call_count += 1
                json_tools_added = True

        if not final_display_content and json_tools_added:
            final_display_content = ""  # Or a message like "Generated tool calls."

        message_placeholder.markdown(final_display_content or "_No text response_")

        if final_display_content:
            llm_response_step = WorkflowStep(
                type="LLM_RESPONSE",
                content="Final response generated.",
                details={"response_text": final_display_content},
            )
            current_workflow_steps.append(llm_response_step)

        final_status_message = "Completed."
        if tool_call_count > 0:
            final_status_message += f" Processed {tool_call_count} tool call(s)."
        current_workflow_steps.append(
            WorkflowStep(type="FINAL_STATUS", content=final_status_message)
        )

        status_placeholder.update(
            label=f"✅ {final_status_message}", state="complete", expanded=False
        )

        with workflow_display_container.container():
            render_workflow(current_workflow_steps, container=st)

        # --- Store results in session state ---
        # Find the last user message added
        last_user_message_index = -1
        for i in range(len(st.session_state.messages) - 1, -1, -1):
            if st.session_state.messages[i]["role"] == "user":
                last_user_message_index = i
                break

        # Append assistant message right after the last user message
        assistant_message = {
            "role": "assistant",
            "content": final_display_content
            or accumulated_response_content,  # Store clean or full
            "workflow_steps": [step.to_dict() for step in current_workflow_steps],
        }
        if last_user_message_index != -1:
            st.session_state.messages.insert(
                last_user_message_index + 1, assistant_message
            )
        else:
            # Should not happen if we added user message first, but as fallback
            st.session_state.messages.append(assistant_message)
        # --- End storing results ---

    except Exception as e:
        error_message = f"An unexpected error occurred in process_chat: {str(e)}"
        st.error(error_message)
        current_workflow_steps.append(WorkflowStep(type="ERROR", content=error_message))
        try:
            with workflow_display_container.container():
                render_workflow(current_workflow_steps, container=st)
        except Exception as render_e:
            st.error(f"Additionally, failed to render workflow after error: {render_e}")

        status_placeholder.update(
            label=f"❌ Error: {error_message[:100]}...", state="error", expanded=True
        )
        # Append error message to history
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Error: {error_message}",
                "workflow_steps": [step.to_dict() for step in current_workflow_steps],
            }
        )
    finally:
        # --- Final UI update ---
        if (
            status_placeholder._label != f"✅ {final_status_message}"
            and status_placeholder._state != "error"
        ):
            status_placeholder.update(
                label="Processing finished.", state="complete", expanded=False
            )

        # ------------------------------------------------------------------
        # IMPORTANT CLEAN‑UP!
        #
        # Each Streamlit rerun executes this script in a *fresh* asyncio
        # event‑loop.  Any MCPClient / ChatSession objects created in a
        # previous loop become invalid and will raise
        # “Attempted to exit cancel scope in a different task…” errors when
        # they try to close themselves later on.
        #
        # Therefore we:
        #   1. Close the AsyncExitStack that owns all MCP clients *inside the
        #      same loop that created them* (`process_chat`’s loop).
        #   2. Drop the references from `st.session_state` so a new set of
        #      clients / ChatSession are created on the next user message.
        # ------------------------------------------------------------------
        try:
            if st.session_state.mcp_client_stack is not None:
                await st.session_state.mcp_client_stack.__aexit__(None, None, None)
        except Exception as cleanup_exc:
            # Log but do not crash UI – the loop is ending anyway.
            print("MCP clean‑up error:", cleanup_exc, file=sys.stderr)
        finally:
            st.session_state.mcp_client_stack = None
            st.session_state.active_mcp_clients = []
            # Do *not* reuse async objects across Streamlit reruns.
            st.session_state.history_messages = chat_session.messages
            st.session_state.chat_session = None


def display_chat_history():
    """Displays the chat history from st.session_state.messages."""
    for idx, message in enumerate(st.session_state.messages):
        # Use a unique key for each chat message element
        with st.chat_message(message["role"]):
            # Workflow Rendering
            if message["role"] == "assistant" and "workflow_steps" in message:
                # Use a unique key for the workflow container
                workflow_history_container = st.container()

                workflow_steps = []
                if isinstance(message["workflow_steps"], list):
                    for step_dict in message["workflow_steps"]:
                        if isinstance(step_dict, dict):
                            workflow_steps.append(
                                WorkflowStep(
                                    type=step_dict.get("type", "UNKNOWN"),
                                    content=step_dict.get("content", ""),
                                    details=step_dict.get("details", {}),
                                )
                            )
                if workflow_steps:
                    render_workflow(
                        workflow_steps, container=workflow_history_container
                    )

            # Message Content Rendering (Rendered after workflow for assistant)
            # Allow basic HTML if needed
            st.markdown(message["content"], unsafe_allow_html=True)


async def main():
    """Main application entry point."""
    # Get MCP tools (cached) - Tool list displayed in sidebar
    mcp_tools = await get_mcp_tools()

    # Render sidebar - Allows config changes and clearing chat
    render_sidebar(mcp_tools)

    # Display existing chat messages and their workflows from session state
    display_chat_history()

    # Handle new chat input
    if prompt := st.chat_input(
        "Ask something... (e.g., 'What files are in the root directory?')"
    ):
        await process_chat(prompt)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Note: Reliable async cleanup on shutdown is still complex in Streamlit
        pass
