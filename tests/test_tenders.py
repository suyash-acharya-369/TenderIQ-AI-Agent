from backend.app.ai.matcher import compute_tender_match_scores
from backend.app.models.keyword import KeywordGroup

def test_tender_match_scores():
    groups = [
        KeywordGroup(
            name="E-Learning Core",
            positive_keywords=["E-Learning", "LMS", "SCORM"],
            negative_keywords=["Hardware"],
            mandatory_keywords=["Learning"],
            priority_weight=1.5
        )
    ]
    scores = compute_tender_match_scores(
        "RFP for Learning Management System (LMS) and E-Learning Content",
        "Full turnkey deployment of SCORM compatible e-learning software.",
        groups
    )
    assert scores["overall_match_score"] > 80.0
    assert scores["keyword_score"] > 80.0
