import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class GPT4Client:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def simple_json(self, prompt: str) -> dict[str, Any]:
        """
        Send a prompt to GPT-4 and get a JSON response.

        Args:
            prompt: The prompt to send to GPT-4

        Returns:
            Dict containing the parsed JSON response
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant that responds in valid JSON format only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return a structured error
                return {
                    "pain_point_label": "Parse Error",
                    "root_cause_explanation": f"Failed to parse GPT-4 response: {content[:100]}...",
                }

        except Exception as e:
            return {
                "pain_point_label": "API Error",
                "root_cause_explanation": f"GPT-4 API error: {e!s}",
            }
