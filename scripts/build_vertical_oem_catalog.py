#!/usr/bin/env python3
"""Write ontology/vertical_oem_sku_catalog.v1.json from verified official pages.

Only URLs that returned HTTP 200 on 2026-08-27 are stored as product_url.
Unverified hosts (Built Robotics 403, Canvas SSL, Honeybee 429, Stretch-on-Spot
risks) are omitted. Empty specs stay UNKNOWN. Resume leftover OEMs in the
mission outcome — do not invent SKUs. 2026-08-27 seed pass adds only HTTP 200
named product pages from the operator list.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.services.oem_sku_catalog import (
    ONTOLOGY_PATH,
    SEED_PATH,
    VERTICAL_CATALOG_PATH,
    compile_vendor_seed,
    merge_vertical_catalog,
    slugify,
    write_json,
)

ROOT = Path(__file__).resolve().parents[1]


def _sku(
    company: str,
    company_slug: str,
    name: str,
    primary_class: str,
    category: str,
    listed_class: str,
    task: str,
    setting: str,
    url: str | None,
    host: str,
    *,
    configuration_kind: str = "standalone",
    host_platform: str = "none",
    region: str = "United States",
) -> dict:
    verified = bool(url)
    return {
        "name": name,
        "slug": f"{company_slug}-{slugify(name)}",
        "company_name": company,
        "company_slug": company_slug,
        "primary_class": primary_class,
        "category": category,
        "listed_class": listed_class,
        "task": task,
        "setting": setting,
        "status": "Deployed",
        "region": region,
        "spreadsheet_sources": [url] if url else [],
        "candidate_sources": [url] if url else [],
        "product_url": url,
        "lookup_host": host if verified else None,
        "url_status": "verified" if verified else "unverified",
        "specs": {},
        "capability_confidence": "UNKNOWN",
        "flags": [],
        "configuration_kind": configuration_kind,
        "host_platform": host_platform,
        "source": "mission-2026-08-27-vertical-robot-catalog",
    }


def _company(
    name: str,
    slug: str,
    host: str,
    home: str,
    category: str,
    products: list[dict],
    region: str = "United States",
) -> dict:
    verified_urls = [p["product_url"] for p in products if p.get("product_url")]
    if home not in verified_urls:
        verified_urls.insert(0, home)
    return {
        "name": name,
        "slug": slug,
        "vendor_role": "robot_oem",
        "regions": region,
        "categories": [category],
        "source_urls": [home],
        "domains": [host],
        "price_indication": "Quote required / not publicly disclosed",
        "products": products,
        "verified_urls": verified_urls,
    }


def build() -> dict:
    companies = [
        _company(
            "Carbon Robotics",
            "carbon-robotics",
            "carbonrobotics.com",
            "https://carbonrobotics.com/",
            "Agriculture",
            [
                _sku(
                    "Carbon Robotics",
                    "carbon-robotics",
                    "LaserWeeder",
                    "agricultural_robot",
                    "Agriculture",
                    "Agricultural weeding robot",
                    "Laser and mechanical weed removal in row crops",
                    "Fields · row crops · vegetable beds",
                    "https://carbonrobotics.com/",
                    "carbonrobotics.com",
                    configuration_kind="implement_on_host",
                    host_platform="tractor",
                )
            ],
        ),
        _company(
            "John Deere",
            "john-deere",
            "deere.com",
            "https://www.deere.com/",
            "Agriculture",
            [
                _sku(
                    "John Deere",
                    "john-deere",
                    "X Series Combine",
                    "agricultural_robot",
                    "Agriculture",
                    "Autonomous combine",
                    "Grain harvest with an X Series combine",
                    "Fields · grain harvest",
                    "https://www.deere.com/en/harvesting/x-series-combines/",
                    "deere.com",
                ),
                _sku(
                    "John Deere",
                    "john-deere",
                    "Autonomous Tractor",
                    "agricultural_robot",
                    "Agriculture",
                    "Autonomous tractor",
                    "Autonomous tractor for planting and field work",
                    "Fields · planting · harvest support",
                    "https://www.deere.com/en/autonomous/",
                    "deere.com",
                ),
                _sku(
                    "John Deere",
                    "john-deere",
                    "See & Spray Ultimate",
                    "agricultural_robot",
                    "Agriculture",
                    "Precision spray implement",
                    "See-and-spray implement on a tractor/sprayer host",
                    "Fields · row crops",
                    "https://www.deere.com/en/sprayers/see-spray-ultimate/",
                    "deere.com",
                    configuration_kind="implement_on_host",
                    host_platform="tractor",
                ),
            ],
        ),
        _company(
            "Monarch Tractor",
            "monarch-tractor",
            "monarchtractor.com",
            "https://www.monarchtractor.com/",
            "Agriculture",
            [
                _sku(
                    "Monarch Tractor",
                    "monarch-tractor",
                    "MK-V",
                    "agricultural_robot",
                    "Agriculture",
                    "Electric autonomous tractor",
                    "Electric tractor for planting and field work",
                    "Vineyards · orchards · fields",
                    "https://www.monarchtractor.com/",
                    "monarchtractor.com",
                )
            ],
        ),
        _company(
            "Naio Technologies",
            "naio-technologies",
            "naio-technologies.com",
            "https://www.naio-technologies.com/",
            "Agriculture",
            [
                _sku(
                    "Naio Technologies",
                    "naio-technologies",
                    "Oz",
                    "agricultural_robot",
                    "Agriculture",
                    "Weeding robot",
                    "Mechanical weeding in vegetable rows",
                    "Fields · vegetable beds",
                    "https://www.naio-technologies.com/en/oz/",
                    "naio-technologies.com",
                    region="France",
                ),
                _sku(
                    "Naio Technologies",
                    "naio-technologies",
                    "Ted",
                    "agricultural_robot",
                    "Agriculture",
                    "Vineyard weeding robot",
                    "Mechanical weeding in vineyards",
                    "Vineyards",
                    "https://www.naio-technologies.com/en/ted/",
                    "naio-technologies.com",
                    region="France",
                ),
                _sku(
                    "Naio Technologies",
                    "naio-technologies",
                    "Jo",
                    "agricultural_robot",
                    "Agriculture",
                    "Large-tool weeding robot",
                    "Mechanical weeding with larger tools",
                    "Fields · vegetable beds",
                    "https://www.naio-technologies.com/en/jo/",
                    "naio-technologies.com",
                    region="France",
                ),
                _sku(
                    "Naio Technologies",
                    "naio-technologies",
                    "Orio",
                    "agricultural_robot",
                    "Agriculture",
                    "Vegetable-crop weeding robot",
                    "Mechanical weeding and sowing in vegetable beds",
                    "Fields · vegetable beds",
                    "https://www.naio-technologies.com/en/orio-robot/",
                    "naio-technologies.com",
                    region="France",
                ),
            ],
            region="France",
        ),
        _company(
            "Ecorobotix",
            "ecorobotix",
            "ecorobotix.com",
            "https://www.ecorobotix.com/",
            "Agriculture",
            [
                _sku(
                    "Ecorobotix",
                    "ecorobotix",
                    "ARA",
                    "agricultural_robot",
                    "Agriculture",
                    "Precision spray implement",
                    "Ultra-high precision spray implement on a tractor host",
                    "Fields · row crops",
                    "https://www.ecorobotix.com/en/ara/",
                    "ecorobotix.com",
                    configuration_kind="implement_on_host",
                    host_platform="tractor",
                    region="Switzerland",
                )
            ],
            region="Switzerland",
        ),
        _company(
            "Burro",
            "burro",
            "goburro.com",
            "https://www.goburro.com/",
            "Agriculture",
            [
                _sku(
                    "Burro",
                    "burro",
                    "Burro",
                    "agricultural_robot",
                    "Agriculture",
                    "Crop transport robot",
                    "Follows crews and hauls harvest totes",
                    "Fields · orchards · nurseries",
                    "https://www.goburro.com/burro",
                    "goburro.com",
                )
            ],
        ),
        _company(
            "CLAAS",
            "claas",
            "claas.com",
            "https://www.claas.com/",
            "Agriculture",
            [
                _sku(
                    "CLAAS",
                    "claas",
                    "LEXION 8000-7000",
                    "agricultural_robot",
                    "Agriculture",
                    "Combine harvester",
                    "Grain harvest with a LEXION combine",
                    "Fields · grain harvest",
                    "https://www.claas.com/en-us/products/combines/lexion-8000-7000",
                    "claas.com",
                    region="Germany",
                )
            ],
            region="Germany",
        ),
        _company(
            "Dusty Robotics",
            "dusty-robotics",
            "dustyrobotics.com",
            "https://www.dustyrobotics.com/",
            "Construction",
            [
                _sku(
                    "Dusty Robotics",
                    "dusty-robotics",
                    "FieldPrinter",
                    "construction_robot",
                    "Construction",
                    "Jobsite layout printer",
                    "Prints construction layout on the floor",
                    "Homes · buildings · jobsites",
                    "https://www.dustyrobotics.com/fieldprinter",
                    "dustyrobotics.com",
                )
            ],
        ),
        _company(
            "ICON",
            "icon",
            "iconbuild.com",
            "https://www.iconbuild.com/",
            "Construction",
            [
                _sku(
                    "ICON",
                    "icon",
                    "Vulcan",
                    "construction_robot",
                    "Construction",
                    "3D home construction printer",
                    "3D-prints walls for homes and buildings",
                    "Residential construction · community build",
                    "https://www.iconbuild.com/vulcan",
                    "iconbuild.com",
                )
            ],
        ),
        _company(
            "COBOD",
            "cobod",
            "cobod.com",
            "https://cobod.com/",
            "Construction",
            [
                _sku(
                    "COBOD",
                    "cobod",
                    "BOD2",
                    "construction_robot",
                    "Construction",
                    "3D construction printer",
                    "3D-prints buildings on site",
                    "Building construction",
                    "https://cobod.com/bod2/",
                    "cobod.com",
                    region="Denmark",
                )
            ],
            region="Denmark",
        ),
        _company(
            "FBR",
            "fbr",
            "fbr.com.au",
            "https://www.fbr.com.au/",
            "Construction",
            [
                _sku(
                    "FBR",
                    "fbr",
                    "Hadrian X",
                    "construction_robot",
                    "Construction",
                    "Block-laying construction robot",
                    "Lays blocks for buildings",
                    "Building construction",
                    "https://www.fbr.com.au/",
                    "fbr.com.au",
                    region="Australia",
                )
            ],
            region="Australia",
        ),
        _company(
            "Advanced Construction Robotics",
            "advanced-construction-robotics",
            "constructionrobots.com",
            "https://www.constructionrobots.com/",
            "Construction",
            [
                _sku(
                    "Advanced Construction Robotics",
                    "advanced-construction-robotics",
                    "TyBOT",
                    "construction_robot",
                    "Construction",
                    "Rebar tying robot",
                    "Ties rebar on decks for buildings and civil work",
                    "Building construction · decks",
                    "https://www.constructionrobots.com/tybot/",
                    "constructionrobots.com",
                )
            ],
        ),
        _company(
            "Skydio",
            "skydio",
            "skydio.com",
            "https://www.skydio.com/",
            "Avionics",
            [
                _sku(
                    "Skydio",
                    "skydio",
                    "X10",
                    "drone",
                    "Avionics",
                    "Autonomous inspection drone",
                    "Autonomous drone inspection of assets and airframes",
                    "Outdoor inspection · flight",
                    "https://www.skydio.com/x10",
                    "skydio.com",
                )
            ],
        ),
        _company(
            "Joby Aviation",
            "joby-aviation",
            "jobyaviation.com",
            "https://www.jobyaviation.com/",
            "Avionics",
            [
                _sku(
                    "Joby Aviation",
                    "joby-aviation",
                    "Joby eVTOL",
                    "evtol",
                    "Avionics",
                    "eVTOL aircraft",
                    "Electric vertical takeoff passenger aircraft",
                    "Urban air mobility",
                    "https://www.jobyaviation.com/aircraft/",
                    "jobyaviation.com",
                )
            ],
        ),
        _company(
            "Archer",
            "archer",
            "archer.com",
            "https://www.archer.com/",
            "Avionics",
            [
                _sku(
                    "Archer",
                    "archer",
                    "Midnight",
                    "evtol",
                    "Avionics",
                    "eVTOL aircraft",
                    "Electric vertical takeoff passenger aircraft",
                    "Urban air mobility",
                    "https://www.archer.com/aircraft",
                    "archer.com",
                )
            ],
        ),
        _company(
            "Beta Technologies",
            "beta-technologies",
            "beta.team",
            "https://www.beta.team/",
            "Avionics",
            [
                _sku(
                    "Beta Technologies",
                    "beta-technologies",
                    "ALIA",
                    "evtol",
                    "Avionics",
                    "eVTOL / electric aircraft",
                    "Electric aircraft for cargo and passenger routes",
                    "Regional flight",
                    "https://www.beta.team/aircraft/",
                    "beta.team",
                )
            ],
        ),
        _company(
            "Wisk Aero",
            "wisk-aero",
            "wisk.aero",
            "https://wisk.aero/",
            "Avionics",
            [
                _sku(
                    "Wisk Aero",
                    "wisk-aero",
                    "Wisk Generation 6",
                    "evtol",
                    "Avionics",
                    "Autonomous eVTOL",
                    "Autonomous eVTOL passenger aircraft",
                    "Urban air mobility",
                    "https://wisk.aero/aircraft",
                    "wisk.aero",
                )
            ],
        ),
        _company(
            "Zipline",
            "zipline",
            "zipline.com",
            "https://www.zipline.com/",
            "Avionics",
            [
                _sku(
                    "Zipline",
                    "zipline",
                    "Zipline Platform 2",
                    "drone",
                    "Avionics",
                    "Delivery drone",
                    "Autonomous drone delivery of medical and retail payloads",
                    "Delivery corridors",
                    "https://www.zipline.com/",
                    "zipline.com",
                )
            ],
        ),
        _company(
            "Shield AI",
            "shield-ai",
            "shield.ai",
            "https://shield.ai/",
            "Avionics",
            [
                _sku(
                    "Shield AI",
                    "shield-ai",
                    "V-BAT",
                    "drone",
                    "Avionics",
                    "VTOL drone",
                    "Autonomous VTOL drone for inspection and ISR flight",
                    "Flight · inspection",
                    "https://shield.ai/v-bat/",
                    "shield.ai",
                )
            ],
        ),
        _company(
            "Astroscale",
            "astroscale",
            "astroscale.com",
            "https://astroscale.com/",
            "Aerospace",
            [
                _sku(
                    "Astroscale",
                    "astroscale",
                    "ELSA-d",
                    "aerospace_robot",
                    "Aerospace",
                    "On-orbit servicing / debris demonstration",
                    "Rendezvous and magnetic capture for end-of-life satellites",
                    "Low Earth orbit",
                    "https://astroscale.com/missions/elsa-d/",
                    "astroscale.com",
                    region="Japan / United Kingdom",
                ),
                _sku(
                    "Astroscale",
                    "astroscale",
                    "ADRAS-J",
                    "aerospace_robot",
                    "Aerospace",
                    "Active debris inspection",
                    "Inspects a large debris object on orbit",
                    "Low Earth orbit",
                    "https://astroscale.com/missions/adras-j/",
                    "astroscale.com",
                    region="Japan / United Kingdom",
                    configuration_kind="implement_on_host",
                    host_platform="satellite",
                ),
            ],
            region="Japan / United Kingdom",
        ),
        _company(
            "ClearSpace",
            "clearspace",
            "clearspace.today",
            "https://clearspace.today/",
            "Aerospace",
            [
                _sku(
                    "ClearSpace",
                    "clearspace",
                    "ClearSpace-1",
                    "aerospace_robot",
                    "Aerospace",
                    "Orbital debris removal",
                    "Captures and deorbits a debris object with a servicing satellite",
                    "Low Earth orbit",
                    "https://clearspace.today/",
                    "clearspace.today",
                    region="Switzerland",
                    configuration_kind="implement_on_host",
                    host_platform="satellite",
                )
            ],
            region="Switzerland",
        ),
        _company(
            "Starfish Space",
            "starfish-space",
            "starfishspace.com",
            "https://www.starfishspace.com/",
            "Aerospace",
            [
                _sku(
                    "Starfish Space",
                    "starfish-space",
                    "Otter",
                    "aerospace_robot",
                    "Aerospace",
                    "Satellite servicing tug",
                    "Rides along and services a client satellite",
                    "On orbit",
                    "https://www.starfishspace.com/",
                    "starfishspace.com",
                )
            ],
        ),
        _company(
            "GITAI",
            "gitai",
            "gitai.tech",
            "https://gitai.tech/",
            "Aerospace",
            [
                _sku(
                    "GITAI",
                    "gitai",
                    "GITAI S2",
                    "aerospace_robot",
                    "Aerospace",
                    "Space robot arm",
                    "In-space work and satellite servicing",
                    "On orbit · space development",
                    "https://gitai.tech/",
                    "gitai.tech",
                    region="Japan / United States",
                )
            ],
            region="Japan / United States",
        ),
        _company(
            "FarmDroid",
            "farmdroid",
            "farmdroid.com",
            "https://farmdroid.com/",
            "Agriculture",
            [
                _sku(
                    "FarmDroid",
                    "farmdroid",
                    "FD20",
                    "agricultural_robot",
                    "Agriculture",
                    "Seeding and weeding robot",
                    "Solar-powered seeding and mechanical weeding in row crops",
                    "Fields · row crops",
                    "https://farmdroid.com/products/farmdroid-fd20/",
                    "farmdroid.com",
                    region="Denmark",
                )
            ],
            region="Denmark",
        ),
        _company(
            "AgXeed",
            "agxeed",
            "agxeed.com",
            "https://www.agxeed.com/",
            "Agriculture",
            [
                _sku(
                    "AgXeed",
                    "agxeed",
                    "AgBot",
                    "agricultural_robot",
                    "Agriculture",
                    "Autonomous tractor robot",
                    "Autonomous tractor for planting and field work",
                    "Fields · planting",
                    "https://www.agxeed.com/agbot/",
                    "agxeed.com",
                    region="Netherlands",
                )
            ],
            region="Netherlands",
        ),
        _company(
            "Agrobot",
            "agrobot",
            "agrobot.com",
            "https://www.agrobot.com/",
            "Agriculture",
            [
                _sku(
                    "Agrobot",
                    "agrobot",
                    "E-Series",
                    "agricultural_robot",
                    "Agriculture",
                    "Robotic strawberry harvester",
                    "Harvests strawberries in the field",
                    "Fields · berry harvest",
                    "https://www.agrobot.com/e-series",
                    "agrobot.com",
                    region="Spain",
                )
            ],
            region="Spain",
        ),
        _company(
            "Verdant Robotics",
            "verdant-robotics",
            "verdantrobotics.com",
            "https://www.verdantrobotics.com/",
            "Agriculture",
            [
                _sku(
                    "Verdant Robotics",
                    "verdant-robotics",
                    "Sharp Shooter",
                    "agricultural_robot",
                    "Agriculture",
                    "Precision spray implement",
                    "See-and-spray implement on a tractor host",
                    "Fields · row crops",
                    "https://www.verdantrobotics.com/",
                    "verdantrobotics.com",
                    configuration_kind="implement_on_host",
                    host_platform="tractor",
                )
            ],
        ),
        _company(
            "Construction Robotics",
            "construction-robotics",
            "construction-robotics.com",
            "https://www.construction-robotics.com/",
            "Construction",
            [
                _sku(
                    "Construction Robotics",
                    "construction-robotics",
                    "MULE",
                    "construction_robot",
                    "Construction",
                    "Jobsite lifting robot",
                    "Lifts and places material on the construction jobsite",
                    "Building construction",
                    "https://www.construction-robotics.com/products/",
                    "construction-robotics.com",
                )
            ],
        ),
        _company(
            "Hilti",
            "hilti",
            "hilti.com",
            "https://www.hilti.com/",
            "Construction",
            [
                _sku(
                    "Hilti",
                    "hilti",
                    "Jaibot",
                    "construction_robot",
                    "Construction",
                    "Jobsite drilling robot",
                    "Autonomous overhead drilling on the construction jobsite",
                    "Building construction",
                    "https://www.hilti.com/content/hilti/W1/US/en/business/business/trends/jaibot.html",
                    "hilti.com",
                    region="Liechtenstein",
                )
            ],
            region="Liechtenstein",
        ),
        _company(
            "Volocopter",
            "volocopter",
            "volocopter.com",
            "https://www.volocopter.com/",
            "Avionics",
            [
                _sku(
                    "Volocopter",
                    "volocopter",
                    "VoloCity",
                    "evtol",
                    "Avionics",
                    "eVTOL aircraft",
                    "Electric vertical takeoff passenger aircraft",
                    "Urban air mobility",
                    "https://www.volocopter.com/en/product/volocity",
                    "volocopter.com",
                    region="Germany",
                )
            ],
            region="Germany",
        ),
        _company(
            "EHang",
            "ehang",
            "ehang.com",
            "https://www.ehang.com/",
            "Avionics",
            [
                _sku(
                    "EHang",
                    "ehang",
                    "EH216-S",
                    "evtol",
                    "Avionics",
                    "Autonomous eVTOL",
                    "Autonomous eVTOL passenger aircraft",
                    "Urban air mobility",
                    "https://www.ehang.com/ehang216s",
                    "ehang.com",
                    region="China",
                )
            ],
            region="China",
        ),
        _company(
            "SkyDrive",
            "skydrive",
            "skydrive2020.com",
            "https://en.skydrive2020.com/",
            "Avionics",
            [
                _sku(
                    "SkyDrive",
                    "skydrive",
                    "SD-05",
                    "evtol",
                    "Avionics",
                    "eVTOL aircraft",
                    "Electric vertical takeoff passenger aircraft",
                    "Urban air mobility",
                    "https://en.skydrive2020.com/sd-05",
                    "skydrive2020.com",
                    region="Japan",
                )
            ],
            region="Japan",
        ),
        _company(
            "AIR",
            "air",
            "theair.co",
            "https://theair.co/",
            "Avionics",
            [
                _sku(
                    "AIR",
                    "air",
                    "AIR ONE",
                    "evtol",
                    "Avionics",
                    "eVTOL aircraft",
                    "Electric vertical takeoff passenger aircraft",
                    "Urban air mobility",
                    "https://theair.co/air-one",
                    "theair.co",
                    region="Israel",
                )
            ],
            region="Israel",
        ),
        _company(
            "Doroni Aerospace",
            "doroni-aerospace",
            "doroni.io",
            "https://www.doroni.io/",
            "Avionics",
            [
                _sku(
                    "Doroni Aerospace",
                    "doroni-aerospace",
                    "H1-X",
                    "evtol",
                    "Avionics",
                    "eVTOL aircraft",
                    "Electric vertical takeoff passenger aircraft",
                    "Urban air mobility",
                    "https://www.doroni.io/h1-x",
                    "doroni.io",
                )
            ],
        ),
        _company(
            "Elroy Air",
            "elroy-air",
            "elroyair.com",
            "https://elroyair.com/",
            "Avionics",
            [
                _sku(
                    "Elroy Air",
                    "elroy-air",
                    "Chaparral",
                    "autonomous_aircraft",
                    "Avionics",
                    "Autonomous cargo VTOL",
                    "Autonomous cargo VTOL for middle-mile logistics",
                    "Cargo flight",
                    "https://elroyair.com/chaparral/aircraft",
                    "elroyair.com",
                )
            ],
        ),
        _company(
            "Flyability",
            "flyability",
            "flyability.com",
            "https://www.flyability.com/",
            "Avionics",
            [
                _sku(
                    "Flyability",
                    "flyability",
                    "Elios 3",
                    "drone",
                    "Avionics",
                    "Indoor inspection drone",
                    "Autonomous drone inspection inside confined assets",
                    "Indoor inspection · flight",
                    "https://www.flyability.com/elios-3",
                    "flyability.com",
                    region="Switzerland",
                )
            ],
            region="Switzerland",
        ),
        _company(
            "DJI",
            "dji",
            "dji.com",
            "https://www.dji.com/",
            "Avionics",
            [
                _sku(
                    "DJI",
                    "dji",
                    "Matrice 350 RTK",
                    "drone",
                    "Avionics",
                    "Enterprise inspection drone",
                    "Autonomous drone inspection of assets",
                    "Outdoor inspection · flight",
                    "https://enterprise.dji.com/matrice-350-rtk",
                    "dji.com",
                    region="China",
                )
            ],
            region="China",
        ),
        _company(
            "Parrot",
            "parrot",
            "parrot.com",
            "https://www.parrot.com/",
            "Avionics",
            [
                _sku(
                    "Parrot",
                    "parrot",
                    "ANAFI USA",
                    "drone",
                    "Avionics",
                    "Inspection drone",
                    "Autonomous drone inspection of assets",
                    "Outdoor inspection · flight",
                    "https://www.parrot.com/en/drones/anafi-usa",
                    "parrot.com",
                    region="France",
                )
            ],
            region="France",
        ),
        _company(
            "Wingtra",
            "wingtra",
            "wingtra.com",
            "https://wingtra.com/",
            "Avionics",
            [
                _sku(
                    "Wingtra",
                    "wingtra",
                    "WingtraOne GEN II",
                    "drone",
                    "Avionics",
                    "Survey mapping drone",
                    "Autonomous drone mapping and inspection",
                    "Survey · flight",
                    "https://wingtra.com/mapping-drone-wingtraone/",
                    "wingtra.com",
                    region="Switzerland",
                )
            ],
            region="Switzerland",
        ),
        _company(
            "Autel Robotics",
            "autel-robotics",
            "autelrobotics.com",
            "https://www.autelrobotics.com/",
            "Avionics",
            [
                _sku(
                    "Autel Robotics",
                    "autel-robotics",
                    "EVO Max Series",
                    "drone",
                    "Avionics",
                    "Enterprise inspection drone",
                    "Autonomous drone inspection of assets",
                    "Outdoor inspection · flight",
                    "https://www.autelrobotics.com/product/evo-max-series/",
                    "autelrobotics.com",
                )
            ],
        ),
        _company(
            "AgEagle",
            "ageagle",
            "ageagle.com",
            "https://ageagle.com/",
            "Avionics",
            [
                _sku(
                    "AgEagle",
                    "ageagle",
                    "eBee X",
                    "drone",
                    "Avionics",
                    "Fixed-wing mapping drone",
                    "Autonomous drone mapping and inspection",
                    "Survey · flight",
                    "https://ageagle.com/drones/ebee-x/",
                    "ageagle.com",
                )
            ],
        ),
        _company(
            "Voliro",
            "voliro",
            "voliro.com",
            "https://voliro.com/",
            "Avionics",
            [
                _sku(
                    "Voliro",
                    "voliro",
                    "Voliro T",
                    "drone",
                    "Avionics",
                    "Aerial inspection drone",
                    "Autonomous drone inspection of industrial assets",
                    "Outdoor inspection · flight",
                    "https://voliro.com/voliro-t",
                    "voliro.com",
                    region="Switzerland",
                )
            ],
            region="Switzerland",
        ),
        _company(
            "Robotnik",
            "robotnik",
            "robotnik.eu",
            "https://robotnik.eu/",
            "Logistics",
            [
                _sku(
                    "Robotnik",
                    "robotnik",
                    "RB-ROBOUT",
                    "amr",
                    "Logistics",
                    "Industrial AMR",
                    "Autonomous indoor material transport",
                    "Factories · warehouses",
                    "https://robotnik.eu/products/mobile-robots/rb-robout/",
                    "robotnik.eu",
                    region="Spain",
                )
            ],
            region="Spain",
        ),
        _company(
            "Neobotix",
            "neobotix",
            "neobotix-robots.com",
            "https://www.neobotix-robots.com/",
            "Logistics",
            [
                _sku(
                    "Neobotix",
                    "neobotix",
                    "MP-400",
                    "amr",
                    "Logistics",
                    "Industrial AMR",
                    "Autonomous indoor material transport",
                    "Factories · warehouses",
                    "https://www.neobotix-robots.com/products/mobile-robots/mobile-robot-mp-400",
                    "neobotix-robots.com",
                    region="Germany",
                )
            ],
            region="Germany",
        ),
        _company(
            "ForwardX Robotics",
            "forwardx-robotics",
            "forwardx.com",
            "https://www.forwardx.com/",
            "Logistics",
            [
                _sku(
                    "ForwardX Robotics",
                    "forwardx-robotics",
                    "Max Series",
                    "amr",
                    "Logistics",
                    "Warehouse AMR",
                    "Autonomous indoor material transport",
                    "Warehouses",
                    "https://www.forwardx.com/max-series/",
                    "forwardx.com",
                )
            ],
        ),
        _company(
            "Exotec",
            "exotec",
            "exotec.com",
            "https://www.exotec.com/",
            "Logistics",
            [
                _sku(
                    "Exotec",
                    "exotec",
                    "Skypod",
                    "amr",
                    "Logistics",
                    "ASRS warehouse robot",
                    "Autonomous goods-to-person storage and retrieval",
                    "Warehouses",
                    "https://www.exotec.com/skypod-system/",
                    "exotec.com",
                    region="France",
                )
            ],
            region="France",
        ),
        _company(
            "SESTO Robotics",
            "sesto-robotics",
            "sestorobotics.com",
            "https://www.sestorobotics.com/",
            "Logistics",
            [
                _sku(
                    "SESTO Robotics",
                    "sesto-robotics",
                    "Magnus",
                    "amr",
                    "Logistics",
                    "Industrial AMR",
                    "Autonomous indoor material transport",
                    "Factories · warehouses",
                    "https://www.sestorobotics.com/magnus",
                    "sestorobotics.com",
                    region="Singapore",
                )
            ],
            region="Singapore",
        ),
    ]
    product_count = sum(len(c["products"]) for c in companies)
    return {
        "ontology_id": "vertical_oem_sku_catalog_v1",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "source": "missions/2026-08-27-seed-verified-oem-catalog",
        "rule": "COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES",
        "notes": [
            "Official sites only. product_url set only after HTTP 200 on 2026-08-27.",
            "Named SKUs only. Empty specs stay UNKNOWN. Not Job Card employers.",
            "Tractor implements are configuration_kind=implement_on_host, not a class.",
            "Avionics split: evtol (air-taxi), drone (inspect/delivery), autonomous_aircraft (cargo VTOL / airplane-like).",
            "ChatGPT names without an official SKU page are leftovers — not invented rows.",
            "Skip software-only (DroneDeploy). Skip AMRA alliance.",
        ],
        "company_count": len(companies),
        "product_count": product_count,
        "skipped_unverified": [
            {"name": "Built Robotics", "reason": "homepage 403 (retry)"},
            {"name": "Canvas", "reason": "SSL handshake failure (retry)"},
            {"name": "Honeybee Robotics", "reason": "homepage 429 (retry)"},
            {"name": "Advanced Farm Technologies", "reason": "connection error / timeout (retry)"},
            {"name": "DroneDeploy", "reason": "software-only, not a manufacturer SKU"},
            {"name": "AMRA", "reason": "alliance, not a manufacturer"},
            {"name": "Eve Air Mobility", "reason": "homepage 403"},
            {"name": "Lilium", "reason": "SSL certificate expired"},
            {"name": "Overair", "reason": "SSL handshake failure"},
            {"name": "Bluewhite Pathfinder", "reason": "named SKU URL 404; homepage 200 has no Pathfinder page"},
            {"name": "MightyFly Cento", "reason": "homepage 200; /cento 404 — do not invent Cento"},
            {"name": "Monumental Pisa/Petra/Panama", "reason": "homepage 200; no official named SKU page"},
            {"name": "Construction Robotics SAM", "reason": "SAM URL 404; ingested MULE from /products/ 200"},
            {"name": "Vertical Aerospace VX4", "reason": "homepage 200; /vx4 404"},
            {"name": "ABB Flexley Tug P603", "reason": "timeout"},
            {"name": "KUKA KMP", "reason": "product URL 404"},
            {"name": "Clearpath", "reason": "timeout"},
            {"name": "Zebra/Fetch AMR", "reason": "406"},
            {"name": "OMRON LD", "reason": "404"},
            {"name": "PeK Agroline", "reason": "connection error"},
            {"name": "Small Robot Company", "reason": "403"},
            {"name": "Urban Aeronautics", "reason": "404"},
            {"name": "HP SitePrint", "reason": "404"},
            {"name": "Quantum-Systems Trinity", "reason": "403"},
        ],
        "companies": companies,
    }


def main() -> int:
    vertical = build()
    write_json(VERTICAL_CATALOG_PATH, vertical)
    catalog = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    merge_vertical_catalog(catalog, vertical)
    catalog["generated_at"] = vertical["generated_at"]
    write_json(ONTOLOGY_PATH, catalog)
    seed = compile_vendor_seed(catalog)
    write_json(SEED_PATH, seed)
    print(
        f"vertical companies={vertical['company_count']} products={vertical['product_count']}"
    )
    print(
        f"merged catalog companies={catalog['company_count']} products={catalog['product_count']}"
    )
    print(f"seed vendors={seed['vendor_count']} robots={seed['robot_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
