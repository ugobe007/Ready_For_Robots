"""Cal relationship ladder — teaching follow-ups (Day 7 / 21 / 45).

Each touch must teach one thing in the advisor voice: contain the company name,
end with Cal's sign-off, clear the completeness guard, and carry none of the
banned AI tells or marketing theater.
"""
from app.services.agent_messaging import (
    LADDER_TOUCHES,
    build_buyer_variant_body,
    build_ladder_touch_body,
    ladder_touch_subject,
)
from app.services.cal_draft_guard import is_complete_cal_draft
from app.services.sequence_runner import (
    DEFAULT_BUYER_SEQUENCE,
    _render_sequence_step,
    _step_touch,
)

_INDUSTRIES = (
    "Logistics",
    "Hospitality",
    "Healthcare",
    "Food Service (Restaurants)",
    "Manufacturing",
    "Retail",
    "",  # generic fallback
)

# Cal's voice never uses these — savvy buyers read them as AI slop.
_AI_TELLS = ("honest", "genuinely", "i'd love", "hope you're well", "circling back", "just bumping")
_THEATER = (
    "innovation theater",
    "carpet demo",
    "where the money hides",
    "annoyingly picky",
    "quietly dies",
    'reply "send it"',
)


def test_every_ladder_touch_is_complete_and_named():
    name = "UPS Supply Chain Solutions"
    for industry in _INDUSTRIES:
        for touch in LADDER_TOUCHES:
            subject = ladder_touch_subject(touch, name, industry)
            body = build_ladder_touch_body(touch, name, industry)
            full = f"Subject: {subject}\n\n{body}"
            ok, reason = is_complete_cal_draft(full)
            assert ok, f"{touch}/{industry!r} failed guard: {reason}"
            assert name in body, f"{touch}/{industry!r} missing company name"
            assert body.rstrip().endswith("Ready For Robots")
            assert "— Cal" in body
            assert subject and len(subject) < 90


def test_ladder_touches_have_no_ai_tells_or_theater():
    name = "Acme Distribution"
    for industry in _INDUSTRIES:
        for touch in LADDER_TOUCHES:
            low = build_ladder_touch_body(touch, name, industry).lower()
            for tell in _AI_TELLS:
                assert tell not in low, f"{touch}/{industry!r} regressed AI tell: {tell}"
            for banned in _THEATER:
                assert banned not in low, f"{touch}/{industry!r} regressed theater: {banned}"


def test_ladder_touches_teach_and_differ_from_intro():
    # Each touch should be substantive and distinct from the Day-1 intro variants.
    name = "Globex Logistics"
    intro_bodies = {
        vid: build_buyer_variant_body(name, "Logistics", vid)
        for vid in ("workflow_first", "what_survives", "bottleneck_first")
    }
    seen: set[str] = set()
    for touch in LADDER_TOUCHES:
        body = build_ladder_touch_body(touch, name, "Logistics")
        assert len(body) > 250, f"{touch} too thin to teach"
        assert body not in intro_bodies.values(), f"{touch} duplicates the intro"
        assert body not in seen, f"{touch} duplicates another touch"
        seen.add(body)


def test_industry_touch_differs_from_generic():
    # A recognised industry should get tailored copy, not the generic fallback.
    for touch in LADDER_TOUCHES:
        logistics = build_ladder_touch_body(touch, "Acme", "Logistics")
        generic = build_ladder_touch_body(touch, "Acme", "Sasquatch Wrangling")
        assert logistics != generic, f"{touch} did not specialise for logistics"


def test_default_cadence_delays_and_labels():
    steps = {s["step_number"]: s for s in DEFAULT_BUYER_SEQUENCE["steps"]}
    assert steps[2]["delay_days"] == 6
    assert steps[3]["delay_days"] == 14
    assert steps[4]["delay_days"] == 24
    assert steps[2]["action_label"] == "Teach"
    assert steps[3]["action_label"] == "Trend"
    assert steps[4]["action_label"] == "Question"


class _FakeStep:
    def __init__(self, step_number, action_label="", subject_template="", body_template=""):
        self.step_number = step_number
        self.action_label = action_label
        self.subject_template = subject_template
        self.body_template = body_template


class _FakeAccount:
    def __init__(self, name="Acme Logistics", industry="Logistics"):
        self.name = name
        self.industry = industry
        self.outreach_draft = None


def test_step_touch_maps_by_label_then_number():
    assert _step_touch(_FakeStep(2, action_label="Teach")) == "teach"
    assert _step_touch(_FakeStep(3, action_label="Trend")) == "trend"
    assert _step_touch(_FakeStep(4, action_label="Question")) == "question"
    # Fallback to step number when the label is unhelpful.
    assert _step_touch(_FakeStep(2, action_label="Value follow-up")) == "teach"
    # Intro step has no ladder touch.
    assert _step_touch(_FakeStep(1, action_label="Intro")) is None


def test_render_uses_ladder_for_cal_sequence_and_falls_back_otherwise():
    step = _FakeStep(2, action_label="Teach", subject_template="fallback {company_name}", body_template="fallback body")
    account = _FakeAccount()
    slug = DEFAULT_BUYER_SEQUENCE["slug"]
    subject, body = _render_sequence_step(step, account, sequence_slug=slug)
    assert body == build_ladder_touch_body("teach", account.name, account.industry)
    assert subject == ladder_touch_subject("teach", account.name, account.industry)

    # Non-Cal sequence uses the static template path.
    subj2, body2 = _render_sequence_step(step, account, sequence_slug="some_other_seq")
    assert body2 == "fallback body"
    assert subj2 == "fallback Acme Logistics"
