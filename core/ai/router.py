from __future__ import annotations

from typing import Any, Dict, Optional, Type

from config.settings import settings
from core.ai.provider import (
    BaseAIProvider,
    HuggingFaceProvider,
    LocalProvider,
    OpenRouterProvider,
)


class TaskRouter:
    """Routes tasks to specific AI providers based on configuration and task type."""

    def __init__(self, provider_overrides: Optional[Dict[str, str]] = None):
        self.provider_overrides = provider_overrides or {}
        self._providers: Dict[str, BaseAIProvider] = {}
        self._default_provider_name = settings.ai_provider

    def get_provider(self, task_name: Optional[str] = None) -> BaseAIProvider:
        """Get the appropriate provider for a given task."""
        provider_name = self.provider_overrides.get(task_name or "", self._default_provider_name)
        
        if provider_name not in self._providers:
            self._providers[provider_name] = self._create_provider(provider_name)
            
        return self._providers[provider_name]

    def _create_provider(self, name: str) -> BaseAIProvider:
        """Factory method to create a provider by name."""
        provider_classes: Dict[str, Type[BaseAIProvider]] = {
            "local": LocalProvider,
            "openrouter": OpenRouterProvider,
            "huggingface": HuggingFaceProvider,
        }
        
        provider_cls = provider_classes.get(name.lower())
        if not provider_cls:
            raise ValueError(f"Unknown AI provider: {name}")
            
        return provider_cls(
            model=settings.ai_model,
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            timeout=settings.ai_timeout,
            max_retries=settings.ai_max_retries,
        )

    def execute_task(self, task_name: str, prompt: str, **kwargs: Any) -> str:
        """Execute a task using the routed provider."""
        provider = self.get_provider(task_name)
        return provider.complete(prompt, **kwargs)

    def execute_json_task(self, task_name: str, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a task expecting a JSON response."""
        provider = self.get_provider(task_name)
        return provider.generate_json(prompt, **kwargs)
