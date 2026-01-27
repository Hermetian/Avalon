from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from ..config import SETTINGS


@dataclass
class LLMResult:
    text: str
    data: Dict[str, Any]


class LLMClient:
    def __init__(self, model_id: str | None = None) -> None:
        self.model_id = model_id or SETTINGS.qwen_model
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self) -> Tuple[Any, Any]:
        if self._model is None or self._tokenizer is None:
            from mlx_lm import load

            self._model, self._tokenizer = load(self.model_id)
        return self._model, self._tokenizer

    def generate_json(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> LLMResult:
        model, tokenizer = self._ensure_loaded()
        from mlx_lm import generate

        text = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temperature,
        )
        data = self._extract_json(text)
        return LLMResult(text=text, data=data)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("Model did not return JSON")
        return json.loads(match.group(0))
