import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class GPT4Client:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4",
        max_tokens: int = 300,
        temperature: float = 0.3,
    ) -> str:
        """
        Send messages to GPT-4 and get a text response.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The model to use (default: gpt-4)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 to 1.0)

        Returns:
            String response from GPT-4
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"GPT-4 API error: {e!s}"

    def simple_json(self, prompt: str) -> dict:
        """
        Send a prompt to GPT-4 and get a JSON response with retry logic.

        Args:
            prompt: The prompt to send to GPT-4

        Returns:
            Dict containing the parsed JSON response
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that responds in valid JSON format only.",
            },
            {"role": "user", "content": prompt},
        ]

        # First attempt with gpt-4
        response = self.chat(messages=messages, model="gpt-4")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print("⚠️ GPT-4 JSON parsing failed, retrying with gpt-4-turbo...")

            # Retry with gpt-4-turbo
            retry_response = self.chat(messages=messages, model="gpt-4-turbo")

            try:
                return json.loads(retry_response)
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse JSON after retry",
                    "gpt4_raw": response,
                    "turbo_raw": retry_response,
                }
