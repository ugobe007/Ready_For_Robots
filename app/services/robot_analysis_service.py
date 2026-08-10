"""V1 Slice 1 — robot analysis orchestration."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.domain.v1_coverage import (
    SUPPORTED_V1_CATEGORIES,
    V1_HUMANOID_INDUSTRIES,
    V1_HUMANOID_USE_CASES,
    V1_LOGISTICS_INDUSTRIES,
    V1_LOGISTICS_USE_CASES,
)
from app.models.robot import Robot
from app.models.robot_catalog import Manufacturer, RobotConfiguration, RobotFamily, RobotModel
from app.models.robot_intelligence import (
    EvidenceClaim,
    RobotAnalysis,
    RobotCapability,
    RobotProfileVersion,
)
from app.services.robot_profile_extract import (
    ExtractionResult,
    extract_robot_profile,
    fetch_product_page,
)
from app.services.robot_url_safety import UrlSafetyError, assert_public_http_url, normalize_product_url



def create_analysis(
    db: Session,
    *,
    source_url: str | None = None,
    description: str | None = None,
    requester_scope: str | None = None,
    created_by_user_id=None,
    fetcher=None,
    process_inline: bool = True,
) -> RobotAnalysis:
    if not source_url and not description:
        raise ValueError("Provide source_url or description")

    normalized = None
    if source_url:
        normalized = assert_public_http_url(source_url)

    # Deduplicate active analyses for same URL + scope.
    if normalized:
        existing = (
            db.query(RobotAnalysis)
            .filter(
                RobotAnalysis.normalized_url == normalized,
                RobotAnalysis.requester_scope == (requester_scope or None),
                RobotAnalysis.status.in_(
                    ["queued", "crawling", "extracting", "needs_review"]
                ),
            )
            .order_by(RobotAnalysis.created_at.desc())
            .first()
        )
        if existing:
            return existing

    analysis = RobotAnalysis(
        id=_new_uuid(db),
        analysis_token=secrets.token_urlsafe(24),
        status="queued",
        progress=0,
        message="Analysis queued",
        retryable=False,
        warnings=[],
        source_url=source_url,
        normalized_url=normalized,
        description=(description or None),
        requester_scope=requester_scope,
        created_by_user_id=_uuid_value(db, created_by_user_id),
    )
    db.add(analysis)
    db.flush()
    if process_inline:
        process_analysis(db, analysis, fetcher=fetcher)
    return analysis


def process_analysis(db: Session, analysis: RobotAnalysis, *, fetcher=None) -> RobotAnalysis:
    try:
        analysis.status = "crawling"
        analysis.progress = 15
        analysis.message = "Fetching product page"
        db.flush()

        html = None
        fetched_at = datetime.now(timezone.utc).isoformat()
        final_url = analysis.normalized_url
        if analysis.normalized_url:
            fetched = fetch_product_page(analysis.normalized_url, fetcher=fetcher)
            html = fetched.get("html")
            final_url = fetched.get("url") or final_url
            fetched_at = fetched.get("fetched_at") or fetched_at
            analysis.raw_fetch = {
                "url": final_url,
                "fetched_at": fetched_at,
                "bytes": len(html or ""),
            }

        analysis.status = "extracting"
        analysis.progress = 55
        analysis.message = "Extracting grounded claims"
        db.flush()

        extraction = extract_robot_profile(
            html=html,
            description=analysis.description,
            source_url=final_url or analysis.source_url,
            fetched_at=fetched_at,
        )
        return _apply_extraction(db, analysis, extraction, source_url=final_url or analysis.source_url)
    except UrlSafetyError as exc:
        analysis.status = "failed"
        analysis.progress = 100
        analysis.message = str(exc)
        analysis.retryable = False
        analysis.warnings = [str(exc)]
        db.flush()
        return analysis
    except Exception as exc:
        analysis.status = "failed"
        analysis.progress = 100
        analysis.message = str(exc)
        analysis.retryable = True
        analysis.warnings = [str(exc)]
        db.flush()
        return analysis


def confirm_analysis(
    db: Session,
    analysis: RobotAnalysis,
    *,
    profile_etag: str,
    corrections: list[dict[str, Any]],
    created_by_user_id=None,
) -> dict[str, Any]:
    if analysis.status not in {"needs_review", "confirmed"}:
        raise ValueError("Analysis is not ready for confirmation")
    if analysis.status == "confirmed" and analysis.confirmed_profile_version_id:
        raise ValueError("Analysis already confirmed")
    if not analysis.profile_etag or analysis.profile_etag != profile_etag:
        raise ValueError("profile_etag mismatch; refresh the draft profile")

    draft = dict(analysis.draft_profile or {})
    fields = {f["field_path"]: f for f in draft.get("fields", []) if f.get("field_path")}

    for correction in corrections:
        path = correction.get("field_path")
        if not path:
            raise ValueError("Each correction requires field_path")
        if correction.get("truth_state") != "oem_verified":
            raise ValueError("Corrections must use truth_state=oem_verified")
        fields[path] = {
            "field_path": path,
            "value": correction.get("value"),
            "truth_state": "oem_verified",
            "confidence": 1.0,
            "evidence_refs": [],
            "unit": (fields.get(path) or {}).get("unit"),
            "note": correction.get("note"),
        }

    draft_fields = list(fields.values())
    manufacturer = _field_value(draft_fields, "manufacturer") or "Unknown"
    model = _field_value(draft_fields, "model") or "Unknown"
    category = _field_value(draft_fields, "category")
    if category not in SUPPORTED_V1_CATEGORIES:
        raise ValueError("Confirm requires a supported V1 robot category")

    robot = _upsert_robot(db, manufacturer=str(manufacturer), model=str(model), category=str(category), source_url=analysis.normalized_url)
    version_no = 1 + (
        db.query(RobotProfileVersion)
        .filter(RobotProfileVersion.robot_id == robot.id)
        .count()
    )
    previous = (
        db.query(RobotProfileVersion)
        .filter(RobotProfileVersion.robot_id == robot.id)
        .order_by(RobotProfileVersion.version.desc())
        .first()
    )

    profile = RobotProfileVersion(
        id=_new_uuid(db),
        robot_id=robot.id,
        version=version_no,
        source_url=analysis.normalized_url or analysis.source_url,
        manufacturer=str(manufacturer),
        model=str(model),
        category=str(category),
        robot_model_id=_uuid_value(db, robot.robot_model_id) if robot.robot_model_id else None,
        robot_configuration_id=_uuid_value(db, robot.robot_configuration_id) if robot.robot_configuration_id else None,
        work_envelope=draft.get("work_envelope") or [],
        physical_capabilities=_physical_from_fields(draft_fields),
        verification_state="oem_verified" if corrections else "inferred",
        confidence=_profile_confidence(draft_fields),
        commercial_maturity=_commercial_maturity_for_robot(db, robot),
        created_by_user_id=_uuid_value(db, created_by_user_id),
        supersedes_version_id=previous.id if previous else None,
        analysis_id=analysis.id,
    )
    db.add(profile)
    db.flush()

    claim_ids_by_field: dict[str, str] = {}
    for field in draft_fields:
        claim = EvidenceClaim(
            id=_new_uuid(db),
            entity_type="robot_profile",
            entity_id=str(profile.id),
            field_path=field["field_path"],
            value=field.get("value"),
            truth_state=field.get("truth_state") or "unknown",
            source_type="oem_correction" if field.get("truth_state") == "oem_verified" else "product_page",
            source_url=analysis.normalized_url or analysis.source_url,
            source_id=analysis.profile_etag,
            excerpt=field.get("excerpt"),
            observed_at=datetime.now(timezone.utc),
            confidence=float(field.get("confidence") or 0),
            recorded_by_user_id=_uuid_value(db, created_by_user_id),
        )
        # Observed claims require excerpt + timestamp (Slice 1 acceptance).
        if claim.truth_state == "observed" and not claim.excerpt:
            raise ValueError(f"Observed claim {claim.field_path} requires source excerpt")
        db.add(claim)
        db.flush()
        claim_ids_by_field[field["field_path"]] = str(claim.id)
        field["evidence_refs"] = [str(claim.id)]

        cap = RobotCapability(
            id=_new_uuid(db),
            robot_profile_version_id=profile.id,
            capability_key=field["field_path"],
            operator="eq" if field.get("value") is not None else None,
            numeric_value=field.get("value") if isinstance(field.get("value"), (int, float)) else None,
            text_value=str(field.get("value")) if field.get("value") is not None and not isinstance(field.get("value"), (int, float)) else None,
            unit=field.get("unit"),
            constraints={},
            truth_state=claim.truth_state,
            confidence=claim.confidence,
            claim_ids=[str(claim.id)],
        )
        db.add(cap)

    search_id = _new_uuid(db)
    analysis.robot_id = robot.id
    analysis.confirmed_profile_version_id = profile.id
    analysis.opportunity_search_id = search_id
    analysis.status = "confirmed"
    analysis.progress = 100
    analysis.message = "Profile confirmed"
    analysis.draft_profile = {
        **draft,
        "fields": draft_fields,
        "robot_id": robot.id,
        "profile_version_id": str(profile.id),
    }
    db.flush()

    unknowns = [
        f["field_path"]
        for f in draft_fields
        if f.get("truth_state") == "unknown" or f.get("value") is None
    ]
    return {
        "schema_version": "v1",
        "robot_id": robot.id,
        "profile_version_id": str(profile.id),
        "opportunity_search_id": str(search_id),
        "critical_unknowns": unknowns,
    }


def analysis_to_api(analysis: RobotAnalysis) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "analysis_id": str(analysis.id),
        "status": analysis.status,
        "progress": int(analysis.progress or 0),
        "message": analysis.message,
        "retryable": bool(analysis.retryable),
        "warnings": analysis.warnings or [],
        "profile_etag": analysis.profile_etag,
        "draft_profile": analysis.draft_profile,
        "robot_id": analysis.robot_id,
        "confirmed_profile_version_id": str(analysis.confirmed_profile_version_id)
        if analysis.confirmed_profile_version_id
        else None,
    }


def get_analysis_for_token(db: Session, analysis_id: str, analysis_token: str | None) -> RobotAnalysis | None:
    analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == analysis_id).first()
    if not analysis:
        # sqlite may store uuid as string
        analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == str(analysis_id)).first()
    if not analysis:
        return None
    if analysis_token and analysis.analysis_token != analysis_token:
        return None
    return analysis


def _apply_extraction(
    db: Session,
    analysis: RobotAnalysis,
    extraction: ExtractionResult,
    *,
    source_url: str | None,
) -> RobotAnalysis:
    fields = []
    for claim in extraction.claims:
        entry = {
            "field_path": claim.field_path,
            "value": claim.value,
            "truth_state": claim.truth_state,
            "confidence": claim.confidence,
            "evidence_refs": [],
            "excerpt": claim.excerpt,
            "unit": claim.unit,
        }
        if claim.truth_state == "observed" and not claim.excerpt:
            entry["truth_state"] = "unknown"
            entry["value"] = None
            entry["confidence"] = 0.0
            analysis.warnings = [*(analysis.warnings or []), f"Dropped observed claim without excerpt: {claim.field_path}"]
        fields.append(entry)

    if not extraction.category_supported:
        if extraction.category == "unsupported" or (
            extraction.category and extraction.category not in SUPPORTED_V1_CATEGORIES
        ):
            analysis.status = "unsupported_robot"
            analysis.progress = 100
            analysis.message = "Robot category is outside the V1 wedge"
        elif not any(f.get("value") is not None for f in fields):
            analysis.status = "insufficient_product_evidence"
            analysis.progress = 100
            analysis.message = "Not enough product evidence to build a profile"
        else:
            # Keep draft for review but mark unsupported if category unknown.
            analysis.status = "needs_review"
            analysis.progress = 100
            analysis.message = "Draft profile ready for review"
            analysis.warnings = [*(analysis.warnings or []), "Category not confirmed as V1 material-movement class"]
    else:
        analysis.status = "needs_review"
        analysis.progress = 100
        analysis.message = "Draft profile ready for review"

    profile_body = {
        "manufacturer": extraction.manufacturer,
        "model": extraction.model,
        "category": extraction.category,
        "source_url": source_url,
        "page_title": extraction.page_title,
        "work_envelope": extraction.work_envelope,
        "fields": fields,
        "confidence": _profile_confidence(fields),
    }
    etag = hashlib.sha256(
        f"{extraction.content_hash}:{source_url}:{extraction.category}".encode("utf-8")
    ).hexdigest()[:32]

    analysis.profile_etag = etag
    analysis.draft_profile = profile_body
    analysis.warnings = list(dict.fromkeys([*(analysis.warnings or []), *extraction.warnings]))
    db.flush()
    return analysis


def _slugify(value: str) -> str:
    raw = "".join(ch.lower() if ch.isalnum() else "-" for ch in (value or "").strip())
    while "--" in raw:
        raw = raw.replace("--", "-")
    return raw.strip("-") or "unknown"


def _ensure_catalog_model(
    db: Session, *, manufacturer: str, model: str, category: str, source_url: str | None
) -> tuple[Manufacturer, RobotFamily, RobotModel, RobotConfiguration]:
    """Resolve or create manufacturer → family → model → default configuration."""
    mfr_slug = _slugify(manufacturer)
    mfr = db.query(Manufacturer).filter(Manufacturer.slug == mfr_slug).first()
    if mfr is None:
        mfr = Manufacturer(
            id=_new_uuid(db),
            slug=mfr_slug,
            name=manufacturer,
            website=source_url,
            calibration_tier=2,
            external_refs={},
        )
        db.add(mfr)
        db.flush()

    fam_slug = f"{mfr_slug}-analyzed"
    fam = (
        db.query(RobotFamily)
        .filter(RobotFamily.manufacturer_id == mfr.id, RobotFamily.slug == fam_slug)
        .first()
    )
    if fam is None:
        fam = RobotFamily(
            id=_new_uuid(db),
            manufacturer_id=mfr.id,
            slug=fam_slug,
            name=f"{manufacturer} analyzed",
            primary_class=category,
        )
        db.add(fam)
        db.flush()

    model_slug = f"{mfr_slug}-{_slugify(model)}"
    robot_model = db.query(RobotModel).filter(RobotModel.slug == model_slug).first()
    if robot_model is None:
        robot_model = RobotModel(
            id=_new_uuid(db),
            manufacturer_id=mfr.id,
            family_id=fam.id,
            slug=model_slug,
            name=model,
            primary_class=category,
            work_to_map=[],
            calibration_tier=2,
            commercial_maturity="unknown",
            product_url=source_url,
            capability_stubs=[],
            work_envelope_stubs=[],
            external_refs={"source": "robot_analysis"},
            is_active=True,
        )
        db.add(robot_model)
        db.flush()
    else:
        if source_url and not robot_model.product_url:
            robot_model.product_url = source_url
        robot_model.primary_class = category or robot_model.primary_class

    cfg = (
        db.query(RobotConfiguration)
        .filter(RobotConfiguration.robot_model_id == robot_model.id, RobotConfiguration.slug == "default")
        .first()
    )
    if cfg is None:
        cfg = RobotConfiguration(
            id=_new_uuid(db),
            robot_model_id=robot_model.id,
            slug="default",
            name="Default",
            is_default=True,
            options={},
        )
        db.add(cfg)
        db.flush()
    return mfr, fam, robot_model, cfg


def _commercial_maturity_for_robot(db: Session, robot: Robot) -> str | None:
    if not robot.robot_model_id:
        return None
    model = db.query(RobotModel).filter(RobotModel.id == robot.robot_model_id).first()
    return model.commercial_maturity if model else None


def _upsert_robot(db: Session, *, manufacturer: str, model: str, category: str, source_url: str | None) -> Robot:
    robot_type = {
        "autonomous_forklift": "logistics",
        "amr": "logistics",
        "autonomous_tugger": "logistics",
        "material_movement": "logistics",
        "humanoid": "humanoid",
    }.get(category, "logistics")

    mfr, _fam, robot_model, cfg = _ensure_catalog_model(
        db, manufacturer=manufacturer, model=model, category=category, source_url=source_url
    )

    existing = (
        db.query(Robot)
        .filter(Robot.vendor == manufacturer, Robot.name == model)
        .first()
    )
    if existing:
        if source_url and not existing.product_url:
            existing.product_url = source_url
        if category == "humanoid":
            existing.industries = list(V1_HUMANOID_INDUSTRIES)
            existing.use_cases = list(V1_HUMANOID_USE_CASES)
        existing.manufacturer_id = str(mfr.id)
        existing.robot_model_id = str(robot_model.id)
        existing.robot_configuration_id = str(cfg.id)
        return existing
    robot = Robot(
        name=model,
        vendor=manufacturer,
        robot_type=robot_type,
        product_url=source_url,
        tagline=f"{category.replace('_', ' ')}",
        description=f"V1 profile for {manufacturer} {model}",
        is_active=True,
        is_preferred=False,
        features=[],
        industries=(
            list(V1_HUMANOID_INDUSTRIES)
            if category == "humanoid"
            else list(V1_LOGISTICS_INDUSTRIES)
        ),
        use_cases=(
            list(V1_HUMANOID_USE_CASES)
            if category == "humanoid"
            else list(V1_LOGISTICS_USE_CASES)
        ),
        manufacturer_id=str(mfr.id),
        robot_model_id=str(robot_model.id),
        robot_configuration_id=str(cfg.id),
    )
    db.add(robot)
    db.flush()
    return robot


def _field_value(fields: list[dict[str, Any]], path: str) -> Any:
    for field in fields:
        if field.get("field_path") == path:
            return field.get("value")
    return None


def _physical_from_fields(fields: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in fields:
        path = field.get("field_path")
        if path in {"payload_max_kg", "lift_height_max_m", "speed_mps", "runtime_hours", "environment", "navigation", "human_interaction"}:
            out[path] = {
                "value": field.get("value"),
                "unit": field.get("unit"),
                "truth_state": field.get("truth_state"),
                "confidence": field.get("confidence"),
            }
    return out


def _profile_confidence(fields: list[dict[str, Any]]) -> float:
    known = [float(f.get("confidence") or 0) for f in fields if f.get("truth_state") not in {None, "unknown"}]
    if not known:
        return 0.0
    return round(sum(known) / len(fields), 4)


def _uuid_value(db: Session, value):
    if value is None:
        return None
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _new_uuid(db: Session):
    value = uuid.uuid4()
    return str(value) if db.bind and db.bind.dialect.name == "sqlite" else value


# re-export for callers
__all__ = [
    "create_analysis",
    "process_analysis",
    "confirm_analysis",
    "analysis_to_api",
    "get_analysis_for_token",
    "normalize_product_url",
]
