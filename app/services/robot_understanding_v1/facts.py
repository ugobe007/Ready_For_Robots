"""
Phase 3 — extract atomic facts from typed sources.

Extraction contract (docs/robot_understanding_v1.md):
  Ask: What concrete claims about this robot are supported by this source?
  Do not ask: What can this robot do?
  Do not resolve contradictions — emit multiple facts.
  Do not invent capabilities, workflows, or jobs.
"""
from __future__ import annotations

import re
from typing import Callable

from app.services.robot_understanding_v1.models import RobotFact, RobotSource
from app.services.robot_understanding_v1.sources import CollectedSource

# predicate extractors: (predicate, pattern, value_fn, units_or_none, confidence)
# value_fn(match) -> value


def extract_facts_from_sources(
    collected: list[CollectedSource],
    *,
    subject: str,
) -> list[RobotFact]:
    facts: list[RobotFact] = []
    for item in collected:
        facts.extend(
            _extract_from_page(
                item.source,
                item.page.text or "",
                subject=subject,
                page_url=item.page.final_url,
                page_title=item.page.title or "",
            )
        )
    return facts


def filter_facts_to_subject(
    facts: list[RobotFact],
    collected: list[CollectedSource],
    *,
    subject: str,
) -> tuple[list[RobotFact], int]:
    """
    Drop material facts whose evidence is about a sibling SKU / off-subject page.

    Gate: selected-product profiles must not present another model's payload etc.
    """
    from app.services.robot_understanding_v1.sources import page_supports_subject, subject_tokens

    by_id = {c.source.id: c for c in collected}
    subj_key = re.sub(r"[^a-z0-9]", "", subject.lower())
    tokens = subject_tokens(subject)
    kept: list[RobotFact] = []
    dropped = 0
    constraint_preds = {
        "carrying_capacity",
        "battery_runtime",
        "reach_or_workspace",
        "max_speed",
        "arm_count",
        "degrees_of_freedom",
        "ingress_protection",
        "product_class",
    }

    for f in facts:
        if f.epistemic == "unknown":
            kept.append(f)
            continue
        item = by_id.get(f.source_id)
        if item is None:
            kept.append(f)
            continue
        page = item.page
        supports = page_supports_subject(
            url=page.final_url,
            title=page.title or "",
            text=page.text or "",
            product_name=subject,
        )
        span = f.evidence_span or ""
        window = span
        if span and page.text:
            idx = page.text.find(span[: min(40, len(span))])
            if idx >= 0:
                window = page.text[max(0, idx - 100) : idx + len(span) + 100]

        if f.predicate in constraint_preds and not supports:
            # Off-subject product/spec page — do not inherit constraints
            dropped += 1
            continue

        if f.predicate in constraint_preds and _evidence_names_sibling_sku(
            window, subj_key=subj_key, tokens=tokens
        ):
            dropped += 1
            continue
        kept.append(f)
    return kept, dropped


def _evidence_names_sibling_sku(window: str, *, subj_key: str, tokens: set[str]) -> bool:
    """True if evidence window cites a different model SKU than the subject."""
    if not window:
        return False
    # Compact model tokens only (MiR250, UR10e, MC-600) — not "Runtime 90" / "Weight 14"
    for m in re.finditer(r"\b([A-Za-z]{2,}[-]?\d{2,4}[A-Za-z]?)\b", window):
        raw = m.group(1)
        key = re.sub(r"[^a-z0-9]", "", raw.lower())
        if key.startswith("ip") and key[2:].isdigit():
            continue
        if key.startswith("iso"):
            continue
        if key == subj_key or any(key == re.sub(r"[^a-z0-9]", "", t) for t in tokens):
            continue
        if subj_key and (key in subj_key or subj_key in key):
            continue
        if re.search(r"\d", key) and key != subj_key:
            return True
    return False


def _extract_from_page(
    source: RobotSource,
    text: str,
    *,
    subject: str,
    page_url: str = "",
    page_title: str = "",
) -> list[RobotFact]:
    if not text or len(text) < 40:
        return []
    out: list[RobotFact] = []
    page_about_subject = True
    if subject and len(subject) >= 2:
        from app.services.robot_understanding_v1.sources import page_supports_subject

        page_about_subject = page_supports_subject(
            url=page_url or source.url,
            title=page_title or (source.title or ""),
            text=text,
            product_name=subject,
        )

    def add(
        predicate: str,
        value,
        *,
        units: str | None = None,
        span: str,
        confidence: float = 0.9,
        require_subject_near: bool = False,
        start: int | None = None,
        end: int | None = None,
        value_scope: str = "whole_robot",
    ) -> None:
        if require_subject_near and start is not None and end is not None:
            if not page_about_subject and not _subject_near(subject, text, start, end):
                return
        if predicate in {
            "carrying_capacity",
            "battery_runtime",
            "reach_or_workspace",
            "max_speed",
        }:
            if not _numeric_value_plausible(
                predicate, value, units, span, value_scope=value_scope
            ):
                return
            if (
                predicate == "carrying_capacity"
                and value_scope in {"per_tray", "per_shelf", "per_deck", "accessory"}
            ):
                return
        out.append(
            RobotFact.create(
                subject=subject,
                predicate=predicate,
                value=value,
                source_id=source.id,
                epistemic="explicit",
                units=units,
                confidence=min(0.98, confidence * source.confidence / 0.85),
                evidence_span=span.strip(),
            )
        )

    # Dense label/value tables first (where datasheet facts live)
    _extract_spec_table_facts(text, add)

    # --- carrying / payload (manufacturer phrasing varies) ---
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*\+?\s*"
        r"(lb|lbs|pound|pounds|kg|kilogram|kilograms)\s+"
        r"(?:carrying\s+capacity|payload(?:\s+capacity)?|high\s+payload|of\s+payload|"
        r"load\s+capacity|rated\s+load)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.95,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(?:carrying\s+capacity|payload(?:\s+capacity)?|high\s+payload|max\s+(?:payload|weight)|"
        r"payload\s+capacity|load\s+capacity|rated\s+(?:load|payload)|max\.?\s*payload)\s*"
        r"(?:\([^)]*\)\s*)?(?:of\s+|[:：\|]\s*)?"
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*\+?\s*"
        r"(lb|lbs|pound|pounds|kg|kilogram|kilograms)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.95,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*\+?\s*"
        r"(lb|lbs|pound|pounds)\s+(?:carrying\s+capacity|per\s+arm)",
        text,
        re.I,
    ):
        scope = (
            "per_arm"
            if re.search(r"per\s+arm", m.group(0), re.I)
            else _infer_payload_scope(text, m.start(), m.end())
        )
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.93,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=scope,
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*\+\s*(lbs?|pounds?|kg)\s+High\s+payload",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    # Compact: "14kg of payload" / "250kg payload" / "1,900 kg payload"
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(kg|lb|lbs)\s+(?:of\s+)?payload(?:\s+capacity)?",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.94,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(?:handle|handles|handling)\s+up\s+to\s+"
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(kg|lb|lbs)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(?:total(?:\s+capacity)?|capacity\s+total)\s*"
        r"(?:of\s+|[:：]\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
        r"(kg|lb|lbs|pound|pounds)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.94,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope="whole_robot",
        )
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(kg|lb|lbs)\s+total\b",
        text,
        re.I,
    ):
        ctx = text[max(0, m.start() - 40) : m.end() + 40]
        if re.search(r"payload|capacit|load|carry", ctx, re.I):
            add(
                "carrying_capacity",
                _num(m.group(1)),
                units=_unit(m.group(2)),
                span=m.group(0),
                confidence=0.9,
                require_subject_near=True,
                start=m.start(),
                end=m.end(),
                value_scope="whole_robot",
            )

    # --- battery / runtime (hours and minutes) ---
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(hour|hours|hr|hrs|h)\s+"
        r"(?:battery(?:\s+life)?|long\s+operation\s+time|operation\s+time)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:battery(?:\s+life)?|operation\s+time|runtime|average\s+runtime|"
        r"run\s*time|operating\s+time)\s*\*?\s*"
        r"(?:of\s+|[:：\|]\s*)?(\d+(?:\.\d+)?)\s*\+?\s*"
        r"(hour|hours|hr|hrs|h|min|mins|minutes)\b",
        text,
        re.I,
    ):
        units = "min" if re.search(r"min", m.group(2), re.I) else "hr"
        add(
            "battery_runtime",
            _num(m.group(1)),
            units=units,
            span=m.group(0),
            confidence=0.93,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*\+\s*h\b[^.]{0,40}(?:operation|battery|charge)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0)[:80],
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:run|operate|operates)\s+up\s+to\s+(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs)\s+a\s+day",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0),
            confidence=0.88,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*(min|mins|minutes)\s+(?:average\s+)?(?:runtime|battery)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="min",
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*[-–/]\s*(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs)\s+"
        r"(?:runtime|battery|operation)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- product class / form (explicit claims only) ---
    for m in re.finditer(
        r"\b((?:commercially\s+deployed\s+)?humanoid(?:\s+robot)?|bipedal(?:\s+robot)?)\b",
        text,
        re.I,
    ):
        if not _subject_near(subject, text, m.start(), m.end()):
            continue
        # Skip third-party news blurbs
        ctx = text[max(0, m.start() - 80) : m.end() + 40]
        if re.search(r"\b(honda|asimo|avatar|in\s+the\s+news|ieee)\b", ctx, re.I):
            continue
        add("product_class", "humanoid", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(autonomous\s+mobile\s+robot|\bAMR\b|autonomous\s+guided\s+vehicle|\bAGV\b)\b",
        text,
        re.I,
    ):
        ctx = text[max(0, m.start() - 60) : m.end() + 40]
        if re.search(
            r"\b(unlike|versus|vs\.?|compared\s+to|different\s+from|not\s+an|"
            r"AGV\s*\(|AMR\s*\(|shift\s+from|platform\s+for\s+enterprise)\b",
            ctx,
            re.I,
        ):
            continue
        if subject and len(subject) >= 2 and not page_about_subject:
            near = text[max(0, m.start() - 100) : m.end() + 100]
            if subject.lower() not in near.lower() and not re.search(
                r"\b(our\s+robot|this\s+robot|collaborative\s+robot)\b", near, re.I
            ):
                continue
        label = "amr" if re.search(r"amr|autonomous\s+mobile", m.group(0), re.I) else "agv"
        add("product_class", label, span=m.group(0), confidence=0.88)

    # Title/H1 style: "Locus Origin: Collaborative Robots Warehouse"
    if subject and re.search(rf"\b{re.escape(subject)}\b", text[:300], re.I):
        head = text[:400]
        if re.search(r"\bcollaborative\s+robots?\b", head, re.I) and re.search(
            r"\bwarehouse\b", head, re.I
        ):
            add(
                "product_class",
                "amr",
                span="collaborative robots warehouse",
                confidence=0.75,
            )

    for m in re.finditer(
        r"\b(floor\s+scrubber|autonomous\s+(?:hard[- ]floor\s+)?scrubber|auto[- ]?scrubber|"
        r"robotic\s+floor\s+scrubber)\b",
        text,
        re.I,
    ):
        add("product_class", "autonomous_scrubber", span=m.group(0), confidence=0.92)

    for m in re.finditer(
        r"\b((?:autonomous|commercial|robotic)\s+vacuum(?:\s+cleaner)?|"
        r"robot\s+vacuum|vacuum\s+cleaning\s+robot|cleaning\s+robot)\b",
        text,
        re.I,
    ):
        if re.search(r"scrub", m.group(0), re.I):
            continue
        add("product_class", "cleaning_robot", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(mobile\s+manipulation(?:\s+robot)?|mobile\s+manipulator|"
        r"general[- ]purpose\s+mobile\s+robot)\b",
        text,
        re.I,
    ):
        # Avoid accessory-arm bleed: require subject near or page about subject
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "mobile_manipulator", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(quadruped|four[- ]legged(?:\s+robot)?|legged\s+mobile\s+robot|"
        r"agile\s+mobile\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        label = (
            "quadruped"
            if re.search(r"quadruped|four[- ]legged|legged", m.group(0), re.I)
            else "mobile_robot"
        )
        add("product_class", label, span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(collaborative\s+(?:robot\s+)?arm|cobot(?:\s+arm)?|"
        r"collaborative\s+industrial\s+robot|6[- ]axis\s+(?:robot\s+)?arm|"
        r"collaborative\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "cobot_arm", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b((?:indoor\s+)?(?:inspection\s+)?drone|UAV|aerial\s+(?:robot|platform)|"
        r"flying\s+robot|confined[- ]space\s+(?:drone|UAV))\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "drone", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(construction\s+robot|drywall\s+(?:finishing|robot)|layout\s+printer|"
        r"field\s*printer|jobsite\s+robot|construction\s+(?:layout|finishing)\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "construction_robot", span=m.group(0), confidence=0.88)

    for m in re.finditer(
        r"\b(service\s+robot|hospitality\s+robot|restaurant\s+(?:delivery\s+)?robot|"
        r"social\s+robot|delivery\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "service_robot", span=m.group(0), confidence=0.88)

    for m in re.finditer(r"\b(dual[- ]arm|two\s+arms|bimanual)\b", text, re.I):
        add("arm_count", 2, span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"(\d+)\s*(?:DoF|DOF|degrees?\s+of\s+freedom)",
        text,
        re.I,
    ):
        add(
            "degrees_of_freedom",
            _num(m.group(1)),
            span=m.group(0),
            confidence=0.88,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:DoF|DOF|degrees?\s+of\s+freedom)\s*[:：\|]?\s*(\d+)",
        text,
        re.I,
    ):
        add(
            "degrees_of_freedom",
            _num(m.group(1)),
            span=m.group(0),
            confidence=0.88,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- reach / work envelope (m / mm / ft) ---
    for m in re.finditer(
        r"(?:stretch(?:es)?\s+up\s+to|reach(?:es)?\s+up\s+to|large\s+workspace|"
        r"workspace|reach|wrist\s+reach|max(?:imum)?\s+reach)\s*[:(|]?\s*"
        r"(\d+(?:\.\d+)?)\s*(mm|cm|m|meters?|ft|feet|'|′)\b",
        text,
        re.I,
    ):
        unit_raw = m.group(2).lower()
        if unit_raw in {"mm"}:
            unit = "mm"
        elif unit_raw in {"cm"}:
            unit = "cm"
        elif unit_raw in {"m", "meter", "meters"}:
            unit = "m"
        else:
            unit = "ft"
        add(
            "reach_or_workspace",
            _num(m.group(1)),
            units=unit,
            span=m.group(0)[:100],
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*(mm|m)\s+reach\b",
        text,
        re.I,
    ):
        add(
            "reach_or_workspace",
            _num(m.group(1)),
            units=m.group(2).lower(),
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:stretch|reach|workspace|high[- ]reaching)[^.]{0,80}\((\d+(?:\.\d+)?)\s*m\)",
        text,
        re.I,
    ):
        add(
            "reach_or_workspace",
            _num(m.group(1)),
            units="m",
            span=m.group(0)[:100],
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- speed ---
    for m in re.finditer(
        r"(?:max(?:imum)?\s+speed|top\s+speed|moves?\s+along\s+at)\s*"
        r"(?:of\s+|[:：]\s*)?(\d+(?:\.\d+)?)\s*(m/s|meters?\s+per\s+second)",
        text,
        re.I,
    ):
        add(
            "max_speed",
            _num(m.group(1)),
            units="m/s",
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- ingress / environment rating ---
    for m in re.finditer(r"\b(IP\d{2}[A-Z]?)\b", text, re.I):
        add(
            "ingress_protection",
            m.group(1).upper(),
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- end effector / hands ---
    for m in re.finditer(
        r"\b(dexterous\s+hands?|end[- ]effectors?|grippers?|bimanual\s+dexterity)\b",
        text,
        re.I,
    ):
        add("has_dexterous_hands", True, span=m.group(0), confidence=0.88)
        add("end_effector", "dexterous_hand", span=m.group(0), confidence=0.85)

    # --- tote handling (explicit demonstration / claim) ---
    for m in re.finditer(
        r"(moves?\s+over\s+[\d,]+\s+totes?|tote[- ]based\s+workflows?|"
        r"managing\s+tote[- ]based|handling\s+(?:different\s+types\s+of\s+)?totes?|"
        r"loading\s+and\s+unloading[^.]*totes?|"
        r"tote[- ]?arrays?|containers?,?\s+including\s+tote|"
        r"from\s+tote[- ]?arrays?)",
        text,
        re.I,
    ):
        add(
            "supports_tote_handling",
            True,
            span=m.group(0),
            confidence=0.9,
        )

    # --- goods movement claims (concrete, not job inference) ---
    for m in re.finditer(
        r"\b(person[- ]to[- ]goods|goods[- ]to[- ]person|P2G|G2P|"
        r"point[- ]to[- ]point\s+transport|warehouse\s+transport)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_warehouse_transport", True, span=m.group(0), confidence=0.85)

    # --- warehouse / factory deployment claims ---
    for m in re.finditer(
        r"\b(commercially\s+deployed|commercial\s+deployment|deployed\s+in\s+"
        r"(?:a\s+)?(?:warehouse|factory|fulfillment)|warehouse(?:s)?\s+and\s+factory(?:ies)?|"
        r"manufacturing\s+and\s+warehous(?:e|ing)|warehousing\s+workflows?)\b",
        text,
        re.I,
    ):
        add("warehouse_or_factory_deployment", True, span=m.group(0), confidence=0.85)

    # --- scrubbing (explicit) ---
    for m in re.finditer(
        r"\b(hard[- ]floor\s+(?:scrub|clean)|floor\s+scrubbing|auto[- ]?scrub(?:bing)?\s+routes?)\b",
        text,
        re.I,
    ):
        add("supports_hard_floor_scrubbing", True, span=m.group(0), confidence=0.93)

    # --- mobile base / mobility architecture ---
    for m in re.finditer(
        r"\b(omni[- ]?directional\s+(?:mobile\s+)?base(?:\s+movement)?|"
        r"omnidirectional\s+mobile\s+base|mobile\s+base|"
        r"wheeled\s+(?:base|platform)|bipedal\s+(?:walk|locomotion|mobility)|"
        r"walk(?:s|ing)?\s+and\s+run(?:s|ning)?|"
        r"autonomous\s+navigation)\b",
        text,
        re.I,
    ):
        if re.search(r"omni|mobile\s+base|wheeled|bipedal|walk", m.group(0), re.I):
            add("has_mobile_base", True, span=m.group(0), confidence=0.9)
            if re.search(r"omni", m.group(0), re.I):
                add(
                    "mobility_architecture",
                    "omnidirectional_base",
                    span=m.group(0),
                    confidence=0.9,
                )
            elif re.search(r"bipedal|walk", m.group(0), re.I):
                add(
                    "mobility_architecture",
                    "bipedal",
                    span=m.group(0),
                    confidence=0.88,
                )
        if re.search(r"autonomous\s+navigation", m.group(0), re.I):
            add("autonomous_navigation", True, span=m.group(0), confidence=0.88)

    for m in re.finditer(
        r"\b(LiDAR\s+navigation|SLAM|programmed\s+routes?|autonomous\s+(?:driving|routing|mapping)|"
        r"AI[- ]?(?:powered\s+)?navigation|indoor\s+(?:GPS|navigation)|FlyAware|"
        r"obstacle\s+avoidance|autonomous(?:ly)?\s+(?:navigat\w+|map\w+|patrol\w+))\b",
        text,
        re.I,
    ):
        add("autonomous_navigation", True, span=m.group(0), confidence=0.86)

    for m in re.finditer(
        r"\b((?:indoor|outdoor)\s+(?:industrial\s+)?(?:spaces?|environments?|facilities?)|"
        r"confined\s+(?:spaces?|industrial)|"
        r"(?:hotels?|airports?|hospitals?|healthcare|retail|restaurants?|hospitality|"
        r"reception|warehouses?|factories?|jobsites?|construction\s+sites?))\b",
        text,
        re.I,
    ):
        raw = m.group(0).lower()
        if re.search(r"hotel|airport|hospital|healthcare|workplace|facility|retail|reception", raw):
            val = "commercial"
        elif re.search(r"restaurant|hospitality", raw):
            val = "restaurant"
        elif re.search(r"construction|jobsite", raw):
            val = "construction"
        elif re.search(r"confined|indoor", raw):
            val = "indoor"
        elif re.search(r"warehouse|factory", raw):
            val = "warehouse"
        else:
            val = raw.split()[0]
        add("operating_environment", val, span=m.group(0)[:120], confidence=0.84)

    # --- load/unload as explicit claim (fact about claim, not capability inference) ---
    for m in re.finditer(
        r"\b(load(?:ing)?\s+and\s+unload(?:ing)?(?:\s+(?:of\s+)?(?:containers?|totes?|parts?))?)\b",
        text,
        re.I,
    ):
        add("claims_load_unload", True, span=m.group(0), confidence=0.85)

    return _dedupe_same_source_same_value(out)


def _extract_spec_table_facts(text: str, add) -> None:
    """Generic dense-table / label:value parser for manufacturer specs."""
    specs: list[tuple[str, re.Pattern[str]]] = [
        (
            "carrying_capacity",
            re.compile(
                r"(?:payload(?:\s+capacity)?|carrying\s+capacity|load\s+capacity|"
                r"max(?:imum)?\s+payload|rated\s+(?:load|payload)|max\.?\s*weight)\s*"
                r"[:：\|\-–—]\s*"
                r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
                r"(kg|lb|lbs|pounds?|kilograms?)",
                re.I,
            ),
        ),
        (
            "battery_runtime",
            re.compile(
                r"(?:(?:average\s+)?runtime|battery(?:\s+life)?|operation\s+time|"
                r"operating\s+time|run\s*time)\s*"
                r"\*?\s*[:：\|\-–—]\s*"
                r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hours?|min|mins|minutes)",
                re.I,
            ),
        ),
        (
            "reach_or_workspace",
            re.compile(
                r"(?:reach|workspace|wrist\s+reach|max(?:imum)?\s+reach)\s*"
                r"[:：\|\-–—]\s*"
                r"(\d+(?:\.\d+)?)\s*(mm|cm|m|meters?|ft)",
                re.I,
            ),
        ),
        (
            "degrees_of_freedom",
            re.compile(
                r"(?:degrees?\s+of\s+freedom|DoF|DOF)\s*[:：\|\-–—]?\s*(\d{1,2})\b",
                re.I,
            ),
        ),
        (
            "max_speed",
            re.compile(
                r"(?:max(?:imum)?\s+speed|top\s+speed)\s*[:：\|\-–—]\s*"
                r"(\d+(?:\.\d+)?)\s*(m/s|km/h)",
                re.I,
            ),
        ),
        (
            "ingress_protection",
            re.compile(
                r"(?:ingress\s+protection|IP\s*rating)\s*[:：\|\-–—]\s*(IP\d{2}[A-Z]?)",
                re.I,
            ),
        ),
    ]
    for predicate, pat in specs:
        for m in pat.finditer(text):
            if predicate == "ingress_protection":
                add(predicate, m.group(1).upper(), span=m.group(0), confidence=0.93)
                continue
            if predicate == "degrees_of_freedom":
                add(
                    predicate,
                    _num(m.group(1)),
                    span=m.group(0),
                    confidence=0.9,
                    require_subject_near=True,
                    start=m.start(),
                    end=m.end(),
                )
                continue
            raw_u = m.group(2)
            if predicate == "battery_runtime":
                units = "min" if re.search(r"min", str(raw_u), re.I) else "hr"
            elif predicate == "carrying_capacity":
                units = _unit(str(raw_u))
            elif predicate == "reach_or_workspace":
                u = str(raw_u).lower()
                units = (
                    "mm"
                    if u == "mm"
                    else ("cm" if u == "cm" else ("ft" if "ft" in u else "m"))
                )
            else:
                units = "m/s" if "m/s" in str(raw_u).lower() else str(raw_u)
            scope = (
                _infer_payload_scope(text, m.start(), m.end())
                if predicate == "carrying_capacity"
                else "whole_robot"
            )
            add(
                predicate,
                _num(m.group(1)),
                units=units,
                span=m.group(0),
                confidence=0.94,
                require_subject_near=True,
                start=m.start(),
                end=m.end(),
                value_scope=scope,
            )


def _infer_payload_scope(text: str, start: int, end: int) -> str:
    window = text[max(0, start - 50) : end + 50].lower()
    if re.search(r"\bper\s+tray\b|\b/tray\b|\beach\s+tray\b|\btray\s+capacity\b", window):
        return "per_tray"
    if re.search(r"\bper\s+shelf\b|\b/shelf\b", window):
        return "per_shelf"
    if re.search(r"\bper\s+deck\b|\b/deck\b", window):
        return "per_deck"
    if re.search(r"\bper\s+arm\b|\b/arm\b|\beach\s+arm\b", window):
        return "per_arm"
    if re.search(r"\baccessory\b|\badd[- ]?on\b|\boptional\s+module\b", window):
        return "accessory"
    if re.search(r"\btotal\b|\bwhole\b|\boverall\b|\bmax(?:imum)?\s+payload\b", window):
        return "whole_robot"
    return "whole_robot"


def _numeric_value_plausible(
    predicate: str,
    value,
    units: str | None,
    span: str,
    *,
    value_scope: str = "whole_robot",
) -> bool:
    """Reject JS placeholders and wrong-scope numerics (prefer unknown)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return True
    if v == 0:
        return False
    if value_scope in {"per_tray", "per_shelf", "per_deck", "accessory"}:
        return False
    return True


def _subject_near(subject: str, text: str, start: int, end: int, window: int = 140) -> bool:
    if not subject or len(subject) < 2:
        return True
    near = text[max(0, start - window) : end + window].lower()
    from app.services.robot_understanding_v1.sources import subject_tokens

    for tok in subject_tokens(subject):
        if tok and tok in near:
            return True
    if subject.lower() in near:
        return True
    return bool(re.search(r"\b(our\s+robot|this\s+robot)\b", near, re.I))


def _num(s: str) -> float:
    v = float(str(s).replace(",", ""))
    return int(v) if v.is_integer() else v


def _unit(raw: str) -> str:
    r = raw.lower()
    if r.startswith("kg") or "kilogram" in r:
        return "kg"
    return "lb"


def _dedupe_same_source_same_value(facts: list[RobotFact]) -> list[RobotFact]:
    """Drop exact duplicates from one source; keep cross-source contradictions."""
    seen: set[tuple] = set()
    out: list[RobotFact] = []
    for f in facts:
        key = (f.source_id, f.predicate, str(f.value), f.units)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


# Predicates where differing values are true contradictions (not multi-label).
_SCALAR_CONTRADICTION_PREDICATES = frozenset(
    {
        "carrying_capacity",
        "battery_runtime",
        "arm_count",
    }
)


def mark_contradictions(facts: list[RobotFact]) -> list[RobotFact]:
    """
    If same subject+scalar-predicate has differing values, mark epistemic
    as contradicted on conflicting rows (do not drop any).

    Multi-label predicates (e.g. product_class=humanoid and mobile_manipulator)
    are not treated as contradictions.
    """
    from collections import defaultdict

    groups: dict[tuple[str, str], list[RobotFact]] = defaultdict(list)
    for f in facts:
        if f.predicate not in _SCALAR_CONTRADICTION_PREDICATES:
            continue
        groups[(f.subject.lower(), f.predicate)].append(f)

    for rows in groups.values():
        values = {(str(r.value), r.units) for r in rows}
        if len(values) <= 1:
            continue
        for r in rows:
            r.epistemic = "contradicted"
    return facts
