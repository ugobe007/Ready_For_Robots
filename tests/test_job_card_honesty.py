"""Phase 0.5: Job Cards claim only what they can source.

Bundled corpus rows are Examples, carry no invented people or mailboxes, and
never list a robot maker as the employer.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.api.robot_jobs_preview import corpus_preview_jobs
from app.services.job_card_provenance import (
    is_example_job,
    job_source_url,
    public_employer_email,
)
from app.services.jobs_apply_draft import employer_contacts_from_job
from app.services.jobs_crm import stored_employer_email
from app.services.robot_class_qualify import thin_class_profile
from app.services.robot_job_capability_match import load_match_corpus, match_from_chip
from app.services.robot_job_live_corpus import corpus_row_from_robot_job
from app.services.robot_requirement_match import match_jobs_from_profile

CORPUS = Path(__file__).resolve().parents[1] / "app" / "data" / "robot_job_match_corpus.json"
INVENTED_FIELDS = {
    "decision_maker_name",
    "decision_maker_title",
    "decision_maker_department",
    "decision_maker_email",
    "employer_email",
    "contact_name",
    "contact_title",
}


def _no_minted_mail(payload: object) -> None:
    assert "operations@" not in json.dumps(payload).lower()


def test_bundled_corpus_has_no_invented_contacts():
    rows = json.loads(CORPUS.read_text(encoding="utf-8"))["jobs"]
    assert rows
    for row in rows:
        assert not (INVENTED_FIELDS & set(row)), row["job_key"]
        assert is_example_job(row)


def test_minted_ops_mailbox_is_never_public():
    assert public_employer_email("operations@sanmar.com", "SanMar") is None
    assert public_employer_email("operations@harrishealth—lbjhospital.com", "Harris Health — LBJ Hospital") is None
    assert public_employer_email("operations@acme.com", "Named Hospital") == "operations@acme.com"
    assert public_employer_email("jane@sanmar.com", "SanMar") == "jane@sanmar.com"


def test_requirement_matcher_cards_are_examples_without_robot_makers():
    for cls in ("healthcare", "warehouse", "hospitality", "factory"):
        out = match_jobs_from_profile(thin_class_profile("Test Robot", cls))
        assert out["jobs"], cls
        _no_minted_mail(out)
        for job in out["jobs"]:
            assert job["is_example"] is True
            assert job["source_url"] is None
            assert job["employer_email"] is None
            assert "intuitive surgical" not in (job["company_name"] or "").lower()


def test_legacy_corpus_matcher_drops_robot_makers_and_invented_people():
    corpus = load_match_corpus()
    assert not any("intuitive surgical" in (r.get("company_name") or "").lower() for r in corpus)
    for row in corpus:
        assert not (INVENTED_FIELDS - {"employer_email"}) & set(row)
    out = match_from_chip("moves_materials")
    _no_minted_mail(out)
    assert all(job["is_example"] for job in out["jobs"])


def test_live_row_with_posting_is_sourced_and_drops_minted_mail():
    row = SimpleNamespace(
        job_key="h1",
        company_name="Named Hospital",
        locality="Portland, OR",
        action="patient_transport",
        robot_compatible_task="Patient transport AMR",
        employer_email="operations@namedhospital.com",
        contact_url=None,
        apply_url="https://named-hospital.org/careers/robotics",
        requirements={"job_function": "patient_transport", "unknowns": []},
        unknowns=[],
    )
    mapped = corpus_row_from_robot_job(row)
    assert mapped is not None
    assert mapped["employer_email"] is None
    assert job_source_url(mapped) == "https://named-hospital.org/careers/robotics"
    assert not is_example_job(mapped)


def test_crm_never_reads_or_sends_to_minted_mailbox():
    kept = SimpleNamespace(employer_email="operations@napaautoparts.com", employer_name="NAPA Auto Parts")
    assert stored_employer_email(kept) is None
    real = SimpleNamespace(employer_email="jobs@napa.example", employer_name="NAPA Auto Parts")
    assert stored_employer_email(real) == "jobs@napa.example"
    contacts = employer_contacts_from_job(
        {"company_name": "SanMar", "employer_email": "operations@sanmar.com"}
    )
    assert contacts == []


def test_home_preview_fallback_rows_are_examples():
    rows = corpus_preview_jobs(8)
    assert rows
    for row in rows:
        assert row["is_example"] is True
        assert row["source_url"] is None
        assert "intuitive surgical" not in row["employer"].lower()


def test_outbound_openings_do_not_claim_verified_job_openings():
    from types import SimpleNamespace as NS

    from app.services.agent_messaging import PHELAN_INTRO, phelan_opening, phelan_vendor_opening
    from app.services.phelan_autonomy import cal_vendor_outreach_body

    bodies = [
        PHELAN_INTRO,
        phelan_opening(audience="buyer"),
        phelan_opening(audience="vendor"),
        phelan_vendor_opening(),
        phelan_vendor_opening(reminder=True),
        cal_vendor_outreach_body(NS(name="Acme Robotics", industry="logistics")),
    ]
    for body in bodies:
        assert "verified job" not in body.lower()
