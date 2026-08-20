"""JS product pages put capability claims in Next.js / JSON-LD, not visible HTML."""
from __future__ import annotations

import json

from bs4 import BeautifulSoup

from app.services.robot_understanding_v1.fetch import _html_to_text
from app.services.robot_understanding_v1 import facts as F
from app.services.robot_understanding_v1.models import RobotSource


def test_html_to_text_reads_next_json_humanoid():
    payload = {
        "props": {
            "pageProps": {
                "faq": [
                    {
                        "question": "How is NEO powered?",
                        "answer": (
                            "NEO is a fully electronic humanoid robot, with a "
                            ".75 kWh battery pack."
                        ),
                    }
                ]
            }
        }
    }
    html = f"""
    <html><head><title>NEO Home Robot</title></head>
    <body>
      <h1>NEO Home Robot</h1>
      <p>Helping Hand. Walk to Person. Works autonomously by default.</p>
      <script type="application/json">{json.dumps(payload)}</script>
    </body></html>
    """
    text = _html_to_text(BeautifulSoup(html, "html.parser"))
    assert "humanoid" in text.lower()
    assert "helping hand" in text.lower()


def test_html_to_text_ignores_javascript_bundles():
    html = """
    <html><body>
      <p>NEO Home Robot</p>
      <script type="application/javascript">
        const copy = "this humanoid string must not leak from a JS bundle";
      </script>
    </body></html>
    """
    text = _html_to_text(BeautifulSoup(html, "html.parser"))
    assert "humanoid" not in text.lower()


def test_humanoid_in_embedded_json_extracts_product_class():
    src = RobotSource(
        id="s",
        url="https://www.1x.tech/neo",
        source_type="product",
        fetched_at="t",
        title="NEO Home Robot",
        confidence=0.85,
    )
    text = (
        "NEO Home Robot Helping Hand. "
        "NEO is a fully electronic humanoid robot, with a .75 kWh battery pack."
    )
    facts = F._extract_from_page(
        src, text, subject="Neo", page_url="https://www.1x.tech/neo", page_title="NEO Home Robot"
    )
    classes = {
        str(f.value).lower()
        for f in facts
        if f.predicate == "product_class" and f.epistemic != "unknown"
    }
    assert "humanoid" in classes
