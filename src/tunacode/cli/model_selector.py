"""Interactive model selector with modern UI."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from tunacode.configuration.models import ModelRegistry
from tunacode.types import ModelName


class ModelProvider(Enum):
    """Model providers with their display names."""

    ANTHROPIC = ("anthropic", "Anthropic", "🤖")
    OPENAI = ("openai", "OpenAI", "🧠")
    GOOGLE = ("google-gla", "Google", "🌐")
    OPENROUTER = ("openrouter", "OpenRouter", "🚀")


@dataclass
class ModelInfo:
    """Enhanced model information."""

    id: ModelName
    provider: ModelProvider
    display_name: str
    short_name: str
    description: str
    cost_tier: str  # low, medium, high, premium


class ModelSelector:
    """Enhanced model selection with categorization and search."""

    def __init__(self):
        self.registry = ModelRegistry()
        self.models = self._build_model_info()

    def _build_model_info(self) -> List[ModelInfo]:
        """Build enhanced model information with metadata."""
        models = []

        # Model metadata mapping
        model_metadata = {
            # Anthropic models
            "anthropic:claude-opus-4-20250514": (
                "Claude Opus 4",
                "opus-4",
                "Most capable Claude model",
                "high",
            ),
            "anthropic:claude-sonnet-4-20250514": (
                "Claude Sonnet 4",
                "sonnet-4",
                "Balanced performance",
                "medium",
            ),
            "anthropic:claude-3-7-sonnet-latest": (
                "Claude 3.7 Sonnet",
                "sonnet-3.7",
                "Previous generation",
                "medium",
            ),
            # Google models
            "google-gla:gemini-2.0-flash": (
                "Gemini 2.0 Flash",
                "flash-2.0",
                "Fast and efficient",
                "low",
            ),
            "google-gla:gemini-2.5-flash-preview-05-20": (
                "Gemini 2.5 Flash",
                "flash-2.5",
                "Latest preview",
                "low",
            ),
            "google-gla:gemini-2.5-pro-preview-05-06": (
                "Gemini 2.5 Pro",
                "pro-2.5",
                "Most capable Gemini",
                "medium",
            ),
            # OpenAI models
            "openai:gpt-4.1": ("GPT-4.1", "gpt-4.1", "Latest GPT-4", "medium"),
            "openai:gpt-4.1-mini": ("GPT-4.1 Mini", "4.1-mini", "Efficient GPT-4", "low"),
            "openai:gpt-4.1-nano": ("GPT-4.1 Nano", "4.1-nano", "Smallest GPT-4", "low"),
            "openai:gpt-4o": ("GPT-4o", "gpt-4o", "Optimized GPT-4", "medium"),
            "openai:o3": ("O3", "o3", "Advanced reasoning", "premium"),
            "openai:o3-mini": ("O3 Mini", "o3-mini", "Efficient reasoning", "high"),
            # OpenRouter models
            "openrouter:mistralai/devstral-small": (
                "Devstral Small",
                "devstral",
                "Code-focused",
                "low",
            ),
            "openrouter:codex-mini-latest": ("Codex Mini", "codex", "Code completion", "medium"),
            "openrouter:o4-mini-high": ("O4 Mini High", "o4-high", "Enhanced O4", "high"),
            "openrouter:o3": ("O3 (OpenRouter)", "o3-or", "O3 via OpenRouter", "premium"),
            "openrouter:o4-mini": ("O4 Mini", "o4-mini", "Standard O4", "high"),
            "openrouter:openai/gpt-4.1": (
                "GPT-4.1 (OR)",
                "gpt-4.1-or",
                "GPT-4.1 via OpenRouter",
                "medium",
            ),
            "openrouter:openai/gpt-4.1-mini": (
                "GPT-4.1 Mini (OR)",
                "4.1-mini-or",
                "GPT-4.1 Mini via OpenRouter",
                "low",
            ),
        }

        for model_id in self.registry.list_model_ids():
            provider = self._get_provider(model_id)
            if provider and model_id in model_metadata:
                display_name, short_name, description, cost_tier = model_metadata[model_id]
                models.append(
                    ModelInfo(
                        id=model_id,
                        provider=provider,
                        display_name=display_name,
                        short_name=short_name,
                        description=description,
                        cost_tier=cost_tier,
                    )
                )

        return models

    def _get_provider(self, model_id: str) -> Optional[ModelProvider]:
        """Get provider from model ID."""
        for provider in ModelProvider:
            if model_id.startswith(provider.value[0]):
                return provider
        return None

    def get_models_by_provider(self) -> Dict[ModelProvider, List[ModelInfo]]:
        """Group models by provider."""
        grouped = {provider: [] for provider in ModelProvider}
        for model in self.models:
            if model.provider:
                grouped[model.provider].append(model)
        return grouped

    def find_model(self, query: str) -> Optional[ModelInfo]:
        """Find model by index, name, or fuzzy match."""
        query = query.lower().strip()

        # Try as index first
        try:
            index = int(query)
            if 0 <= index < len(self.models):
                return self.models[index]
        except ValueError:
            pass

        # Exact match on ID
        for model in self.models:
            if model.id.lower() == query:
                return model

        # Match on short name
        for model in self.models:
            if model.short_name.lower() == query:
                return model

        # Fuzzy match on display name or short name
        for model in self.models:
            if query in model.display_name.lower() or query in model.short_name.lower():
                return model

        return None

    def get_cost_emoji(self, cost_tier: str) -> str:
        """Get emoji representation of cost tier."""
        return {"low": "💚", "medium": "💛", "high": "🧡", "premium": "❤️"}.get(cost_tier, "⚪")
