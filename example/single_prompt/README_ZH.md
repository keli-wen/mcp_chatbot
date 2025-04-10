# 单一提示示例

本示例展示了如何使用 MCPChatbot 进行单一提示交互，包含两种模式：

- 常规模式（`single_prompt.py`）：处理单一提示并返回完整响应
- 流式模式（`single_prompt_stream.py`）：处理单一提示并提供流式响应

## 使用方法

### 常规模式

```bash
python example/single_prompt/single_prompt.py
```

该脚本将：

1. 初始化 MCP 服务器
2. 处理一个用于总结 Markdown 内容的单一提示
3. 显示完整响应和工作流程

### 流式模式

```bash
python example/single_prompt/single_prompt_stream.py
```

该脚本将：

1. 初始化 MCP 服务器
2. 使用流式输出处理单一提示
3. 实时显示响应，包括状态更新、工具处理和结果
4. 完成后显示工作流跟踪

## 示例输出

```text
...
2025-04-11 00:15:17,440 - INFO - WorkflowTrace
├── 🔍 USER_QUERY: Please summarize the content of the /Users/wenkeli
├── 💭 LLM_THINKING: LLM is processing your query...
├── 🤖 LLM_RESPONSE: { "tool": "read_markdown_file", "arguments
├── 🔧 TOOL_CALL: Call 1: read_markdown_file
│   └── Tool: read_markdown_file, Args: {"directory_path": "...
├── ⚡️ TOOL_EXECUTION: Executing read_markdown_file...
├── 📊 TOOL_RESULT: Success
│   └── Status: Success
│      └── Result: meta=None content=[TextContent(type='text', tex...
├── 💭 LLM_THINKING: LLM processing tool results (iteration 1)...
├── 🤖 LLM_RESPONSE: { "tool": "write_markdown_file", "argument
├── 🔧 TOOL_CALL: Call 1: write_markdown_file
│   └── Tool: write_markdown_file, Args: {"directory_path": "...
├── ⚡️ TOOL_EXECUTION: Executing write_markdown_file...
├── 📊 TOOL_RESULT: Success
│   └── Status: Success
│      └── Result: meta=None content=[TextContent(type='text', tex...
├── 💭 LLM_THINKING: LLM processing tool results (iteration 2)...
├── 🤖 LLM_RESPONSE: 在尝试写入总结文件时，发现文件 "...
└── ✅ FINAL_RESPONSE: Final response after 2 tool iterations
```

## 配置

运行示例前：

1. 确保您已在 `.env` 文件中配置了正确的路径
2. 按照主 README 中的说明设置 MCP 服务器

## 参数

两个脚本都接受 `--llm` 参数来指定要使用的 LLM 提供者：

- `openai`（默认）：使用 OpenAI 兼容的 API
- `ollama`：使用 Ollama 进行本地 LLM 处理

示例：

```bash
python example/single_prompt/single_prompt.py --llm=ollama
```
