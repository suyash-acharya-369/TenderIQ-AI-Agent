import math
import re
from typing import Dict, List, Set, Optional
from backend.app.models.keyword import KeywordGroup

def _tokenize(text: str) -> Set[str]:
    """Tokenize text into lowercase alphanumeric word tokens."""
    return set(re.findall(r'\b[a-z0-9]+\b', text.lower()))

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vector embeddings."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot_product / (norm1 * norm2)

def compute_tender_match_scores(
    tender_title: str,
    tender_scope: str,
    keyword_groups: List[KeywordGroup],
    tender_embedding: Optional[List[float]] = None,
    query_embedding: Optional[List[float]] = None
) -> Dict[str, float]:
    content = f"{tender_title} {tender_scope}".lower()
    content_tokens = _tokenize(content)
    
    total_keyword_matches = 0
    total_possible = 0
    priority_boost = 1.0
    has_global_negative = False

    all_positive_keywords = []

    for group in keyword_groups:
        positives = group.positive_keywords or []
        negatives = group.negative_keywords or []
        mandatories = group.mandatory_keywords or []
        weight = group.priority_weight or 1.0

        all_positive_keywords.extend(positives)

        # Check negative keywords - if present, flag negative penalty
        if any(neg.lower() in content for neg in negatives if neg and len(neg) > 2):
            has_global_negative = True
            continue

        # Check mandatory keywords - if missing, skip group
        has_mandatory = all(man.lower() in content for man in mandatories if man)
        if mandatories and not has_mandatory:
            continue

        # Count positive matches
        matches = sum(1 for pos in positives if pos and pos.lower() in content)
        total_keyword_matches += matches * weight
        total_possible += max(len(positives), 1) * weight
        priority_boost = max(priority_boost, weight)

    keyword_score = min(100.0, (total_keyword_matches / max(total_possible, 1)) * 100.0 * 1.5) if total_possible > 0 else 75.0
    
    # Calculate Semantic Score using vector embedding cosine similarity OR token Jaccard overlap
    if tender_embedding and query_embedding:
        sim = _cosine_similarity(tender_embedding, query_embedding)
        semantic_score = round(sim * 100.0, 1)
    else:
        # Token Jaccard similarity between content and positive keyword corpus
        keyword_tokens = _tokenize(" ".join(all_positive_keywords))
        if keyword_tokens and content_tokens:
            intersection = content_tokens.intersection(keyword_tokens)
            union = content_tokens.union(keyword_tokens)
            jaccard = len(intersection) / max(len(union), 1)
            semantic_score = min(100.0, (jaccard * 250.0) + (keyword_score * 0.6))
        else:
            semantic_score = round(keyword_score * 0.9, 1)

    # Negative keyword penalty deduction
    if has_global_negative:
        keyword_score *= 0.2
        semantic_score *= 0.2

    ai_score = min(100.0, (keyword_score + semantic_score) / 2.0)
    priority_score = min(100.0, keyword_score * priority_boost)
    
    overall_match_score = round(
        (keyword_score * 0.35) + (semantic_score * 0.25) + (ai_score * 0.25) + (priority_score * 0.15),
        1
    )

    return {
        "keyword_score": round(keyword_score, 1),
        "semantic_score": round(min(100.0, max(0.0, semantic_score)), 1),
        "ai_score": round(ai_score, 1),
        "priority_score": round(priority_score, 1),
        "overall_match_score": min(100.0, max(0.0, overall_match_score))
    }
