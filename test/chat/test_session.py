import json
import unittest
from unittest.mock import Mock

from mcp_chatbot.chat.session import ChatSession, ToolCall


class TestToolCall(unittest.TestCase):
    """Unit tests for the ToolCall class."""

    def test_tool_call_is_successful(self):
        """Test ToolCall.is_successful method."""
        # Test successful tool call
        successful_call = ToolCall(
            tool="test_tool",
            arguments={"arg": "value"},
            result="Success result",
            error=None,
        )
        self.assertTrue(successful_call.is_successful())

        # Test failed tool call
        failed_call = ToolCall(
            tool="test_tool",
            arguments={"arg": "value"},
            result=None,
            error="Error message",
        )
        self.assertFalse(failed_call.is_successful())

        # Test tool call with both result and error
        ambiguous_call = ToolCall(
            tool="test_tool", arguments={"arg": "value"}, result="Result", error="Error"
        )
        self.assertFalse(ambiguous_call.is_successful())

    def test_to_description(self):
        """Test ToolCall.to_description method."""
        # Test successful tool call
        successful_call = ToolCall(
            tool="test_tool",
            arguments={"arg": "value"},
            result="Success result",
            error=None,
        )
        expected_output = (
            f"Tool Name: test_tool\n"
            f"- Arguments: {json.dumps({'arg': 'value'}, indent=2)}\n"
            f"- Tool call result: Success result\n"
        )
        self.assertEqual(successful_call.to_description(), expected_output)

        # Test failed tool call
        failed_call = ToolCall(
            tool="test_tool",
            arguments={"arg": "value"},
            result=None,
            error="Error message",
        )
        expected_output = (
            f"Tool Name: test_tool\n"
            f"- Arguments: {json.dumps({'arg': 'value'}, indent=2)}\n"
            f"- Tool call error: Error message\n"
        )
        self.assertEqual(failed_call.to_description(), expected_output)


class TestChatSessionUtils(unittest.TestCase):
    """Unit tests for utility methods in the ChatSession class."""

    def setUp(self):
        """Set up test environment before each test."""
        self.mcp_client = Mock()
        self.llm_client = Mock()
        self.session = ChatSession(
            clients=[self.mcp_client], llm_client=self.llm_client
        )

    def test_extract_tool_calls_single_json(self):
        """Test extracting a single JSON object tool call."""
        # Test with a single valid JSON object
        llm_response = '{"tool": "test_tool", "arguments": {"arg1": "value1"}}'
        result = self.session._extract_tool_calls(llm_response)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool"], "test_tool")
        self.assertEqual(result[0]["arguments"]["arg1"], "value1")

    def test_extract_tool_calls_multiple_json(self):
        """Test extracting multiple JSON object tool calls."""
        # Test with multiple valid JSON objects
        llm_response = (
            '{"tool": "tool1", "arguments": {"arg1": "value1"}} '
            '{"tool": "tool2", "arguments": {"arg2": "value2"}}'
        )
        result = self.session._extract_tool_calls(llm_response)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["tool"], "tool1")
        self.assertEqual(result[1]["tool"], "tool2")

    def test_extract_tool_calls_with_text(self):
        """Test extracting JSON object tool calls mixed with text."""
        # Test with JSON objects embedded in text
        llm_response = (
            "I'll use a tool to help you. "
            '{"tool": "search", "arguments": {"query": "python unittest"}} '
            "Let me process this for you."
        )
        result = self.session._extract_tool_calls(llm_response)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool"], "search")
        self.assertEqual(result[0]["arguments"]["query"], "python unittest")

    def test_extract_tool_calls_invalid_json(self):
        """Test handling of invalid JSON in response."""
        # Test with invalid JSON
        llm_response = "This is not a valid JSON response."
        result = self.session._extract_tool_calls(llm_response)

        self.assertEqual(len(result), 0)

    def test_extract_tool_calls_missing_fields(self):
        """Test handling of JSON missing required fields."""
        # Test with JSON missing required fields
        llm_response = '{"not_tool": "test_tool", "not_arguments": {"arg1": "value1"}}'
        result = self.session._extract_tool_calls(llm_response)

        self.assertEqual(len(result), 0)

    def test_extract_tool_calls_nested_json(self):
        """Test extracting tool calls with nested JSON arguments."""
        # Test with nested JSON in arguments
        llm_response = """
{"tool": "complex_tool", "arguments": {"nested": {"key1": "value1", "key2": 42}}}
"""
        result = self.session._extract_tool_calls(llm_response)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool"], "complex_tool")
        self.assertEqual(result[0]["arguments"]["nested"]["key1"], "value1")
        self.assertEqual(result[0]["arguments"]["nested"]["key2"], 42)

    def test_format_tool_results(self):
        """Test formatting of tool results."""
        tool_calls = [
            ToolCall(
                tool="tool1",
                arguments={"arg1": "value1"},
                result="Success result",
                error=None,
            ),
            ToolCall(
                tool="tool2",
                arguments={"arg2": "value2"},
                result=None,
                error="Error message",
            ),
        ]

        result = self.session._format_tool_results(tool_calls)

        # Check if the result contains expected substrings
        self.assertIn("Tool Call 1:", result)
        self.assertIn("Tool Name: tool1", result)
        self.assertIn("- Arguments: {", result)
        self.assertIn('"arg1": "value1"', result)
        self.assertIn("- Tool call result: Success result", result)
        self.assertIn("Tool Call 2:", result)
        self.assertIn("Tool Name: tool2", result)
        self.assertIn("- Arguments: {", result)
        self.assertIn('"arg2": "value2"', result)
        self.assertIn("- Tool call error: Error message", result)


if __name__ == "__main__":
    unittest.main()
