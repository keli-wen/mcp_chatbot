# MCPChatbot Example

This project demonstrates how to integrate the Model Context Protocol (MCP) with customized LLM (e.g. Qwen), creating a powerful chatbot that can interact with various tools through MCP servers. The implementation showcases the flexibility of MCP by enabling LLMs to use external tools seamlessly.

For Chinese version, please refer to [README_ZH.md](README_ZH.md).

## Overview

This project includes:

- A simple CLI chatbot interface
- Integration with Markdown processing tools via MCP
- Support for customized LLM (e.g. Qwen)
- Example implementation for processing and summarizing Markdown files (**very simple, just for demo**)

## Requirements

- Python 3.10+
- Dependencies (automatically installed via requirements):
  - python-dotenv
  - mcp[cli]
  - openai
  - colorama

## Installation

1. **Clone the repository:**

   ```bash
   git clone git@github.com:keli-wen/mcp_chatbot.git
   cd mcp_chatbot
   ```

2. **Set up a virtual environment (recommended):**

   ```bash
   cd folder
   
   # Install uv if you don't have it already
   pip install uv

   # Create a virtual environment and install dependencies
   uv venv .venv --python=3.10

   # Activate the virtual environment
   # For macOS/Linux
   source .venv/bin/activate
   # For Windows
   .venv\Scripts\activate

   # Deactivate the virtual environment
   deactivate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   # or use uv for faster installation
   uv pip install -r requirements.txt
   ```

4. **Configure your environment:**
   - Copy the `.env.example` file to `.env`:

     ```bash
     cp .env.example .env
     ```

   - Edit the `.env` file to add your Qwen API key (just for demo, you can use any LLM API key, remember to set the base_url and api_key in the .env file) and set the paths:

     ```
     LLM_MODEL_NAME=your_llm_model_name_here
     LLM_BASE_URL=your_llm_base_url_here
     LLM_API_KEY=your_llm_api_key_here
     MARKDOWN_FOLDER_PATH=/path/to/your/markdown/folder
     RESULT_FOLDER_PATH=/path/to/your/result/folder
     ```

## Important Configuration Notes ⚠️

Before running the application, you need to modify the following:

1. **MCP Server Configuration**:
   Edit `mcp_servers/servers_config.json` to match your local setup:

   ```json
   {
       "mcpServers": {
           "markdown_processor": {
               "command": "/path/to/your/uv",
               "args": [
                   "--directory",
                   "/path/to/your/project/mcp_servers",
                   "run",
                   "markdown_processor.py"
               ]
           }
       }
   }
   ```

   Replace `/path/to/your/uv` with the actual path to your uv executable. **You can use `which uv` to get the path**.
   Replace `/path/to/your/project/mcp_servers` with the absolute path to the mcp_servers directory in your project.

2. **Environment Variables**:
   Make sure to set proper paths in your `.env` file:

   ```
   MARKDOWN_FOLDER_PATH="/path/to/your/markdown/folder"
   RESULT_FOLDER_PATH="/path/to/your/result/folder"
   ```

   The application will validate these paths and throw an error if they contain placeholder values.

You can run the following command to check your configuration:

```bash
bash check.sh
```

## Usage

### Basic Chatbot

To run the basic chatbot interface:

```bash
python main.py
```

This will start an interactive session where you can chat with the AI. The AI has access to the tools provided by the configured MCP servers.

### Running the Example

To run the provided example that summarizes Markdown content:

```bash
python run_example.py
```

This script will:

1. Initialize the MCP servers
2. Connect to the Qwen API
3. Process the Markdown files from the configured directory
4. Generate a summary in Chinese

## Project Structure

- `main.py`: Entry point for the interactive chatbot
- `run_example.py`: Example script showing how to use the system for a specific task
- `mcp_chatbot/`: Core library code
  - `chat/`: Chat session management
  - `config/`: Configuration handling
  - `llm/`: LLM client implementation
  - `mcp_server/`: MCP server and tool integration
- `mcp_servers/`: Custom MCP servers implementation
  - `markdown_processor.py`: Server for processing Markdown files
  - `servers_config.json`: Configuration for MCP servers
- `data-example/`: Example Markdown files for testing

## Extending the Project

You can extend this project by:

1. Adding new MCP servers in the `mcp_servers/` directory
2. Updating the `servers_config.json` to include your new servers
3. Implementing new functionalities in the existing servers

## Troubleshooting

- **Path Issues**: Ensure all paths in the configuration files are absolute paths appropriate for your system
- **MCP Server Errors**: Make sure the tools are properly installed and configured
- **API Key Errors**: Verify your API key is correctly set in the `.env` file
