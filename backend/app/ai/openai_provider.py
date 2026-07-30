import json
import logging
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.ai.provider import BaseAIProvider

logger = logging.getLogger("TenderIQ.AI.OpenAI")

class OpenAIProvider(BaseAIProvider):
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY
        self.is_openrouter = bool(self.api_key and (self.api_key.startswith("sk-or-v1-") or settings.OPENROUTER_API_KEY))
        self.base_url = "https://openrouter.ai/api/v1" if self.is_openrouter else None
        self.default_model = "openai/gpt-4o-mini" if self.is_openrouter else "gpt-4o-mini"
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self.client = OpenAI(**kwargs)
                logger.info(f"Initialized AI client (OpenRouter={self.is_openrouter}, model={self.default_model})")
            except Exception as e:
                logger.warning(f"AI client initialization failed: {e}")

    def generate_summary(self, text: str, prompt_template: Optional[str] = None) -> Dict[str, Any]:
        if not self.client:
            return self._heuristic_fallback_summary()

        try:
            # V3.1 Zero Hallucination Guardrails
            system_prompt = (
                "You are an Enterprise Procurement AI. "
                "CRITICAL RULE: NEVER fabricate or infer missing information. "
                "If a field cannot be definitively verified from the provided text, you MUST output strictly: 'Not Available on Official Source'. "
                "Do not guess. Do not estimate. Provide exact text citations."
            )
            prompt = f"{prompt_template}\n\nTENDER TEXT CONTENT:\n{text[:12000]}"
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} if not self.is_openrouter else None,
                temperature=0.0
            )
            content = response.choices[0].message.content
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI completion error: {e}")
            return self._heuristic_fallback_summary()

    def generate_embeddings(self, text: str) -> List[float]:
        if not self.client:
            return [0.0] * 1536
        try:
            response = self.client.embeddings.create(
                input=text[:8000],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return [0.0] * 1536

    def _heuristic_fallback_summary(self) -> Dict[str, Any]:
        """V3.1 Zero Hallucination: If AI fails, fallback returns safe empty values, never fake text."""
        return {
            "executive_summary": "Not Available on Official Source",
            "scope_of_work": "Not Available on Official Source",
            "deliverables": "Not Available on Official Source",
            "eligibility_criteria": "Not Available on Official Source",
            "technical_requirements": "Not Available on Official Source",
            "financial_requirements": "Not Available on Official Source",
            "required_documents": "Not Available on Official Source",
            "ai_citations": {},
            "keyword_evidence": [],
            "risk_analysis": "Not Available on Official Source",
            "bid_recommendation": "Review",
            "winning_probability": 0.0,
            "estimated_team": "Not Available on Official Source",
            "estimated_duration": "Not Available on Official Source"
        }
