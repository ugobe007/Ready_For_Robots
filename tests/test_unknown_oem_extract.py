"""Unknown-OEM FIND extraction: catalog is cache, evidence is the resolver.

Held-out picker: chrome/vehicle/nav never SKUs. Empty is honest.
Do not flake on live 403 — fixtures from measured pages; one live smoke if 200.
"""
from __future__ import annotations

import json
import urllib.request

from app.services.jobs_oem_listing import listing_payload_for_url
from app.services.oem_sku_discover import (
    classify_href_candidate,
    href_is_vehicle_path,
    is_site_chrome_name,
    is_site_chrome_slug,
    name_is_proven_product,
)
from app.services.pstack_protocol import CRITIC_HELDOUT_FIND_URLS
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import NAMESPACE, clear_profile_cache_memory
from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.resolve import (
    _discover_product_names,
    _sku_from_product_href,
    resolve_identity,
)
from app.services.vendor_robot_lookup import lookup_vendor_by_url


CHROME = (
    "Product",
    "Products",
    "Produkt",
    "Imprint",
    "Impressum",
    "AGB",
    "Datenschutz",
    "Terms",
    "Privacy",
    "Investors",
    "Vehicles",
    "News",
    "Blog",
    "Careers",
    "Contact",
    "Shop",
    "About",
)

_CHROME_SLUGS = (
    "product",
    "imprint",
    "agb",
    "about",
    "investors",
    "vehicles",
    "news",
    "blog",
    "careers",
    "contact",
    "shop",
)


def _page(*, title: str, text: str, url: str, links: list[tuple[str, str]], html: str = "") -> FetchedPage:
    body = html or f"<html><title>{title}</title><body>{text}</body></html>"
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        text=text,
        html=body,
        links=links,
    )


def setup_function():
    clear_profile_cache_memory()


def test_chrome_slugs_never_products():
    for slug in _CHROME_SLUGS:
        assert is_site_chrome_slug(slug)
        assert _sku_from_product_href(f"https://oem.example/{slug}") is None
        assert classify_href_candidate(f"https://oem.example/{slug}", slug) == "chrome"
    for name in CHROME:
        assert is_site_chrome_name(name)
    assert not is_site_chrome_slug("bot25")
    assert not is_site_chrome_slug("pm01")
    assert not is_site_chrome_name("BERRY")
    assert not is_site_chrome_name("BOT#25")


def test_evidence_required_to_name_a_product():
    origin = "https://unknown-oem.example"
    home = _page(
        title="Acme",
        url=f"{origin}/",
        text="Acme builds machines. Product Imprint AGB Investors Vehicles.",
        links=[
            (f"{origin}/product", "Product"),
            (f"{origin}/imprint", "Imprint"),
            (f"{origin}/agb", "AGB"),
            (f"{origin}/investors", "Investors"),
            (f"{origin}/vehicles", "Vehicles"),
        ],
    )
    names = _discover_product_names(home)
    lowered = {n.lower() for n in names}
    for noise in ("product", "imprint", "agb", "investors", "vehicles"):
        assert noise not in lowered
    resolved = resolve_identity(f"{origin}/", home)
    assert resolved.products == []
    assert name_is_proven_product("Product", text=home.text, html=home.html) is False


def test_advanced_farm_harvesting_not_nav():
    origin = "https://advanced.farm"
    home = _page(
        title="Advanced Farm Technologies",
        url=f"{origin}/",
        text=(
            "Advanced Farm builds harvesting systems for orchards. "
            "Autonomous apple harvesting. Not a Product nav. Careers News About."
        ),
        links=[
            (f"{origin}/", "Home"),
            (f"{origin}/about", "About"),
            (f"{origin}/news", "News"),
            (f"{origin}/careers", "Careers"),
            (f"{origin}/contact", "Contact"),
        ],
    )
    names = {n.lower() for n in _discover_product_names(home)}
    for noise in ("about", "news", "careers", "contact", "product", "apple harvester"):
        assert noise not in names
    assert lookup_vendor_by_url(f"{origin}/") is None or not listing_payload_for_url(
        f"{origin}/"
    ).get("matched")


def test_catalog_index_does_not_treat_apple_harvester_as_sku():
    from app.services.jobs_oem_listing import listing_from_catalog
    from app.services.oem_sku_discover import _CATEGORY_BLOB, is_junk_sku_name

    assert _CATEGORY_BLOB.fullmatch("apple harvester")
    assert is_junk_sku_name("apple harvester")
    vendor = lookup_vendor_by_url("https://advanced.farm/")
    names = [str(row.get("name") or "").strip().lower() for row in listing_from_catalog(vendor)]
    assert "apple harvester" not in names
    listing = listing_payload_for_url("https://advanced.farm/")
    assert listing["matched"] is False
    assert listing["robots"] == []


def test_bedrock_excavation_not_nav():
    origin = "https://bedrockrobotics.com"
    home = _page(
        title="Bedrock Robotics",
        url=f"{origin}/",
        text=(
            "Bedrock Robotics Advanced Autonomy for the Built World. "
            "Equip Your Fleet with Autonomy. Today, excavators. "
            "Home About Technology Partners Careers News Contact."
        ),
        links=[
            (f"{origin}/", "Home"),
            (f"{origin}/about", "About"),
            (f"{origin}/technology", "Technology"),
            (f"{origin}/partners", "Partners"),
            (f"{origin}/careers", "Careers"),
            (f"{origin}/news", "News"),
            (f"{origin}/contact", "Contact"),
            (f"{origin}/privacy-policy", "Privacy Policy"),
        ],
    )
    names = {n.lower() for n in _discover_product_names(home)}
    for noise in ("about", "careers", "news", "contact", "privacy policy", "home"):
        assert noise not in names
    assert resolve_identity(f"{origin}/", home).products == []


def test_xpeng_cars_and_investors_are_not_robots():
    origin = "https://www.xpeng.com"
    home = _page(
        title="XPENG - Smart Electric Vehicles, SUVs & MPVs",
        url=f"{origin}/",
        text=(
            "XPENG Smart Electric Vehicles SUVs MPVs Models Discover "
            "About XPENG News Events ESG Investor Relations L03 X9 P7+ G9 G6 P7 "
            "Charging Service."
        ),
        html=(
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Vehicle","name":"G6"}'
            "</script>"
            "<body>XPENG G6 P7 Investor Relations Vehicles</body>"
        ),
        links=[
            (f"{origin}/model/g6", "G6"),
            (f"{origin}/model/p7", "P7"),
            (f"{origin}/model/g9", "G9"),
            (f"{origin}/model/x9", "X9"),
            (f"{origin}/x9", "X9"),
            (f"{origin}/news", "News"),
            (f"{origin}/esg", "ESG"),
            (f"{origin}/charging", "Charging"),
            (f"{origin}/join-us", "join-us"),
            (f"{origin}/find-us", "Find Us"),
        ],
    )
    assert href_is_vehicle_path(f"{origin}/model/g6")
    assert _sku_from_product_href(f"{origin}/model/g6") is None
    assert _sku_from_product_href(f"{origin}/model/p7") is None
    names = {n.lower() for n in _discover_product_names(home)}
    for noise in (
        "g6",
        "p7",
        "g9",
        "x9",
        "l03",
        "investor relations",
        "vehicles",
        "news",
        "find us",
        "join-us",
        "join us",
    ):
        assert noise not in names
    found = {p.name.lower() for p in resolve_identity(f"{origin}/", home).products}
    for noise in ("g6", "p7", "xpeng iron", "xpeng px5", "iron", "px5"):
        assert noise not in found
    listing = listing_payload_for_url(f"{origin}/")
    assert listing["matched"] is False
    assert lookup_vendor_by_url(f"{origin}/") is None


def test_aandk_cruz_if_evidenced_not_product_nav():
    origin = "https://www.aandkrobotics.com"
    home = _page(
        title="A&K ROBOTICS",
        url=f"{origin}/",
        text=(
            "Redefining Mobility with Cruz™ Experience a new flow of mobility. "
            "Home Product Company Careers News."
        ),
        links=[
            (f"{origin}/product", "Product"),
            (f"{origin}/about-us", "Company"),
            (f"{origin}/careers", "Careers"),
            (f"{origin}/news", "News"),
        ],
    )
    assert _sku_from_product_href(f"{origin}/product") is None
    names = _discover_product_names(home)
    lowered = {n.lower() for n in names}
    assert "product" not in lowered
    assert "careers" not in lowered
    assert any(n.lower() == "cruz" for n in names)


def test_avatar_does_not_pick_handle_or_company_name():
    origin = "https://www.avatarrobotics.com"
    home = _page(
        title="Avatar Robotics | Agile Robots for Warehouse Automation",
        url=f"{origin}/",
        text=(
            "Avatar Robotics Agile Robots for Warehouse Automation. "
            "Solutions Industries Platform Book a demo. See Avatar In Action."
        ),
        links=[
            (f"{origin}/solutions", "Solutions"),
            (f"{origin}/industries", "Industries"),
            (f"{origin}/platform", "Platform"),
            (f"{origin}/book-a-demo", "Book a demo"),
        ],
    )
    names = {n.lower() for n in _discover_product_names(home)}
    assert "handle" not in names
    assert "solutions" not in names
    assert "platform" not in names
    assert "industries" not in names
    # Company name is not a SKU unless Meet {Name} / schema Product.
    assert "avatar" not in names
    assert resolve_identity(f"{origin}/", home).products == []


def test_agtonomy_handle_the_routine_is_not_a_robot():
    origin = "https://www.agtonomy.com"
    home = _page(
        title="Agtonomy",
        url=f"{origin}/",
        text=(
            "Agtonomy Home About News Careers. Smart Automation Made Simple. "
            "Let Automation Handle the Routine From mowing to hauling. "
            "Trusted Equipment. About Us Contact Us FAQ News Careers."
        ),
        links=[
            (f"{origin}/", "Home"),
            (f"{origin}/about", "About"),
            (f"{origin}/news", "News"),
            (f"{origin}/careers", "Careers"),
            (f"{origin}/contact", "Contact Us"),
        ],
    )
    names = {n.lower() for n in _discover_product_names(home)}
    assert "handle" not in names
    for noise in ("about", "news", "careers", "contact", "home"):
        assert noise not in names
    assert resolve_identity(f"{origin}/", home).products == []


def test_greenfield_bot25_only():
    origin = "https://www.greenfieldincorporated.com"
    home = _page(
        title="GREENFIELD ROBOTICS",
        url=f"{origin}/",
        text=(
            "Greenfield Robotics BOT#25 agricultural weeding robot. "
            "BOT#25 BOT25 weeding robot."
        ),
        links=[
            (f"{origin}/farmers", "FARMERS"),
            (f"{origin}/story", "STORY"),
            (f"{origin}/bot25", "BOT#25"),
            (f"{origin}/contact", "CONTACT"),
        ],
    )
    names = _discover_product_names(home)
    keys = {n.lower().replace("#", "") for n in names}
    assert any("bot25" in k or "bot#25" in n.lower() for k, n in zip(keys, names, strict=False)) or any(
        "bot" in n.lower() and "25" in n for n in names
    )
    assert "farmers" not in {n.lower() for n in names}
    assert "story" not in {n.lower() for n in names}


def test_organifarms_berry_only_not_product_imprint_agb():
    origin = "https://www.organifarms.de"
    home = _page(
        title="Organifarms I Harvesting Robots",
        url=f"{origin}/",
        text=(
            "Harvesting the future One BERRY at a time Meet BERRY "
            "Integrated Quality Control Autonomous Navigation."
        ),
        links=[
            (f"{origin}/product", "Product"),
            (f"{origin}/imprint", "Imprint"),
            (f"{origin}/agb", "Terms and Conditions"),
            (f"{origin}/datenschutz", "View Privacy Policy"),
        ],
    )
    names = _discover_product_names(home)
    lowered = {n.lower() for n in names}
    for noise in ("product", "imprint", "agb", "terms and conditions", "view privacy policy"):
        assert noise not in lowered
    assert any(n.upper() == "BERRY" for n in names)


def test_compose_unknown_oem_empty_does_not_match_jobs(monkeypatch):
    from unittest.mock import MagicMock

    class _Obj:
        def to_dict(self):
            return {
                "company": {"name": "Bedrock Robotics"},
                "selected_product": None,
                "products": [],
                "needs_product_choice": False,
                "facts": [],
                "sources": [],
                "profile_confidence": "C",
                "coverage_level": "low",
            }

    match = MagicMock(side_effect=AssertionError("must not match jobs without a proven product"))
    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", MagicMock(return_value=_Obj()))
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    monkeypatch.setattr("app.services.robot_job_search.match_jobs_from_profile", match)
    out = compose_robot_job_search("https://bedrockrobotics.com/")
    assert out["state"] == "qualify_robot"
    assert out["products"] == []
    assert out["job_count"] == 0
    match.assert_not_called()


def test_a_then_b_identity_stays_isolated(monkeypatch):
    from unittest.mock import MagicMock

    class _Berry:
        def to_dict(self):
            return {
                "company": {"name": "Organifarms"},
                "selected_product": {"name": "BERRY"},
                "products": [{"name": "BERRY"}],
                "needs_product_choice": False,
                "facts": [{"predicate": "product_class", "value": "agricultural_robot"}],
                "sources": [{"url": "https://www.organifarms.de/"}],
                "profile_confidence": "B",
                "coverage_level": "medium",
            }

    class _Bot:
        def to_dict(self):
            return {
                "company": {"name": "GREENFIELD ROBOTICS"},
                "selected_product": {"name": "BOT#25"},
                "products": [{"name": "BOT#25"}],
                "needs_product_choice": False,
                "facts": [{"predicate": "product_class", "value": "agricultural_robot"}],
                "sources": [{"url": "https://www.greenfieldincorporated.com/"}],
                "profile_confidence": "B",
                "coverage_level": "medium",
            }

    def _build(url, **_k):
        if "organifarms" in url:
            return _Berry()
        return _Bot()

    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", _build)
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda profile, **k: {
            "state": "qualify_robot",
            "robot_name": (profile.get("selected_product") or {}).get("name"),
            "company_name": (profile.get("company") or {}).get("name"),
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "matcher": None,
            "robot_class": "agricultural_robot",
        },
    )
    a = compose_robot_job_search("https://www.organifarms.de/")
    b = compose_robot_job_search("https://www.greenfieldincorporated.com/")
    a_names = [p.get("name") for p in a["products"]]
    b_names = [p.get("name") for p in b["products"]]
    assert a_names == ["BERRY"]
    assert b_names == ["BOT#25"]
    assert "BOT#25" not in a_names
    assert "BERRY" not in b_names


def test_cache_namespace_busts_stale_unknown_oem_lineups():
    assert NAMESPACE == "robot_profile_v12"


def test_critic_heldout_set_is_the_acceptance_list():
    assert len(CRITIC_HELDOUT_FIND_URLS) >= 8
    assert "https://www.xpeng.com/" in CRITIC_HELDOUT_FIND_URLS


def test_live_smoke_if_http_200():
    """One live homepage: if the host answers 200, chrome still is not a SKU."""
    url = "https://bedrockrobotics.com/"
    req = urllib.request.Request(url, headers={"User-Agent": "ReadyForRobots-test/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status != 200:
                return
            html = resp.read(80_000).decode("utf-8", "replace")
    except Exception:
        return
    home = FetchedPage(
        url=url,
        final_url=url,
        status_code=200,
        title="Bedrock Robotics",
        text="Bedrock Robotics excavators autonomy Careers News Contact About",
        html=html,
        links=[],
    )
    names = {n.lower() for n in _discover_product_names(home)}
    for noise in ("careers", "news", "contact", "about", "privacy"):
        assert noise not in names
