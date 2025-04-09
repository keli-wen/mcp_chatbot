import os
from typing import Optional

import dotenv
import requests

dotenv.load_dotenv()


class OllamaClient:
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME")
        self.api_base = api_base or os.getenv(
            "OLLAMA_API_BASE", "http://localhost:11434"
        )

    def get_response(self, messages: list[dict[str, str]]) -> str:
        """Get a response from the Ollama LLM.

        Args:
            messages: A list of message dictionaries with 'role' and 'content'.

        Returns:
            The LLM's response as a string.
        """
        # Ollama API expects a specific format for the request
        response = requests.post(
            f"{self.api_base}/api/chat",
            json={
                "model": self.model_name,
                "messages": messages,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def get_stream_response(self, messages: list[dict[str, str]]):
        """Get a streaming response from the Ollama LLM.

        Args:
            messages: A list of message dictionaries.

        Yields:
            Chunks of the response as they arrive.
        """
        # Use requests to stream the response
        response = requests.post(
            f"{self.api_base}/api/chat",
            json={
                "model": self.model_name,
                "messages": messages,
                "stream": True,
            },
            stream=True,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                data = line.decode("utf-8")
                # Skip "done" message
                if data == '{"done":true}':
                    continue

                # Parse the JSON response
                import json

                try:
                    chunk = json.loads(data)
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue


if __name__ == "__main__":
    client = OllamaClient(
        model_name="deepseek-r1:32b", api_base="http://localhost:11434"
    )
    # Testing
    print(client.get_response([{"role": "user", "content": "你是谁？"}]))

    # Testing stream response
    print("\nStreaming response:")
    for chunk in client.get_stream_response([{"role": "user", "content": "你是谁？"}]):
        print(chunk, end="", flush=True)
