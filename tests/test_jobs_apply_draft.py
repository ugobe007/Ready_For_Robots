"""Apply draft: YouTube optional, why, contacts only when present. Never invent."""
from __future__ import annotations

import json

from app.services.jobs_apply_draft import (
    CONTACTS_EMPTY_NOTE,
    apply_why,
    compose_apply_draft,
    employer_contacts_from_job,
)
from app.services.robot_youtube_evidence import (
    VIDEO_EMPTY_NOTE,
    find_robot_youtube_evidence,
    title_names_robot,
    youtube_search_query,
    youtube_search_url,
)


def test_title_must_name_the_sku():
    assert title_names_robot("Aethon TUG hospital delivery", sku="TUG", company="Aethon")
    assert title_names_robot("Diligent Moxi at work", sku="Moxi", company="Diligent")
    assert title_names_robot("OTTO BOT#25 warehouse", sku="BOT#25", company="OTTO")
    assert not title_names_robot("Warehouse AMR demo", sku="TUG", company="Aethon")
    assert not title_names_robot("Aethon corporate overview", sku="TUG", company="Aethon")
    assert not title_names_robot("Hospital robot", sku="Moxi", company="Diligent")


def test_search_query_and_url_from_company_and_sku():
    q = youtube_search_query("Aethon", "TUG", "TUG")
    assert "Aethon" in q
    assert "TUG" in q
    url = youtube_search_url("Aethon", "TUG", "TUG")
    assert url.startswith("https://www.youtube.com/results?search_query=")
    assert "TUG" in url


def test_data_api_fills_watch_url_when_title_names_sku(monkeypatch):
    payload = {
        "items": [
            {
                "id": {"videoId": "abcdefghijk"},
                "snippet": {
                    "title": "Aethon TUG autonomous delivery",
                    "description": "TUG moving carts in a hospital.",
                },
            }
        ]
    }
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.robot_youtube_evidence._http_get",
        lambda url: json.dumps(payload) if "googleapis.com" in url else None,
    )
    hit = find_robot_youtube_evidence(company="Aethon", sku="TUG", robot="TUG")
    assert hit["video_url"] == "https://www.youtube.com/watch?v=abcdefghijk"
    assert "TUG" in (hit["clip_description"] or hit["video_note"] or "")
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.setattr(
        "app.services.robot_youtube_evidence._http_get",
        lambda url: None,
    )
    hit = find_robot_youtube_evidence(company="Aethon", sku="TUG", robot="TUG")
    assert hit["video_url"] is None
    assert hit["clip_description"] is None
    assert "youtube.com/results" in (hit["video_search_url"] or "")
    assert "empty" in (hit["video_note"] or "").lower() or "guess" in (hit["video_note"] or "").lower()


def test_why_is_spoken_recruiter_not_machine():
    why = apply_why(
        robot_name="TUG",
        employer="Named Hospital",
        work="Cart delivery to the floor",
        workplace="Portland",
    )
    assert "TUG" in why
    assert "Named Hospital" in why
    assert "Cart delivery" in why
    assert "we're putting" in why.lower()
    assert "leverage" not in why.lower()
    assert "unlock" not in why.lower()
    assert "—" not in why


def test_contacts_only_when_present_never_invented():
    assert employer_contacts_from_job({}) == []
    assert employer_contacts_from_job({"employer_email": "Named Employer Inc"}) == []
    assert employer_contacts_from_job({"company_name": "Hospital"}) == []
    people = employer_contacts_from_job({"employer_email": "ops@named-hospital.com"})
    assert people == [{"email": "ops@named-hospital.com", "source": "job_card"}]
    nested = employer_contacts_from_job(
        {"employer": {"contact_email": "facilities@named-hospital.com"}}
    )
    assert nested[0]["email"] == "facilities@named-hospital.com"
    listed = employer_contacts_from_job(
        {"page_emails": ["info@named-hospital.com", "not-an-email"]}
    )
    assert [c["email"] for c in listed] == ["info@named-hospital.com"]


def test_draft_includes_optional_youtube_why_and_contacts():
    with_video = compose_apply_draft(
        robot_name="TUG",
        models=["TUG"],
        employer="Named Hospital",
        work="Cart delivery",
        why="We're putting TUG forward for cart delivery at Named Hospital.",
        video_url="https://www.youtube.com/watch?v=abcdefghijk",
        clip_description="TUG moving carts in a hospital corridor.",
        contacts=[{"email": "ops@named-hospital.com", "source": "job_card"}],
    )
    assert with_video["operator_sends"] is True
    assert with_video["video_url"] == "https://www.youtube.com/watch?v=abcdefghijk"
    assert "ops@named-hospital.com" in with_video["body"]
    assert "TUG" in with_video["why"]
    assert "youtube.com/watch" in with_video["body"]
    assert "Video résumé" in with_video["body"]

    empty = compose_apply_draft(
        robot_name="TUG",
        models=["TUG"],
        employer="Named Hospital",
        work="Cart delivery",
        video_url=None,
        video_note=VIDEO_EMPTY_NOTE,
        contacts=[],
    )
    assert empty["video_url"] is None
    assert empty["contacts"] == []
    assert CONTACTS_EMPTY_NOTE in empty["body"]
    assert "invent" in empty["body"].lower()
    assert VIDEO_EMPTY_NOTE in empty["body"] or "empty" in empty["body"].lower()
