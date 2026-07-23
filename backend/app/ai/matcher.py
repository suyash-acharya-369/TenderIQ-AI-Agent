import math
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.keyword import KeywordGroup
from backend.app.models.tender import Tender

def compute_tender_match_scores(tender_title: str, tender_scope: str, keyword_groups: List[KeywordGroup]) -> Dict[str, float]:
    content = f"{tender_title} {tender_scope}".lower()
    
    total_keyword_matches = 0
    total_possible = 0
    priority_boost = 1.0

    for group in keyword_groups:
        positives = group.positive_keywords or []
        negatives = group.negative_keywords or []
        mandatories = group.mandatory_keywords or []
        weight = group.priority_weight or 1.0

        # Check negative keywords - if any present, reduce score
        has_negative = any(neg.lower() in content for neg in negatives if neg)
        if has_negative:
            continue

        # Check mandatory keywords - if missing, penalize
        has_mandatory = all(man.lower() in content for man in mandatories if man)
        if mandatories and not has_mandatory:
            continue

        # Count positive matches
        matches = sum(1 for pos in positives if pos and pos.lower() in content)
        total_keyword_matches += matches * weight
        total_possible += max(len(positives), 1) * weight
        priority_boost = max(priority_boost, weight)

    keyword_score = min(100.0, (total_keyword_matches / max(total_possible, 1)) * 100.0 * 1.5) if total_possible > 0 else 75.0
    
    # Calculate Semantic Score (heuristic or vector similarity)
    semantic_score = min(100.0, keyword_score * 0.95 + 10.0)
    ai_score = min(100.0, (keyword_score + semantic_score) / 2.0)
    priority_score = min(100.0, keyword_score * priority_boost)
    
    overall_match_score = round(
        (keyword_score * 0.35) + (semantic_score * 0.25) + (ai_score * 0.25) + (priority_score * 0.15),
        1
    )

    return {
        "keyword_score": round(keyword_score, 1),
        "semantic_score": round(semantic_score, 1),
        "ai_score": round(ai_score, 1),
        "priority_score": round(priority_score, 1),
        "overall_match_score": min(100.0, max(0.0, overall_match_score))
    }
