import json
import os
from typing import Any, Optional

import dotenv


class Configuration:
    """Manages configuration and environment variables for the MCP client."""

    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        self.load_env()
        self._llm_api_key = os.getenv("LLM_API_KEY")
        self._llm_base_url = os.getenv("LLM_BASE_URL")
        self._llm_model_name = os.getenv("LLM_MODEL_NAME")

        self._ollama_model_name = os.getenv("OLLAMA_MODEL_NAME")
        self._ollama_base_url = os.getenv("OLLAMA_BASE_URL")

    @staticmethod
    def load_env() -> None:
        """Load environment variables from .env file."""
        dotenv.load_dotenv()

    @staticmethod
    def load_config(file_path: str) -> dict[str, Any]:
        """Load server configuration from JSON file.

        Args:
            file_path: Path to the JSON configuration file.

        Returns:
            Dict containing server configuration.

        Raises:
            FileNotFoundError: If configuration file doesn't exist.
            JSONDecodeError: If configuration file is invalid JSON.
        """
        with open(file_path, "r") as f:
            return json.load(f)

    @property
    def llm_api_key(self) -> str:
        """Get the LLM API key.

        Returns:
            The API key as a string.

        Raises:
            ValueError: If the API key is not found in environment variables.
        """
        if not self._llm_api_key:
            raise ValueError("LLM_API_KEY not found in environment variables")
        return self._llm_api_key

    @property
    def llm_base_url(self) -> Optional[str]:
        """Get the LLM base URL.

        Returns:
            The base URL as a string.
        """
        return self._llm_base_url

    @property
    def llm_model_name(self) -> str:
        """Get the LLM model name.

        Returns:
            The model name as a string.

        Raises:
            ValueError: If the model name is not found in environment variables.
        """
        if not self._llm_model_name:
            raise ValueError("LLM_MODEL_NAME not found in environment variables")
        return self._llm_model_name

    @property
    def ollama_model_name(self) -> str:
        """Get the Ollama model name.

        Returns:
            The model name as a string.
        """
        if not self._ollama_model_name:
            raise ValueError("OLLAMA_MODEL_NAME not found in environment variables")
        return self._ollama_model_name

    @property
    def ollama_base_url(self) -> Optional[str]:
        """Get the Ollama base URL.

        Returns:
            The base URL as a string.
        """
        if not self._ollama_base_url:
            raise ValueError("OLLAMA_BASE_URL not found in environment variables")
        return self._ollama_base_url
