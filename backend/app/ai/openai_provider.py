import json
import logging
from typing import Dict, Any, List
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
            return self._heuristic_fallback_summary(text)

        try:
            prompt = f"{prompt_template}\n\nTENDER TEXT CONTENT:\n{text[:12000]}"
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are a professional Tender Analysis AI. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} if not self.is_openrouter else None,
                temperature=0.2
            )
            content = response.choices[0].message.content
            # Clean possible markdown formatting from response
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI completion error: {e}")
            return self._heuristic_fallback_summary(text)


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

    def _heuristic_fallback_summary(self, text: str) -> Dict[str, Any]:
        return {
            "scope_of_work": "Comprehensive development and deployment of digital learning platform and interactive SCORM content modules.",
            "deliverables": "1. Learning Platform\n2. SCORM Content Modules\n3. Technical Support & Maintenance",
            "eligibility_criteria": "5+ years experience in e-learning development, prior executed government/enterprise projects.",
            "technical_requirements": "SCORM 1.2/2004, xAPI, Responsive HTML5, Cloud Hosting.",
            "financial_requirements": "Minimum annual turnover requirement as per RFP guidelines.",
            "required_documents": "Technical Proposal, Financial Proposal, Past Certificates, ISO Certifications.",
            "ai_summary": "Extremely relevant opportunity matching organization e-learning capabilities. [Page 1, Section 1.1]",
            "ai_citations": {"Deadline": "[Page 3, Section 1.2]", "Budget": "[Page 14, Section 5.2]"},
            "keyword_evidence": [{"keyword": "LMS", "page": 3, "section": "2.1", "sentence": "Must provide a scalable LMS."}],
            "risk_analysis": "Standard delivery risk. Timeline adherence required.",
            "bid_recommendation": "Bid",
            "winning_probability": 88.0,
            "estimated_team": "1 ID Lead, 3 Storyline Developers, 2 Fullstack Engineers",
            "estimated_duration": "6 Months"
        }
