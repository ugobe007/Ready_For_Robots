"""Vendor URL lookup from the /robots index — no homepage guessing."""
from __future__ import annotations

from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.resolve import resolve_identity
from app.services.vendor_robot_lookup import (
    is_junk_lookup_host,
    lookup_vendor_by_url,
    profile_from_specs,
    select_index_robot,
)


def _page(*, url: str, title: str = "", text: str = "", links: list[tuple[str, str]] | None = None) -> FetchedPage:
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        text=text,
        html=f"<html><title>{title}</title><body>{text}</body></html>",
        links=links or [],
    )


UNITREE = {
    "vendor_name": "Unitree Robotics",
    "domains": ["unitree.com"],
    "vendor_url": "https://www.unitree.com",
    "list_category": "humanoid",
    "robots": [
        {
            "name": "Unitree G1",
            "model_slug": "unitree-g1",
            "product_url": "https://www.unitree.com/g1",
        },
        {
            "name": "Unitree H1",
            "model_slug": "unitree-h1",
            "product_url": "https://www.unitree.com/h1",
        },
        {
            "name": "Unitree R1",
            "model_slug": "unitree-r1",
            "product_url": "https://www.unitree.com",
        },
    ],
}


def test_junk_press_hosts_are_not_vendor_keys():
    assert is_junk_lookup_host("morningstar.com")
    assert is_junk_lookup_host("www.tmcnet.com")
    assert is_junk_lookup_host("finance.yahoo.com")
    assert not is_junk_lookup_host("unitree.com")
    assert not is_junk_lookup_host("en.engineai.com.cn")


def test_lookup_matches_vendor_homepage_and_sku_path():
    idx = {"vendors": [UNITREE]}
    home = lookup_vendor_by_url("https://www.unitree.com/", index=idx)
    assert home is not None
    assert home["vendor_name"] == "Unitree Robotics"
    assert len(home["robots"]) == 3
    sku = select_index_robot("https://www.unitree.com/g1", home)
    assert sku is not None
    assert sku["name"] == "Unitree G1"
    assert lookup_vendor_by_url("https://www.morningstar.com/news/ubtech", index=idx) is None


def test_resolve_returns_indexed_skus_when_homepage_is_empty(monkeypatch):
    import app.services.robot_understanding_v1.resolve as R

    monkeypatch.setattr(R, "lookup_vendor_by_url", lambda url: UNITREE)
    resolved = resolve_identity("https://www.unitree.com/", _page(url="https://www.unitree.com/"))
    names = {p.name for p in resolved.products}
    assert {"Unitree G1", "Unitree H1", "Unitree R1"} <= names
    assert resolved.company.name == "Unitree Robotics"
    assert any("Vendor index matched" in n for n in resolved.notes)


def test_resolve_selects_sku_from_product_url(monkeypatch):
    import app.services.robot_understanding_v1.resolve as R

    monkeypatch.setattr(R, "lookup_vendor_by_url", lambda url: UNITREE)
    resolved = resolve_identity(
        "https://www.unitree.com/g1",
        _page(url="https://www.unitree.com/g1", title="G1"),
    )
    assert resolved.selected_product is not None
    assert "G1" in resolved.selected_product.name


def test_catalog_vendor_picker_does_not_add_homepage_extras(monkeypatch):
    import app.services.robot_understanding_v1.resolve as R

    monkeypatch.setattr(R, "lookup_vendor_by_url", lambda url: UNITREE)
    home = _page(
        url="https://www.unitree.com/",
        title="Unitree",
        text="Unitree B2 robot payload Unitree B2 quadruped robot. Learn More. 4D LiDAR G1.",
        links=[
            ("https://www.unitree.com/b2", "B2"),
            ("https://www.unitree.com/learn-more", "Learn More"),
            ("https://www.unitree.com/lidar", "4D LiDAR G1"),
        ],
    )
    resolved = resolve_identity("https://www.unitree.com/", home)
    names = {p.name for p in resolved.products}
    assert "Unitree G1" in names
    assert "Unitree H1" in names
    assert not any("B2" == n or n.endswith(" B2") for n in names)
    assert "Learn More" not in names
    assert not any("lidar" in n.lower() for n in names)
    assert any("index SKUs only" in n for n in resolved.notes)


def test_homepage_and_locale_root_do_not_select_a_sku():
    assert select_index_robot("https://www.unitree.com/", UNITREE) is None
    assert select_index_robot("https://www.unitree.com", UNITREE) is None
    ubtech = {
        "vendor_name": "UBTECH Robotics",
        "robots": [
            {
                "name": "Walker X",
                "model_slug": "ubtech-walker-x",
                "product_url": "https://www.ubtrobot.com/en/",
            },
            {
                "name": "U1 Pro",
                "model_slug": "ubtech-u1-pro",
                "product_url": "https://www.ubtrobot.com",
            },
        ],
    }
    assert select_index_robot("https://www.ubtrobot.com/", ubtech) is None
    assert select_index_robot("https://www.ubtrobot.com/en/", ubtech) is None


def test_shipped_index_resolves_oem_homepages_without_guessing():
    from app.services.vendor_robot_lookup import (
        index_robot_names,
        load_vendor_robots_index,
        reload_vendor_robots_index,
    )

    reload_vendor_robots_index()
    index = load_vendor_robots_index()
    assert index["robot_count"] >= 114
    assert index["vendor_count"] >= 60

    unitree = lookup_vendor_by_url("https://www.unitree.com/")
    assert unitree is not None
    unitree_names = " ".join(index_robot_names(unitree))
    assert "G1" in unitree_names
    assert "H1" in unitree_names
    assert len(unitree["robots"]) >= 3

    engine_com = lookup_vendor_by_url("https://www.engineai.com/")
    engine_cn = lookup_vendor_by_url("https://en.engineai.com.cn/")
    assert engine_com is not None
    assert engine_cn is not None
    slugs_com = {r["model_slug"] for r in engine_com["robots"]}
    slugs_cn = {r["model_slug"] for r in engine_cn["robots"]}
    assert slugs_com == slugs_cn
    assert {"engineai-pm01", "engineai-t800", "engineai-sa01"} <= slugs_com

    ubtech = lookup_vendor_by_url("https://www.ubtrobot.com/")
    assert ubtech is not None
    ub_names = " ".join(index_robot_names(ubtech))
    assert "Walker" in ub_names
    assert "U1" in ub_names

    assert lookup_vendor_by_url("https://www.figure.ai/") is not None
    assert lookup_vendor_by_url("https://www.keenonrobot.com/") is not None
    assert lookup_vendor_by_url("https://www.magiclab.top/") is not None
    assert lookup_vendor_by_url("https://www.agibot.com/") is not None
    assert lookup_vendor_by_url("https://www.morningstar.com/news/ubtech") is None
    assert lookup_vendor_by_url("https://www.tmcnet.com/usubmit/keenon") is None


def test_jobs_seed_name_collision_still_pins_ur20_url():
    from app.services.vendor_robot_lookup import names_are_same_sku

    assert names_are_same_sku("UR20", "Universal Robots UR20")
    assert names_are_same_sku("T8", "Keenon T8")
    assert not names_are_same_sku("T8", "T80")
    assert not names_are_same_sku("Servi", "Servi Plus")
    jobs = {
        "vendor_name": "Universal Robots",
        "domains": ["universal-robots.com"],
        "robots": [
            {
                "name": "Universal Robots UR20",
                "model_slug": "universal-robots-universal-robots-ur20",
                "product_url": "https://www.universal-robots.com",
                "catalog_claims": [{"predicate": "product_class", "value": "cobot"}],
            }
        ],
    }
    oem = {
        "vendor_name": "Universal Robots",
        "domains": ["universal-robots.com"],
        "robots": [
            {
                "name": "UR20",
                "model_slug": "universal-robots-ur20",
                "product_url": "https://www.universal-robots.com/products/ur20/",
                "catalog_claims": [],
                "specs": {},
            }
        ],
    }
    merged = lookup_vendor_by_url(
        "https://www.universal-robots.com/products/ur20/",
        index={"vendors": [jobs, oem]},
    )
    assert merged is not None
    assert len(merged["robots"]) == 1
    assert merged["robots"][0]["name"] == "Universal Robots UR20"
    assert merged["robots"][0]["product_url"].rstrip("/").endswith("/ur20")
    sku = select_index_robot("https://www.universal-robots.com/products/ur20/", merged)
    assert sku is not None
    assert "UR20" in sku["name"]


def test_vega_and_stretch_keep_richer_rows_on_merge():
    dexmate = {
        "vendor_name": "Dexmate",
        "domains": ["dexmate.ai"],
        "robots": [
            {
                "name": "Dexmate Vega",
                "model_slug": "dexmate-vega",
                "product_url": "https://www.dexmate.ai/product/vega",
                "catalog_claims": [{"predicate": "product_class", "value": "mobile_manipulator"}],
                "specs": {"payload_kg": 10},
            }
        ],
    }
    thin = {
        "vendor_name": "Dexmate",
        "domains": ["dexmate.ai"],
        "robots": [
            {
                "name": "Vega",
                "model_slug": "dexmate-vega-thin",
                "product_url": "https://www.dexmate.ai/",
                "catalog_claims": [],
                "specs": {},
            }
        ],
    }
    hit = lookup_vendor_by_url("https://www.dexmate.ai/product/vega", index={"vendors": [dexmate, thin]})
    assert hit is not None
    assert len(hit["robots"]) == 1
    assert hit["robots"][0]["name"] == "Dexmate Vega"
    assert hit["robots"][0]["specs"]["payload_kg"] == 10
    sku = select_index_robot("https://www.dexmate.ai/product/vega", hit)
    assert sku is not None
    assert "Vega" in sku["name"]


def test_oem_sku_seed_replaces_humanoid_index_dump():
    idx = {
        "vendors": [
            {
                "vendor_name": "Galbot",
                "domains": ["galbot.com"],
                "vendor_url": "https://www.galbot.com",
                "list_category": "humanoid",
                "robots": [
                    {"name": "Galbot G1", "model_slug": "galbot-g1"},
                    {"name": "Galbot G2", "model_slug": "galbot-g2"},
                ],
            },
            {
                "vendor_name": "Galbot",
                "domains": ["galbot.com"],
                "vendor_url": "https://www.galbot.com",
                "list_category": "oem_sku",
                "robots": [
                    {"name": "Galbot G1", "model_slug": "galbot-galbot-g1"},
                    {"name": "Galbot S1", "model_slug": "galbot-galbot-s1"},
                ],
            },
        ]
    }
    hit = lookup_vendor_by_url("https://galbot.com/", index=idx)
    assert hit is not None
    names = [r["name"] for r in hit["robots"]]
    assert names == ["Galbot G1", "Galbot S1"]
    assert "Galbot G2" not in names


def test_profile_from_specs_is_identity_not_a_guess():
    profile = profile_from_specs(
        robot_name="Unitree G1",
        vendor_name="Unitree Robotics",
        domain="unitree.com",
        product_url="https://www.unitree.com/g1",
        specs={"payload_kg": 3, "battery_life_h": 2, "height_cm": 127},
    )
    assert profile["source"] == "vendor_robots_index"
    assert profile["profile_confidence"] in {"B", "C"}
    predicates = {f["predicate"] for f in profile["facts"]}
    assert "product_class" in predicates
    assert "payload" in predicates
