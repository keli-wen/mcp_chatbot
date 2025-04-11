# MCP Chatbot - Streamlit Example

> [!TIP]
> For Chinese version, please refer to [README_ZH.md](README_ZH.md).

This example demonstrates how to create an interactive chatbot web interface using Streamlit and the `MCPChatbot` library.

![MCP Chatbot Streamlit Demo](../../assets/mcp_chatbot_streamlit_demo_low.gif)

![MCP Chatbot Streamlit Demo](../../assets/chatbot_streamlit_demo_light.png)

## Features

- 💬 **Interactive Chat**: User-friendly chat interface for seamless conversation.
- 🌊 **Streaming Responses**: See LLM responses generated in real-time.
- 🛠️ **Tool Workflow Visualization**: Real-time updates on MCP tool execution, including:
    - Tool calls initiated.
    - Arguments passed to tools.
    - Execution status updates.
    - Results received from tools.
    - LLM-generated tool calls (parsed from response).
- 🔄 **Context Maintenance**: Conversation history is preserved within the session.
- ⚙️ **Configurable**:
    - Select LLM provider (OpenAI, Ollama) via the sidebar.
    - Set API keys, base URLs, and model names directly in the interface.
    - View and refresh available MCP tools.
    - Clear chat history and reset the session.
- ✨ **Modern UI**: Clean interface built with Streamlit, including status indicators and expanders for detailed views.

## Requirements

- Python 3.10+
- Dependencies from the main project's `requirements.txt` (includes `streamlit`, `mcp[cli]`, `openai`, `python-dotenv`).

## Setup

> [!TIP]
> Before running the example:
>
> 1. Make sure you've configured the .env file with proper API keys
> 2. Set up the MCP servers as described in the main [README](../../README.md)
> 3. Run `bash scripts/check.sh` to verify your environment setup

## Usage

1.  **Run the Streamlit app from the project root:**

    ```bash
    streamlit run example/chatbot_streamlit/app.py
    ```

2.  **Use the Sidebar:**
    - Select the desired **LLM Provider** (OpenAI or Ollama).
    - Enter the corresponding **API Key**, **Model Name**, and **Base URL** (if applicable). *These settings override the `.env` file for the current session.*
    - Explore the **MCP** tab to see loaded tools or **Refresh Tools**.
    - Click **Clear Chat** to start a new conversation.

3.  **Start Chatting**: Enter your query in the chat input at the bottom.

## How It Works

This application integrates Streamlit with the `MCPChatbot` library:

1.  **UI Layer (Streamlit)**: Provides the chat interface, sidebar configuration, status updates, and workflow visualization elements (expanders, status indicators).
2.  **Configuration (`mcp_chatbot.Configuration`)**: Loads base settings from `.env` but allows runtime overrides via the Streamlit sidebar.
3.  **LLM Client (`mcp_chatbot.llm.create_llm_client`)**: Creates the appropriate LLM client (OpenAI or Ollama) based on sidebar selection.
4.  **MCP Clients (`mcp_chatbot.MCPClient`)**: Initializes clients based on `servers_config.json` to interact with MCP servers. `AsyncExitStack` is used for proper lifecycle management.
5.  **Chat Session (`mcp_chatbot.chat.ChatSession`)**: Manages the conversation flow, state, LLM interaction, and MCP tool integration. Handles streaming responses and workflow events.
6.  **State Management (`st.session_state`)**: Stores messages, configuration, active clients, and the chat session itself to persist across Streamlit reruns.
7.  **Workflow Rendering**: Custom functions (`render_workflow`, `extract_json_tool_calls`) process and display the steps of the LLM's reasoning and tool usage.

## Tips

- Ensure your API keys and base URLs are correct for the selected LLM provider.
- Verify the paths in `mcp_servers/servers_config.json` are absolute and correct for your system.
- Use the **Refresh Tools** button if you modify the server configuration or tools while the app is running.
- If you encounter errors, check the terminal where you ran `streamlit run` for detailed logs, as well as the error messages displayed in the UI.
- The "Clear Chat" button resets the conversation history *and* the underlying `ChatSession`, requiring re-initialization on the next message. 