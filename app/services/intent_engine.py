"""
Intent Engine
=============
Manages per-company intent scoring using the InferenceEngine.
Provides an in-memory index for fast lookups and batch rescoring.
"""
from typing import Dict, List, Optional
from app.services.inference_engine import analyze_signals, IntentResult


class IntentEngine:
    """
    Orchestrates intent scoring for companies.
    Maintains a lightweight in-memory score index.
    """

    def __init__(self):
        self._index: Dict[int, IntentResult] = {}  # company_id → IntentResult

    def score_company(self,
                      company_id: int,
                      signal_texts: List[str],
                      company_name: str = "",
                      industry: Optional[str] = None) -> IntentResult:
        """
        Run inference on a company's signals and cache the result.
        """
        result = analyze_signals(signal_texts, company_name, industry)
        self._index[company_id] = result
        return result

    def get_score(self, company_id: int) -> Optional[IntentResult]:
        """Retrieve cached score for a company."""
        return self._index.get(company_id)

    def update_index(self, company_id: int, result: IntentResult):
        """Manually update index with a pre-computed result."""
        self._index[company_id] = result

    def batch_score(self,
                    companies: List[Dict]) -> Dict[int, IntentResult]:
        """
        Score multiple companies.
        Each dict must have: id, signals (list of str), name, industry.
        """
        results = {}
        for c in companies:
            result = self.score_company(
                company_id=c["id"],
                signal_texts=c.get("signals", []),
                company_name=c.get("name", ""),
                industry=c.get("industry")
            )
            results[c["id"]] = result
        return results

    def top_leads(self, n: int = 20, min_score: float = 0.5) -> List[Dict]:
        """Return top N leads from the in-memory index above a threshold."""
        ranked = [
            {"company_id": cid, "overall_intent": r.overall_intent,
             "scores": r.to_score_dict()}
            for cid, r in self._index.items()
            if r.overall_intent >= min_score
        ]
        return sorted(ranked, key=lambda x: x["overall_intent"], reverse=True)[:n]


# Module-level singleton
_intent_engine = IntentEngine()


def get_intent_engine() -> IntentEngine:
    return _intent_engine