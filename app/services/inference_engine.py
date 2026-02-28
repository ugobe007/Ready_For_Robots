"""
Inference Engine
================
Forward-chaining rule engine that reasons over semantic parse results
to produce final robotics-fit intent scores.

Pipeline:
  text(s)
    → SemanticParser.parse()     # concept activations
    → InferenceEngine.infer()    # apply rules, compute domain scores
    → IntentResult               # structured output with explanations
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.services.semantic_parser import SemanticParser, ParseResult
from app.services.ontology import (
    INFERENCE_RULES, InferenceRule, get_industry_prior
)


# ──────────────────────────────────────────────
# Output types
# ──────────────────────────────────────────────
@dataclass
class FiredRule:
    rule_name: str
    description: str
    conclusion_domain: str
    boost: float
    conditions_met: List[str]


@dataclass
class IntentResult:
    # Raw domain scores from parser (0–1)
    automation_score: float = 0.0
    labor_pain_score:  float = 0.0
    expansion_score:   float = 0.0
    industry_fit_score: float = 0.0

    # Post-inference boosts applied
    fired_rules: List[FiredRule] = field(default_factory=list)

    # Final scores after rule boosts (0–100 for API compat)
    final_automation:   float = 0.0
    final_labor_pain:   float = 0.0
    final_expansion:    float = 0.0
    final_industry_fit: float = 0.0
    overall_intent:     float = 0.0

    # Top activated concepts for UI explainability
    activated_concepts: List[Dict] = field(default_factory=list)

    def to_score_dict(self) -> Dict[str, float]:
        """Returns dict compatible with Score ORM model (0–100 scale)."""
        return {
            "automation_score":    round(self.final_automation * 100, 2),
            "labor_pain_score":    round(self.final_labor_pain * 100, 2),
            "expansion_score":     round(self.final_expansion * 100, 2),
            "robotics_fit_score":  round(self.final_industry_fit * 100, 2),
            "overall_intent_score": round(self.overall_intent * 100, 2),
        }

    def to_api_dict(self) -> Dict:
        """Full API response with explanations."""
        return {
            **self.to_score_dict(),
            "fired_rules": [
                {
                    "rule": r.rule_name,
                    "description": r.description,
                    "boost_domain": r.conclusion_domain,
                    "boost": r.boost,
                    "conditions_met": r.conditions_met,
                }
                for r in self.fired_rules
            ],
            "activated_concepts": self.activated_concepts,
        }


# ──────────────────────────────────────────────
# Inference Engine
# ──────────────────────────────────────────────
class InferenceEngine:
    """
    Applies ontological inference rules to ParseResults.

    Usage:
        engine = InferenceEngine()
        result = engine.infer("expanding our warehouse, can't find enough staff")
        print(result.overall_intent)       # e.g. 0.78
        print(result.to_api_dict())
    """

    # Cap on total rule boosts per domain to prevent runaway scores
    MAX_BOOST_PER_DOMAIN = 0.50
    # Weights for final score combination
    WEIGHTS = {
        "automation":   0.30,
        "labor_pain":   0.25,
        "expansion":    0.20,
        "industry_fit": 0.25,
    }

    def __init__(self):
        self._parser = SemanticParser()

    # ── Public API ──────────────────────────────────────────────
    def infer(self, text: str, industry: Optional[str] = None) -> IntentResult:
        """Infer intent from a single text string."""
        parse = self._parser.parse(text)
        return self._run_inference(parse, industry)

    def infer_multi(self, texts: List[str], industry: Optional[str] = None) -> IntentResult:
        """Infer intent from multiple text fragments (job desc + news + about page)."""
        parse = self._parser.parse_multi(texts)
        return self._run_inference(parse, industry)

    def infer_from_signals(self,
                            signal_texts: List[str],
                            company_name: str = "",
                            industry: Optional[str] = None) -> IntentResult:
        """
        Convenience method for scoring a company from its collected signals.
        Merges all signal texts then runs inference.
        """
        all_text = f"{company_name} {industry or ''} " + " ".join(signal_texts)
        return self.infer(all_text, industry=industry)

    # ── Private logic ───────────────────────────────────────────
    def _run_inference(self, parse: ParseResult, industry: Optional[str]) -> IntentResult:
        result = IntentResult()

        # 1. Base domain scores from parser
        result.automation_score   = parse.domain_score("automation")
        result.labor_pain_score   = parse.domain_score("labor_pain")
        result.expansion_score    = parse.domain_score("expansion")
        result.industry_fit_score = parse.domain_score("industry_fit")

        # 2. Apply industry prior if explicit industry provided
        if industry:
            prior = get_industry_prior(industry)
            result.industry_fit_score = max(result.industry_fit_score, prior)

        # 3. Forward-chain rules
        boosts = {
            "automation": 0.0,
            "labor_pain": 0.0,
            "expansion":  0.0,
            "industry_fit": 0.0,
        }
        active = set(parse.active_concepts(min_confidence=0.25))

        for rule in INFERENCE_RULES:
            # Check if ALL conditions are met
            if all(cond in active for cond in rule.conditions):
                domain = rule.conclusion_domain
                current_boost = boosts.get(domain, 0.0)
                if current_boost < self.MAX_BOOST_PER_DOMAIN:
                    actual_boost = min(rule.boost,
                                       self.MAX_BOOST_PER_DOMAIN - current_boost)
                    boosts[domain] = current_boost + actual_boost
                    result.fired_rules.append(FiredRule(
                        rule_name=rule.name,
                        description=rule.description,
                        conclusion_domain=domain,
                        boost=actual_boost,
                        conditions_met=list(rule.conditions),
                    ))

        # 4. Apply boosts (noisy-OR style: don't just add linearly)
        result.final_automation   = self._apply_boost(result.automation_score,   boosts["automation"])
        result.final_labor_pain   = self._apply_boost(result.labor_pain_score,   boosts["labor_pain"])
        result.final_expansion    = self._apply_boost(result.expansion_score,    boosts["expansion"])
        result.final_industry_fit = self._apply_boost(result.industry_fit_score, boosts["industry_fit"])

        # 5. Weighted overall intent
        result.overall_intent = round(
            result.final_automation   * self.WEIGHTS["automation"]
            + result.final_labor_pain   * self.WEIGHTS["labor_pain"]
            + result.final_expansion    * self.WEIGHTS["expansion"]
            + result.final_industry_fit * self.WEIGHTS["industry_fit"],
            4
        )

        # 6. Top concepts for explainability
        result.activated_concepts = [
            {
                "concept":    a.concept_name,
                "domain":     a.domain,
                "confidence": a.confidence,
                "propagated": a.propagated,
            }
            for a in parse.top_concepts(8)
        ]

        return result

    @staticmethod
    def _apply_boost(base: float, boost: float) -> float:
        """Add boost using noisy-OR: 1 - (1-base)(1-boost)."""
        result = 1.0 - (1.0 - base) * (1.0 - boost)
        return round(min(result, 1.0), 4)


# ──────────────────────────────────────────────
# Module-level singleton
# ──────────────────────────────────────────────
_engine = InferenceEngine()


def analyze(text: str, industry: str = None) -> IntentResult:
    return _engine.infer(text, industry=industry)


def analyze_signals(signal_texts: List[str],
                    company_name: str = "",
                    industry: str = None) -> IntentResult:
    return _engine.infer_from_signals(signal_texts, company_name, industry)
