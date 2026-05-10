from app.services.lead_signal_display import (
    core_need_from_top_signal,
    format_signal_for_sales,
    normalize_signal_text_for_storage,
    pick_primary_sentence,
    strip_extraction_artifacts,
)


def test_strip_bracket_code_and_fenced():
    raw = (
        "[code] Acme opened a 200k sq ft automated fulfillment hub in Ohio. "
        '```json\n{"x": 1}\n``` '
        "The site will deploy palletizing robots next year."
    )
    out = strip_extraction_artifacts(raw)
    assert "[code]" not in out.lower()
    assert "```" not in out
    assert "fulfillment hub" in out.lower()
    assert "palletizing" in out.lower()


def test_strip_meta_lines():
    raw = "Confidence: 0.9\nRationale: labor shortage\nThe plant added a second shift and is hiring 40 operators."
    out = strip_extraction_artifacts(raw)
    assert "confidence" not in out.lower()
    assert "second shift" in out.lower()


def test_pick_primary_sentence_skips_leadin():
    raw = (
        "According to the press release, nothing happened. "
        "Marriott is piloting service robots at two flagship hotels to address housekeeping gaps."
    )
    s = pick_primary_sentence(raw, max_chars=300)
    assert "marriott" in s.lower()
    assert "according" not in s.lower()


def test_normalize_signal_text_for_storage_preserves_story():
    raw = "[code] " + ("word " * 500)
    s = normalize_signal_text_for_storage(raw, max_chars=200)
    assert len(s) <= 201
    assert "word" in s


def test_format_signal_for_sales_caps():
    long = "word " * 200
    s = format_signal_for_sales(long, max_chars=80)
    assert len(s) <= 83
    assert s.endswith("…")


class _Sig:
    def __init__(self, text):
        self.signal_text = text


def test_core_need_from_top_signal():
    top = _Sig("[explanation] Series B closed. Warehouse plans AMR rollout for Q3.")
    out = core_need_from_top_signal(top)
    assert "warehouse" in out.lower()
    assert "[explanation]" not in out.lower()
