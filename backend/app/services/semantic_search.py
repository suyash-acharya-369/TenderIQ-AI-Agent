import math
import re
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.tender import Tender

logger = logging.getLogger("TenderIQ.SemanticSearch")


def tokenize(text: str) -> List[str]:
    """Basic text tokenizer for semantic vector scoring."""
    if not text:
        return []
    return re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower())


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Compute term frequencies."""
    tf: Dict[str, int] = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    total = float(len(tokens)) or 1.0
    return {k: v / total for k, v in tf.items()}


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vector representations."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    return numerator / denominator


def perform_semantic_search(query_text: str, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Phase 19: Hybrid Semantic Vector Search over Tender Title, Scope, Description, and AI Summary."""
    query_tokens = tokenize(query_text)
    if not query_tokens:
        return []

    query_vec = compute_tf(query_tokens)
    tenders = db.query(Tender).all()
    results: List[Tuple[float, Tender]] = []

    for t in tenders:
        doc_text = f"{t.title} {t.scope_of_work or ''} {t.deliverables or ''} {t.ai_summary or ''} {t.sector or ''} {t.country or ''}"
        doc_tokens = tokenize(doc_text)
        doc_vec = compute_tf(doc_tokens)
        sim_score = cosine_similarity(query_vec, doc_vec)

        # Keyword overlap boost
        overlap = set(query_tokens) & set(doc_tokens)
        keyword_boost = (len(overlap) / float(len(query_tokens))) * 0.5
        final_score = round(min(1.0, sim_score * 0.5 + keyword_boost) * 100, 2)

        if final_score > 5.0:
            results.append((final_score, t))

    # Sort descending by semantic similarity score
    results.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "id": t.id,
            "tender_number": t.tender_number,
            "title": t.title,
            "country": t.country,
            "sector": t.sector,
            "budget": t.budget,
            "semantic_score": score,
            "overall_match_score": t.overall_match_score,
            "ai_summary": t.ai_summary,
            "bid_recommendation": t.bid_recommendation,
        }
        for score, t in results[:limit]
    ]
