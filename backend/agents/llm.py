import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Tuple, Dict, Any

load_dotenv()

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def call(self, system_prompt: str, user_prompt: str) -> Tuple[str, Dict[str, int]]:
        """
        Returns (content, usage_info)
        usage_info = {"prompt_tokens": int, "completion_tokens": int}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={ "type": "json_object" } if "JSON" in system_prompt else { "type": "text" }
            )
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
            return content, usage
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return "ERROR", {"prompt_tokens": 0, "completion_tokens": 0}
