"""
Semantic Parser
===============
Parses raw text strings into activated ontology concepts using:
  1. Regex pattern matching against CONCEPTS
  2. Synonym / surface-form matching (fuzzy)
  3. Relationship propagation (if concept A implies B, partially activate B)

Returns a ParseResult with activated concepts and their confidence scores.
"""
import re
import math
from difflib import SequenceMatcher
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

from app.services.ontology import CONCEPTS, RELATIONSHIPS, Concept


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────
@dataclass
class ConceptActivation:
    concept_name: str
    domain: str
    confidence: float          # 0.0 – 1.0
    matched_by: List[str] = field(default_factory=list)   # which patterns fired
    propagated: bool = False   # True if activated via relationship, not direct match


@dataclass
class ParseResult:
    text: str
    activations: Dict[str, ConceptActivation] = field(default_factory=dict)

    def domain_score(self, domain: str) -> float:
        """Aggregate confidence across all concepts of a domain (0–1)."""
        vals = [a.confidence for a in self.activations.values() if a.domain == domain]
        if not vals:
            return 0.0
        # Noisy-OR: 1 - product(1 - p_i)  →  combines multiple weak signals
        result = 1.0 - math.prod(1.0 - min(v, 1.0) for v in vals)
        return round(min(result, 1.0), 4)

    def active_concepts(self, min_confidence: float = 0.3) -> List[str]:
        return [name for name, act in self.activations.items()
                if act.confidence >= min_confidence]

    def top_concepts(self, n: int = 5) -> List[ConceptActivation]:
        return sorted(self.activations.values(),
                      key=lambda a: a.confidence, reverse=True)[:n]


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, remove punctuation noise."""
    text = text.lower()
    text = re.sub(r"[^\w\s\$\%\.\-\/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fuzzy_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


# ──────────────────────────────────────────────
# Core Parser
# ──────────────────────────────────────────────
class SemanticParser:
    """
    Parses text into concept activations using the robotics ontology.

    Usage:
        parser = SemanticParser()
        result = parser.parse("We are expanding our warehouse and struggling with staff shortages.")
        print(result.domain_score("automation"))  # e.g. 0.72
        print(result.active_concepts())
    """

    # Fuzzy similarity threshold for synonym matching
    SYNONYM_THRESHOLD = 0.82
    # How much to decay confidence when propagating through a relationship
    PROPAGATION_DECAY = 0.6

    def __init__(self):
        # Pre-compile all concept patterns
        self._compiled: Dict[str, List[re.Pattern]] = {}
        for name, concept in CONCEPTS.items():
            compiled = []
            for pat in concept.patterns:
                try:
                    compiled.append(re.compile(pat, re.IGNORECASE))
                except re.error:
                    compiled.append(re.compile(re.escape(pat), re.IGNORECASE))
            self._compiled[name] = compiled

        # Build relationship lookup: source → [(target, relation, weight)]
        self._rel_map: Dict[str, List[Tuple[str, str, float]]] = {}
        for rel in RELATIONSHIPS:
            self._rel_map.setdefault(rel.source, []).append(
                (rel.target, rel.relation, rel.weight)
            )

    # ── Public API ──────────────────────────────
    def parse(self, text: str) -> ParseResult:
        """Full parse pipeline: normalize → match → synonyms → propagate."""
        norm = _normalize(text)
        result = ParseResult(text=text)

        # 1. Direct pattern matching
        for name, concept in CONCEPTS.items():
            confidence, matched = self._match_patterns(name, norm)
            if confidence > 0:
                result.activations[name] = ConceptActivation(
                    concept_name=name,
                    domain=concept.domain,
                    confidence=round(confidence * concept.base_weight, 4),
                    matched_by=matched,
                )

        # 2. Synonym / fuzzy matching for concepts not yet activated
        for name, concept in CONCEPTS.items():
            if name in result.activations:
                continue
            syn_conf = self._match_synonyms(concept, norm)
            if syn_conf > 0:
                result.activations[name] = ConceptActivation(
                    concept_name=name,
                    domain=concept.domain,
                    confidence=round(syn_conf * concept.base_weight * 0.75, 4),
                    matched_by=["synonym_match"],
                )

        # 3. Relationship propagation
        self._propagate(result)

        return result

    def parse_multi(self, texts: List[str]) -> ParseResult:
        """Parse multiple text fragments and merge activations (max confidence)."""
        merged = ParseResult(text=" | ".join(texts[:3]))
        for text in texts:
            r = self.parse(text)
            for name, act in r.activations.items():
                if name not in merged.activations:
                    merged.activations[name] = act
                elif act.confidence > merged.activations[name].confidence:
                    merged.activations[name] = act
        return merged

    # ── Private helpers ─────────────────────────
    def _match_patterns(self, concept_name: str, norm_text: str) -> Tuple[float, List[str]]:
        matched = []
        for pat in self._compiled.get(concept_name, []):
            if pat.search(norm_text):
                matched.append(pat.pattern)
        if not matched:
            return 0.0, []
        # More matches → higher confidence (diminishing returns)
        confidence = 1.0 - math.prod(0.4 for _ in matched)
        return min(confidence, 1.0), matched

    def _match_synonyms(self, concept: Concept, norm_text: str) -> float:
        best = 0.0
        words = norm_text.split()
        for syn in concept.synonyms:
            syn_low = syn.lower()
            # Direct substring
            if syn_low in norm_text:
                best = max(best, 0.90)
                continue
            # Sliding window fuzzy match
            n = len(syn_low.split())
            for i in range(len(words) - n + 1):
                window = " ".join(words[i:i + n])
                score = _fuzzy_score(window, syn_low)
                if score >= self.SYNONYM_THRESHOLD:
                    best = max(best, score)
        return best

    def _propagate(self, result: ParseResult):
        """
        Forward-propagate activations through RELATIONSHIPS.
        If concept A is active and A implies B, partially activate B.
        Only runs one hop to avoid explosive chaining.
        """
        new_activations: Dict[str, ConceptActivation] = {}
        for source_name, source_act in result.activations.items():
            for target_name, relation, weight in self._rel_map.get(source_name, []):
                if target_name in result.activations:
                    continue  # already directly activated
                prop_conf = round(source_act.confidence * weight * self.PROPAGATION_DECAY, 4)
                if prop_conf < 0.10:
                    continue
                target_concept = CONCEPTS.get(target_name)
                if not target_concept:
                    continue
                # Keep strongest propagated confidence
                existing = new_activations.get(target_name)
                if not existing or prop_conf > existing.confidence:
                    new_activations[target_name] = ConceptActivation(
                        concept_name=target_name,
                        domain=target_concept.domain,
                        confidence=prop_conf,
                        matched_by=[f"propagated_from:{source_name}:{relation}"],
                        propagated=True,
                    )
        result.activations.update(new_activations)
