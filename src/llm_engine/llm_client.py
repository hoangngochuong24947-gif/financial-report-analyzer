"""DeepSeek LLM client (direct HTTP call, no OpenAI/LangChain dependency)."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from src.config.settings import settings
from src.utils.logger import logger


class LLMClient:
    """LLM client backed by DeepSeek Chat Completions API."""

    def __init__(self) -> None:
        if not settings.deepseek_api_key:
            logger.warning("DEEPSEEK_API_KEY is not set. LLM features will be unavailable.")

        self._api_base = settings.deepseek_api_base.rstrip("/")
        self._model = settings.deepseek_model or "deepseek-chat"
        logger.info(
            "LLMClient initialized with DeepSeek API: "
            f"model={self._model}, base_url={self._api_base}"
        )

    def analyze(self, prompt: str, system_prompt: str = "") -> str:
        """Send a prompt to DeepSeek and return text response."""
        if not settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured.")

        messages: List[Dict[str, str]] = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.info(f"Sending prompt to DeepSeek ({len(prompt)} chars)...")
            response_json = self._chat_completion(messages=messages)
            result = self._extract_content(response_json)
            logger.info(f"DeepSeek response received ({len(result)} chars)")
            logger.debug(f"DeepSeek response preview: {result[:200]}...")
            return result
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"LLM analysis failed: {e}") from e

    def _chat_completion(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        url = f"{self._api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _extract_content(response_json: Dict[str, Any]) -> str:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Invalid DeepSeek response: missing choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise RuntimeError("Invalid DeepSeek response: malformed first choice")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Invalid DeepSeek response: missing message")

        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts: List[str] = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        texts.append(text)
            if texts:
                return "\n".join(texts)

        raise RuntimeError("Invalid DeepSeek response: empty content")


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get process-wide singleton client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
