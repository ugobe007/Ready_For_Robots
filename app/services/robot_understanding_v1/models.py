"""Persistent-shaped objects for Robot Understanding v1 (Phases 1–3)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

SourceType = Literal[
    "product",
    "specifications",
    "solutions",
    "documentation",
    "case_study",
    "press_release",
    "support",
    "homepage",
    "other",
]

Epistemic = Literal["explicit", "strongly_inferred", "weakly_inferred", "unknown", "contradicted"]
PublisherRole = Literal["manufacturer", "third_party"]
ProfileTier = Literal["A", "B", "C"]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class RobotCompany:
    id: str
    name: str
    primary_domain: str
    aliases: list[str] = field(default_factory=list)

    @staticmethod
    def create(name: str, primary_domain: str, aliases: list[str] | None = None) -> "RobotCompany":
        return RobotCompany(
            id=_new_id("co"),
            name=name,
            primary_domain=primary_domain,
            aliases=list(aliases or []),
        )


@dataclass
class RobotProduct:
    id: str
    company_id: str
    name: str
    generation: Optional[str] = None
    display_class: Optional[str] = None  # descriptive only
    description: Optional[str] = None  # name first; blurb/specs only if present

    @staticmethod
    def create(
        company_id: str,
        name: str,
        *,
        generation: str | None = None,
        display_class: str | None = None,
        description: str | None = None,
    ) -> "RobotProduct":
        return RobotProduct(
            id=_new_id("prod"),
            company_id=company_id,
            name=name,
            generation=generation,
            display_class=display_class,
            description=(description or "").strip() or None,
        )


@dataclass
class RobotSource:
    id: str
    url: str
    source_type: SourceType
    fetched_at: str
    publisher_role: PublisherRole = "manufacturer"
    title: Optional[str] = None
    document_date: Optional[str] = None
    confidence: float = 0.7
    product_id: Optional[str] = None
    text_excerpt: Optional[str] = None  # truncated evidence for audit (not full page)

    @staticmethod
    def create(
        url: str,
        source_type: SourceType,
        *,
        publisher_role: PublisherRole = "manufacturer",
        title: str | None = None,
        document_date: str | None = None,
        confidence: float = 0.7,
        product_id: str | None = None,
        text_excerpt: str | None = None,
    ) -> "RobotSource":
        return RobotSource(
            id=_new_id("src"),
            url=url,
            source_type=source_type,
            fetched_at=_utcnow(),
            publisher_role=publisher_role,
            title=title,
            document_date=document_date,
            confidence=confidence,
            product_id=product_id,
            text_excerpt=(text_excerpt or "")[:500] or None,
        )


@dataclass
class RobotFact:
    id: str
    subject: str  # product name or product_id
    predicate: str
    value: Any
    units: Optional[str]
    epistemic: Epistemic
    source_id: str
    confidence: float
    evidence_span: Optional[str] = None
    product_version: Optional[str] = None
    observed_at: Optional[str] = None

    @staticmethod
    def create(
        subject: str,
        predicate: str,
        value: Any,
        *,
        source_id: str,
        epistemic: Epistemic = "explicit",
        units: str | None = None,
        confidence: float = 0.85,
        evidence_span: str | None = None,
        product_version: str | None = None,
    ) -> "RobotFact":
        return RobotFact(
            id=_new_id("fact"),
            subject=subject,
            predicate=predicate,
            value=value,
            units=units,
            epistemic=epistemic,
            source_id=source_id,
            confidence=confidence,
            evidence_span=(evidence_span or "")[:240] or None,
            product_version=product_version,
            observed_at=_utcnow(),
        )


@dataclass
class RobotProfile:
    """Phase 1–3 deliverable. No jobs. No derived capabilities beyond display_class hint."""

    submitted_url: str
    company: RobotCompany
    products: list[RobotProduct]
    selected_product: Optional[RobotProduct]
    sources: list[RobotSource]
    facts: list[RobotFact]
    profile_confidence: ProfileTier
    source_grounding_rate: float
    ungrounded_fact_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    needs_product_choice: bool = False
    research_stages: list[dict[str, Any]] = field(default_factory=list)
    # Honest quality dimensions (tier is derived from these)
    coverage_rate: float = 0.0
    coverage_level: str = "low"
    source_quality_rate: float = 0.0
    source_quality_level: str = "low"
    research_morphology: Optional[str] = None
    # Robot Inference Engine summary (explicit facts / inferred facts / capabilities
    # / workflows, each with basis + confidence + provenance) — additive display
    # metadata; the matcher consumes facts, not this.
    inference: Optional[dict[str, Any]] = None
    preview_images: list[str] = field(default_factory=list)
    built_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "submitted_url": self.submitted_url,
            "built_at": self.built_at,
            "profile_confidence": self.profile_confidence,
            "source_grounding_rate": round(self.source_grounding_rate, 4),
            "coverage_rate": round(self.coverage_rate, 4),
            "coverage_level": self.coverage_level,
            "source_quality_rate": round(self.source_quality_rate, 4),
            "source_quality_level": self.source_quality_level,
            "research_morphology": self.research_morphology,
            "inference": self.inference,
            "preview_images": list(self.preview_images),
            "ungrounded_fact_ids": list(self.ungrounded_fact_ids),
            "notes": list(self.notes),
            "needs_product_choice": self.needs_product_choice,
            "research_stages": list(self.research_stages),
            "company": asdict(self.company),
            "products": [asdict(p) for p in self.products],
            "selected_product": asdict(self.selected_product) if self.selected_product else None,
            "sources": [asdict(s) for s in self.sources],
            "facts": [asdict(f) for f in self.facts],
        }

    def to_audit_markdown(self) -> str:
        """Human-readable profile for robotics-professional review."""
        lines: list[str] = []
        lines.append("# Robot Profile (Understanding v1 · Phases 1–3)")
        lines.append("")
        lines.append(f"Submitted: `{self.submitted_url}`")
        lines.append(f"Built: `{self.built_at}`")
        lines.append(f"Profile confidence: **{self.profile_confidence}**")
        lines.append(
            f"Grounding: **{self.source_grounding_rate:.0%}** · "
            f"Coverage: **{self.coverage_level}** ({self.coverage_rate:.0%}) · "
            f"Source quality: **{self.source_quality_level}** ({self.source_quality_rate:.0%})"
        )
        if self.research_morphology:
            lines.append(f"Research checklist: `{self.research_morphology}`")
        lines.append("")
        lines.append("## Company")
        lines.append(f"- {self.company.name} (`{self.company.primary_domain}`)")
        if self.company.aliases:
            lines.append(f"- Aliases: {', '.join(self.company.aliases)}")
        lines.append("")
        lines.append("## Products found")
        if not self.products:
            lines.append("- *(none resolved)*")
        for p in self.products:
            mark = " ← selected" if self.selected_product and p.id == self.selected_product.id else ""
            gen = f" [{p.generation}]" if p.generation else ""
            cls = f" · {p.display_class}" if p.display_class else ""
            lines.append(f"- **{p.name}**{gen}{cls}{mark}")
        lines.append("")
        lines.append("## Sources")
        by_id = {s.id: s for s in self.sources}
        for s in self.sources:
            date = f" · doc {s.document_date}" if s.document_date else ""
            title = f" — {s.title}" if s.title else ""
            lines.append(
                f"- `{s.source_type}` · {s.publisher_role} · conf {s.confidence:.2f}{date}{title}"
            )
            lines.append(f"  - {s.url}")
        lines.append("")
        lines.append("## Facts")
        known = [f for f in self.facts if f.epistemic != "unknown"]
        unknowns = [f for f in self.facts if f.epistemic == "unknown"]
        if not known:
            lines.append("- *(no concrete claims extracted)*")
        for f in known:
            src = by_id.get(f.source_id)
            units = f" {f.units}" if f.units else ""
            lines.append(
                f"- **{f.predicate}** = `{f.value}{units}` · {f.epistemic} · conf {f.confidence:.2f}"
            )
            if f.evidence_span:
                lines.append(f"  - evidence: “{f.evidence_span}”")
            if src:
                lines.append(f"  - source: [{src.source_type}]({src.url})")
            else:
                lines.append(f"  - source: UNGROUNDED (`{f.source_id}`)")
        if unknowns:
            lines.append("")
            lines.append("## Unknowns (research checklist)")
            for f in unknowns:
                lines.append(f"- **{f.predicate}** — UNKNOWN")
                if f.evidence_span:
                    lines.append(f"  - {f.evidence_span}")
        contradicted = [f for f in known if f.epistemic == "contradicted"]
        if contradicted:
            lines.append("")
            lines.append("## Contradictions")
            for f in contradicted:
                units = f" {f.units}" if f.units else ""
                lines.append(f"- **{f.predicate}** = `{f.value}{units}` (conflicted)")
        if self.notes:
            lines.append("")
            lines.append("## Notes")
            for n in self.notes:
                lines.append(f"- {n}")
        lines.append("")
        lines.append("---")
        lines.append("*STOP — no jobs, no derived capability inference, no match scores.*")
        return "\n".join(lines)
