# MCP Chatbot - Streamlit 示例

本示例展示了如何使用 Streamlit 和 `MCPChatbot` 库创建一个交互式的聊天机器人 Web 界面。

![MCP Chatbot Streamlit Demo](../../assets/mcp_chatbot_streamlit_demo_low.gif)

![MCP Chatbot Streamlit Demo](../../assets/chatbot_streamlit_demo_light.png)

## 特点

- 💬 **交互式聊天**：用户友好的聊天界面，实现无缝对话。
- 🌊 **流式响应**：实时查看 LLM 生成的回复。
- 🛠️ **工具工作流可视化**：实时更新 MCP 工具执行状态，包括：
    - 已发起的工具调用。
    - 传递给工具的参数。
    - 执行状态更新。
    - 从工具接收到的结果。
    - LLM 生成的工具调用（从响应中解析）。
- 🔄 **上下文维护**：在会话期间保留对话历史记录。
- ⚙️ **可配置**：
    - 通过侧边栏选择 LLM 提供商（OpenAI、Ollama）。
    - 直接在界面中设置 API 密钥、基础 URL 和模型名称。
    - 查看和刷新可用的 MCP 工具。
    - 清除聊天记录并重置会话。
- ✨ **现代化 UI**：使用 Streamlit 构建的简洁界面，包含状态指示器和用于详细视图的扩展器。

## 要求

- Python 3.10+
- 主项目 `requirements.txt` 中的依赖项（包括 `streamlit`、`mcp[cli]`、`openai`、`python-dotenv`）。

## 设置

> [!TIP]
> 在运行示例之前：
>
> 1. 确保你已经配置了 .env 文件中的正确 API 密钥。
> 2. 按照主项目 [README](../../README.md) 中的说明设置 MCP 服务器。
> 3. 运行 `bash scripts/check.sh` 验证你的环境设置。

## 使用方法

1.  **从项目根目录运行 Streamlit 应用：**

    ```bash
    streamlit run example/chatbot_streamlit/app.py
    ```

2.  **使用侧边栏：**
    - 选择所需的 **LLM 提供商**（OpenAI 或 Ollama）。
    - 输入相应的 **API 密钥**、**模型名称** 和 **基础 URL**（如果适用）。*这些设置将覆盖当前会话的 `.env` 文件配置。*
    - 浏览 **MCP** 选项卡以查看加载的工具或**刷新工具**。
    - 点击 **Clear Chat** 开始新的对话。

3.  **开始聊天**：在底部的聊天输入框中输入你的问题。

## 工作原理

此应用程序将 Streamlit 与 `MCPChatbot` 库集成：

1.  **UI 层 (Streamlit)**：提供聊天界面、侧边栏配置、状态更新和工作流可视化元素（扩展器、状态指示器）。
2.  **配置 (`mcp_chatbot.Configuration`)**：从 `.env` 加载基本设置，但允许通过 Streamlit 侧边栏进行运行时覆盖。
3.  **LLM 客户端 (`mcp_chatbot.llm.create_llm_client`)**：根据侧边栏的选择创建相应的 LLM 客户端（OpenAI 或 Ollama）。
4.  **MCP 客户端 (`mcp_chatbot.MCPClient`)**：根据 `servers_config.json` 初始化客户端，以与 MCP 服务器交互。使用 `AsyncExitStack` 进行正确的生命周期管理。
5.  **聊天会话 (`mcp_chatbot.chat.ChatSession`)**：管理对话流程、状态、LLM 交互和 MCP 工具集成。处理流式响应和工作流事件。
6.  **状态管理 (`st.session_state`)**：存储消息、配置、活动客户端和聊天会话本身，以便在 Streamlit 重新运行时保持持久化。
7.  **工作流渲染**：自定义函数（`render_workflow`、`extract_json_tool_calls`）处理并显示 LLM 推理和工具使用的步骤。

## 提示

- 确保为所选的 LLM 提供商提供了正确的 API 密钥和基础 URL。
- 验证 `mcp_servers/servers_config.json` 中的路径是绝对路径且对你的系统是正确的。
- 如果在应用运行时修改了服务器配置或工具，请使用 **Refresh Tools** 按钮。
- 如果遇到错误，请检查运行 `streamlit run` 的终端以获取详细日志，以及 UI 中显示的错误消息。
- "Clear Chat" 按钮会重置对话历史记录*和*底层的 `ChatSession`，需要在下一条消息时重新初始化。 