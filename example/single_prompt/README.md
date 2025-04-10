# Single Prompt Example

> [!TIP]
> For Chinese version, please refer to [README_ZH.md](README_ZH.md)

This example demonstrates how to use MCPChatbot for single prompt interactions with different modes:

- Regular mode (`single_prompt.py`): Processes a single prompt and returns the complete response
- Streaming mode (`single_prompt_stream.py`): Processes a single prompt with streaming response

## Usage

### Regular Mode

```bash
python example/single_prompt/single_prompt.py
```

This script will:

1. Initialize the MCP servers
2. Process a single prompt to summarize Markdown content
3. Display the complete response and workflow

### Streaming Mode

```bash
python example/single_prompt/single_prompt_stream.py
```

This script will:

1. Initialize the MCP servers
2. Process a single prompt with stream output
3. Display the response in real-time, including status updates, tool processing, and results
4. Show the workflow trace after completion

## Example Output

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

## Configuration

Before running the example:

1. Make sure you've configured the `.env` file with proper paths
2. Set up the MCP servers as described in the main README

## Parameters

Both scripts accept the `--llm` parameter to specify which LLM provider to use:

- `openai` (default): Use OpenAI-compatible API
- `ollama`: Use Ollama for local LLM processing

Example:

```bash
python example/single_prompt/single_prompt.py --llm=ollama
```
