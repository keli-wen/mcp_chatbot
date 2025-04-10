# Terminal Chatbot Example

> [!TIP]
> For Chinese version, please refer to [README_ZH.md](README_ZH.md).

This example demonstrates how to create interactive chatbot interfaces with MCPChatbot:

- Regular mode (`chatbot_terminal.py`): Interactive terminal chat with complete responses
- Streaming mode (`chatbot_terminal_stream.py`): Interactive terminal chat with streaming responses

## Usage

### Regular Mode

```bash
python example/chatbot_terminal/chatbot_terminal.py
```

Options:

- `--llm [openai|ollama]`: Choose LLM provider (default: openai)
- `--no-workflow`: Hide workflow trace display

This script will:

1. Initialize the MCP servers
2. Start an interactive chat session
3. Process your prompts and display full responses
4. Show the workflow trace after each response (unless disabled)

### Streaming Mode

```bash
python example/chatbot_terminal/chatbot_terminal_stream.py
```

Options:

- `--llm [openai|ollama]`: Choose LLM provider (default: openai)
- `--no-workflow`: Hide workflow trace display

This script will:

1. Initialize the MCP servers
2. Start an interactive chat session
3. Display responses in real-time, including:
   - Status updates
   - Tool processing steps
   - Incremental response chunks
4. Show the workflow trace after completion (unless disabled)

## Example Output

<details>
<summary>Click to expand example output</summary>

```text
╰─ python example/chatbot_terminal/chatbot_terminal.py --llm openai                  ─╯
[04/11/25 00:32:41] INFO     Processing request of type ListToolsRequest   server.py:432
                    INFO     Processing request of type ListToolsRequest   server.py:432
You: 你好，能帮我总结下 /Users/{{USER_NAME}}/OpenSource/mcp_chatbot/README.md 这个 readme 中是否有指导我如何配置项目的tutorial？ 
2025-04-11 00:33:26,088 - INFO - HTTP Request: POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions "HTTP/1.1 200 OK"
2025-04-11 00:33:26,094 - INFO - 
[Debug] LLM Response: {
    "tool": "read_markdown_file",
    "arguments": {
        "directory_path": "/Users/{{USER_NAME}}/OpenSource/mcp_chatbot"
    }
}
2025-04-11 00:33:26,095 - INFO - Executing read_markdown_file...
[04/11/25 00:33:26] INFO     Processing request of type CallToolRequest    server.py:432
2025-04-11 00:33:26,102 - INFO - 
[Debug] Tool Results: Tool execution results:

Tool Call 1:
Tool Name: read_markdown_file
- Arguments: {
  "directory_path": "/Users/{{USER_NAME}}/OpenSource/mcp_chatbot"
}
- Tool call result: meta=None content=[TextContent(type='text', text='# MCPChatbot Example\n\nThis project demonstrates how to integrate the Model Context Protocol (MCP) with customized LLM (e.g. Qwen), creating a powerf

2025-04-11 00:33:33,314 - INFO - HTTP Request: POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions "HTTP/1.1 200 OK"
2025-04-11 00:33:33,316 - INFO - 
[Debug] LLM Response: 在README.md文件中，确实有指导如何配置项目的教程。以下是一些关键步骤：

1. **克隆仓库**：使用`git clone`命令将项目克隆到本地。
2. **设置虚拟环境**（推荐）：创建并激活一个Python 3.10+的虚拟环境。
3. **安装依赖**：通过`pip install -r requirements.txt`或使用`uv pip install -r requirements.txt`来安装所需的依赖项。
4. **配置环境**：
   - 复制`.env.example`文件为`.env`。
   - 编辑`.env`文件以添加你的LLM API密钥和相关路径等信息。
5. **重要配置说明**：
   - 修改`mcp_servers/servers_config.json`以匹配您的本地MCP服务器设置。
   - 确保在`.env`文件中正确设置了Markdown文件夹路径和其他必要的环境变量。

此外，文档还提供了运行前检查配置的脚本以及如何启动基本聊天界面和示例脚本的方法。如果你按照这些步骤操作，应该能够成功配置并运行这个项目。
2025-04-11 00:33:33,317 - INFO - WorkflowTrace
├── 🔍 USER_QUERY: 你好，能帮我总结下 /Users/{{USER_NAME}}/OpenSource/mcp_chatbot/RE
├── 💭 LLM_THINKING: LLM is processing your query...
├── 🤖 LLM_RESPONSE: { "tool": "read_markdown_file", "arguments
├── 🔧 TOOL_CALL: Call 1: read_markdown_file
│   └── Tool: read_markdown_file, Args: {"directory_path": "/Users/{{USER_NAME}}/OpenSource/m...
├── ⚡️ TOOL_EXECUTION: Executing read_markdown_file...
├── 📊 TOOL_RESULT: Success
│   └── Status: Success
│      └── Result: meta=None content=[TextContent(type='text', tex...
├── 💭 LLM_THINKING: LLM processing tool results (iteration 1)...
├── 🤖 LLM_RESPONSE: 在README.md文件中，确实有指导如何配置项目的教程。以下是一些关键步骤：

1. **克隆仓库
└── ✅ FINAL_RESPONSE: Final response after 1 tool iterations
Assistant: 在README.md文件中，确实有指导如何配置项目的教程。以下是一些关键步骤：

1. **克隆仓库**：使用`git clone`命令将项目克隆到本地。
2. **设置虚拟环境**（推荐）：创建并激活一个Python 3.10+的虚拟环境。
3. **安装依赖**：通过`pip install -r requirements.txt`或使用`uv pip install -r requirements.txt`来安装所需的依赖项。
4. **配置环境**：
   - 复制`.env.example`文件为`.env`。
   - 编辑`.env`文件以添加你的LLM API密钥和相关路径等信息。
5. **重要配置说明**：
   - 修改`mcp_servers/servers_config.json`以匹配您的本地MCP服务器设置。
   - 确保在`.env`文件中正确设置了Markdown文件夹路径和其他必要的环境变量。

此外，文档还提供了运行前检查配置的脚本以及如何启动基本聊天界面和示例脚本的方法。如果你按照这些步骤操作，应该能够成功配置并运行这个项目。
```

</details>

## Configuration

> [!TIP]
> Before running the example:
>
> 1. Make sure you've configured the `.env` file with proper API keys
> 2. Set up the MCP servers as described in the main README
> 3. Run `bash scripts/check.sh` to verify your environment setup

## Features

- 🌈 **Colorful Terminal Output**: Uses colorama for better readability
- 🔀 **Workflow Visualization**: Optionally displays the workflow trace after each response
- 🔄 **Interactive Session**: Maintains context between messages in a conversation
- 📊 **Tool Integration**: Shows real-time tool calls and results
- 🚪 **Easy Exit**: Type "exit" or "quit" to end the session
