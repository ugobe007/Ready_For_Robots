"""
Robot understanding golden suite — fixture HTML only (no live OEM fetches in CI).

Hard bar: Agility-like and Dexmate-like company homepages must never land on
Level-5 capability chips (could_not_understand).
"""
from __future__ import annotations

from app.services.robot_job_capability_match import match_robot_url, match_from_chip
from app.services.robot_capability_profile import build_capability_profile


AGILITY_HOME = """
<html><head><title>Industrial Humanoid Automation | Agility</title>
<meta name="description" content="Agility's humanoid robots are deployed today in manufacturing, distribution, and logistics."/>
</head><body>
<a href="/solutions">Solutions</a>
<a href="/industries">Industries</a>
<h1>Humanoid robots. Proven results.</h1>
<p>Digit is a commercially deployed humanoid robot. Arc is the cloud platform that runs it.
Together, they bring advanced automation to facility floors with clear ROI.</p>
<p>Warehouses and factories are where we've built momentum.</p>
</body></html>
"""

AGILITY_SOLUTIONS = """
<html><head><title>Humanoid Solutions | Agility</title></head><body>
<a href="/solutions">Solutions</a>
<a href="/content/digit-moves-over-100k-totes">Digit Moves Over 100,000 Totes</a>
<h1>Solutions</h1>
<p>humanoid Digit A fully autonomous tool with proven commercial deployments.</p>
<p>Durable Digit has a 35 pound carrying capacity, 4 hour battery life, and the capability to work continuous shifts.</p>
<p>Connectivity to existing warehouse automation—including AMRs and management and execution systems—so integration is seamless.</p>
<p>Digit Moves Over 100,000 Totes in Commercial Deployment</p>
</body></html>
"""

DEXMATE_HOME = """
<html><head><title>Dexmate</title></head>
<body><a href="./product/vega">Product</a><p>Welcome.</p></body></html>
"""

DEXMATE_VEGA = """
<html><head><title>Vega | Dexmate</title></head>
<body>
<h1>Vega mobile manipulator</h1>
<p>Omnidirectional mobile base with dual-arm dexterous hands for factory floors.</p>
<p>Autonomous navigation, load and unload, kitting and material handling.</p>
<p>10 lb payload per arm, 8 hour runtime.</p>
</body></html>
"""

LOCUS_ORIGIN = """
<html><head><title>Origin AMR | Locus Robotics</title></head>
<body>
<p>Autonomous mobile robot for warehouse tote transport and goods-to-person fulfillment.</p>
<p>Material handling AMR with navigation for distribution centers.</p>
</body></html>
"""

NEO_SCRUB = """
<html><head><title>Neo Floor Scrubber | Avidbots</title></head>
<body>
<p>Autonomous hard-floor scrubber for overnight cleaning routes in hospitals and airports.</p>
<p>Large indoor floor area coverage with repeatable scrubbing.</p>
</body></html>
"""

SPOT_PAGE = """
<html><head><title>Spot | Boston Dynamics</title></head>
<body>
<p>Spot is an agile mobile robot for industrial inspection and remote sensing.</p>
<p>Autonomous navigation and patrol routes for gauge read and thermography inspection.</p>
</body></html>
"""

MULTI_ROBOT_HOME = """
<html><head><title>Unitree Robotics</title></head>
<body>
<a href="/robots/g1">G1</a>
<a href="/robots/h1">H1</a>
<a href="/robots/b2">B2</a>
<p>G1 is a humanoid robot. H1 is a humanoid robot. B2 is a quadruped robot for industrial use.</p>
</body></html>
"""

OPAQUE = """
<html><head><title>Home</title></head>
<body><p>Welcome. Contact us for more information.</p></body></html>
"""

WEAK_MARKETING = """
<html><head><title>Future of Work Inc</title></head>
<body>
<p>We reimagine automation for tomorrow's workforce. Innovation. Partnership. Excellence.</p>
<a href="/about">About</a>
</body></html>
"""


def _fetcher_map(pages: dict[str, str]):
    def fetcher(url: str):
        # longest path match
        for key, html in sorted(pages.items(), key=lambda kv: -len(kv[0])):
            if url.rstrip("/") == key.rstrip("/") or url.rstrip("/").endswith(key.rstrip("/")):
                return html, url
        # try path suffix
        from urllib.parse import urlparse

        path = urlparse(url).path or "/"
        for key, html in pages.items():
            if key.startswith("/") and path.rstrip("/") == key.rstrip("/"):
                return html, url
        raise RuntimeError(f"no fixture for {url}")

    return fetcher


def test_agility_homepage_hard_bar_never_l5():
    pages = {
        "https://example-agility.test/": AGILITY_HOME,
        "https://example-agility.test/solutions": AGILITY_SOLUTIONS,
        "https://example-agility.test/industries": AGILITY_HOME,
        "/solutions": AGILITY_SOLUTIONS,
        "/industries": AGILITY_HOME,
    }
    # Use url that assert_public allows — example.com is fine with fetcher
    pages = {
        "https://example.com/": AGILITY_HOME,
        "https://example.com/solutions": AGILITY_SOLUTIONS,
        "https://example.com/industries": "<html><body><p>Industries humanoid Digit warehouses</p></body></html>",
    }

    result = match_robot_url("https://example.com/", fetcher=_fetcher_map(pages))
    assert result["state"] != "could_not_understand"
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    caps = {c["key"] for c in result["capabilities"]}
    assert "humanoid" in caps or "tote_handling" in caps or "mobile" in caps
    # Confirmed tote/payload language from solutions
    assert "tote_handling" in caps or "carry" in caps or "payload" in caps
    # Must not invent CNC machine tending as confirmed
    machine = [c for c in result["capabilities"] if c["key"] == "machine_interaction"]
    assert not machine or machine[0].get("truth_state") != "confirmed"


def test_dexmate_homepage_hard_bar_never_l5():
    pages = {
        "https://example.com/": DEXMATE_HOME,
        "https://example.com/product/vega": DEXMATE_VEGA,
    }
    result = match_robot_url("https://example.com/", fetcher=_fetcher_map(pages))
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    caps = {c["key"] for c in result["capabilities"]}
    assert "dual_arm" in caps or "mobile" in caps


def test_locus_origin_product_page():
    result = match_robot_url("https://example.com/origin", html=LOCUS_ORIGIN)
    assert result["state"] in {"matches", "thin_corpus"}
    fams = {f["id"] for f in result["families"]}
    assert fams & {"transport_amr", "mobile_manipulation"}


def test_neo_scrub_product_page():
    result = match_robot_url("https://example.com/neo", html=NEO_SCRUB)
    assert result["state"] in {"matches", "thin_corpus"}
    assert result["families"][0]["id"] == "floor_scrub"


def test_spot_inspection_page():
    result = match_robot_url("https://example.com/spot", html=SPOT_PAGE)
    assert result["state"] in {"matches", "thin_corpus"}
    fams = {f["id"] for f in result["families"]}
    assert "inspection_mobile" in fams or "inspect" in {c["key"] for c in result["capabilities"]}


def test_multi_product_asks_selection():
    pages = {
        "https://example.com/": MULTI_ROBOT_HOME,
        "https://example.com/robots/g1": "<html><body><p>G1 humanoid bipedal robot autonomous navigation</p></body></html>",
        "https://example.com/robots/h1": "<html><body><p>H1 humanoid robot</p></body></html>",
        "https://example.com/robots/b2": "<html><body><p>B2 quadruped robot</p></body></html>",
    }
    result = match_robot_url("https://example.com/", fetcher=_fetcher_map(pages))
    # Either select_product or auto-picked if confidence gap is clear
    if result["state"] == "select_product":
        names = {p["name"].lower() for p in result.get("products") or []}
        assert len(names) >= 2
    else:
        assert result["state"] in {"matches", "thin_corpus", "could_not_understand"}


def test_opaque_and_weak_marketing_may_l5():
    assert match_robot_url("https://example.com/", html=OPAQUE)["state"] == "could_not_understand"
    weak = match_robot_url("https://example.com/", html=WEAK_MARKETING)
    assert weak["state"] == "could_not_understand"
    assert weak["jobs"] == []


def test_chip_still_works_as_last_resort():
    result = match_from_chip("manipulates")
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0


def test_no_hostname_allowlist_invention():
    profile = build_capability_profile(text="https://dexmate.ai/", robot_name="Dexmate")
    keys = {c.key for c in profile.capabilities}
    assert "dual_arm" not in keys
    assert "dexterous" not in keys


def test_research_stages_present_on_success():
    pages = {
        "https://example.com/": DEXMATE_HOME,
        "https://example.com/product/vega": DEXMATE_VEGA,
    }
    result = match_robot_url("https://example.com/", fetcher=_fetcher_map(pages))
    stages = result.get("research_stages") or []
    ids = {s["id"] for s in stages}
    assert "identify_company" in ids
    assert "find_robots" in ids or "research_capabilities" in ids
