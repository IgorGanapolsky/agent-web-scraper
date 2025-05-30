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
        Send a prompt to GPT-4 and get a JSON response.

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

        response = self.chat(messages=messages)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response}
