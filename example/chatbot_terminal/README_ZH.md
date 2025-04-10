# 终端聊天机器人示例

本示例展示了如何使用 MCPChatbot 创建交互式聊天机器人界面：

- 常规模式（`chatbot_terminal.py`）：带有完整响应的交互式终端聊天
- 流式模式（`chatbot_terminal_stream.py`）：带有流式响应的交互式终端聊天

## 使用方法

### 常规模式

```bash
python example/chatbot_terminal/chatbot_terminal.py
```

选项：

- `--llm [openai|ollama]`：选择 LLM 提供者（默认：openai）
- `--no-workflow`：隐藏工作流程跟踪显示

该脚本将：

1. 初始化 MCP 服务器
2. 启动交互式聊天会话
3. 处理您的提示并显示完整响应
4. 在每个响应后显示工作流程跟踪（除非禁用）

### 流式模式

```bash
python example/chatbot_terminal/chatbot_terminal_stream.py
```

选项：

- `--llm [openai|ollama]`：选择 LLM 提供者（默认：openai）
- `--no-workflow`：隐藏工作流程跟踪显示

该脚本将：

1. 初始化 MCP 服务器
2. 启动交互式聊天会话
3. 实时显示响应，包括：
   - 状态更新
   - 工具处理步骤
   - 增量响应块
4. 完成后显示工作流程跟踪（除非禁用）

## 示例输出

<details>
<summary>点击展开示例输出</summary>

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

## 配置

> [!TIP]
> 在运行示例之前：
>
> 1. 确保您已在 `.env` 文件中配置了正确的 API 密钥
> 2. 按照主 README 中的说明设置 MCP 服务器
> 3. 运行 `bash scripts/check.sh` 以验证您的环境设置

## 功能特点

- 🌈 **彩色终端输出**：使用 colorama 提高可读性
- 🔀 **工作流可视化**：可选择性地在每个响应后显示工作流跟踪
- 🔄 **交互式会话**：在对话中维持上下文连贯性
- 📊 **工具集成**：实时显示工具调用和结果
- 🚪 **便捷退出**：输入 "exit" 或 "quit" 结束会话
