"""Share summary excerpt cleanup and hire-aware evidence labels."""

from app.api.leads import _evidence_display_label, _normalize_share_excerpt, _pick_evidence_signal


class _Sig:
    def __init__(self, signal_type: str, signal_text: str, signal_strength: float = 50.0):
        self.signal_type = signal_type
        self.signal_text = signal_text
        self.signal_strength = signal_strength


def test_normalize_share_excerpt_nbsp_and_duplicate_sentence():
    raw = (
        "PM Hotel Group names Kirk Pederson chief operating officer. "
        "PM Hotel Group names Kirk Pederson chief operating officer&nbsp;&nbsp;Hotel Dive"
    )
    out = _normalize_share_excerpt(raw)
    assert "&nbsp;" not in out
    assert "\xa0" not in out
    assert out.lower().count("names kirk pederson") == 1


def test_evidence_label_expansion_coo_headline_reads_as_leadership_hire():
    s = _Sig(
        "expansion",
        "PM Hotel Group names Kirk Pederson chief operating officer. Hotel Dive",
    )
    assert _evidence_display_label(s) == "Leadership Hire"


def test_pick_evidence_prefers_strategic_hire_over_stronger_expansion_when_both_hire_shaped():
    coo = "PM Hotel Group names Kirk Pederson chief operating officer."
    deduped = [
        _Sig("expansion", coo, 90.0),
        _Sig("strategic_hire", "Earlier VP operations hire " + coo, 40.0),
    ]
    top = _pick_evidence_signal(deduped)
    assert top.signal_type == "strategic_hire"
