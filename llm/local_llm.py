"""Optional Ollama adapter. The deterministic planner remains usable without Ollama."""

from __future__ import annotations

import json
from typing import Any


class LocalLLMAdapter:
    def __init__(self, model_name: str = "llama3.1:8b", client: Any = None) -> None:
        self.model_name = model_name
        self._client = client

    def _ollama(self) -> Any:
        if self._client is None:
            try:
                import ollama
            except ImportError as error:
                raise RuntimeError("Ollama is not installed; use the deterministic planner fallback") from error
            self._client = ollama
        return self._client

    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        messages = ([{"role": "system", "content": system_prompt}] if system_prompt else [])
        messages.append({"role": "user", "content": prompt})
        try:
            response = self._ollama().chat(model=self.model_name, messages=messages, **kwargs)
            return response["message"]["content"]
        except Exception as error:
            raise RuntimeError(f"Local LLM inference failed: {error}") from error

    def generate_structured(self, prompt: str, output_schema: dict[str, Any], system_prompt: str | None = None) -> dict:
        response = self.generate(
            f"{prompt}\nReturn only JSON matching this schema:\n{json.dumps(output_schema)}",
            system_prompt,
            format="json",
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Local LLM returned invalid JSON: {error}") from error

    def plan_task(self, task_description: str, context: dict[str, Any]) -> dict:
        return self.generate_structured(
            f"Plan this task: {task_description}\nContext: {json.dumps(context)}",
            {"type": "object", "required": ["task_id", "description", "steps", "context"]},
            "Create a verifiable, idempotent task plan.",
        )


local_llm = LocalLLMAdapter()
