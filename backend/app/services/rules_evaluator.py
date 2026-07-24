import logging
from typing import Dict, Any, List
from backend.app.models.tender import Tender

logger = logging.getLogger("TenderIQ.RulesEvaluator")

def evaluate_condition(tender: Tender, condition_dict: Dict[str, Any]) -> bool:
    """
    Evaluates a single condition dictionary against a Tender object.
    Supports complex nested AND/OR logic.
    Example:
    {
        "condition": "AND",
        "rules": [
            {"field": "overall_match_score", "op": ">=", "val": 90},
            {"field": "submission_deadline", "op": "IS_NOT_NULL", "val": None}
        ]
    }
    """
    if not condition_dict:
        return True # Empty condition always passes
    
    # Check if it's a grouped condition
    if "condition" in condition_dict and "rules" in condition_dict:
        cond_type = condition_dict.get("condition", "AND").upper()
        rules = condition_dict.get("rules", [])
        
        if not rules:
            return True
            
        results = [evaluate_condition(tender, r) for r in rules]
        if cond_type == "AND":
            return all(results)
        elif cond_type == "OR":
            return any(results)
        else:
            logger.warning(f"Unknown condition type: {cond_type}")
            return False

    # Check if it's a single rule
    field = condition_dict.get("field")
    op = condition_dict.get("op")
    val = condition_dict.get("val")

    if not field or not op:
        return True
    
    # Dynamically get tender attribute safely
    tender_val = getattr(tender, field, None)

    try:
        if op == ">": return tender_val is not None and tender_val > val
        if op == ">=": return tender_val is not None and tender_val >= val
        if op == "<": return tender_val is not None and tender_val < val
        if op == "<=": return tender_val is not None and tender_val <= val
        if op == "==": return tender_val == val
        if op == "!=": return tender_val != val
        if op == "IN": return tender_val in val
        if op == "NOT_IN": return tender_val not in val
        if op == "IS_NULL": return tender_val is None
        if op == "IS_NOT_NULL": return tender_val is not None
        if op == "CONTAINS": return val and val.lower() in str(tender_val).lower() if tender_val else False
    except TypeError as e:
        logger.warning(f"Type error during evaluation of field {field} (val={tender_val}) against {val}: {e}")
        return False
        
    logger.warning(f"Unsupported operator {op} for field {field}")
    return False
