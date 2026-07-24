import logging
from backend.app.config import settings
from backend.app.ai.provider import BaseAIProvider
from backend.app.ai.openai_provider import OpenAIProvider

logger = logging.getLogger("TenderIQ.AI.Router")

def get_ai_provider(provider_name: str = None) -> BaseAIProvider:
    provider = (provider_name or settings.DEFAULT_AI_PROVIDER or "openai").lower()
    
    if provider in ["openai", "openrouter", "gpt-4o", "gpt-4o-mini"]:
        return OpenAIProvider()
    
    logger.info(f"Requested AI provider '{provider}' defaulting to OpenAI/OpenRouter Provider.")
    return OpenAIProvider()
