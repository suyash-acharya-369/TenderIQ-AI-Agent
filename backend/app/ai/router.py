from backend.app.config import settings
from backend.app.ai.provider import BaseAIProvider
from backend.app.ai.openai_provider import OpenAIProvider

def get_ai_provider(provider_name: str = None) -> BaseAIProvider:
    provider = provider_name or settings.DEFAULT_AI_PROVIDER
    # Default to OpenAI Provider (which handles fallback automatically if API key is not configured)
    return OpenAIProvider()
