from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> str:
        """Send a prompt to the AI provider and return the text response."""
        pass

    def generate_json(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Send a prompt and expect a JSON response."""
        response = self.complete(prompt, **kwargs)
        try:
            # Basic cleanup in case of markdown blocks
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            raise AIProviderError(f"Failed to parse AI response as JSON: {e}\nResponse: {response}")


class LocalProvider(BaseAIProvider):
    """Provider for local LLMs (e.g., Ollama)."""

    def complete(self, prompt: str, **kwargs: Any) -> str:
        # Implementation for Ollama or similar
        # For now, this is a placeholder that would use httpx
        import httpx

        url = self.base_url or "http://localhost:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "")
        except Exception as e:
            raise AIProviderError(f"Local provider error: {e}")


class OpenRouterProvider(BaseAIProvider):
    """Provider for OpenRouter API."""

    def complete(self, prompt: str, **kwargs: Any) -> str:
        import httpx

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/maie-ai/maie",
            "X-Title": "MAIE",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise AIProviderError(f"OpenRouter provider error: {e}")


class HuggingFaceProvider(BaseAIProvider):
    """Provider for Hugging Face Inference API."""

    def complete(self, prompt: str, **kwargs: Any) -> str:
        import httpx

        url = f"https://api-inference.huggingface.co/models/{self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt, "parameters": kwargs}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                # HF returns a list for text generation models
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                return str(result)
        except Exception as e:
            raise AIProviderError(f"HuggingFace provider error: {e}")
