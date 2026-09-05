"""
Semantic frame extraction for news headlines and scraper blobs.

Verb-as-anchor decomposition (actor, action, topic, goals/outcomes) built on
headline_parser, sentence_parser, and semantic_roles. Descriptors and hyperbolic
language are separated from entities so downstream pipelines do not treat
adjectives as actors.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from app.services.headline_parser import extract_actor
from app.services.sentence_parser import parse_headline
from app.services.semantic_roles import parse_semantic_roles

# Extraordinary / clickbait modifiers — not entities
HYPERBOLIC_TERMS = frozenset({
    "extraordinary", "revolutionary", "unprecedented", "game-changing", "game changing",
    "massive", "huge", "enormous", "historic", "groundbreaking", "shocking",
    "stunning", "incredible", "unbelievable", "explosive", "dramatic", "surging",
    "skyrocketing", "soaring", "plummeting", "crushing", "destroying", "annihilating",
    "all-time", "record-breaking", "record breaking", "never-before-seen", "never before seen",
    "world-first", "world first", "first-ever", "first ever",
})

# Leading descriptor phrases that masquerade as subjects
DESCRIPTOR_PREFIXES = (
    "new ", "major ", "big ", "top ", "leading ", "global ", "international ",
    "local ", "regional ", "national ", "emerging ", "fast-growing ", "fast growing ",
    "high-growth ", "high growth ", "next-generation ", "next generation ",
    "cutting-edge ", "cutting edge ", "state-of-the-art ", "state of the art ",
)

GOAL_PARTICIPLE_RE = re.compile(
    r"(?:,\s*|\bwhile\s+|\band\s+)?"
    r"(?P<verb>reducing|improving|increasing|decreasing|cutting|boosting|lowering|raising|"
    r"eliminating|accelerating|expanding|growing|slashing|trimming|enhancing|optimizing)"
    r"\s+(?P<metric>.+?)\s+by\s+(?P<quant>\d+(?:\.\d+)?%?)",
    re.IGNORECASE,
)

GOAL_NOUN_RE = re.compile(
    r"(?P<quant>\d+(?:\.\d+)?%?)\s+"
    r"(?P<direction>reduction|improvement|increase|decrease|cut|gain|boost|drop|rise|growth|decline)"
    r"\s+(?:in|to|of)\s+(?P<metric>.+?)(?:[,.]|$|\s+while|\s+and\s+)",
    re.IGNORECASE,
)

TOPIC_STOP = frozenset({
    "a", "an", "the", "its", "their", "his", "her", "all", "of", "at", "in", "on",
    "to", "for", "by", "with", "from", "is", "are", "was", "were", "be", "been",
    "plan", "plans", "planning", "planned", "roll", "out", "rollout",
})


@dataclass
class ParsedGoal:
    metric: str
    direction: str
    quantifier: Optional[str] = None
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticFrame:
    source_text: str
    actor: Optional[str] = None
    actors: list[str] = field(default_factory=list)
    action_verb: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None
    goals: list[ParsedGoal] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    descriptors: list[str] = field(default_factory=list)
    hyperbolic_terms: list[str] = field(default_factory=list)
    confidence: float = 0.0
    ontology_concepts: list[str] = field(default_factory=list)
    parse_debug: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["goals"] = [g.to_dict() if isinstance(g, ParsedGoal) else g for g in self.goals]
        return d

    def summary_line(self) -> str:
        """One-line frame for Cal / supply pipeline copy."""
        parts: list[str] = []
        if self.actor:
            parts.append(self.actor)
        if self.action_verb and self.topic:
            parts.append(f"{self.action_verb} → {self.topic}")
        elif self.topic:
            parts.append(self.topic)
        if self.goals:
            g = self.goals[0]
            q = f" ({g.quantifier})" if g.quantifier else ""
            parts.append(f"goal: {g.direction} {g.metric}{q}")
        return " · ".join(parts) if parts else self.source_text[:120]


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _find_hyperbolic(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for term in HYPERBOLIC_TERMS:
        if term in lower:
            found.append(term)
    return found


def _strip_hyperbolic_from_actor(name: str) -> tuple[str, list[str]]:
    if not name:
        return name, []
    lower = name.lower()
    stripped = name
    desc: list[str] = []
    for term in sorted(HYPERBOLIC_TERMS, key=len, reverse=True):
        if term in lower:
            desc.append(term)
            stripped = re.sub(re.escape(term), "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\s+", " ", stripped).strip(" -,")
    return stripped or name, desc


def _clean_actor_candidate(name: str) -> Optional[str]:
    if not name or len(name) < 2:
        return None
    name = _normalize_ws(name)
    name, _ = _strip_hyperbolic_from_actor(name)
    lower = name.lower()
    for prefix in DESCRIPTOR_PREFIXES:
        if lower.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    if len(name) < 2 or name.lower() in TOPIC_STOP:
        return None
    if name.islower() and " " not in name:
        return None
    return name[:120]


def _extract_goals(text: str) -> tuple[list[ParsedGoal], list[str], str]:
    """Return goals, raw outcome strings, and text with goal clauses removed."""
    goals: list[ParsedGoal] = []
    outcomes: list[str] = []
    remainder = text

    for m in GOAL_PARTICIPLE_RE.finditer(text):
        raw = m.group(0).lstrip(", ").strip()
        verb = m.group("verb").lower()
        metric = _normalize_ws(m.group("metric"))
        quant = m.group("quant")
        direction = {
            "reducing": "reduction",
            "decreasing": "reduction",
            "cutting": "reduction",
            "lowering": "reduction",
            "slashing": "reduction",
            "trimming": "reduction",
            "eliminating": "elimination",
            "improving": "improvement",
            "increasing": "improvement",
            "boosting": "improvement",
            "raising": "increase",
            "accelerating": "acceleration",
            "expanding": "expansion",
            "growing": "growth",
            "enhancing": "enhancement",
            "optimizing": "optimization",
        }.get(verb, verb)
        goals.append(ParsedGoal(metric=metric, direction=direction, quantifier=quant, raw=raw))
        outcomes.append(f"{direction} in {metric} by {quant}")
        remainder = remainder.replace(m.group(0), " ")

    for m in GOAL_NOUN_RE.finditer(text):
        raw = m.group(0).strip()
        if any(g.raw == raw for g in goals):
            continue
        goals.append(ParsedGoal(
            metric=_normalize_ws(m.group("metric")),
            direction=m.group("direction").lower(),
            quantifier=m.group("quant"),
            raw=raw,
        ))
        outcomes.append(raw)
        remainder = remainder.replace(m.group(0), " ")

    remainder = _normalize_ws(remainder)
    return goals, outcomes, remainder


def _derive_topic(remainder: str, verb_lemma: Optional[str]) -> Optional[str]:
    """Topic stem after goal clauses removed from direct object."""
    text = _normalize_ws(remainder)
    if not text:
        return None

    # "to roll out automation at all of its logistics centers" → automation at logistics centers
    text = re.sub(r"^to\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:roll\s+out|deploy|implement|introduce|launch|expand|build|install)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\ball\s+of\s+(?:its|their|the)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:its|their|the)\s+", "", text, flags=re.IGNORECASE)
    text = _normalize_ws(text)

    # Prefer "automation of X" / "automation at X"
    auto = re.search(
        r"\b(automation|robotics|robots|humanoids|amrs?|cobots?|warehouse automation|"
        r"logistics automation|manufacturing automation)\b(.{0,80})?",
        text,
        re.IGNORECASE,
    )
    if auto:
        tail = (auto.group(2) or "").strip()
        tail = re.sub(r"^[\s,]+", "", tail)
        tail = re.sub(r"\s+at\s+", " at ", tail)
        topic = auto.group(1)
        if tail and len(tail) > 3:
            topic = f"{topic}{tail[:60]}"
        return _normalize_ws(topic)[:160]

    if len(text) > 8:
        return text[:160]
    return None


def _ontology_tags(text: str, topic: Optional[str]) -> list[str]:
    blob = f"{topic or ''} {text}".lower()
    tags: list[str] = []
    mapping = {
        "logistics": "logistics_automation",
        "warehouse": "warehouse_automation",
        "fulfillment": "fulfillment_automation",
        "manufacturing": "manufacturing_automation",
        "humanoid": "humanoid_robotics",
        "human labor": "workforce_reduction",
        "workforce": "workforce_reduction",
        "throughput": "operational_throughput",
        "amr": "mobile_robot",
        "cobot": "collaborative_robot",
        "oem": "robot_oem",
        "integrator": "systems_integrator",
    }
    for needle, tag in mapping.items():
        if needle in blob and tag not in tags:
            tags.append(tag)
    return tags


def _frame_confidence(
    *,
    actor: Optional[str],
    action: Optional[str],
    topic: Optional[str],
    goals: list[ParsedGoal],
    hyperbolic: list[str],
) -> float:
    score = 0.0
    if actor:
        score += 0.35
    if action:
        score += 0.2
    if topic:
        score += 0.25
    if goals:
        score += 0.15
    if hyperbolic:
        score -= min(0.15, 0.03 * len(hyperbolic))
    return round(max(0.0, min(1.0, score)), 3)


def parse_news_semantic_frame(text: str) -> SemanticFrame:
    """
    Decompose a news headline or snippet into actor, action, topic, and goals.

    Example:
        "Amazon is planning to roll out automation at all of its logistics centers,
         reducing human labor by 50% while improving operational throughput by 75%."
        → actor=Amazon, action=plan, topic=automation at logistics centers,
          goals=[50% labor reduction, 75% throughput improvement]
    """
    source = _normalize_ws(text)
    if not source:
        return SemanticFrame(source_text="", confidence=0.0)

    hyperbolic = _find_hyperbolic(source)
    headline = parse_headline(source)
    roles = parse_semantic_roles(source)
    actor_raw = extract_actor(source)
    actor = _clean_actor_candidate(actor_raw) if actor_raw else None

    svo = headline.svo_triples[0] if headline.svo_triples else None
    subj = svo.subject if svo else None
    if subj:
        cleaned = _clean_actor_candidate(subj)
        if cleaned and (not actor or len(cleaned) <= len(actor) + 5):
            actor = cleaned

    if not actor and headline.actors:
        actor = _clean_actor_candidate(headline.actors[0])

    verb_lemma = (svo.verb_lemma if svo else None) or (
        roles.verb_anchor.lower().rstrip("s") if roles.verb_anchor else None
    )
    direct_object = (svo.direct_object if svo else None) or roles.head_object or ""

    goals, outcomes, topic_remainder = _extract_goals(direct_object or source)
    if not goals:
        goals, outcomes, topic_remainder = _extract_goals(source)

    topic = _derive_topic(topic_remainder, verb_lemma)
    if not topic and direct_object:
        topic = _derive_topic(direct_object, verb_lemma)

    descriptors: list[str] = list(roles.descriptors or [])

    actors: list[str] = []
    if actor:
        actors.append(actor)

    concepts = _ontology_tags(source, topic)
    confidence = _frame_confidence(
        actor=actor,
        action=verb_lemma,
        topic=topic,
        goals=goals,
        hyperbolic=hyperbolic,
    )

    description = topic_remainder[:240] if topic_remainder else None

    return SemanticFrame(
        source_text=source,
        actor=actor,
        actors=actors,
        action_verb=verb_lemma,
        topic=topic,
        description=description,
        goals=goals,
        outcomes=outcomes,
        descriptors=descriptors,
        hyperbolic_terms=hyperbolic,
        confidence=confidence,
        ontology_concepts=concepts,
        parse_debug={
            "sentence_type": headline.sentence_type,
            "svo_count": len(headline.svo_triples),
            "roles_verb": roles.verb_anchor,
            "direct_object_raw": direct_object,
        },
    )


def frame_signal_line(frame: SemanticFrame) -> str:
    """Cal-ready one sentence from a semantic frame (StageGate / R4R consistent voice)."""
    if not frame.actor and not frame.topic:
        return frame.source_text[:200]

    actor = frame.actor or "The company"
    verb = frame.action_verb or "is moving on"
    topic = frame.topic or "automation"

    line = f"{actor} {verb} {topic}"
    if frame.goals:
        g = frame.goals[0]
        if g.quantifier:
            line += f", targeting a {g.quantifier} {g.direction} in {g.metric}"
    if frame.hyperbolic_terms:
        line += " (headline language is promotional — frame is normalized)"
    return _normalize_ws(line)[:320]
