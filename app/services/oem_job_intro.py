"""Phelan intros for a named-employer job.

OEM copy goes to the robot company. Employer copy goes to the company that
posted the job. Fill only facts we have. Leave blanks for robot SKU, pay,
term, skills, and people — never invent dollars, robots, or match%.
Not FIND. Not SIGNAL buyer mail. FIND does not call this.
"""
from __future__ import annotations

import re
from typing import Any, Optional

BLANK = "_______"
PAY_BLANK = "______"
TERM_BLANK = "_____________ months/years"
_INVENTED_LEAD_RE = re.compile(r"^operational lead\b", re.I)
_EMPTY_CONTACT_RE = re.compile(
    r"not named|hunter\.io found no|will not invent",
    re.I,
)


def _clean(value: Any, *, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _first_name(value: Any) -> str:
    text = _clean(value, limit=80)
    if not text or _EMPTY_CONTACT_RE.search(text) or _INVENTED_LEAD_RE.search(text):
        return ""
    return text.split()[0]


def _named(value: Any) -> str:
    text = _clean(value, limit=240)
    if not text or _EMPTY_CONTACT_RE.search(text) or _INVENTED_LEAD_RE.search(text):
        return ""
    return text


def _clause(value: Any) -> str:
    """A fact dropped into a sentence — no trailing period."""
    text = _named(value)
    return text.rstrip(".,;:") if text else ""


def _insert_words(text: str) -> str:
    """Lowercase Title Case fill-ins so they read mid-sentence.

    Keep ALLCAPS tokens (AMR, GEODIS) and blanks. Do not run this on
    people or employer names.
    """
    if not text or text in {BLANK, PAY_BLANK, TERM_BLANK}:
        return text
    parts: list[str] = []
    for token in text.split(" "):
        if not token:
            continue
        core = token.rstrip(".,;:")
        letters = [c for c in core if c.isalpha()]
        if letters and all(c.isupper() for c in letters) and len(letters) >= 2:
            parts.append(token)
            continue
        parts.append(token.lower())
    return " ".join(parts)


def _pay(value: Any) -> str:
    text = _clean(value, limit=40)
    if not text:
        return ""
    if text.startswith("$"):
        text = text[1:].strip()
    if not re.search(r"\d", text):
        return ""
    return text


def _job_line(
    *,
    title: str = "",
    employer: str = "",
    locality: str = "",
) -> str:
    work = _insert_words(_clean(title, limit=240))
    company = _named(employer)
    place = _clean(locality, limit=160)
    if work and company and place:
        return f"{work} at {company} in {place}"
    if work and company:
        return f"{work} at {company}"
    if work:
        return work
    if company and place:
        return f"work at {company} in {place}"
    if company:
        return f"work at {company}"
    return ""


def _call_with(*, employer: str = "", decision_maker_name: str = "") -> str:
    company = _named(employer)
    person = _named(decision_maker_name)
    first = _first_name(person)
    if first and company:
        return f"{first} at {company}"
    if company:
        return company
    if first:
        return first
    return ""


def compose_robot_company_intro(
    *,
    contact_name: str | None = None,
    robot_name: str | None = None,
    title: str | None = None,
    employer: str | None = None,
    locality: str | None = None,
    job_line: str | None = None,
    monthly_comp: str | None = None,
    duration: str | None = None,
    requirements: str | None = None,
    employer_for_call: str | None = None,
    decision_maker_name: str | None = None,
) -> str:
    """Phelan intro to a robot OEM about one real job. Blanks stay blanks."""
    hi = _first_name(contact_name) or BLANK
    robot = _named(robot_name) or BLANK
    work = _clean(job_line, limit=360) or _job_line(
        title=title or "",
        employer=employer or "",
        locality=locality or "",
    ) or BLANK
    pay = _pay(monthly_comp) or PAY_BLANK
    term = _clean(duration, limit=80) or TERM_BLANK
    reqs = _insert_words(_clean(requirements, limit=360)) or BLANK
    call_with = _named(employer_for_call) or _call_with(
        employer=employer or "",
        decision_maker_name=decision_maker_name or "",
    ) or BLANK
    return (
        f"Hi {hi}, nice to meet you. My name is Phelan and I am a Robot Coordinator "
        "for ReadyForRobots. My job is to help identify and place robots into robot "
        "automation jobs. On that note I found a few job opportunities for your "
        f"{robot} robot that I would like to discuss with you. The job is {work} "
        f"with an expected comp level of ${pay} per month for {term}. The job "
        f"requirements of {reqs} match up with your {robot} robot(s). If interested "
        f"in the job I can arrange a call with {call_with} to discuss their "
        "requirements and how your robots are an ideal match. Let me know you are "
        "interested and available for a quick chat on the job for more specifics. "
        "Thanks and look forward to speaking with you.\n\nPhelan."
    )


def intro_from_sales_card(job: dict[str, Any]) -> str:
    """Build the OEM intro from a daily sales card. Robot SKU and pay stay blank."""
    return compose_robot_company_intro(
        title=str(job.get("title") or job.get("job_type") or ""),
        employer=str(job.get("employer") or ""),
        locality=str(job.get("locality") or ""),
        requirements=str(job.get("description") or job.get("title") or ""),
        decision_maker_name=str(job.get("decision_maker_name") or ""),
        monthly_comp=job.get("monthly_comp"),
        duration=job.get("duration"),
        robot_name=job.get("robot_name"),
        contact_name=job.get("oem_contact_name"),
    )


def compose_employer_need_intro(
    *,
    contact_name: str | None = None,
    announced_need: str | None = None,
    automation_tasks: str | None = None,
    skills: str | None = None,
    capabilities: str | None = None,
) -> str:
    """Phelan intro to a company that posted a robot job. Blanks stay blanks."""
    hi = _first_name(contact_name) or BLANK
    need = _insert_words(_clause(announced_need)) or BLANK
    tasks = _insert_words(_clause(automation_tasks)) or BLANK
    if tasks.lower() == need.lower():
        tasks = BLANK
    skill = _insert_words(_clause(skills)) or BLANK
    caps = _insert_words(_clause(capabilities)) or BLANK
    return (
        f"Hi {hi}, nice to meet you. My name is Phelan, I am a Robot Coordinator "
        "for ReadyForRobots where I help find robots for automation jobs. I noticed "
        f"you announced the need for {need} to help with {tasks} automation tasks "
        f"at your company. I understand the task requires robots with {skill} skills "
        f"and capabilities of {caps}. On that note I found a few robots that match "
        "these requirements I would like to share with you. May I send them to you "
        "for review? Thanks and look forward to learning more.\n\nPhelan."
    )


def employer_intro_from_sales_card(job: dict[str, Any]) -> str:
    """Employer-side intro from a daily sales card. Skills stay blank unless named."""
    title = str(job.get("title") or job.get("job_type") or "")
    description = str(job.get("description") or "")
    return compose_employer_need_intro(
        contact_name=str(job.get("decision_maker_name") or job.get("contact_name") or ""),
        announced_need=title,
        automation_tasks=description if description != title else "",
        skills=job.get("skills"),
        capabilities=job.get("capabilities"),
    )
