"""API signal list dedupe: same headline must not repeat across signal_type rows."""

from app.api.leads import _dedup_top_signals


class _Sig:
    def __init__(self, signal_type: str, signal_text: str, signal_strength: float):
        self.signal_type = signal_type
        self.signal_text = signal_text
        self.signal_strength = signal_strength


def test_dedup_top_signals_same_press_story_one_row_across_types():
    title = (
        "Trailborn Hotels & Resorts Appoints Paul Eckert as Chief Operations Officer "
        "to Lead Next Phase of Growth"
    )
    sigs = [
        _Sig("news", title, 50.0),
        _Sig("strategic_hire", title, 48.0),
        _Sig("expansion", title, 44.0),
    ]
    out = _dedup_top_signals(sigs, 5)
    assert len(out) == 1
    assert out[0].signal_type == "news"
    assert out[0].signal_strength == 50.0


def test_dedup_top_signals_still_one_per_type_when_bodies_differ():
    sigs = [
        _Sig("news", "Company A announces warehouse expansion in Ohio", 40.0),
        _Sig("strategic_hire", "Company A hires VP of supply chain", 39.0),
    ]
    out = _dedup_top_signals(sigs, 5)
    assert len(out) == 2
    types = {s.signal_type for s in out}
    assert types == {"news", "strategic_hire"}
