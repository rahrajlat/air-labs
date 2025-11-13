from typing import Iterable
from .base import LLMBackend
import os

class OpenAIBackend(LLMBackend):
    def __init__(self):
        from openai import OpenAI
        self.model = os.getenv("OPEN_AI_MODEL", "gpt-4o-mini")
        self.base_url=os.getenv("OPENAI_BASE_URL")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI backend.")
        self.client = OpenAI(api_key=api_key, base_url=self.base_url or os.getenv("OPENAI_BASE_URL"))
        self.model = self.model 
        self.temperature = os.getenv("TEMPERATURE", 0.2)

    def generate(self, prompts: Iterable[str]) -> Iterable[str]:
        # one request per prompt to keep parity with Ollama backend
        for p in prompts:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=float(self.temperature),
                messages=[
                    {"role": "system", "content": "You write concise, factual data documentation for dbt models. Respond with plain text only."},
                    {"role": "user", "content": p},
                ],
            )
            yield (resp.choices[0].message.content or "").strip()