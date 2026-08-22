"""Discover robot SKUs from manufacturer product URLs (not an OEM allowlist)."""
from __future__ import annotations

from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.resolve import (
    _discover_product_names,
    _sku_from_product_href,
    resolve_identity,
)
from app.services.robot_profile_cache import NAMESPACE


def _page(*, title: str, text: str, url: str, links: list[tuple[str, str]]) -> FetchedPage:
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        text=text,
        html=f"<html><title>{title}</title><body>{text}</body></html>",
        links=links,
    )


def test_sku_from_engineai_product_paths():
    assert _sku_from_product_href("https://en.engineai.com.cn/product-pm01.html") == "PM01"
    assert _sku_from_product_href("https://en.engineai.com.cn/product-t800") == "T800"
    assert _sku_from_product_href("https://en.engineai.com.cn/product-s2.html") == "S2"
    assert _sku_from_product_href("https://en.engineai.com.cn/product-purchase.html") is None
    assert _sku_from_product_href("https://en.engineai.com.cn/about.html") is None


def test_engineai_homepage_links_yield_product_picker():
    origin = "https://en.engineai.com.cn"
    home = _page(
        title="ENGINEAI",
        url=f"{origin}/",
        text=(
            "ENGINEAI Products PM01 T800 JS01 SA01 SE01 S2 "
            "PM01 A lightweight embodied intelligent agent. "
            "SE01 general-purpose humanoid robot. "
            "T800 Full-Scale High-Mobility General-Purpose Robot."
        ),
        links=[
            (f"{origin}/product-pm01.html", "PM01"),
            (f"{origin}/product-t800.html", "T800"),
            (f"{origin}/product-js01.html", "JS01"),
            (f"{origin}/product-sa01.html", "SA01"),
            (f"{origin}/product-se01.html", "SE01"),
            (f"{origin}/product-s2.html", "S2"),
            (f"{origin}/product-purchase.html", "Product Purchase"),
        ],
    )
    names = _discover_product_names(home)
    assert "PM01" in names
    assert "T800" in names
    assert "SE01" in names
    assert "Purchase" not in names
    assert "Product Purchase" not in names
    resolved = resolve_identity(f"{origin}/", home)
    assert resolved.company.primary_domain == "engineai.com.cn"
    assert resolved.company.name.upper() == "ENGINEAI"
    found = {p.name for p in resolved.products}
    assert any("PM01" in n for n in found)
    assert any("T800" in n for n in found)
    assert any("SE01" in n or "SA01" in n for n in found)
    assert "Purchase" not in found
    assert "Learn More" not in found
    assert len(resolved.products) >= 3


def test_allowlist_digit_still_discovered_without_product_href():
    home = _page(
        title="Digit | Agility Robotics",
        url="https://www.agilityrobotics.com/",
        text="Digit humanoid robot Digit warehouses Digit totes Digit.",
        links=[
            ("https://www.agilityrobotics.com/robots/digit", "Digit"),
        ],
    )
    names = _discover_product_names(home)
    assert "Digit" in names


def test_sku_from_magiclab_locale_paths():
    assert _sku_from_product_href("https://www.magiclab.top/en/x1") == "X1"
    assert _sku_from_product_href("https://www.magiclab.top/en/z1") == "Z1"
    assert _sku_from_product_href("https://www.magiclab.top/en/app/g1") == "G1"
    assert _sku_from_product_href("https://www.magiclab.top/en/dog-w") == "dog-w"
    assert _sku_from_product_href("https://www.magiclab.top/en/human") == "Human"
    assert _sku_from_product_href("https://www.magiclab.top/en/about") is None
    assert _sku_from_product_href("https://www.magiclab.top/en/news") is None


def test_magiclab_homepage_links_yield_product_picker():
    origin = "https://www.magiclab.top"
    home = _page(
        title="MagicLab",
        url=f"{origin}/en",
        text="MagicBot MagicDog Magic Panda humanoid quadruped robot.",
        links=[
            (f"{origin}/en/human", "MagicBot"),
            (f"{origin}/en/x1", "MagicBot X1"),
            (f"{origin}/en/z1", "MagicBot Z1"),
            (f"{origin}/en/app/g1", "G1"),
            (f"{origin}/en/dog", "MagicDog"),
            (f"{origin}/en/dog-w", "MagicDog-W"),
            (f"{origin}/en/panda", "Magic Panda"),
            (f"{origin}/en/about", "About"),
            (f"{origin}/en/news", "News"),
        ],
    )
    names = _discover_product_names(home)
    joined = " ".join(names).lower()
    assert "g1" in joined
    assert any("x1" in n.lower() for n in names)
    assert any("z1" in n.lower() for n in names)
    assert any("dog" in n.lower() for n in names)
    assert "About" not in names
    assert "News" not in names
    assert "Human" not in names
    assert len(names) >= 4
    assert names != ["G1"]


def test_href_label_keeps_hidden_sku():
    from app.services.robot_understanding_v1.resolve import _href_product_name

    assert (
        _href_product_name("https://www.magiclab.top/en/app/g1", "MagicBot")
        == "MagicBot G1"
    )
    assert (
        _href_product_name("https://www.magiclab.top/en/x1", "MagicBot X1")
        == "MagicBot X1"
    )
    assert _href_product_name("https://www.magiclab.top/en/x1", "") == "X1"


def test_profile_cache_namespace_busts_stale_engineai_identity():
    assert NAMESPACE == "robot_profile_v10"


def test_sku_from_root_named_product_paths():
    assert _sku_from_product_href("https://www.richtechrobotics.com/adam") == "ADAM"
    assert _sku_from_product_href("https://www.richtechrobotics.com/matradee-l")
    assert _sku_from_product_href("https://www.richtechrobotics.com/scorpion") == "Scorpion"
    assert _sku_from_product_href("https://www.richtechrobotics.com/about") is None
    assert _sku_from_product_href("https://www.richtechrobotics.com/solutions") is None
    assert _sku_from_product_href("https://www.agilityrobotics.com/robots/digit")


def test_homepage_prose_names_yield_product_picker():
    """Hospitality OEM homepages name robots in copy without /product-sku hrefs."""
    origin = "https://www.richtechrobotics.com"
    home = _page(
        title="AI-driven robotics to solve real-world challenges - Richtech Robotics",
        url=f"{origin}/",
        text=(
            "ADAM serves cocktails at NVIDIA HQ. "
            "Scorpion shows off AI intelligence. "
            "Titan skyrockets efficiency at Mercedes-Benz of Plano. "
            "ADAM serves premium coffee in Walmart."
        ),
        links=[
            (f"{origin}/solutions", "See all robots"),
            (f"{origin}/company", "Company"),
            (f"{origin}/contact", "Get in touch"),
        ],
    )
    names = _discover_product_names(home)
    joined = " ".join(names).lower()
    assert "adam" in joined
    assert "scorpion" in joined
    assert "titan" in joined
    assert "Solutions" not in names
    assert "Company" not in names
    resolved = resolve_identity(f"{origin}/", home)
    found = {p.name for p in resolved.products}
    assert len(found) >= 3
    assert resolved.company.primary_domain == "richtechrobotics.com"


def test_family_prefix_is_oem_agnostic():
    from app.services.robot_understanding_v1.resolve import _apply_family_prefix

    out = _apply_family_prefix(["Unitree G1", "H1"])
    assert "Unitree H1" in out
    assert "H1" not in out


def test_discover_drops_nav_and_lidar_labels():
    home = _page(
        title="Bear Robotics",
        url="https://www.bearrobotics.ai/",
        text="Servi delivers food in restaurants. Learn More. EULA. 4D LiDAR G1 sensor.",
        links=[
            ("https://www.bearrobotics.ai/servi", "Servi"),
            ("https://www.bearrobotics.ai/learn-more", "Learn More"),
            ("https://www.bearrobotics.ai/eula", "EULA"),
            ("https://www.bearrobotics.ai/lidar", "4D LiDAR G1"),
            ("https://www.bearrobotics.ai/industry", "Industry"),
        ],
    )
    names = _discover_product_names(home)
    assert any("servi" in n.lower() for n in names)
    assert "Learn More" not in names
    assert "EULA" not in names
    assert "Industry" not in names
    assert not any("lidar" in n.lower() for n in names)


def test_richtech_resolve_picker_is_catalog_skus_not_prose_only():
    origin = "https://www.richtechrobotics.com"
    home = _page(
        title="Richtech Robotics",
        url=f"{origin}/",
        text="ADAM serves cocktails. Learn More. Contact Us.",
        links=[
            (f"{origin}/learn-more", "Learn More"),
            (f"{origin}/contact", "Contact Us"),
        ],
    )
    resolved = resolve_identity(f"{origin}/", home)
    found = {p.name for p in resolved.products}
    assert "ADAM" in found
    assert "MATRADEE" in found
    assert "Learn More" not in found
    assert "Contact Us" not in found
    assert len(found) == 10


def test_omron_hub_nav_is_not_a_robot_lineup():
    origin = "https://robotics.omron.com"
    home = _page(
        title="Mobile Robots | OMRON",
        url=f"{origin}/products/mobile-robots/",
        text=(
            "OMRON LD-250 AMR and HD-1500 MD-650 autonomous mobile robots "
            "move pallets in warehouses. LD-250 LD-250 HD-1500 MD-650."
        ),
        links=[
            (f"{origin}/products/mobile-robots/", "Products overview"),
            (f"{origin}/products/amrs", "AMRs"),
            (f"{origin}/industries", "Industries"),
            (f"{origin}/about-us", "About Us"),
            (f"{origin}/products/collaborative", "Collaborative"),
            (f"{origin}/products/discontinued-products", "Discontinued Products"),
            (f"{origin}/products/mobile-robots/activate-license", "Activate your AMR License"),
            (f"{origin}/de/", "Deutsch"),
            (f"{origin}/es/", "Español"),
            (f"{origin}/fr/", "Français"),
            (f"{origin}/products/ld-250", "LD-250"),
            (f"{origin}/products/hd-1500", "HD-1500"),
            (f"{origin}/products/md-650", "MD-650"),
        ],
    )
    names = _discover_product_names(home)
    lowered = {n.lower() for n in names}
    for noise in (
        "about us",
        "industries",
        "products overview",
        "discontinued products",
        "deutsch",
        "español",
        "espanol",
        "français",
        "francais",
        "amrs",
        "collaborative",
        "activate your amr license",
    ):
        assert noise not in lowered
    assert any("ld-250" in n.lower() or "ld250" in n.lower() for n in names)
    assert any("hd-1500" in n.lower() or "hd1500" in n.lower() for n in names)
    assert _sku_from_product_href(f"{origin}/products/mobile-robots/") is None
    assert _sku_from_product_href(f"{origin}/products/ld-250") == "LD250"

