import re
import logging
from typing import Dict, Any

logger = logging.getLogger("TenderIQ.RegexExtractor")

class RegexExtractor:
    @staticmethod
    def extract_all(text: str) -> Dict[str, Any]:
        """Extract structured fields using robust regex heuristics (Zero Hallucination)."""
        results = {}
        
        # 1. RFP/Tender Number extraction
        rfp_match = re.search(r'(RFP|Tender No|Reference No|Bid No)[\s\.:-]+([A-Z0-9/-]+)', text, re.IGNORECASE)
        if rfp_match:
            results["tender_number"] = {
                "value": rfp_match.group(2).strip(),
                "confidence": 0.85,
                "method": "Regex"
            }
            
        # 2. Budget extraction (INR or USD)
        budget_match = re.search(r'(Budget|Estimated Cost|Value)[\s\.:-]+(INR|Rs|USD|\$)?\s*([\d,]+(\.\d{1,2})?)\s*(Lakhs|Crores|Million)?', text, re.IGNORECASE)
        if budget_match:
            val_str = budget_match.group(3).replace(',', '')
            multiplier = 1
            suffix = (budget_match.group(5) or "").lower()
            if "lakh" in suffix:
                multiplier = 100000
            elif "crore" in suffix:
                multiplier = 10000000
            elif "million" in suffix:
                multiplier = 1000000
                
            try:
                numeric_val = float(val_str) * multiplier
                results["budget"] = {
                    "value": numeric_val,
                    "confidence": 0.75,
                    "method": "Regex"
                }
            except ValueError:
                pass
                
        # 3. Deadline extraction
        deadline_match = re.search(r'(Deadline|Closing Date|Submission Date|Last Date)[\s\.:-]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text, re.IGNORECASE)
        if deadline_match:
            results["submission_deadline"] = {
                "value": deadline_match.group(2),
                "confidence": 0.90,
                "method": "Regex"
            }
            
        return results
