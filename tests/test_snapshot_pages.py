"""snapshot_pages.entries must see OEM sets stored under products."""

import json
from pathlib import Path

from scripts.snapshot_pages import entries

ROOT = Path(__file__).resolve().parents[1]
RICHTECH = ROOT / "tests" / "fixtures" / "robot_oem_richtech_set.v1.json"


def test_entries_reads_products_as_well_as_robots():
    rows = entries({
        "robots": [{"id": "r1", "url": "https://r.example", "company": "R"}],
        "products": [{
            "id": "p1",
            "url": "https://p.example/adam",
            "company": "Richtech Robotics",
            "target_product": "ADAM",
        }],
        "taxonomy_gap_probes": [],
        "negative_controls": [{"id": "n1", "url": "https://n.example", "description": "not a robot"}],
    })
    assert [(r["id"], r["section"], r["product"]) for r in rows] == [
        ("r1", "robots", ""),
        ("p1", "products", "ADAM"),
        ("n1", "negative_controls", ""),
    ]


def test_richtech_set_snapshots_eight_product_pages():
    benchmark = json.loads(RICHTECH.read_text())
    rows = entries(benchmark)
    assert [r["id"] for r in rows] == [p["id"] for p in benchmark["products"]]
    assert len(rows) == 8
    assert rows[0]["product"] == "ADAM"
    assert rows[0]["url"].endswith("/solutions/adam")
    assert {r["section"] for r in rows} == {"products"}
