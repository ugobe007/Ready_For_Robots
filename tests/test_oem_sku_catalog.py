"""OEM/SKU workbook → ontology identity → FIND host lookup."""
from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.robot_catalog import Manufacturer, RobotFamily, RobotModel
from app.services.oem_sku_catalog import (
    apply_to_catalog,
    apply_verified_urls,
    compile_vendor_seed,
    is_wrong_product_url,
    lookup_urls,
    map_primary_class,
    parse_workbook,
)
from app.services.robot_ontology import oem_sku_catalog
from app.services.vendor_robot_lookup import (
    index_robot_names,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
    select_index_robot,
)


def test_parse_workbook_named_skus_no_fake_specs():
    catalog = parse_workbook()
    assert catalog["company_count"] == 61
    assert catalog["product_count"] == 133
    slugs = {
        p["slug"]: p
        for c in catalog["companies"]
        for p in c["products"]
    }
    assert "universal-robots-ur20" in slugs
    ur20 = slugs["universal-robots-ur20"]
    assert ur20["name"] == "UR20"
    assert ur20["company_name"] == "Universal Robots"
    assert ur20["specs"] == {}
    assert ur20["capability_confidence"] == "UNKNOWN"
    assert ur20["product_url"] is None

    stretch = slugs["boston-dynamics-stretch"]
    assert "wrong_product_url" in stretch["flags"]
    assert stretch["product_url"] is None
    assert not stretch["candidate_sources"]


def test_stretch_spot_url_is_rejected():
    assert is_wrong_product_url("Stretch", "https://bostondynamics.com/products/spot/")
    assert not is_wrong_product_url("Spot", "https://bostondynamics.com/products/spot/")
    assert not is_wrong_product_url(
        "Stretch", "https://bostondynamics.com/products/stretch/"
    )


def test_class_map_is_descriptor_only():
    assert map_primary_class("Humanoid", "Humanoid general-purpose") == "humanoid"
    assert map_primary_class("Manufacturing", "Collaborative robot") == "cobot"
    assert map_primary_class("Logistics", "AMR") == "amr"
    assert map_primary_class("Service", "Inspection robot") == "quadruped"
    assert map_primary_class("Commercial", "Bipedal service") == "humanoid"
    assert map_primary_class("Commercial", "Table service waiter") == "serving"
    assert map_primary_class("Commercial", "Cleaning drone") == "cleaning_drone"
    assert map_primary_class("Commercial", "Autonomous floor scrubber") == "cleaning_robot"


def test_seed_has_no_invented_claims_or_stretch_spot_url():
    catalog = parse_workbook()
    seed = compile_vendor_seed(catalog)
    by_slug = {
        r["model_slug"]: r
        for v in seed["vendors"]
        for r in v["robots"]
    }
    assert all(
        c.get("predicate") in {"product_class"}
        for c in by_slug["universal-robots-ur20"]["catalog_claims"]
    )
    assert by_slug["universal-robots-ur20"]["specs"] == {}
    stretch = by_slug["boston-dynamics-stretch"]
    assert stretch.get("product_url") in (None, "")
    assert "spot" not in (stretch.get("product_url") or "")


def test_lookup_stores_only_verified_urls():
    catalog = {
        "companies": [
            {
                "name": "Universal Robots",
                "domains": ["universal-robots.com"],
                "products": [
                    {
                        "name": "UR20",
                        "slug": "universal-robots-ur20",
                        "flags": [],
                        "candidate_sources": ["https://www.universal-robots.com/products/ur20/"],
                    },
                    {
                        "name": "Stretch",
                        "slug": "boston-dynamics-stretch",
                        "flags": ["wrong_product_url"],
                        "candidate_sources": [],
                    },
                ],
            }
        ]
    }

    def fake_fetch(url, allow_archive=False):
        return SimpleNamespace(
            status_code=200,
            title="UR20 collaborative robot",
            text="The UR20 cobot from Universal Robots.",
            links=[],
            final_url=url,
        )

    result = lookup_urls(catalog, fetch_page=fake_fetch, rate_limit_s=0, sleep=lambda _s: None)
    assert result["counts"]["verified"] == 1
    assert result["verified"][0]["url"].endswith("/ur20/")
    assert result["counts"]["skipped"] == 1
    apply_verified_urls(catalog, result)
    ur20 = catalog["companies"][0]["products"][0]
    assert ur20["url_status"] == "verified"
    assert ur20["lookup_host"] == "universal-robots.com"


def test_apply_upserts_manufacturers_and_models():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    seed = {
        "source": "test",
        "vendors": [
            {
                "vendor_name": "Universal Robots",
                "domains": ["universal-robots.com"],
                "vendor_url": "https://www.universal-robots.com",
                "robots": [
                    {
                        "name": "UR20",
                        "model_slug": "universal-robots-ur20",
                        "primary_class": "cobot",
                        "product_url": "https://www.universal-robots.com/products/ur20/",
                        "lookup_host": "universal-robots.com",
                        "url_status": "verified",
                    }
                ],
            }
        ],
    }
    stats = apply_to_catalog(seed, db=db)
    assert stats["manufacturers"] == 1
    assert stats["models"] == 1
    mfr = db.query(Manufacturer).filter(Manufacturer.slug == "universal-robots").one()
    assert mfr.lookup_host == "universal-robots.com"
    model = db.query(RobotModel).filter(RobotModel.slug == "universal-robots-ur20").one()
    assert model.lookup_host == "universal-robots.com"
    assert model.product_url.endswith("/ur20/")
    family = db.query(RobotFamily).filter(RobotFamily.manufacturer_id == mfr.id).one()
    assert family.slug == "catalog"
    db.close()


def test_find_host_lookup_ur20_and_dexmate_no_regress():
    reload_vendor_robots_index()
    ur = lookup_vendor_by_url("https://www.universal-robots.com/")
    assert ur is not None
    names = index_robot_names(ur)
    assert "UR20" in names or any("UR20" in n for n in names)

    dex = lookup_vendor_by_url("https://www.dexmate.ai/")
    assert dex is not None
    assert any("Vega" in n for n in index_robot_names(dex))
    sku = select_index_robot("https://www.dexmate.ai/product/vega", dex)
    assert sku is not None
    assert "Vega" in sku["name"]

    bd = lookup_vendor_by_url("https://bostondynamics.com/")
    assert bd is not None
    stretch = next(r for r in bd["robots"] if r.get("name") == "Stretch")
    assert "spot" not in (stretch.get("product_url") or "").lower()


def test_ontology_loader_sees_catalog_identity():
    data = oem_sku_catalog()
    assert data.get("ontology_id") == "oem_sku_catalog_v1"
    slugs = {
        p["slug"]
        for c in data.get("companies") or []
        for p in c.get("products") or []
    }
    assert "universal-robots-ur20" in slugs
    assert "boston-dynamics-stretch" in slugs


def test_discover_indexes_named_skus_and_rejects_series_blobs():
    from app.services.oem_sku_discover import (
        discover_skus,
        is_junk_sku_name,
        looks_like_named_sku,
        merge_discovered_skus,
    )

    assert is_junk_sku_name("UR Series")
    assert is_junk_sku_name("Collaborative robots")
    assert is_junk_sku_name("Privacy Policy")
    assert is_junk_sku_name("Skip to content")
    assert is_junk_sku_name("Machine Tending")
    assert not is_junk_sku_name("UR30")
    assert not looks_like_named_sku("Investor Relations")
    assert looks_like_named_sku("UR30")
    assert looks_like_named_sku("FIGURE 03")
    assert is_junk_sku_name("Farmers")
    assert is_junk_sku_name("STORY")
    assert is_junk_sku_name("Invest")
    assert is_junk_sku_name("Contact")
    assert not is_junk_sku_name("BOT25")
    assert not is_junk_sku_name("BOT#25")
    assert looks_like_named_sku("BOT25")
    assert looks_like_named_sku("BOT#25")
    assert not looks_like_named_sku("Farmers")
    assert not looks_like_named_sku("Story")
    assert is_junk_sku_name("Product")
    assert is_junk_sku_name("Products")
    assert is_junk_sku_name("Imprint")
    assert is_junk_sku_name("Impressum")
    assert is_junk_sku_name("Terms and Conditions")
    assert is_junk_sku_name("AGB")
    assert is_junk_sku_name("Datenschutz")
    assert is_junk_sku_name("View Privacy Policy")
    assert not looks_like_named_sku("Product")
    assert not looks_like_named_sku("Imprint")

    catalog = {
        "ontology_id": "oem_sku_catalog_v1",
        "version": "1.0.0",
        "notes": [],
        "companies": [
            {
                "name": "Universal Robots",
                "slug": "universal-robots",
                "domains": ["universal-robots.com"],
                "source_urls": ["https://www.universal-robots.com/products/"],
                "products": [
                    {
                        "name": "UR20",
                        "slug": "universal-robots-ur20",
                        "primary_class": "cobot",
                        "product_url": "https://www.universal-robots.com/products/ur20/",
                    }
                ],
            }
        ],
    }
    pages = {
        "https://www.universal-robots.com/products/": SimpleNamespace(
            status_code=200,
            title="UR cobots",
            text="Universal Robots product lineup.",
            links=[
                ("https://www.universal-robots.com/products/ur30/", "UR30"),
                ("https://www.universal-robots.com/products/ur-series/", "UR Series"),
                ("https://www.universal-robots.com/products/collaborative-robots/", "Collaborative robots"),
            ],
            final_url="https://www.universal-robots.com/products/",
        ),
        "https://www.universal-robots.com/products/ur30/": SimpleNamespace(
            status_code=200,
            title="UR30 cobot",
            text="The UR30 from Universal Robots handles heavy payloads.",
            links=[],
            final_url="https://www.universal-robots.com/products/ur30/",
        ),
    }

    def fake_fetch(url, allow_archive=False):
        if url in pages:
            return pages[url]
        if url.rstrip("/").endswith("/ur30"):
            return pages["https://www.universal-robots.com/products/ur30/"]
        if "universal-robots.com" in url and "ur-series" not in url and "collaborative" not in url:
            return pages["https://www.universal-robots.com/products/"]
        return SimpleNamespace(status_code=404, title="", text="", links=[], final_url=url)

    def fake_text(url):
        return (404, "")

    result = discover_skus(
        catalog,
        fetch_page=fake_fetch,
        fetch_text=fake_text,
        rate_limit_s=0,
        sleep=lambda _s: None,
        max_listings_per_oem=2,
    )
    names = {row["name"] for row in result["verified"]}
    assert "UR30" in names
    assert "UR Series" not in names
    assert "Collaborative robots" not in names
    merge_discovered_skus(catalog, result)
    product_names = [p["name"] for p in catalog["companies"][0]["products"]]
    assert "UR20" in product_names
    assert "UR30" in product_names
    assert "UR Series" not in product_names
    ur30 = next(p for p in catalog["companies"][0]["products"] if p["name"] == "UR30")
    assert ur30["specs"] == {}
    assert ur30["capability_confidence"] == "UNKNOWN"
    assert ur30["source"] == "oem_listing"
