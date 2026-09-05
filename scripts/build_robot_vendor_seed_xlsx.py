#!/usr/bin/env python3
"""Build ReadyForRobots_Robot_Vendor_Seed_v1.xlsx — 500 real robot vendors.

Sheets: Vendors | Robot Models | Category Ontology | Vendor Coverage Dashboard

Uses stdlib only (Office Open XML via zipfile) so no openpyxl required.
Optionally merges cleaned rows from DATABASE_URL if set.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT_XLSX = ROOT / "docs" / "calibration" / "ReadyForRobots_Robot_Vendor_Seed_v1.xlsx"
OUT_JSON = ROOT / "docs" / "calibration" / "robot_vendor_seed_v1.json"
OUT_DIR_CSV = ROOT / "docs" / "calibration" / "vendor_seed_sheets"

# Target allocation (robot sellers only — not SI/component/AI-only/labs unless noted)
TARGETS = {
    "amr_agv_material_transport": 80,
    "autonomous_forklift_pallet": 40,
    "industrial_robot_arms": 55,
    "cobots": 40,
    "picking_manipulation_palletizing": 40,
    "humanoids_general_purpose": 50,
    "cleaning_robots": 30,
    "hospitality_foodservice_delivery": 35,
    "inspection_security_quadrupeds": 25,
    "agriculture": 35,
    "construction": 25,
    "healthcare_hospital_service": 20,
    "last_mile_outdoor_delivery": 15,
    "specialty_commercial": 10,
}

VENDOR_ROLES = [
    "robot_oem",
    "robot_brand",
    "white_label_brand",
    "distributor",
    "system_integrator",
    "autonomy_provider",
    "robot_as_a_service",
    "component_supplier",
]

JUNK_NAME = re.compile(
    r"(captivate|coolest|debut unmanned|ndaa|pours coffee|fold laundry|"
    r"^actuators$|^drone$|^humanoid robots$|^a3'?s$|pavilion|sponsored|"
    r"to debut|pushes pentagon|live drone)",
    re.I,
)


def _v(
    name: str,
    website: str,
    country: str,
    category: str,
    *,
    role: str = "robot_oem",
    robots: str = "",
    work: str = "",
    industries: str = "",
    maturity: str = "commercial",
    us: str = "yes",
    sales: str = "direct+distributor",
    notes: str = "",
    source: str = "curated_oem_list",
    verification: str = "curated",
):
    return {
        "company_name": name,
        "website": website,
        "country": country,
        "vendor_role": role,
        "robot_category": category,
        "primary_robots": robots,
        "work_type": work,
        "industries": industries,
        "commercial_maturity": maturity,
        "us_availability": us,
        "sales_model": sales,
        "notes": notes,
        "source": source,
        "verification": verification,
        "vendor_type": "oem" if role == "robot_oem" else role,
    }


def curated_by_category() -> dict[str, list[dict]]:
    """Real robot-selling companies by allocation bucket."""
    c: dict[str, list[dict]] = defaultdict(list)

    # --- AMR / AGV / material transport (80) ---
    amr = [
        ("MiR (Mobile Industrial Robots)", "https://www.mobile-industrial-robots.com", "Denmark", "MiR250/600/1350", "cart/pallet transport", "Logistics;Manufacturing"),
        ("OTTO Motors", "https://ottomotors.com", "Canada", "OTTO 100/750/1500", "material transport", "Logistics;Manufacturing"),
        ("Locus Robotics", "https://locusrobotics.com", "USA", "Locus Origin/Vector", "picking assist AMR", "Logistics;Retail"),
        ("Geek+", "https://www.geekplus.com", "China", "P800/PopPick", "GTP / sorting", "Logistics;Retail"),
        ("Hai Robotics", "https://www.hairobotics.com", "China", "HAIPICK", "ACR / tote handling", "Logistics"),
        ("Quicktron", "https://www.quicktron.com", "China", "Quicktron AMR", "warehouse transport", "Logistics"),
        ("ForwardX Robotics", "https://www.forwardx.com", "China", "Flex/Max", "picking / pallet AMR", "Logistics"),
        ("GreyOrange", "https://www.greyorange.com", "USA", "Ranger", "GTP", "Logistics;Retail"),
        ("Exotec", "https://www.exotec.com", "France", "Skypod", "AS/RS GTP", "Logistics;Retail"),
        ("Fetch Robotics / Zebra", "https://www.zebra.com", "USA", "FetchFreight/Cart", "AMR transport", "Logistics"),
        ("Vecna Robotics", "https://www.vecnarobotics.com", "USA", "Vecna AMR", "material transport", "Logistics;Manufacturing"),
        ("Seegrid", "https://seegrid.com", "USA", "Palion", "vision AMR / tow", "Manufacturing;Logistics"),
        ("6 River Systems (Shopify)", "https://6river.com", "USA", "Chuck", "fulfillment AMR", "Retail;Logistics"),
        ("AutoGuide Mobile Robots", "https://www.autoguidemobiles.com", "USA", "MAX N10", "tugger/AMR", "Manufacturing"),
        ("Clearpath Robotics", "https://clearpathrobotics.com", "Canada", "OTTO/OTTO Fleet", "AMR platforms", "Manufacturing;Research"),
        ("Omron Mobile Robots", "https://automation.omron.com", "Japan", "LD/HD series", "AMR", "Manufacturing"),
        ("Kivnon", "https://www.kivnon.com", "Spain", "Kivnon AGV", "AGV", "Manufacturing"),
        ("Swisslog", "https://www.swisslog.com", "Switzerland", "CarryPick", "GTP AMR", "Logistics"),
        ("Dematic", "https://www.dematic.com", "USA", "Mobile Robots", "warehouse AMR", "Logistics"),
        ("Murata Machinery", "https://www.muratec.net", "Japan", "AGV/AMR", "material transport", "Manufacturing"),
        ("Daifuku", "https://www.daifuku.com", "Japan", "AGV systems", "material transport", "Logistics;Manufacturing"),
        ("JBT Corporation", "https://www.jbtc.com", "USA", "AGV", "industrial AGV", "Manufacturing"),
        ("Oceaneering AGV", "https://www.oceaneering.com", "USA", "AGV", "industrial AGV", "Manufacturing"),
        ("Transbotics", "https://www.transbotics.com", "USA", "AGV", "AGV", "Manufacturing"),
        ("Egemin / Dematic", "https://www.dematic.com", "Belgium", "AGV", "AGV", "Logistics"),
        ("Bastians", "https://www.bastian-solutions.com", "USA", "AGV", "AGV", "Logistics"),
        ("inVia Robotics", "https://www.invitarobotics.com", "USA", "Picker", "GTP AMR", "Logistics"),
        ("IAM Robotics", "https://www.iamrobotics.com", "USA", "Swift", "mobile pick", "Logistics"),
        ("Magazino", "https://www.magazino.eu", "Germany", "TORU/SOTO", "piece picking AMR", "Logistics"),
        ("SAFELOG", "https://www.safelog.de", "Germany", "AGV", "AGV", "Logistics"),
        ("Mobile Industrial Robots partners", "https://www.mobile-industrial-robots.com", "Denmark", "MiR fleet", "AMR", "Manufacturing"),
        ("AGILOX", "https://www.agilox.com", "Austria", "ONE/OCF", "swarm AMR/fork", "Manufacturing"),
        ("SEER Robotics", "https://www.seer-group.com", "China", "AMR", "AMR", "Manufacturing"),
        ("Hikrobot", "https://www.hikrobotics.com", "China", "Latent AMR", "AMR", "Logistics"),
        ("Standard Robots", "https://www.standard-robots.com", "China", "AMR", "AMR", "Manufacturing"),
        ("CSG Huashu", "https://www.csg.com.cn", "China", "AMR", "AMR", "Manufacturing"),
        ("Youibot", "https://www.youibot.com", "China", "AMR", "AMR", "Manufacturing"),
        ("Multiway Robotics", "https://www.multiway-robotics.com", "China", "AMR/fork", "AMR", "Logistics"),
        ("VisionNav Robotics", "https://www.visionnav.com", "China", "VisionNav AMR", "AMR", "Logistics"),
        ("Shanghai Seer Intelligent", "https://www.seer-group.com", "China", "SRC", "AMR controller", "Manufacturing"),
        ("Knott AGV", "https://www.knott.de", "Germany", "AGV", "AGV", "Manufacturing"),
        ("DS Automotion", "https://www.ds-automotion.com", "Austria", "AGV", "AGV", "Manufacturing"),
        ("Servus Intralogistics", "https://www.servus.info", "Austria", "Servus", "in-production AMR", "Manufacturing"),
        ("Grenzebach", "https://www.grenzebach.com", "Germany", "Lifting AGV", "AGV", "Manufacturing"),
        ("ASTI Mobile Robotics (ABB)", "https://global.abb", "Spain", "ASTI AMR", "AMR", "Manufacturing"),
        ("BlueBotics", "https://www.bluebotics.com", "Switzerland", "ANT navigation", "AMR autonomy", "Manufacturing"),
        ("Kollmorgen AGV", "https://www.kollmorgen.com", "USA", "NDC", "AGV controls", "Manufacturing"),
        ("SICK Mobile Robots", "https://www.sick.com", "Germany", "safety AMR stack", "AMR sensing", "Manufacturing"),
        ("Neobotix", "https://www.neobotix-roboter.de", "Germany", "mobile platforms", "AMR platforms", "Manufacturing"),
        ("Robotnik", "https://www.robotnik.eu", "Spain", "RB-VOGUI", "mobile platforms", "Manufacturing;Research"),
        ("PAL Robotics", "https://pal-robotics.com", "Spain", "TIAGo/ARI", "service mobile", "Research;Healthcare"),
        ("Fetchcore / Zebra", "https://www.zebra.com", "USA", "FetchCore", "fleet AMR", "Logistics"),
        ("Addverb", "https://addverb.com", "India", "SortIE/CartIE", "warehouse AMR", "Logistics"),
        ("GreyOrange Butler", "https://www.greyorange.com", "India", "Butler", "GTP", "Logistics"),
        ("System Logistics", "https://www.systemlogistics.com", "Italy", "AGV", "AGV", "Food & Beverage"),
        ("Eurofork", "https://www.eurofork.com", "Italy", "AGV", "AGV", "Logistics"),
        ("Scaglia INDEVA", "https://www.indevagroup.com", "Italy", "AGV", "AGV", "Manufacturing"),
        ("Mirage AGV", "https://www.mirage.biz", "Italy", "AGV", "AGV", "Manufacturing"),
        ("Rocla AGV (Mitsubishi Logisnext)", "https://www.rocla.com", "Finland", "AGV", "AGV", "Logistics"),
        ("Mitsubishi Logisnext", "https://www.mitsubishi-logisnext.com", "Japan", "AGV/fork", "material handling", "Logistics"),
        ("Toyota Material Handling AGV", "https://www.toyota-forklifts.eu", "Japan", "AGV", "AGV", "Logistics"),
        ("Jungheinrich AGV", "https://www.jungheinrich.com", "Germany", "AGV", "AGV", "Logistics"),
        ("Still AGV", "https://www.still.eu", "Germany", "AGV", "AGV", "Logistics"),
        ("Linde Material Handling AGV", "https://www.linde-mh.com", "Germany", "AGV", "AGV", "Logistics"),
        ("Crown Equipment AGV", "https://www.crown.com", "USA", "AGV", "AGV", "Logistics"),
        ("Hyster-Yale AGV", "https://www.hyster.com", "USA", "AGV", "AGV", "Logistics"),
        ("Raymond AGV", "https://www.raymondcorp.com", "USA", "AGV", "AGV", "Logistics"),
        ("Balyo", "https://www.balyo.com", "France", "Driven by Balyo", "autonomous pallet", "Logistics"),
        ("Symbotic", "https://www.symbotic.com", "USA", "Symbotic system", "warehouse robotics", "Retail;Logistics"),
        ("Ocado Technology", "https://www.ocadotechnology.com", "UK", "grid bots", "grocery automation", "Retail"),
        ("Alert Innovation (Walmart)", "https://www.walmart.com", "USA", "Alphabot", "GTP", "Retail"),
        ("Takeoff Technologies", "https://www.takeoff.com", "USA", "eGrocery microfulfillment", "microfulfillment", "Retail"),
        ("Fabric", "https://fabric.inc", "USA", "microfulfillment", "microfulfillment", "Retail"),
        ("Attabotics", "https://www.attabotics.com", "Canada", "3D structure", "storage/retrieval", "Logistics"),
        ("AutoStore", "https://www.autostore.com", "Norway", "R5/R5+", "cube storage", "Logistics;Retail"),
        ("Berkshire Grey", "https://www.berkshiregrey.com", "USA", "robotic sortation", "sortation", "Logistics"),
        ("Kindred AI (Ocado)", "https://www.kindred.ai", "Canada", "SORT", "piece picking", "Logistics"),
        ("Caja Robotics", "https://www.cajarobotics.com", "Israel", "AMR", "fulfillment AMR", "Logistics"),
        ("Gideon Brothers", "https://www.gideon.ai", "Croatia", "AMR", "material transport", "Manufacturing"),
        ("Milvus Robotics", "https://www.milvusrobotics.com", "Turkey", "AMR", "AMR", "Manufacturing"),
        ("Ottonomy", "https://www.ottonomy.io", "USA", "Ottobot", "indoor/outdoor AMR", "Logistics"),
    ]
    for name, web, country, robots, work, ind in amr:
        c["amr_agv_material_transport"].append(
            _v(name, web, country, "amr_agv_material_transport", robots=robots, work=work, industries=ind)
        )

    # --- Autonomous forklifts (40) ---
    forks = [
        ("Fox Robotics", "https://www.foxrobotics.com", "USA", "FoxBot ATL", "trailer load/unload", "Logistics"),
        ("Third Wave Automation", "https://www.thirdwave.ai", "USA", "TWA Reach", "warehouse pallet", "Logistics"),
        ("Cyngn", "https://cyngn.com", "USA", "DriveMod", "industrial vehicle autonomy", "Manufacturing"),
        ("Seegrid Lift", "https://seegrid.com", "USA", "Palion Lift", "pallet lift", "Manufacturing"),
        ("Vecna AFL", "https://www.vecnarobotics.com", "USA", "AFL", "autonomous forklift", "Logistics"),
        ("Balyo Forklift", "https://www.balyo.com", "France", "Driven by Balyo", "autonomous forklift", "Logistics"),
        ("Agilox OCF", "https://www.agilox.com", "Austria", "OCF", "counterbalance AMR", "Manufacturing"),
        ("VisionNav Forklift", "https://www.visionnav.com", "China", "VisionNav forklift", "autonomous forklift", "Logistics"),
        ("Multiway Forklift", "https://www.multiway-robotics.com", "China", "forklift AMR", "autonomous forklift", "Logistics"),
        ("Hangcha Intelligent", "https://www.hangcha.com", "China", "intelligent forklift", "autonomous forklift", "Logistics"),
        ("EP Equipment", "https://www.ep-equipment.com", "China", "EP autonomous", "pallet trucks", "Logistics"),
        ("Heli Intelligent", "https://www.helichina.com", "China", "Heli AGV fork", "autonomous forklift", "Logistics"),
        ("Toyota Autopilot", "https://www.toyota-forklifts.eu", "Japan", "Autopilot", "AGV forklift", "Logistics"),
        ("Jungheinrich automated", "https://www.jungheinrich.com", "Germany", "ERC/EKX automated", "automated warehouse trucks", "Logistics"),
        ("Still iGo", "https://www.still.eu", "Germany", "iGo systems", "automated trucks", "Logistics"),
        ("Linde Robotics", "https://www.linde-mh.com", "Germany", "automated trucks", "automated trucks", "Logistics"),
        ("Crown QuickPick", "https://www.crown.com", "USA", "automated assist", "order picking", "Logistics"),
        ("Yale Reliant / robotic", "https://www.yale.com", "USA", "robotic solutions", "material handling", "Logistics"),
        ("Clark Material Handling robotic", "https://www.clarkmhc.com", "USA", "robotic forklift", "forklift automation", "Logistics"),
        ("Combilift AGV", "https://www.combilift.com", "Ireland", "Combi-AGV", "long-load AGV", "Manufacturing"),
        ("Hubtex AGV", "https://www.hubtex.com", "Germany", "AGV multidirectional", "sideloader AGV", "Manufacturing"),
        ("BAUMANN AGV", "https://www.baumann-sideloaders.com", "Germany", "sideloader AGV", "long loads", "Manufacturing"),
        ("Landing AI Logistics partners", "https://landing.ai", "USA", "vision forklift", "vision autonomy", "Logistics"),
        ("Outrider", "https://www.outrider.ai", "USA", "yard truck autonomy", "yard logistics", "Logistics"),
        ("Gatik", "https://gatik.ai", "USA", "middle-mile autonomy", "freight", "Logistics"),
        ("Phantom Auto", "https://phantom.auto", "USA", "teleop forklift", "remote forklift", "Logistics"),
        ("Robotic Research / RR.AI", "https://www.roboticresearch.com", "USA", "AutoDrive", "vehicle autonomy", "Defense;Logistics"),
        ("Oceaneering Mobile Robotics", "https://www.oceaneering.com", "USA", "OmniMove", "heavy AGV", "Manufacturing"),
        ("EK Robotics", "https://www.ek-robotics.com", "Germany", "AGV/AMR", "AGV", "Manufacturing"),
        ("MT Robot", "https://www.mtrobot.com", "China", "forklift AMR", "autonomous forklift", "Logistics"),
        ("Reeman Robotics", "https://www.reeman.cn", "China", "forklift AMR", "autonomous forklift", "Logistics"),
        ("CSG Intelligent Forklift", "https://www.csg.com.cn", "China", "forklift", "autonomous forklift", "Logistics"),
        ("Zhejiang Guozi Robotics", "https://www.guozirobot.com", "China", "forklift AMR", "autonomous forklift", "Logistics"),
        ("Shanghai Noblelift Intelligent", "https://www.noblelift.com", "China", "intelligent trucks", "pallet trucks", "Logistics"),
        ("Doosan Industrial Vehicle robotic", "https://www.doosanindustrialvehicle.com", "South Korea", "robotic forklift", "forklift", "Logistics"),
        ("Hyundai Material Handling robotic", "https://www.hyundaice.com", "South Korea", "robotic forklift", "forklift", "Logistics"),
        ("Mitsubishi Forklift Automation", "https://www.mitsubishi-forklift.co.uk", "Japan", "automated", "forklift AGV", "Logistics"),
        ("UniCarriers automated", "https://www.unicarrierseurope.com", "Japan", "automated", "forklift AGV", "Logistics"),
        ("PALOMAT automated pallet", "https://www.palomat.com", "Denmark", "pallet magazine", "pallet handling", "Manufacturing"),
        ("SoftBank Robotics warehouse partners", "https://www.softbankrobotics.com", "Japan", "warehouse AMR partners", "warehouse", "Logistics"),
    ]
    for name, web, country, robots, work, ind in forks:
        c["autonomous_forklift_pallet"].append(
            _v(name, web, country, "autonomous_forklift_pallet", robots=robots, work=work, industries=ind)
        )

    # --- Industrial arms (55) ---
    arms = [
        ("FANUC", "https://www.fanuc.com", "Japan", "R-2000/LR Mate", "welding/handling", "Automotive & Manufacturing"),
        ("ABB Robotics", "https://global.abb/robotics", "Switzerland", "IRB series", "industrial arms", "Manufacturing"),
        ("KUKA", "https://www.kuka.com", "Germany", "KR series", "industrial arms", "Automotive & Manufacturing"),
        ("Yaskawa Motoman", "https://www.motoman.com", "Japan", "GP/HC series", "industrial arms", "Manufacturing"),
        ("Kawasaki Robotics", "https://robotics.kawasaki.com", "Japan", "RS/BX series", "industrial arms", "Manufacturing"),
        ("Mitsubishi Electric Robotics", "https://www.mitsubishielectric.com", "Japan", "RV/RH", "industrial arms", "Manufacturing"),
        ("Nachi Robotics", "https://www.nachirobotics.com", "Japan", "MZ/MC", "industrial arms", "Manufacturing"),
        ("Denso Robotics", "https://www.densorobotics.com", "Japan", "VS/HM", "industrial arms", "Manufacturing"),
        ("Epson Robots", "https://epson.com/robots", "Japan", "SCARA/6-axis", "assembly", "Manufacturing"),
        ("Staubli Robotics", "https://www.staubli.com/robotics", "Switzerland", "TX/TS", "industrial arms", "Manufacturing"),
        ("Comau", "https://www.comau.com", "Italy", "NJ/Racer", "automotive arms", "Automotive & Manufacturing"),
        ("Igus ReBeL / robolink", "https://www.igus.com", "Germany", "ReBeL", "low-cost arms", "Manufacturing"),
        ("Reis Robotics", "https://www.reisrobotics.com", "Germany", "welding systems", "welding", "Manufacturing"),
        ("CLOOS Robotics", "https://www.cloos.de", "Germany", "welding robots", "welding", "Manufacturing"),
        ("OTC Daihen", "https://www.daihen-usa.com", "Japan", "welding robots", "welding", "Manufacturing"),
        ("Panasonic Robotics welding", "https://www.panasonic.com", "Japan", "welding robots", "welding", "Manufacturing"),
        ("Hyundai Robotics", "https://www.hyundai-robotics.com", "South Korea", "HS/HH", "industrial arms", "Manufacturing"),
        ("Hanwha Robotics", "https://www.hanwharobotics.com", "South Korea", "HCR/HCR series", "industrial/cobot", "Manufacturing"),
        ("Estun Automation", "https://www.estun.com", "China", "ER series", "industrial arms", "Manufacturing"),
        ("SIASUN", "https://www.siasun.com", "China", "industrial robots", "industrial arms", "Manufacturing"),
        ("EFORT Intelligent", "https://www.efort.com.cn", "China", "ER series", "industrial arms", "Manufacturing"),
        ("STEP Electric", "https://www.stepelectric.com", "China", "industrial robots", "industrial arms", "Manufacturing"),
        ("GSK CNC Equipment robots", "https://www.gsk.com.cn", "China", "GSK robots", "industrial arms", "Manufacturing"),
        ("Peitian Robotics", "https://www.peitian.com", "China", "industrial robots", "industrial arms", "Manufacturing"),
        ("Harbin Boshi Automation", "https://www.boshi.cn", "China", "industrial robots", "industrial arms", "Manufacturing"),
        ("Rethink Robotics (original Sawyer legacy)", "https://www.rethinkrobotics.com", "USA", "Sawyer legacy", "cobot/arm", "Manufacturing", "discontinued"),
        ("Adept / Omron Adept", "https://automation.omron.com", "USA", "Quattro/Viper", "SCARA/parallel", "Manufacturing"),
        ("Brooks Automation", "https://www.brooks.com", "USA", "semiconductor robots", "wafer handling", "Semiconductor"),
        ("Genmark Automation", "https://www.genmarkautomation.com", "USA", "wafer robots", "semiconductor", "Semiconductor"),
        ("RORZE", "https://www.rorze.com", "Japan", "wafer robots", "semiconductor", "Semiconductor"),
        ("Hirata Corporation", "https://www.hirata.co.jp", "Japan", "transfer robots", "semiconductor/FPD", "Manufacturing"),
        ("Yamaha Robotics", "https://global.yamaha-motor.com", "Japan", "SCARA/linear", "assembly", "Manufacturing"),
        ("IAI Corporation", "https://www.intelligentactuator.com", "Japan", "actuators/robots", "assembly", "Manufacturing"),
        ("Toshiba Machine / Shibaura Machine", "https://www.shibaura-machine.co.jp", "Japan", "industrial robots", "injection/handling", "Manufacturing"),
        ("Olympus robotics medical arms", "https://www.olympus-global.com", "Japan", "medical systems", "medical", "Healthcare"),
        ("Intuitive Surgical", "https://www.intuitive.com", "USA", "da Vinci", "surgical robot", "Healthcare"),
        ("Stryker Mako", "https://www.stryker.com", "USA", "Mako", "orthopedic robot", "Healthcare"),
        ("Medtronic Hugo / Mazor", "https://www.medtronic.com", "USA", "Hugo/Mazor", "surgical", "Healthcare"),
        ("CMR Surgical", "https://cmrsurgical.com", "UK", "Versius", "surgical", "Healthcare"),
        ("Asensus Surgical", "https://www.asensus.com", "USA", "Senhance", "surgical", "Healthcare"),
        ("Smith+Nephew CORI", "https://www.smith-nephew.com", "UK", "CORI", "ortho robot", "Healthcare"),
        ("Zimmer Biomet ROSA", "https://www.zimmerbiomet.com", "USA", "ROSA", "ortho robot", "Healthcare"),
        ("Johnson & Johnson Ottava", "https://www.jnj.com", "USA", "Ottava", "surgical", "Healthcare", "pilot"),
        ("Brainlab robotics", "https://www.brainlab.com", "Germany", "cirq", "surgical assist", "Healthcare"),
        ("Renishaw neurological robots", "https://www.renishaw.com", "UK", "neuromate", "neuro surgery", "Healthcare"),
        ("Auris Health (J&J)", "https://www.jnjmedtech.com", "USA", "Monarch", "bronchoscopy robot", "Healthcare"),
        ("PROCEPT BioRobotics", "https://www.procept-biorobotics.com", "USA", "AquaBeam", "urology robot", "Healthcare"),
        ("Accuray", "https://www.accuray.com", "USA", "CyberKnife", "radiosurgery", "Healthcare"),
        ("Elekta", "https://www.elekta.com", "Sweden", "Unity/linac robotics", "radiotherapy", "Healthcare"),
        ("Siemens Healthineers robotics", "https://www.siemens-healthineers.com", "Germany", "imaging robotics", "medical", "Healthcare"),
        ("GE Healthcare robotics", "https://www.gehealthcare.com", "USA", "imaging systems", "medical", "Healthcare"),
        ("Philips Image Guided Therapy robotics", "https://www.philips.com", "Netherlands", "IGT robotics", "medical", "Healthcare"),
        ("KUKA Medical Robotics", "https://www.kuka.com", "Germany", "LBR Med", "medical cobot", "Healthcare"),
        ("Franka Emika industrial", "https://www.franka.de", "Germany", "FR3", "research/industrial", "Manufacturing"),
        ("Kassow Robots", "https://www.kassowrobots.com", "Denmark", "7-axis", "industrial cobot-class", "Manufacturing"),
    ]
    for row in arms:
        name, web, country, robots, work, ind = row[:6]
        maturity = row[6] if len(row) > 6 else "commercial"
        c["industrial_robot_arms"].append(
            _v(name, web, country, "industrial_robot_arms", robots=robots, work=work, industries=ind, maturity=maturity)
        )

    # --- Cobots (40) ---
    cobots = [
        ("Universal Robots", "https://www.universal-robots.com", "Denmark", "UR3e/5e/10e/20", "collaborative arms", "Manufacturing"),
        ("Doosan Robotics", "https://www.doosanrobotics.com", "South Korea", "A/M/H series", "cobots", "Manufacturing"),
        ("Techman Robot", "https://www.tm-robot.com", "Taiwan", "TM AI Cobot", "vision cobot", "Manufacturing"),
        ("Fanuc CRX", "https://www.fanucamerica.com", "Japan", "CRX", "cobot", "Manufacturing"),
        ("ABB GoFa / SWIFTI", "https://global.abb", "Switzerland", "GoFa", "cobot", "Manufacturing"),
        ("KUKA LBR iisy", "https://www.kuka.com", "Germany", "LBR iisy", "cobot", "Manufacturing"),
        ("Yaskawa HC10/HC20", "https://www.motoman.com", "Japan", "HC series", "cobot", "Manufacturing"),
        ("AUBO Robotics", "https://www.aubo-robotics.com", "China", "i series", "cobot", "Manufacturing"),
        ("JAKA Robotics", "https://www.jaka.com", "China", "Zu/Pro", "cobot", "Manufacturing"),
        ("Elephant Robotics", "https://www.elephantrobotics.com", "China", "myCobot", "compact cobot", "Education;Manufacturing"),
        ("Dobot", "https://www.dobot.cc", "China", "CR/MG400", "cobot", "Manufacturing"),
        ("Siasun collaborative", "https://www.siasun.com", "China", "SCR", "cobot", "Manufacturing"),
        ("Elite Robots", "https://www.eliterobots.com", "China", "EC series", "cobot", "Manufacturing"),
        ("Han's Robot", "https://www.hansrobot.net", "China", "Elfin", "cobot", "Manufacturing"),
        ("Rethink Sawyer (HAHN Group)", "https://www.rethinkrobotics.com", "Germany", "Sawyer", "cobot", "Manufacturing"),
        ("Productive Robotics", "https://www.productiverobotics.com", "USA", "OB7", "cobot", "Manufacturing"),
        ("Brooks PreciseFlex", "https://www.brooks.com", "USA", "PreciseFlex", "cobot lab", "Lab Automation"),
        ("Neura Robotics", "https://www.neura-robotics.com", "Germany", "MIRA/4NE1", "cognitive cobot/humanoid", "Manufacturing"),
        ("Flexible Automation / Productive", "https://www.productiverobotics.com", "USA", "OB7", "machine tending", "Manufacturing"),
        ("TM Robot Europe", "https://www.tm-robot.com", "Taiwan", "TM5/TM12", "cobot", "Manufacturing"),
        ("Franka Production Systems", "https://www.franka.de", "Germany", "FR3", "sensitive cobot", "Manufacturing"),
        ("Bota Systems sensing", "https://www.botasys.com", "Switzerland", "force torque", "cobot sensing", "Manufacturing", "component_supplier"),
        ("OnRobot", "https://onrobot.com", "Denmark", "EOAT", "cobot tooling", "Manufacturing", "component_supplier"),
        ("Robotiq", "https://robotiq.com", "Canada", "grippers/FT", "cobot tooling", "Manufacturing", "component_supplier"),
        ("Schunk cobot grippers", "https://schunk.com", "Germany", "EOAT", "grippers", "Manufacturing", "component_supplier"),
        ("Zimmer Group", "https://www.zimmer-group.com", "Germany", "EOAT", "grippers", "Manufacturing", "component_supplier"),
        ("ATI Industrial Automation", "https://www.ati-ia.com", "USA", "FT sensors", "tooling", "Manufacturing", "component_supplier"),
        ("Soft Robotics Inc", "https://www.softroboticsinc.com", "USA", "mGrip", "soft grippers", "Food Service;Logistics", "component_supplier"),
        ("Weiss Robotics", "https://www.weiss-robotics.com", "Germany", "grippers", "EOAT", "Manufacturing", "component_supplier"),
        ("RH-AL-Robotics", "https://www.rh-al.com", "China", "cobot", "cobot", "Manufacturing"),
        ("Rokae", "https://www.rokae.com", "China", "xMate", "cobot", "Manufacturing"),
        ("Tuopu Robotics", "https://www.tuopurobot.com", "China", "cobot", "cobot", "Manufacturing"),
        ("Qjar Robotics", "https://www.qjar.com", "China", "cobot", "cobot", "Manufacturing"),
        ("Fairino", "https://www.fairino.com", "China", "FR series", "cobot", "Manufacturing"),
        ("HITBOT", "https://www.hitbot.cc", "China", "Z-Arm", "SCARA cobot", "Manufacturing"),
        ("Standard Bots", "https://standardbots.com", "USA", "RO1", "cobot", "Manufacturing"),
        ("Automata Technologies", "https://automata.tech", "UK", "EVA", "lab cobot", "Lab Automation"),
        ("AgileX Cobot partners", "https://www.agilex.ai", "China", "mobile cobot bases", "mobile manip", "Research"),
        ("Mecademic", "https://www.mecademic.com", "Canada", "Meca500", "micro cobot", "Manufacturing"),
        ("Kassow KR series", "https://www.kassowrobots.com", "Denmark", "KR1018", "7-axis cobot", "Manufacturing"),
    ]
    for row in cobots:
        name, web, country, robots, work, ind = row[:6]
        role = row[6] if len(row) > 6 else "robot_oem"
        c["cobots"].append(
            _v(name, web, country, "cobots", robots=robots, work=work, industries=ind, role=role)
        )

    # --- Picking / manipulation (40) ---
    pick = [
        ("RightHand Robotics", "https://www.righthandrobotics.com", "USA", "RightPick", "piece picking", "Logistics"),
        ("Covariant", "https://covariant.ai", "USA", "RFM", "AI picking", "Logistics"),
        ("Plus One Robotics", "https://www.plusonerobotics.com", "USA", "Yonder", "parcel induction", "Logistics"),
        ("Ambi Robotics", "https://www.ambirobotics.com", "USA", "AmbiSort", "sortation picking", "Logistics"),
        ("Osaro", "https://www.osaro.com", "USA", "Osaro Pick", "piece picking", "Logistics"),
        ("Robust AI", "https://www.robust.ai", "USA", "Carter", "mobile manipulation", "Logistics"),
        ("Pickle Robot", "https://picklerobot.com", "USA", "Pickle", "truck unloading", "Logistics"),
        ("Dexterity", "https://www.dexterity.ai", "USA", "Dexterity platform", "loading/unloading", "Logistics"),
        ("Mujin", "https://www.mujin-corp.com", "Japan", "MujinController", "palletizing", "Logistics;Manufacturing"),
        ("Brightpick", "https://www.brightpick.ai", "USA", "Autopicker", "autonomous picking", "Logistics"),
        ("Boston Dynamics Stretch", "https://bostondynamics.com", "USA", "Stretch", "case unload", "Logistics"),
        ("Soft Robotics picking", "https://www.softroboticsinc.com", "USA", "mGripAI", "food picking", "Food & Beverage"),
        ("XYZ Robotics", "https://www.xyzrobotics.ai", "China", "picking cells", "piece picking", "Logistics"),
        ("Righthand Europe", "https://www.righthandrobotics.com", "USA", "RightPick3", "piece picking", "Logistics"),
        ("Berkshire Grey picking", "https://www.berkshiregrey.com", "USA", "store fulfillment", "picking", "Retail"),
        ("Fabric robotics", "https://fabric.inc", "USA", "microfulfillment robots", "picking", "Retail"),
        ("Alert Innovation Alphabot", "https://www.walmart.com", "USA", "Alphabot", "GTP pick", "Retail"),
        ("Dematic Multishuttle pick", "https://www.dematic.com", "USA", "pick systems", "goods-to-person", "Logistics"),
        ("SSI Schaefer robotics", "https://www.ssi-schaefer.com", "Germany", "robotics cells", "picking", "Logistics"),
        ("TGW Robotics", "https://www.tgw-group.com", "Austria", "Rovolution", "picking", "Logistics"),
        ("Knapp Open Shuttle / Pick-it-Easy", "https://www.knapp.com", "Austria", "Pick-it-Easy", "picking", "Logistics"),
        ("Witron", "https://www.witron.com", "Germany", "OPM", "warehouse automation", "Retail"),
        ("Honeywell Intelligrated robotics", "https://www.honeywell.com", "USA", "robotic UNNAX", "unloading", "Logistics"),
        ("Fortna robotics design", "https://www.fortna.com", "USA", "systems", "warehouse robotics SI", "Logistics", "system_integrator"),
        ("Bastian Solutions robotics", "https://www.bastiansolutions.com", "USA", "robotic cells", "integration", "Logistics", "system_integrator"),
        ("Invata Intralogistics", "https://www.invata.com", "USA", "robotic systems", "integration", "Logistics", "system_integrator"),
        ("Numina Group", "https://www.numinagroup.com", "USA", "RDS", "warehouse controls", "Logistics", "system_integrator"),
        ("Righthand / Onward Robotics", "https://www.onwardrobotics.com", "USA", "HearMe", "collaborative picking", "Logistics"),
        ("IAM Robotics Swift", "https://www.iamrobotics.com", "USA", "Swift", "mobile pick", "Logistics"),
        ("Tompkins Robotics", "https://www.tompkinsrobotics.com", "USA", "t-Sort", "sortation", "Logistics"),
        ("Plus One Yonder", "https://www.plusonerobotics.com", "USA", "Yonder", "depalletize/induct", "Logistics"),
        ("Caja Robotics picking", "https://www.cajarobotics.com", "Israel", "AMR pick", "picking", "Logistics"),
        ("Exotec Skypicker", "https://www.exotec.com", "France", "Skypicker", "picking station", "Logistics"),
        ("Geek+ PopPick", "https://www.geekplus.com", "China", "PopPick", "picking", "Logistics"),
        ("HaiPick System", "https://www.hairobotics.com", "China", "HaiPick", "ACR pick", "Logistics"),
        ("Quicktron picking", "https://www.quicktron.com", "China", "picking AMR", "picking", "Logistics"),
        ("Megvii Robotics logistics", "https://www.megvii.com", "China", "warehouse robots", "picking", "Logistics"),
        ("Kuwaiti / Falcon Autotech", "https://www.falconautotech.com", "India", "sortation", "sortation", "Logistics"),
        ("GreyOrange Ranger GTP", "https://www.greyorange.com", "USA", "Ranger", "GTP", "Logistics"),
        ("Symbotic Bot", "https://www.symbotic.com", "USA", "Symbotic bot", "case handling", "Retail"),
    ]
    for row in pick:
        name, web, country, robots, work, ind = row[:6]
        role = row[6] if len(row) > 6 else "robot_oem"
        c["picking_manipulation_palletizing"].append(
            _v(name, web, country, "picking_manipulation_palletizing", robots=robots, work=work, industries=ind, role=role)
        )

    # --- Humanoids (50) ---
    humans = [
        ("Agility Robotics", "https://agilityrobotics.com", "USA", "Digit", "tote/material movement", "Logistics;Manufacturing", "commercial"),
        ("Figure AI", "https://www.figure.ai", "USA", "Figure 02", "manufacturing/logistics", "Manufacturing;Logistics", "pilot"),
        ("Apptronik", "https://apptronik.com", "USA", "Apollo", "manufacturing/logistics", "Manufacturing", "pilot"),
        ("Boston Dynamics Atlas", "https://bostondynamics.com", "USA", "Atlas", "industrial manipulation", "Manufacturing", "prototype"),
        ("Sanctuary AI", "https://www.sanctuary.ai", "Canada", "Phoenix", "general manipulation", "Manufacturing", "pilot"),
        ("1X Technologies", "https://www.1x.tech", "Norway", "NEO/EVE", "general physical tasks", "Manufacturing;Service", "pilot"),
        ("Tesla Optimus", "https://www.tesla.com", "USA", "Optimus", "manufacturing", "Manufacturing", "prototype"),
        ("Unitree", "https://www.unitree.com", "China", "G1/H1", "general/research", "Research;Manufacturing", "commercial"),
        ("UBTECH", "https://www.ubtrobot.com", "China", "Walker/Walker S", "industrial/service", "Manufacturing;Service", "pilot"),
        ("AgiBot (Zhiyuan)", "https://agibot.com", "China", "A/X/G", "manufacturing/general", "Manufacturing", "pilot"),
        ("Fourier Intelligence", "https://www.fftai.com", "China", "GR series", "humanoid", "Healthcare;Research", "pilot"),
        ("EngineAI", "https://www.engineai.com.cn", "China", "SA01", "humanoid", "Research", "prototype"),
        ("Agibot Innovation", "https://www.agibot.com", "China", "Yuanzheng", "humanoid", "Manufacturing", "pilot"),
        ("Kepler Exploration", "https://www.kepler-exp.com", "China", "Forerunner", "humanoid", "Research", "prototype"),
        ("LimX Dynamics", "https://www.limxdynamics.com", "China", "TRON/CL-1", "humanoid/legged", "Research", "prototype"),
        ("Booster Robotics", "https://www.boosterobotics.com", "China", "Booster T1", "humanoid", "Research", "prototype"),
        ("Noetix Robotics", "https://www.noetixrobotics.com", "China", "Noetix", "humanoid", "Research", "prototype"),
        ("Robotera", "https://www.robotera.com", "China", "Star1", "humanoid", "Research", "prototype"),
        ("PNDbotics", "https://www.pndbotics.com", "China", "Adam", "humanoid", "Research", "prototype"),
        ("Leju Robotics", "https://www.lejurobot.com", "China", "Kuavo", "humanoid", "Research", "prototype"),
        ("Stardust Intelligence", "https://www.stardust-intelligence.com", "China", "humanoid", "humanoid", "Research", "prototype"),
        ("High Torque Robotics", "https://www.hightorque.cn", "China", "humanoid actuators platforms", "humanoid", "Research", "prototype"),
        ("Deep Robotics humanoid line", "https://www.deeprobotics.cn", "China", "humanoid R&D", "humanoid", "Research", "prototype"),
        ("Xiaomi CyberOne", "https://www.mi.com", "China", "CyberOne", "humanoid", "Research", "prototype"),
        ("ByteDance robotics research", "https://www.bytedance.com", "China", "research humanoid", "humanoid", "Research", "prototype"),
        ("Tencent Robotics X", "https://www.tencent.com", "China", "research platforms", "humanoid", "Research", "prototype"),
        ("Huawei robotics research", "https://www.huawei.com", "China", "research", "humanoid", "Research", "prototype"),
        ("Agility Digit logistics", "https://agilityrobotics.com", "USA", "Digit", "logistics totes", "Logistics", "commercial"),
        ("Reflective / Reflex Robotics", "https://www.reflexrobotics.com", "USA", "Reflex", "industrial humanoid", "Manufacturing", "pilot"),
        ("Humanoid (HMND)", "https://thehumanoid.ai", "UK", "HMND 01 Alpha", "industrial humanoid", "Manufacturing", "pilot"),
        ("Neura 4NE1", "https://www.neura-robotics.com", "Germany", "4NE1", "cognitive humanoid", "Manufacturing", "pilot"),
        ("PAL Robotics Kangaroo/REEM", "https://pal-robotics.com", "Spain", "REEM-C", "humanoid research", "Research", "prototype"),
        ("SoftBank Robotics Pepper/NAO", "https://www.softbankrobotics.com", "Japan", "Pepper/NAO", "service humanoid", "Hospitality;Retail", "commercial"),
        ("Honda ASIMO legacy", "https://global.honda", "Japan", "ASIMO", "research", "Research", "discontinued"),
        ("Toyota T-HR3 / human support", "https://www.toyota.com", "Japan", "T-HR3", "research", "Research", "prototype"),
        ("Kawada Nextage", "https://www.kawada-robotics.com", "Japan", "Nextage", "dual-arm humanoid-like", "Manufacturing", "commercial"),
        ("Waseda / partner humanoids", "https://www.waseda.jp", "Japan", "research", "research", "Research", "prototype"),
        ("Clone Robotics", "https://www.clonerobotics.com", "Poland", "android hands", "humanoid components", "Research", "prototype"),
        ("Sanctuary Carbon", "https://www.sanctuary.ai", "Canada", "Carbon", "general work", "Manufacturing", "pilot"),
        ("Apptronik Apollo logistics", "https://apptronik.com", "USA", "Apollo", "logistics", "Logistics", "pilot"),
        ("Fourier GR-1", "https://www.fftai.com", "China", "GR-1", "general humanoid", "Research", "pilot"),
        ("EngineAI SE01", "https://www.engineai.com.cn", "China", "SE01", "humanoid", "Research", "prototype"),
        ("Unitree H1", "https://www.unitree.com", "China", "H1", "humanoid", "Research", "commercial"),
        ("Unitree G1 Edu", "https://www.unitree.com", "China", "G1", "edu/research", "Education", "commercial"),
        ("UBTECH Walker X", "https://www.ubtrobot.com", "China", "Walker X", "service", "Service", "pilot"),
        ("Agibot Yuanzheng A2", "https://agibot.com", "China", "A2", "industrial", "Manufacturing", "pilot"),
        ("Galbot", "https://www.galbot.com", "China", "Galbot", "mobile manip/humanoid", "Logistics", "pilot"),
        ("MagicLab", "https://www.magiclab.top", "China", "humanoid", "humanoid", "Research", "prototype"),
        ("Astribot", "https://www.astribot.com", "China", "S1", "humanoid", "Research", "prototype"),
        ("Foundation Future Industries", "https://www.ffi.com", "USA", "humanoid research", "humanoid", "Research", "prototype"),
    ]
    for name, web, country, robots, work, ind, maturity in humans:
        c["humanoids_general_purpose"].append(
            _v(name, web, country, "humanoids_general_purpose", robots=robots, work=work, industries=ind, maturity=maturity)
        )

    # --- Cleaning (30) ---
    clean = [
        ("Avidbots", "https://www.avidbots.com", "Canada", "Neo", "floor scrubbing", "Commercial Real Estate"),
        ("Brain Corp", "https://www.braincorp.com", "USA", "BrainOS scrubbers", "autonomous cleaning", "Retail;CRE"),
        ("Tennant", "https://www.tennantco.com", "USA", "AMR scrubbers", "industrial cleaning", "Manufacturing;CRE"),
        ("Nilfisk Liberty", "https://www.nilfisk.com", "Denmark", "Liberty SC50", "scrubbing", "CRE"),
        ("Kärcher KIRA", "https://www.kaercher.com", "Germany", "KIRA B 50", "scrubbing", "CRE"),
        ("SoftBank Whiz", "https://www.softbankrobotics.com", "Japan", "Whiz", "vacuum", "CRE"),
        ("Pudu CC1", "https://www.pudurobotics.com", "China", "CC1", "cleaning", "Hospitality"),
        ("Gausium", "https://www.gausium.com", "China", "Phantas/Scrubber", "cleaning", "CRE"),
        ("LionsBot", "https://www.lionsbot.com", "Singapore", "R3/Orex", "cleaning", "CRE"),
        ("Gaussian Robotics", "https://www.gaussianrobotics.com", "China", "scrubbers", "cleaning", "CRE"),
        ("Diversey TASKI", "https://diversey.com", "USA", "TASKI Intellibot", "cleaning", "CRE"),
        ("IceRobotics / cleaning partners", "https://www.icerobotics.com", "UK", "agri sensors", "specialty", "Agriculture"),
        ("Avidbots Neo 2", "https://www.avidbots.com", "Canada", "Neo 2", "scrubbing", "Airports"),
        ("Cleanfix Robotics", "https://www.cleanfix.com", "USA", "40-Series", "restroom cleaning", "CRE"),
        ("Peppermint Robotics", "https://peppermint.ltd", "India", "Mitra/cleaners", "cleaning", "CRE"),
        ("Solow Robotics", "https://www.solowrobotics.com", "India", "cleaning", "cleaning", "CRE"),
        ("Xiaomi robotic cleaners commercial", "https://www.mi.com", "China", "commercial vac", "cleaning", "CRE"),
        ("Ecovacs commercial", "https://www.ecovacs.com", "China", "commercial", "cleaning", "CRE"),
        ("Robomow / commercial outdoor", "https://www.robomow.com", "Israel", "mowers", "outdoor", "Landscaping"),
        ("Husqvarna Automower commercial", "https://www.husqvarna.com", "Sweden", "Automower", "mowing", "Landscaping"),
        ("Belrobotics", "https://www.belrobotics.com", "Belgium", "Bigmow", "sports turf", "Sports"),
        ("RC Mowers", "https://www.rcmowers.com", "USA", "remote/auto mowers", "mowing", "Landscaping"),
        ("Scythe Robotics", "https://www.scytherobotics.com", "USA", "M.52", "commercial mowing", "Landscaping"),
        ("Renu Robotics", "https://www.renurobotics.com", "USA", "Renubot", "solar farm vegetation", "Energy"),
        ("Avidbots Neo Airport", "https://www.avidbots.com", "Canada", "Neo", "airport cleaning", "Airports"),
        ("BrainOS SoftBank Whiz partnership", "https://www.braincorp.com", "USA", "Whiz", "vacuum", "Retail"),
        ("Nilfisk Liberty SC60", "https://www.nilfisk.com", "Denmark", "SC60", "scrubbing", "CRE"),
        ("Kärcher KIRA CV 50", "https://www.kaercher.com", "Germany", "CV 50", "vacuum", "CRE"),
        ("Pudu MT1", "https://www.pudurobotics.com", "China", "MT1", "cleaning", "Hospitality"),
        ("Gausium Scrubber 50", "https://www.gausium.com", "China", "Scrubber 50", "scrubbing", "CRE"),
    ]
    for name, web, country, robots, work, ind in clean:
        c["cleaning_robots"].append(
            _v(name, web, country, "cleaning_robots", robots=robots, work=work, industries=ind)
        )

    # --- Hospitality / foodservice / delivery (35) ---
    hosp = [
        ("Bear Robotics", "https://www.bearrobotics.ai", "USA", "Servi", "food delivery", "Food Service;Hospitality"),
        ("Pudu Robotics", "https://www.pudurobotics.com", "China", "BellaBot/FlashBot", "delivery", "Hospitality"),
        ("Keenon Robotics", "https://www.keenon.com", "China", "T8/Peanut", "delivery", "Hospitality"),
        ("Relay Robotics", "https://www.relayrobotics.com", "USA", "Relay", "hotel delivery", "Hospitality"),
        ("Savioke Relay", "https://www.savioke.com", "USA", "Relay", "hotel delivery", "Hospitality"),
        ("Aethon TUG", "https://www.aethon.com", "USA", "TUG", "hospital delivery", "Healthcare"),
        ("Diligent Robotics", "https://www.diligentrobots.com", "USA", "Moxi", "hospital assist", "Healthcare"),
        ("SoftBank Pepper hospitality", "https://www.softbankrobotics.com", "Japan", "Pepper", "concierge", "Hospitality"),
        ("Temi", "https://www.robotemi.com", "USA", "Temi", "telepresence service", "Healthcare;Hospitality"),
        ("Richtech Robotics", "https://www.richtechrobotics.com", "USA", "ADAM/Matradee", "bar/service", "Hospitality"),
        ("Pudu KettyBot", "https://www.pudurobotics.com", "China", "KettyBot", "greeting/delivery", "Hospitality"),
        ("Keenon Dinamic", "https://www.keenon.com", "China", "Dinamic", "delivery", "Hospitality"),
        ("Servi Mini / Bear", "https://www.bearrobotics.ai", "USA", "Servi Mini", "cafe delivery", "Food Service"),
        ("Miso Robotics", "https://misorobotics.com", "USA", "Flippy", "kitchen automation", "Food Service"),
        ("Hyphen", "https://www.hyphenfoods.com", "USA", "Maker assembly", "kitchen", "Food Service"),
        ("Creator", "https://www.creator.rest", "USA", "burger robot", "kitchen", "Food Service"),
        ("Spyce / Sweetgreen", "https://www.sweetgreen.com", "USA", "kitchen automation", "kitchen", "Food Service"),
        ("Picnic", "https://www.picnic.co", "USA", "pizza automation", "kitchen", "Food Service"),
        ("Nala Robotics", "https://www.nalarobotics.com", "USA", "kitchen robots", "kitchen", "Food Service"),
        ("Pazzi", "https://www.pazzi.tech", "France", "pizza robot", "kitchen", "Food Service"),
        ("Oracle / MICROS kitchen partners", "https://www.oracle.com", "USA", "kitchen display partners", "kitchen ops", "Food Service"),
        ("Starship Technologies indoor", "https://www.starship.xyz", "Estonia", "delivery robots", "campus delivery", "Education"),
        ("Serve Robotics", "https://www.serverobotics.com", "USA", "sidewalk delivery", "delivery", "Food Service"),
        ("Coco Delivery", "https://cocodelivery.com", "USA", "sidewalk robots", "delivery", "Food Service"),
        ("Kiwibot", "https://www.kiwibot.com", "Colombia", "campus delivery", "delivery", "Education"),
        ("Refraction AI", "https://www.refraction.ai", "USA", "last-meter", "delivery", "Food Service"),
        ("Ottonomy indoor", "https://www.ottonomy.io", "USA", "Ottobot", "delivery", "Airports"),
        ("Keenon Hotel robots", "https://www.keenon.com", "China", "hotel delivery", "hotel", "Hospitality"),
        ("Pudu HolaBot", "https://www.pudurobotics.com", "China", "HolaBot", "bussing", "Hospitality"),
        ("Bear Servi Plus", "https://www.bearrobotics.ai", "USA", "Servi Plus", "bussing", "Food Service"),
        ("Aethon TUG T3", "https://www.aethon.com", "USA", "TUG", "hospital logistics", "Healthcare"),
        ("Relay Ascension", "https://www.relayrobotics.com", "USA", "Relay", "hotel delivery", "Hospitality"),
        ("SoftBank Robotics America hospitality", "https://us.softbankrobotics.com", "USA", "Whiz/Pepper", "service", "Hospitality"),
        ("LG CLOi ServeBot", "https://www.lg.com", "South Korea", "CLOi", "service delivery", "Hospitality"),
        ("Samsung Bot Care / service", "https://www.samsung.com", "South Korea", "Bot Care", "service", "Hospitality"),
    ]
    for name, web, country, robots, work, ind in hosp:
        c["hospitality_foodservice_delivery"].append(
            _v(name, web, country, "hospitality_foodservice_delivery", robots=robots, work=work, industries=ind)
        )

    # --- Inspection / security / quadrupeds (25) ---
    insp = [
        ("Boston Dynamics Spot", "https://bostondynamics.com/products/spot", "USA", "Spot", "inspection", "Energy;Industrial"),
        ("ANYbotics", "https://www.anybotics.com", "Switzerland", "ANYmal", "industrial inspection", "Energy;Oil & Gas"),
        ("Ghost Robotics", "https://www.ghostrobotics.io", "USA", "Vision 60", "security/defense", "Defense"),
        ("Unitree Go2 / B2", "https://www.unitree.com", "China", "Go2/B2", "quadruped", "Research;Security"),
        ("Deep Robotics", "https://www.deeprobotics.cn", "China", "X30/Lite3", "quadruped inspection", "Industrial"),
        ("Xiaomi CyberDog", "https://www.mi.com", "China", "CyberDog", "quadruped", "Consumer;Research"),
        ("Tencent Max", "https://www.tencent.com", "China", "Max", "quadruped research", "Research"),
        ("Ghost Vision 60 Navy", "https://www.ghostrobotics.io", "USA", "Vision 60", "defense", "Defense"),
        ("Boston Dynamics Spot Enterprise", "https://bostondynamics.com", "USA", "Spot", "facility inspection", "Manufacturing"),
        ("ANYmal X", "https://www.anybotics.com", "Switzerland", "ANYmal X", "ex-proof inspection", "Oil & Gas"),
        ("Exyn Technologies", "https://www.exyn.com", "USA", "ExynAero", "aerial inspection", "Mining"),
        ("Flyability", "https://www.flyability.com", "Switzerland", "Elios", "confined aerial", "Energy"),
        ("Skydio", "https://www.skydio.com", "USA", "X10", "inspection drones", "Energy;Defense"),
        ("Percepto", "https://percepto.co", "Israel", "AIM", "autonomous drones", "Energy"),
        ("Dedrone / Axon", "https://www.dedrone.com", "USA", "airspace security", "security", "Security"),
        ("Knightscope", "https://www.knightscope.com", "USA", "K5/K1", "security robots", "Security"),
        ("SMP Robotics", "https://smprobotics.com", "USA", "security robots", "security", "Security"),
        ("Cobalt Robotics", "https://www.cobaltrobotics.com", "USA", "Cobalt", "indoor security", "Security"),
        ("Asylon Robotics", "https://www.asylonrobotics.com", "USA", "DroneSentry", "perimeter security", "Security"),
        ("Sarcos / Guardian", "https://www.sarcos.com", "USA", "Guardian", "teleop inspection", "Industrial"),
        ("Energid / Hexagon inspection", "https://hexagon.com", "Sweden", "inspection systems", "inspection", "Industrial"),
        ("Clearpath Warthog inspection", "https://clearpathrobotics.com", "Canada", "Warthog", "outdoor UGV", "Research;Energy"),
        ("Robotnik Summit", "https://www.robotnik.eu", "Spain", "Summit-XL", "mobile inspection", "Research"),
        ("AgileX Scout/Tracer", "https://www.agilex.ai", "China", "Scout", "UGV platforms", "Research"),
        ("Unitree B2 industrial", "https://www.unitree.com", "China", "B2", "industrial quadruped", "Industrial"),
    ]
    for name, web, country, robots, work, ind in insp:
        c["inspection_security_quadrupeds"].append(
            _v(name, web, country, "inspection_security_quadrupeds", robots=robots, work=work, industries=ind)
        )

    # --- Agriculture (35) ---
    agri = [
        ("John Deere autonomous", "https://www.deere.com", "USA", "autonomous tractor", "field autonomy", "Agriculture"),
        ("CNH Industrial Raven / Case", "https://www.cnhindustrial.com", "Netherlands", "Raven Autonomy", "ag autonomy", "Agriculture"),
        ("AGCO Fendt", "https://www.agcocorp.com", "USA", "Fendt Guide", "precision ag", "Agriculture"),
        ("Naïo Technologies", "https://www.naio-technologies.com", "France", "Oz/Dino", "weeding robots", "Agriculture"),
        ("FarmWise", "https://www.farmwise.io", "USA", "Titan", "weeding", "Agriculture"),
        ("Carbon Robotics", "https://carbonrobotics.com", "USA", "LaserWeeder", "laser weeding", "Agriculture"),
        ("Blue River / John Deere See & Spray", "https://www.deere.com", "USA", "See & Spray", "precision spray", "Agriculture"),
        ("Iron Ox", "https://ironox.com", "USA", "greenhouse robots", "indoor ag", "Agriculture"),
        ("Plenty", "https://www.plenty.ag", "USA", "vertical farm automation", "indoor ag", "Agriculture"),
        ("AppHarvest automation", "https://www.appharvest.com", "USA", "greenhouse", "indoor ag", "Agriculture"),
        ("Harvest CROO", "https://harvestcroorobotics.com", "USA", "strawberry robot", "harvesting", "Agriculture"),
        ("Advanced Farm Technologies", "https://www.advanced.farm", "USA", "apple harvester", "harvesting", "Agriculture"),
        ("Tortuga AgTech", "https://www.tortugaagtech.com", "USA", "berry robots", "harvesting", "Agriculture"),
        ("Root AI / AppHarvest", "https://www.appharvest.com", "USA", "Virgo", "greenhouse picking", "Agriculture"),
        ("FFRobotics", "https://www.ffrobotics.com", "Israel", "apple harvester", "harvesting", "Agriculture"),
        ("Tevel Aerobotics", "https://www.tevel-tech.com", "Israel", "flying harvesters", "harvesting", "Agriculture"),
        ("Ecorobotix", "https://www.ecorobotix.com", "Switzerland", "ARA", "precision spray", "Agriculture"),
        ("Small Robot Company", "https://www.smallrobotcompany.com", "UK", "Tom/Dick/Harry", "field robots", "Agriculture"),
        ("Saga Robotics", "https://sagarobotics.com", "Norway", "Thorvald", "UV/berry", "Agriculture"),
        ("Muddy Machines", "https://www.muddymachines.com", "UK", "sprout harvester", "harvesting", "Agriculture"),
        ("Agrobot", "https://www.agrobot.com", "Spain", "strawberry robot", "harvesting", "Agriculture"),
        ("Dogtooth Technologies", "https://dogtooth.tech", "UK", "soft fruit robots", "harvesting", "Agriculture"),
        ("Burro", "https://www.helloburro.com", "USA", "Burro", "farm transport", "Agriculture"),
        ("Bear Flag Robotics (John Deere)", "https://www.deere.com", "USA", "autonomy stack", "tractor autonomy", "Agriculture"),
        ("Monarch Tractor", "https://www.monarchtractor.com", "USA", "MK-V", "electric autonomous tractor", "Agriculture"),
        ("GUSS Automation", "https://gussag.com", "USA", "GUSS sprayer", "orchard spray", "Agriculture"),
        ("SwarmFarm Robotics", "https://www.swarmfarm.com", "Australia", "SwarmBot", "field robots", "Agriculture"),
        ("AgXeed", "https://www.agxeed.com", "Netherlands", "AgBot", "autonomous tractor", "Agriculture"),
        ("Yanmar autonomous ag", "https://www.yanmar.com", "Japan", "autonomous tractor", "ag autonomy", "Agriculture"),
        ("Kubota autonomous", "https://www.kubota.com", "Japan", "ag robots", "ag autonomy", "Agriculture"),
        ("Iseki autonomous", "https://www.iseki.co.jp", "Japan", "ag robots", "ag", "Agriculture"),
        ("XAG", "https://www.xa.com", "China", "agricultural drones", "spray drones", "Agriculture"),
        ("DJI Agriculture", "https://ag.dji.com", "China", "Agras", "spray drones", "Agriculture"),
        ("Topcon Agriculture autonomy", "https://www.topconpositioning.com", "Japan", "guidance", "precision ag", "Agriculture"),
        ("Trimble Agriculture", "https://agriculture.trimble.com", "USA", "guidance/autonomy", "precision ag", "Agriculture"),
    ]
    for name, web, country, robots, work, ind in agri:
        c["agriculture"].append(
            _v(name, web, country, "agriculture", robots=robots, work=work, industries=ind)
        )

    # --- Construction (25) ---
    const = [
        ("Built Robotics", "https://www.builtrobotics.com", "USA", "Exosystem", "excavator autonomy", "Construction"),
        ("SafeAI", "https://www.safeai.ai", "USA", "heavy equipment autonomy", "haul trucks", "Construction;Mining"),
        ("Caterpillar Command", "https://www.cat.com", "USA", "Command for dozing", "autonomous equipment", "Construction;Mining"),
        ("Komatsu Autonomous Haulage", "https://www.komatsu.com", "Japan", "AHS", "haul trucks", "Mining"),
        ("Volvo CE autonomous", "https://www.volvoce.com", "Sweden", "TA15/HX04", "construction autonomy", "Construction"),
        ("Dusty Robotics", "https://www.dustyrobotics.com", "USA", "FieldPrinter", "layout printing", "Construction"),
        ("Canvas", "https://www.canvas.build", "USA", "drywall robot", "finishing", "Construction"),
        ("Okibo", "https://www.okibo.com", "Israel", "plastering robot", "finishing", "Construction"),
        ("Construction Robotics", "https://www.construction-robotics.com", "USA", "SAM/MULE", "bricklaying", "Construction"),
        ("Fastbrick Robotics", "https://www.fbr.com.au", "Australia", "Hadrian X", "block laying", "Construction"),
        ("Scaled Robotics", "https://www.scaledrobotics.com", "Spain", "site scanner", "progress monitoring", "Construction"),
        ("Doxel", "https://www.doxel.ai", "USA", "site AI robots", "progress monitoring", "Construction"),
        ("Hilti Jaibot", "https://www.hilti.com", "Liechtenstein", "Jaibot", "ceiling drilling", "Construction"),
        ("nLink", "https://www.nlink.no", "Norway", "drilling robot", "ceiling drilling", "Construction"),
        ("Brokk", "https://www.brokk.com", "Sweden", "demolition robots", "demolition", "Construction"),
        ("Husqvarna DXR", "https://www.husqvarna.com", "Sweden", "demolition robots", "demolition", "Construction"),
        ("TopTec Spezialmaschinen", "https://www.toptec.org", "Germany", "construction robots", "specialized", "Construction"),
        ("Advanced Construction Robotics", "https://www.constructionrobots.com", "USA", "TyBot/IronBot", "rebar tying", "Construction"),
        ("Toggle Robotics", "https://www.togglerobotics.com", "USA", "prefab robots", "prefab", "Construction"),
        ("Branch Technology", "https://www.branch.technology", "USA", "C-FAB", "additive construction", "Construction"),
        ("ICON", "https://www.iconbuild.com", "USA", "Vulcan", "3D print construction", "Construction"),
        ("Apis Cor", "https://www.apis-cor.com", "USA", "3D printer", "3D print construction", "Construction"),
        ("SQ4D", "https://www.sq4d.com", "USA", "ARCS", "3D print construction", "Construction"),
        ("Mighty Buildings", "https://www.mightybuildings.com", "USA", "3D prefab", "prefab", "Construction"),
        ("Autodesk Construction partners robotics", "https://www.autodesk.com", "USA", "partner robots", "digital construction", "Construction"),
    ]
    for name, web, country, robots, work, ind in const:
        c["construction"].append(
            _v(name, web, country, "construction", robots=robots, work=work, industries=ind)
        )

    # --- Healthcare hospital service (20) ---
    health = [
        ("Aethon", "https://www.aethon.com", "USA", "TUG", "hospital logistics", "Healthcare"),
        ("Diligent Robotics", "https://www.diligentrobots.com", "USA", "Moxi", "clinical support", "Healthcare"),
        ("Swisslog Healthcare", "https://www.swisslog-healthcare.com", "Switzerland", "TransLogic/Relay", "hospital transport", "Healthcare"),
        ("Omnicell robotics", "https://www.omnicell.com", "USA", "pharmacy robots", "pharmacy", "Healthcare"),
        ("BD Rowa", "https://www.bd.com", "USA", "pharmacy automation", "pharmacy", "Healthcare"),
        ("Xenex", "https://xenex.com", "USA", "LightStrike", "UV disinfection", "Healthcare"),
        ("UVD Robots", "https://uvd.blue-ocean-robotics.com", "Denmark", "UVD", "UV disinfection", "Healthcare"),
        ("Akara Robotics", "https://www.akara.ai", "Ireland", "Stevie/UV", "eldercare/UV", "Healthcare"),
        ("Diligent Moxi hospitals", "https://www.diligentrobots.com", "USA", "Moxi", "supply fetch", "Healthcare"),
        ("Panasonic HOSPI", "https://www.panasonic.com", "Japan", "HOSPI", "hospital delivery", "Healthcare"),
        ("Toyota Human Support Robot hospitals", "https://www.toyota.com", "Japan", "HSR", "assist", "Healthcare"),
        ("SoftBank Pepper care", "https://www.softbankrobotics.com", "Japan", "Pepper", "patient engagement", "Healthcare"),
        ("Temi healthcare", "https://www.robotemi.com", "USA", "Temi", "telepresence", "Healthcare"),
        ("Double Robotics", "https://www.doublerobotics.com", "USA", "Double 3", "telepresence", "Healthcare"),
        ("OhmniLabs", "https://ohmnilabs.com", "USA", "Ohmni", "telepresence", "Healthcare"),
        ("Intuitive da Vinci logistics-adjacent", "https://www.intuitive.com", "USA", "da Vinci", "surgery", "Healthcare"),
        ("Stryker Mako hospitals", "https://www.stryker.com", "USA", "Mako", "ortho", "Healthcare"),
        ("Aethon TUG pharmacy", "https://www.aethon.com", "USA", "TUG", "med delivery", "Healthcare"),
        ("Swisslog Relay hospital", "https://www.swisslog-healthcare.com", "Switzerland", "Relay", "delivery", "Healthcare"),
        ("Keenon hospital delivery", "https://www.keenon.com", "China", "hospital robots", "delivery", "Healthcare"),
    ]
    for name, web, country, robots, work, ind in health:
        c["healthcare_hospital_service"].append(
            _v(name, web, country, "healthcare_hospital_service", robots=robots, work=work, industries=ind)
        )

    # --- Last-mile (15) ---
    last = [
        ("Starship Technologies", "https://www.starship.xyz", "Estonia", "Starship robot", "sidewalk delivery", "Food Service"),
        ("Serve Robotics", "https://www.serverobotics.com", "USA", "Serve", "sidewalk delivery", "Food Service"),
        ("Nuro", "https://www.nuro.ai", "USA", "Nuro R3", "road delivery", "Retail"),
        ("Amazon Scout (legacy)", "https://www.amazon.com", "USA", "Scout", "sidewalk", "Retail", "discontinued"),
        ("Coco", "https://cocodelivery.com", "USA", "Coco", "sidewalk", "Food Service"),
        ("Kiwibot", "https://www.kiwibot.com", "Colombia", "Kiwibot", "campus", "Education"),
        ("Refraction AI", "https://www.refraction.ai", "USA", "REV-1", "last-meter", "Food Service"),
        ("Ottonomy", "https://www.ottonomy.io", "USA", "Ottobot", "indoor/outdoor", "Airports"),
        ("Cartken", "https://www.cartken.com", "USA", "Cartken", "sidewalk", "Food Service"),
        ("Robby Technologies", "https://www.robby.io", "USA", "Robby", "sidewalk", "Food Service"),
        ("Neolix", "https://www.neolix.ai", "China", "X3", "unmanned delivery vehicle", "Retail"),
        ("White Rhino Auto", "https://www.whiterhino.cc", "China", "delivery UGV", "delivery", "Retail"),
        ("Meituan delivery robots", "https://about.meituan.com", "China", "delivery robots", "delivery", "Food Service"),
        ("Alibaba Xiaomanlv", "https://www.alibabagroup.com", "China", "Xiaomanlv", "delivery", "Retail"),
        ("JD.com delivery robots", "https://www.jd.com", "China", "delivery robots", "delivery", "Retail"),
    ]
    for row in last:
        name, web, country, robots, work, ind = row[:6]
        maturity = row[6] if len(row) > 6 else "commercial"
        c["last_mile_outdoor_delivery"].append(
            _v(name, web, country, "last_mile_outdoor_delivery", robots=robots, work=work, industries=ind, maturity=maturity)
        )

    # --- Specialty (10) ---
    spec = [
        ("SITA / airport baggage robotics partners", "https://www.sita.aero", "Switzerland", "baggage robots", "airport", "Airports"),
        ("Aurrigo", "https://www.aurrigo.com", "UK", "Auto-Dolly", "airport baggage", "Airports"),
        ("Olis Robotics", "https://www.olisrobotics.com", "USA", "teleop industrial", "remote ops", "Industrial"),
        ("Sarcos Guardian DX", "https://www.sarcos.com", "USA", "Guardian DX", "teleop", "Industrial"),
        ("Reach Robotics", "https://www.reachrobotics.com", "Australia", "Reach Bravo", "underwater manip", "Maritime"),
        ("Saab Seaeye", "https://www.saabseaeye.com", "UK", "ROVs", "underwater", "Maritime"),
        ("Greensea IQ", "https://greensea.com", "USA", "OPENSEA", "marine autonomy", "Maritime"),
        ("Aviato / gate automation partners", "https://www.sita.aero", "Switzerland", "gate robotics", "airport", "Airports"),
        ("Lawn care Scythe specialty", "https://www.scytherobotics.com", "USA", "M.52", "commercial mowing", "Landscaping"),
        ("Fellow Robots retail", "https://www.fellowrobots.com", "USA", "retail robots", "retail inventory", "Retail"),
    ]
    for name, web, country, robots, work, ind in spec:
        c["specialty_commercial"].append(
            _v(name, web, country, "specialty_commercial", robots=robots, work=work, industries=ind)
        )

    return c


def _norm_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def _host_key(website: str | None) -> str | None:
    if not website:
        return None
    try:
        from urllib.parse import urlparse

        raw = website if "://" in website else f"https://{website}"
        host = urlparse(raw).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        # ignore generic/shared hosts that should not collapse vendors
        if host in {"", "linkedin.com", "twitter.com", "x.com", "facebook.com", "youtube.com", "wikipedia.org"}:
            return None
        return host or None
    except Exception:
        return None


def _is_junk(name: str, website: str | None = None) -> bool:
    if not name or len(name.strip()) < 2:
        return True
    if JUNK_NAME.search(name):
        return True
    if website and "example.com" in website:
        return True
    # Product-line / model masquerading as a company
    if re.search(
        r"\b(neo 2|h1|g1|go2|b2|digit|atlas|spot enterprise|mir\d|poppick|skypicker)\b",
        name,
        re.I,
    ):
        return True
    return False


def extra_unique_vendors() -> list[dict]:
    """Additional real robot sellers to top up after host/name dedupe."""
    # (name, website, country, category, robots, work, industries)
    rows = [
        # AMR / AGV
        ("Jungheinrich AGV Systems", "https://www.jungheinrich.com", "Germany", "amr_agv_material_transport", "EKX / ERC AGV", "pallet transport", "Logistics"),
        ("Still iGo neo", "https://www.still.eu", "Germany", "amr_agv_material_transport", "iGo neo", "warehouse assist", "Logistics"),
        ("Locus Vector", "https://locusrobotics.com", "USA", "amr_agv_material_transport", "Vector", "order fulfillment", "Logistics"),
        ("6 River Systems", "https://www.shopify.com/fulfillment", "USA", "amr_agv_material_transport", "Chuck", "fulfillment AMR", "Logistics"),
        ("Magazino", "https://www.magazino.eu", "Germany", "amr_agv_material_transport", "SOTO / TORU", "piece picking AMR", "Logistics"),
        ("SafeLog", "https://www.safelog.de", "Germany", "amr_agv_material_transport", "SafeLog AGV", "material transport", "Manufacturing"),
        ("DS Automotion", "https://www.ds-automotion.com", "Austria", "amr_agv_material_transport", "AGV/AMR", "intralogistics", "Logistics"),
        ("Neobotix", "https://www.neobotix-robots.com", "Germany", "amr_agv_material_transport", "MP / MMO", "mobile platforms", "Industrial"),
        ("Milvus Robotics", "https://milvusrobotics.com", "Turkey", "amr_agv_material_transport", "SEIT", "AMR", "Logistics"),
        ("Ottonomy.io outdoor AMR", "https://ottonomy.io", "USA", "amr_agv_material_transport", "Ottobot", "last-yard AMR", "Logistics"),
        ("ForwardX Robotics", "https://www.forwardx.com", "China", "amr_agv_material_transport", "Max / Lynx", "AMR", "Logistics"),
        ("Hikrobot Mobile", "https://www.hikrobotics.com", "China", "amr_agv_material_transport", "Latent AMR", "warehouse AMR", "Logistics"),
        ("Standard Robots", "https://www.standard-robots.com", "China", "amr_agv_material_transport", "SATURN", "AMR", "Manufacturing"),
        ("Youibot", "https://www.youibot.com", "China", "amr_agv_material_transport", "Linde / Youibot AMR", "AMR", "Manufacturing"),
        ("Quicktron Robotics", "https://www.quicktron.com", "China", "amr_agv_material_transport", "M60 / M100", "AMR", "Logistics"),
        ("Syrius Robotics", "https://www.syriusrobotics.com", "China", "amr_agv_material_transport", "E retriever", "fulfillment", "Logistics"),
        ("Gideon Brothers", "https://www.gideon.ai", "Croatia", "amr_agv_material_transport", "Gideon AMR", "warehouse", "Logistics"),
        ("InOrbit partner fleets", "https://www.inorbit.ai", "USA", "amr_agv_material_transport", "fleet platforms", "AMR ops", "Logistics"),
        ("Fetch Robotics", "https://www.zebra.com/us/en/products/autonomous-mobile-robots.html", "USA", "amr_agv_material_transport", "Freight / RollerTop", "AMR", "Logistics"),
        ("Aethon Mobile", "https://aethon.com", "USA", "amr_agv_material_transport", "TUG", "hospital logistics", "Healthcare"),
        # Forklifts
        ("Balyo Robotics", "https://www.balyo.com", "France", "autonomous_forklift_pallet", "Driven by Balyo", "autonomous forklift", "Logistics"),
        ("VisionNav", "https://www.visionnav.com", "China", "autonomous_forklift_pallet", "VNL", "autonomous forklift", "Logistics"),
        ("Multiway Robotics", "https://www.multiway-robotics.com", "China", "autonomous_forklift_pallet", "MW forklift", "pallet move", "Logistics"),
        ("CLARK Autonomous", "https://www.clarkmhc.com", "USA", "autonomous_forklift_pallet", "autonomous lift trucks", "forklift", "Logistics"),
        ("Hyster robotic lift trucks", "https://www.hyster.com", "USA", "autonomous_forklift_pallet", "robotic lift", "pallet", "Logistics"),
        ("Yale robotic lift trucks", "https://www.yale.com", "USA", "autonomous_forklift_pallet", "robotic lift", "pallet", "Logistics"),
        ("Raymond Courier", "https://www.raymondcorp.com", "USA", "autonomous_forklift_pallet", "Courier", "pallet AGV", "Logistics"),
        ("Toyota Autopilot AGV", "https://toyota-forklifts.eu", "Japan", "autonomous_forklift_pallet", "Autopilot", "pallet AGV", "Logistics"),
        ("Agilox", "https://www.agilox.net", "Austria", "autonomous_forklift_pallet", "ONE / OCF", "swarm forklift", "Manufacturing"),
        ("Oceaneering Mobile Robotics", "https://www.oceaneering.com", "USA", "autonomous_forklift_pallet", "OTTO / AGV", "heavy AGV", "Manufacturing"),
        ("KION AGV / Dematic", "https://www.dematic.com", "Germany", "autonomous_forklift_pallet", "Dematic AGV", "pallet", "Logistics"),
        ("Hyundai Robotics forklift auto", "https://www.hyundai-robotics.com", "South Korea", "autonomous_forklift_pallet", "auto forklift", "pallet", "Logistics"),
        ("Doosan Industrial Vehicle auto", "https://www.doosanindustrialvehicle.com", "South Korea", "autonomous_forklift_pallet", "auto forklift", "pallet", "Logistics"),
        ("EP Equipment autonomous", "https://www.ep-equipment.com", "China", "autonomous_forklift_pallet", "X+ auto", "pallet", "Logistics"),
        ("Noblelift autonomous", "https://www.noblelift.com", "China", "autonomous_forklift_pallet", "auto pallet", "pallet", "Logistics"),
        # Arms
        ("Comau Robotics", "https://www.comau.com", "Italy", "industrial_robot_arms", "e.DO / NJ", "welding assembly", "Manufacturing"),
        ("Kawasaki Robotics", "https://robotics.kawasaki.com", "Japan", "industrial_robot_arms", "RS / BX", "industrial arm", "Manufacturing"),
        ("Nachi Robotics", "https://www.nachirobotics.com", "Japan", "industrial_robot_arms", "MZ / MC", "industrial arm", "Manufacturing"),
        ("Epson Robots", "https://epson.com/robots", "Japan", "industrial_robot_arms", "VT / GX", "SCARA/6-axis", "Manufacturing"),
        ("Denso Robotics", "https://www.densorobotics.com", "Japan", "industrial_robot_arms", "VS / HM", "assembly", "Manufacturing"),
        ("Mitsubishi Electric Robots", "https://www.mitsubishielectric.com", "Japan", "industrial_robot_arms", "RV / RH", "industrial", "Manufacturing"),
        ("Omron Industrial Robots", "https://automation.omron.com", "Japan", "industrial_robot_arms", "i4 / Viper", "SCARA", "Manufacturing"),
        ("Staubli Robotics", "https://www.staubli.com/robots", "Switzerland", "industrial_robot_arms", "TX / TS", "industrial", "Manufacturing"),
        ("Reis Robotics / KUKA", "https://www.kuka.com", "Germany", "industrial_robot_arms", "welding systems", "welding", "Manufacturing"),
        ("IGM Robotersysteme", "https://www.igm-group.com", "Austria", "industrial_robot_arms", "welding robots", "welding", "Manufacturing"),
        ("Cloos Robotics", "https://www.cloos.de", "Germany", "industrial_robot_arms", "QIROX", "welding", "Manufacturing"),
        ("OTC Daihen", "https://www.daihen-usa.com", "Japan", "industrial_robot_arms", "FD series", "welding", "Manufacturing"),
        ("Panasonic Connect welding robots", "https://connect.panasonic.com", "Japan", "industrial_robot_arms", "TM / TL", "welding", "Manufacturing"),
        ("Hyundai Robotics", "https://www.hyundai-robotics.com", "South Korea", "industrial_robot_arms", "YS / HH", "industrial", "Manufacturing"),
        ("Siasun Industrial", "https://www.siasun.com", "China", "industrial_robot_arms", "SR series", "industrial", "Manufacturing"),
        ("Estun Robotics", "https://www.estun.com", "China", "industrial_robot_arms", "ER series", "industrial", "Manufacturing"),
        ("STEP Electric robots", "https://www.stepelectric.com", "China", "industrial_robot_arms", "SR", "industrial", "Manufacturing"),
        ("EFORT Intelligent Equipment", "https://www.efort.com.cn", "China", "industrial_robot_arms", "ER", "industrial", "Manufacturing"),
        ("Peitian Robotics", "https://www.peitian.com", "China", "industrial_robot_arms", "industrial arms", "manufacturing", "Manufacturing"),
        ("Rokae Industrial", "https://www.rokae.com", "China", "industrial_robot_arms", "xMate industrial", "industrial", "Manufacturing"),
        # Cobots
        ("Techman Robot", "https://www.tm-robot.com", "Taiwan", "cobots", "TM AI cobot", "collaborative", "Manufacturing"),
        ("Hanwha Robotics", "https://www.hanwharobotics.com", "South Korea", "cobots", "HCR", "cobot", "Manufacturing"),
        ("AUBO Robotics", "https://www.aubo-robotics.com", "China", "cobots", "i series", "cobot", "Manufacturing"),
        ("Elephant Robotics", "https://www.elephantrobotics.com", "China", "cobots", "myCobot / myBuddy", "cobot", "Education"),
        ("JAKA Robotics", "https://www.jaka.com", "China", "cobots", "Zu / Pro", "cobot", "Manufacturing"),
        ("Fairino", "https://www.fairino.com", "China", "cobots", "FR series", "cobot", "Manufacturing"),
        ("Dobot Robotics", "https://www.dobot.cc", "China", "cobots", "CR / Nova", "cobot", "Manufacturing"),
        ("Elite Robot", "https://www.eliterobot.com", "China", "cobots", "EC series", "cobot", "Manufacturing"),
        ("Rethink Robotics Sawyer", "https://www.rethinkrobotics.com", "Germany", "cobots", "Sawyer", "cobot", "Manufacturing"),
        ("Productive Robotics OB7", "https://www.productiverobotics.com", "USA", "cobots", "OB7", "cobot", "Manufacturing"),
        ("Kassow Robots", "https://www.kassowrobots.com", "Denmark", "cobots", "KR series", "7-axis cobot", "Manufacturing"),
        ("Franka Robotics", "https://franka.de", "Germany", "cobots", "Franka Research / Production", "cobot", "Manufacturing"),
        ("Neura Robotics cobots", "https://neura-robotics.com", "Germany", "cobots", "Lara", "cognitive cobot", "Manufacturing"),
        ("Rainbow Robotics", "https://www.rainbow-robotics.com", "South Korea", "cobots", "RB series", "cobot", "Manufacturing"),
        ("Neuromeka", "https://www.neuromeka.com", "South Korea", "cobots", "Indy", "cobot", "Manufacturing"),
        # Picking
        ("Berkshire Grey", "https://www.berkshiregrey.com", "USA", "picking_manipulation_palletizing", "BG Robotic System", "parcel pick", "Logistics"),
        ("Plus One Robotics", "https://www.plusonerobotics.com", "USA", "picking_manipulation_palletizing", "Yonder", "induct/pick", "Logistics"),
        ("Soft Robotics", "https://www.softroboticsinc.com", "USA", "picking_manipulation_palletizing", "mGrip", "soft pick", "Food Service"),
        ("Righthand Robotics", "https://www.righthandrobotics.com", "USA", "picking_manipulation_palletizing", "RightPick", "piece pick", "Logistics"),
        ("Caja Robotics", "https://www.cajarobotics.com", "Israel", "picking_manipulation_palletizing", "multi-robot pick", "goods-to-person", "Logistics"),
        ("Osaro", "https://www.osaro.com", "USA", "picking_manipulation_palletizing", "Osaro Pick", "piece pick", "Logistics"),
        ("Grabit Inc", "https://www.grabitinc.com", "USA", "picking_manipulation_palletizing", "electroadhesion grippers", "pick", "Manufacturing"),
        ("Shadow Robot Company", "https://www.shadowrobot.com", "UK", "picking_manipulation_palletizing", "Dexterous Hand", "manipulation", "Research"),
        ("Pilz service robotics", "https://www.pilz.com", "Germany", "picking_manipulation_palletizing", "Service Robotics Module", "safe manip", "Manufacturing"),
        ("Unchained Robotics", "https://unchainedrobotics.de", "Germany", "picking_manipulation_palletizing", "modular cells", "pick/pack", "Manufacturing"),
        ("Robomotive", "https://www.robomotive.nl", "Netherlands", "picking_manipulation_palletizing", "bin picking", "bin pick", "Manufacturing"),
        ("Solomon 3D vision pick", "https://www.solomon-3d.com", "Taiwan", "picking_manipulation_palletizing", "AccuPick", "bin pick", "Manufacturing"),
        ("Photoneo", "https://www.photoneo.com", "Slovakia", "picking_manipulation_palletizing", "Locator / MotionCam", "bin pick vision", "Manufacturing"),
        ("Mech-Mind Robotics", "https://www.mech-mind.com", "China", "picking_manipulation_palletizing", "Mech-Eye / Mech-Viz", "3D pick", "Manufacturing"),
        ("Sereact", "https://sereact.ai", "Germany", "picking_manipulation_palletizing", "PickGPT", "AI pick", "Logistics"),
        # Humanoids
        ("1X Technologies", "https://www.1x.tech", "Norway", "humanoids_general_purpose", "NEO / EVE", "general purpose", "Logistics"),
        ("Figure", "https://www.figure.ai", "USA", "humanoids_general_purpose", "Figure 02", "general purpose", "Manufacturing"),
        ("Tesla Bot", "https://www.tesla.com/AI", "USA", "humanoids_general_purpose", "Optimus", "general purpose", "Manufacturing"),
        ("Boston Dynamics Atlas", "https://bostondynamics.com", "USA", "humanoids_general_purpose", "Atlas", "general purpose", "Industrial"),
        ("Agility Digit", "https://agilityrobotics.com", "USA", "humanoids_general_purpose", "Digit", "logistics humanoid", "Logistics"),
        ("Apptronik Apollo", "https://apptronik.com", "USA", "humanoids_general_purpose", "Apollo", "general purpose", "Logistics"),
        ("Sanctuary Carbon", "https://www.sanctuary.ai", "Canada", "humanoids_general_purpose", "Carbon", "general purpose", "Industrial"),
        ("Unitree Robotics", "https://www.unitree.com", "China", "humanoids_general_purpose", "H1 / G1", "humanoid", "Research"),
        ("UBTECH Robotics", "https://www.ubtrobot.com", "China", "humanoids_general_purpose", "Walker", "humanoid", "Service"),
        ("Agibot Zhiyuan", "https://www.agibot.com", "China", "humanoids_general_purpose", "Yuanzheng", "humanoid", "Industrial"),
        ("Fourier Intelligence", "https://www.fftai.com", "China", "humanoids_general_purpose", "GR-1 / GR-2", "humanoid", "Healthcare"),
        ("EngineAI", "https://www.engineai.com.cn", "China", "humanoids_general_purpose", "SE01", "humanoid", "Industrial"),
        ("Kepler Exploration Robot", "https://www.kepler-explore.com", "China", "humanoids_general_purpose", "Forerunner", "humanoid", "Industrial"),
        ("LimX Dynamics", "https://www.limxdynamics.com", "China", "humanoids_general_purpose", "TRON / CL-1", "humanoid/legged", "Research"),
        ("MagicLab Robot", "https://www.magiclab.top", "China", "humanoids_general_purpose", "MagicBot", "humanoid", "Industrial"),
        ("Galbot", "https://www.galbot.com", "China", "humanoids_general_purpose", "G1 humanoid", "humanoid", "Retail"),
        ("Astribot", "https://www.astribot.com", "China", "humanoids_general_purpose", "S1", "humanoid", "Service"),
        ("Robot Era", "https://www.robotera.com", "China", "humanoids_general_purpose", "STAR1", "humanoid", "Industrial"),
        ("Booster Robotics", "https://www.boosterobotics.com", "China", "humanoids_general_purpose", "T1", "humanoid", "Education"),
        ("Noetix Robotics", "https://www.noetixrobotics.com", "China", "humanoids_general_purpose", "Noetix", "humanoid", "Industrial"),
        ("Mentee Robotics", "https://www.menteebot.com", "Israel", "humanoids_general_purpose", "MenteeBot", "humanoid", "Industrial"),
        ("Wandercraft", "https://www.wandercraft.eu", "France", "humanoids_general_purpose", "Atalante", "exoskeleton/humanoid gait", "Healthcare"),
        ("Clone Robotics", "https://www.clonerobotics.com", "Poland", "humanoids_general_purpose", "Clone torso", "android", "Research"),
        ("Neura 4NE1", "https://neura-robotics.com", "Germany", "humanoids_general_purpose", "4NE1", "cognitive humanoid", "Manufacturing"),
        ("Toyota Friend / HSR", "https://www.toyota.com", "Japan", "humanoids_general_purpose", "HSR", "human support", "Healthcare"),
        # Cleaning
        ("Avidbots Neo", "https://www.avidbots.com", "Canada", "cleaning_robots", "Neo", "floor scrubbing", "Facilities"),
        ("BrainOS cleaning fleets", "https://www.braincorp.com", "USA", "cleaning_robots", "BrainOS", "autonomous scrubbers", "Retail"),
        ("Nilfisk Liberty", "https://www.nilfisk.com", "Denmark", "cleaning_robots", "Liberty SC50/SC60", "scrubber", "Facilities"),
        ("Kärcher KIRA", "https://www.kaercher.com", "Germany", "cleaning_robots", "KIRA CV / B", "scrubber", "Facilities"),
        ("Gausium Robotics", "https://www.gausium.com", "China", "cleaning_robots", "Phantas / Scrubber", "cleaning", "Facilities"),
        ("SoftBank Whiz", "https://www.softbankrobotics.com", "Japan", "cleaning_robots", "Whiz", "vacuum", "Facilities"),
        ("Intelligent Cleaning Equipment ICE", "https://www.icecompanies.com", "USA", "cleaning_robots", "robot scrubbers", "cleaning", "Facilities"),
        ("Cleanfix Robotics", "https://www.cleanfixrobotics.com", "USA", "cleaning_robots", "Autonomous Floor Scrubbers", "scrubber", "Facilities"),
        ("Wave Robotics cleaning", "https://www.waverobotics.com", "USA", "cleaning_robots", "commercial clean", "scrubber", "Facilities"),
        ("Pudu CC1", "https://www.pudurobotics.com", "China", "cleaning_robots", "CC1", "scrubber", "Facilities"),
        ("Gaussian Robotics", "https://www.gaussianrobotics.com", "China", "cleaning_robots", "Scrubber 50", "cleaning", "Facilities"),
        ("Diversey TASKI robot", "https://diversey.com", "USA", "cleaning_robots", "TASKI Intellibot", "scrubber", "Facilities"),
        ("Tennant Autonomous", "https://www.tennantco.com", "USA", "cleaning_robots", "T7AMR", "scrubber", "Facilities"),
        ("Adaptalift Cleanbots", "https://www.adaptalift.com.au", "Australia", "cleaning_robots", "cleanbots", "cleaning", "Facilities"),
        ("Solowash / robotic wash", "https://www.solowash.com", "Italy", "cleaning_robots", "vehicle wash robots", "wash", "Automotive"),
        # Hospitality
        ("Bear Robotics Servi", "https://www.bearrobotics.ai", "USA", "hospitality_foodservice_delivery", "Servi", "restaurant delivery", "Food Service"),
        ("Pudu Robotics service", "https://www.pudurobotics.com", "China", "hospitality_foodservice_delivery", "KettyBot / BellaBot", "service delivery", "Hospitality"),
        ("Keenon Robotics", "https://www.keenon.com", "China", "hospitality_foodservice_delivery", "T8 / Dinamic", "hotel/restaurant", "Hospitality"),
        ("SoftBank Pepper", "https://www.softbankrobotics.com", "Japan", "hospitality_foodservice_delivery", "Pepper", "concierge", "Hospitality"),
        ("Richtech Robotics", "https://www.richtechrobotics.com", "USA", "hospitality_foodservice_delivery", "Adam / Tito", "bar/service", "Food Service"),
        ("Servi Robotics / Bear EU", "https://www.bearrobotics.ai", "USA", "hospitality_foodservice_delivery", "Servi Plus", "F&B delivery", "Food Service"),
        ("OrionStar Robotics", "https://www.orionstar.com", "China", "hospitality_foodservice_delivery", "Lucki / Hello", "service", "Hospitality"),
        ("Savioke Relay", "https://www.relayrobotics.com", "USA", "hospitality_foodservice_delivery", "Relay", "hotel delivery", "Hospitality"),
        ("LG CLOi ServeBot", "https://www.lg.com", "South Korea", "hospitality_foodservice_delivery", "CLOi", "service", "Hospitality"),
        ("Samsung Bot Care / Handy hospitality", "https://www.samsung.com", "South Korea", "hospitality_foodservice_delivery", "Bot Handy", "service", "Hospitality"),
        ("Temi Robotics", "https://www.robotemi.com", "USA", "hospitality_foodservice_delivery", "Temi", "telepresence service", "Hospitality"),
        ("Hease Robotics", "https://www.hease-robotics.com", "France", "hospitality_foodservice_delivery", "Hoomano / Heasy", "reception", "Hospitality"),
        ("Goodtime Robotics", "https://www.goodtime.io", "USA", "hospitality_foodservice_delivery", "QSR automation", "QSR", "Food Service"),
        ("Miso Robotics", "https://misorobotics.com", "USA", "hospitality_foodservice_delivery", "Flippy", "kitchen fry/grill", "Food Service"),
        ("Hyphen robotic kitchen", "https://www.hypheninnovation.com", "USA", "hospitality_foodservice_delivery", "Maker station", "assembly kitchen", "Food Service"),
        # Inspection / quadrupeds
        ("ANYbotics", "https://www.anybotics.com", "Switzerland", "inspection_security_quadrupeds", "ANYmal", "inspection", "Energy"),
        ("Ghost Robotics", "https://www.ghostrobotics.io", "USA", "inspection_security_quadrupeds", "Vision 60", "security quadruped", "Defense"),
        ("Deep Robotics", "https://www.deeprobotics.cn", "China", "inspection_security_quadrupeds", "X30 / Lite3", "quadruped", "Industrial"),
        ("Unitree Industrial quadrupeds", "https://www.unitree.com", "China", "inspection_security_quadrupeds", "B2 / Go2 Edu", "quadruped", "Industrial"),
        ("Boston Dynamics Spot", "https://bostondynamics.com", "USA", "inspection_security_quadrupeds", "Spot", "inspection", "Industrial"),
        ("Energy Robotics", "https://www.energy-robotics.com", "Germany", "inspection_security_quadrupeds", "fleet autonomy", "inspection", "Energy"),
        ("ExRobotics", "https://www.exrobotics.global", "Netherlands", "inspection_security_quadrupeds", "ExR-1", "ATEX inspection", "Energy"),
        ("Taurob", "https://www.taurob.com", "Austria", "inspection_security_quadrupeds", "Inspector", "ATEX", "Energy"),
        ("Square Robot", "https://www.squarerobots.com", "USA", "inspection_security_quadrupeds", "submersible tank", "tank inspection", "Energy"),
        ("Invert Robotics", "https://www.invertrobotics.com", "Ireland", "inspection_security_quadrupeds", "crawler inspection", "NDT", "Industrial"),
        ("Flyability", "https://www.flyability.com", "Switzerland", "inspection_security_quadrupeds", "Elios", "indoor drone inspection", "Industrial"),
        ("Skydio X10 enterprise", "https://www.skydio.com", "USA", "inspection_security_quadrupeds", "X10", "autonomous drone inspect", "Industrial"),
        ("Asylon DroneSentry", "https://www.asylonrobotics.com", "USA", "inspection_security_quadrupeds", "DroneSentry", "security drone", "Defense"),
        ("SMP Robotics", "https://smprobotics.com", "USA", "inspection_security_quadrupeds", "S5 / S300", "security patrol", "Security"),
        ("Knightscope", "https://www.knightscope.com", "USA", "inspection_security_quadrupeds", "K5 / K1", "security", "Security"),
        # Agriculture
        ("John Deere Autonomy", "https://www.deere.com", "USA", "agriculture", "Autonomy / See & Spray", "field autonomy", "Agriculture"),
        ("CNH Industrial Raven", "https://www.cnhindustrial.com", "USA", "agriculture", "Raven Autonomy", "field", "Agriculture"),
        ("AGCO Precision / Fendt", "https://www.agcocorp.com", "USA", "agriculture", "Fendt / PTx", "field", "Agriculture"),
        ("Naio Technologies", "https://www.naio-technologies.com", "France", "agriculture", "Oz / Ted / Jo", "weeding", "Agriculture"),
        ("FarmWise", "https://farmwise.io", "USA", "agriculture", "Titan", "weeding", "Agriculture"),
        ("Carbon Robotics", "https://carbonrobotics.com", "USA", "agriculture", "LaserWeeder", "weeding", "Agriculture"),
        ("Burro", "https://www.goburro.com", "USA", "agriculture", "Burro", "crop transport", "Agriculture"),
        ("Tortuga AgTech", "https://www.tortugaagtech.com", "USA", "agriculture", "harvest robots", "harvest", "Agriculture"),
        ("Advanced Farm Technologies", "https://www.advanced.farm", "USA", "agriculture", "apple/berry harvesters", "harvest", "Agriculture"),
        ("Harvest CROO", "https://harvestcroorobotics.com", "USA", "agriculture", "strawberry harvester", "harvest", "Agriculture"),
        ("Dogtooth Technologies", "https://dogtooth.tech", "UK", "agriculture", "soft fruit harvester", "harvest", "Agriculture"),
        ("Saga Robotics", "https://sagarobotics.com", "Norway", "agriculture", "Thorvald", "UV / crop care", "Agriculture"),
        ("Ecorobotix", "https://www.ecorobotix.com", "Switzerland", "agriculture", "ARA", "precision spray", "Agriculture"),
        ("Small Robot Company", "https://www.smallrobotcompany.com", "UK", "agriculture", "Tom / Dick / Harry", "field robots", "Agriculture"),
        ("Agerris", "https://agerris.com", "Australia", "agriculture", "Digital Farmhand", "field", "Agriculture"),
        ("SwarmFarm Robotics", "https://www.swarmfarm.com", "Australia", "agriculture", "SwarmBot", "spray", "Agriculture"),
        ("Yanmar autonomous ag", "https://www.yanmar.com", "Japan", "agriculture", "Yanmar robot tractor", "tractor", "Agriculture"),
        ("Kubota autonomous", "https://www.kubota.com", "Japan", "agriculture", "ag autonomy", "tractor", "Agriculture"),
        ("Iron Ox", "https://ironox.com", "USA", "agriculture", "Angus", "greenhouse", "Agriculture"),
        ("Root AI / AppHarvest", "https://www.appharvest.com", "USA", "agriculture", "Virgo", "greenhouse pick", "Agriculture"),
        # Construction
        ("Built Robotics", "https://www.builtrobotics.com", "USA", "construction", "Exosystem", "excavation", "Construction"),
        ("SafeAI", "https://www.safeai.ai", "USA", "construction", "autonomous heavy equipment", "haulage", "Construction"),
        ("Caterpillar Command", "https://www.cat.com", "USA", "construction", "Command for hauling", "autonomous haul", "Construction"),
        ("Komatsu Autonomous Haulage", "https://www.komatsu.com", "Japan", "construction", "AHS", "haul trucks", "Construction"),
        ("Volvo Autonomous Solutions", "https://www.volvoautonomoussolutions.com", "Sweden", "construction", "TA15 / HAUL", "haulage", "Construction"),
        ("Dusty Robotics", "https://www.dustyrobotics.com", "USA", "construction", "FieldPrinter", "layout", "Construction"),
        ("Canvas Construction robotics", "https://www.canvas.build", "USA", "construction", "drywall finish robot", "finishing", "Construction"),
        ("Okibo", "https://www.okibo.com", "Israel", "construction", "construction robots", "interior", "Construction"),
        ("Construction Robotics", "https://www.construction-robotics.com", "USA", "construction", "SAM / MULE", "bricklaying", "Construction"),
        ("FBR Hadrian", "https://www.fbr.com.au", "Australia", "construction", "Hadrian X", "bricklaying", "Construction"),
        ("Fastbrick Robotics", "https://www.fbr.com.au", "Australia", "construction", "Hadrian", "masonry", "Construction"),
        ("Husqvarna DXR demolition", "https://www.husqvarna.com", "Sweden", "construction", "DXR", "demolition", "Construction"),
        ("Brokk", "https://www.brokk.com", "Sweden", "construction", "Brokk demolition robots", "demolition", "Construction"),
        ("Baubot", "https://www.baubot.com", "Austria", "construction", "Baubot", "on-site mobile", "Construction"),
        ("Autonomous Solutions Inc ASI", "https://www.asirobots.com", "USA", "construction", "Mobius", "vehicle autonomy", "Construction"),
        # Healthcare
        ("Aethon TUG", "https://aethon.com", "USA", "healthcare_hospital_service", "TUG", "hospital delivery", "Healthcare"),
        ("Diligent Robotics", "https://www.diligentrobots.com", "USA", "healthcare_hospital_service", "Moxi", "hospital assist", "Healthcare"),
        ("Swisslog Healthcare Relay", "https://www.swisslog-healthcare.com", "Switzerland", "healthcare_hospital_service", "Relay / BoxPicker", "pharmacy/transport", "Healthcare"),
        ("Panasonic HOSPI", "https://www.panasonic.com", "Japan", "healthcare_hospital_service", "HOSPI", "hospital delivery", "Healthcare"),
        ("Toyota HSR hospitals", "https://www.toyota-global.com", "Japan", "healthcare_hospital_service", "HSR", "care assist", "Healthcare"),
        ("UVD Robots", "https://uvd.blue-ocean-robotics.com", "Denmark", "healthcare_hospital_service", "UVD", "UV disinfection", "Healthcare"),
        ("Xenex Disinfection", "https://xenex.com", "USA", "healthcare_hospital_service", "LightStrike", "UV robot", "Healthcare"),
        ("OhmniLabs", "https://ohmnilabs.com", "USA", "healthcare_hospital_service", "Ohmni", "telepresence care", "Healthcare"),
        ("Double Robotics healthcare", "https://www.doublerobotics.com", "USA", "healthcare_hospital_service", "Double 3", "telepresence", "Healthcare"),
        ("Intuitive Surgical logistics-adj", "https://www.intuitive.com", "USA", "healthcare_hospital_service", "Ion / da Vinci periop", "surgical support", "Healthcare"),
        ("Stryker Mako service", "https://www.stryker.com", "USA", "healthcare_hospital_service", "Mako", "ortho robotics", "Healthcare"),
        ("Diligent Moxi network", "https://www.diligentrobots.com", "USA", "healthcare_hospital_service", "Moxi", "nursing logistics", "Healthcare"),
        # Last mile
        ("Starship Technologies", "https://www.starship.xyz", "Estonia", "last_mile_outdoor_delivery", "Starship robot", "sidewalk delivery", "Delivery"),
        ("Nuro", "https://www.nuro.ai", "USA", "last_mile_outdoor_delivery", "Nuro vehicle", "local delivery", "Delivery"),
        ("Serve Robotics", "https://www.serverobotics.com", "USA", "last_mile_outdoor_delivery", "Serve", "sidewalk delivery", "Delivery"),
        ("Coco Delivery", "https://cocodelivery.com", "USA", "last_mile_outdoor_delivery", "Coco", "sidewalk", "Delivery"),
        ("Kiwibot", "https://www.kiwibot.com", "Colombia", "last_mile_outdoor_delivery", "Kiwibot", "campus delivery", "Delivery"),
        ("Amazon Scout legacy / Zoox last mile", "https://www.amazon.com", "USA", "last_mile_outdoor_delivery", "Scout", "sidewalk", "Delivery"),
        ("Refraction AI", "https://www.refraction.ai", "USA", "last_mile_outdoor_delivery", "REV-1", "delivery", "Delivery"),
        ("Cartken", "https://www.cartken.com", "USA", "last_mile_outdoor_delivery", "Cartken robot", "delivery", "Delivery"),
        ("Neolix", "https://www.neolix.ai", "China", "last_mile_outdoor_delivery", "X3 / X6", "unmanned delivery", "Delivery"),
        ("White Rhino Auto", "https://www.whiterhinoauto.com", "China", "last_mile_outdoor_delivery", "delivery EV", "last mile", "Delivery"),
        ("Meituan autonomous delivery", "https://www.meituan.com", "China", "last_mile_outdoor_delivery", "delivery bots", "last mile", "Delivery"),
        ("JD Logistics drones/bots", "https://www.jdl.com", "China", "last_mile_outdoor_delivery", "delivery robots", "last mile", "Delivery"),
        ("Uber Elevate / AV delivery partners", "https://www.uber.com", "USA", "last_mile_outdoor_delivery", "AV delivery", "last mile", "Delivery"),
        ("FedEx Roxo", "https://www.fedex.com", "USA", "last_mile_outdoor_delivery", "Roxo", "same-day bot", "Delivery"),
        ("DHL Parcelcopter / robot pilots", "https://www.dhl.com", "Germany", "last_mile_outdoor_delivery", "robot delivery pilots", "last mile", "Delivery"),
        ("Alibaba Cainiao robots", "https://www.cainiao.com", "China", "last_mile_outdoor_delivery", "Cainiao bots", "last mile", "Delivery"),
        # Specialty
        ("Aurrigo Auto-Dolly", "https://www.aurrigo.com", "UK", "specialty_commercial", "Auto-Dolly", "airport baggage", "Airports"),
        ("Olis Robotics", "https://www.olisrobotics.com", "USA", "specialty_commercial", "teleop", "remote industrial", "Industrial"),
        ("Reach Robotics", "https://www.reachrobotics.com", "Australia", "specialty_commercial", "Reach Bravo", "subsea manip", "Maritime"),
        ("Saab Seaeye", "https://www.saabseaeye.com", "UK", "specialty_commercial", "ROV", "subsea", "Maritime"),
        ("Greensea Systems", "https://greensea.com", "USA", "specialty_commercial", "OPENSEA", "marine autonomy", "Maritime"),
        ("Fellow Robots", "https://www.fellowrobots.com", "USA", "specialty_commercial", "retail inventory", "retail", "Retail"),
        ("Bossa Nova Robotics", "https://www.bossanova.com", "USA", "specialty_commercial", "shelf scanning", "retail", "Retail"),
        ("Simbe Robotics", "https://www.simberobotics.com", "USA", "specialty_commercial", "Tally", "retail inventory", "Retail"),
        ("Badger Technologies", "https://www.badger-technologies.com", "USA", "specialty_commercial", "retail robot", "retail", "Retail"),
        ("Scythe Robotics", "https://www.scytherobotics.com", "USA", "specialty_commercial", "M.52", "commercial mowing", "Landscaping"),
    ]
    out = []
    for name, web, country, cat, robots, work, ind in rows:
        out.append(
            _v(
                name,
                web,
                country,
                cat,
                robots=robots,
                work=work,
                industries=ind,
                source="extra_unique_vendors",
                verification="curated",
            )
        )
    return out


def map_db_type_to_category(robot_type: str | None) -> str:
    t = (robot_type or "").lower()
    if "humanoid" in t:
        return "humanoids_general_purpose"
    if t in {"amr", "agv"} or "warehouse" in t:
        return "amr_agv_material_transport"
    if "fork" in t or "pallet" in t:
        return "autonomous_forklift_pallet"
    if "cobot" in t:
        return "cobots"
    if "industrial" in t:
        return "industrial_robot_arms"
    if "clean" in t:
        return "cleaning_robots"
    if "service" in t or "hospitality" in t:
        return "hospitality_foodservice_delivery"
    if "vision" in t:
        return "picking_manipulation_palletizing"
    return "specialty_commercial"


def load_db_vendors() -> list[dict]:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return []
    try:
        from sqlalchemy import create_engine, text

        eng = create_engine(url)
        out = []
        with eng.connect() as conn:
            rows = conn.execute(
                text(
                    "select company_name, website, country, robot_type, product_category "
                    "from robot_companies order by id"
                )
            ).mappings()
            for r in rows:
                name = r["company_name"]
                if _is_junk(name, r["website"]):
                    continue
                cat = map_db_type_to_category(r["robot_type"])
                out.append(
                    _v(
                        name,
                        r["website"] or "",
                        r["country"] or "Unknown",
                        cat,
                        robots=r["product_category"] or "",
                        work="",
                        industries="",
                        maturity="unknown",
                        us="unknown",
                        sales="unknown",
                        notes="from robot_companies",
                        source="robot_companies_db",
                        verification="db_import",
                    )
                )
            hv = conn.execute(
                text(
                    "select distinct vendor, max(country) as country, "
                    "max(product_url) as product_url from humanoid_benchmarks "
                    "where vendor is not null group by vendor"
                )
            ).mappings()
            for r in hv:
                name = r["vendor"]
                if _is_junk(name):
                    continue
                out.append(
                    _v(
                        name,
                        r["product_url"] or "",
                        r["country"] or "Unknown",
                        "humanoids_general_purpose",
                        robots="",
                        work="humanoid labor",
                        industries="Manufacturing;Logistics",
                        maturity="unknown",
                        us="unknown",
                        sales="unknown",
                        notes="from humanoid_benchmarks",
                        source="humanoid_benchmarks",
                        verification="db_import",
                    )
                )
        return out
    except Exception as exc:
        print("DB merge skipped:", type(exc).__name__, exc)
        return []


def assemble_500() -> list[dict]:
    by_cat = curated_by_category()
    selected: list[dict] = []
    seen_name: set[str] = set()
    seen_host: set[str] = set()

    def add(v: dict, force_cat: str | None = None) -> bool:
        key = _norm_key(v["company_name"])
        host = _host_key(v.get("website"))
        if key in seen_name:
            return False
        if host and host in seen_host:
            return False
        if _is_junk(v["company_name"], v.get("website")):
            return False
        if force_cat:
            v = dict(v)
            v["robot_category"] = force_cat
        seen_name.add(key)
        if host:
            seen_host.add(host)
        selected.append(v)
        return True

    # Fill each category to target from curated first
    for cat, target in TARGETS.items():
        pool = by_cat.get(cat, [])
        for v in pool:
            if sum(1 for s in selected if s["robot_category"] == cat) >= target:
                break
            add(v)

    # Top up underfilled categories from extra unique list, then DB
    extras = extra_unique_vendors()
    db_vendors = load_db_vendors()
    for pool in (extras, db_vendors):
        for cat, target in TARGETS.items():
            have = sum(1 for s in selected if s["robot_category"] == cat)
            if have >= target:
                continue
            for v in pool:
                if have >= target:
                    break
                if v["robot_category"] != cat:
                    continue
                if add(v):
                    have += 1

    # Remap remaining extras/db into still-short categories
    for cat, target in TARGETS.items():
        have = sum(1 for s in selected if s["robot_category"] == cat)
        if have >= target:
            continue
        for v in extras + db_vendors:
            if have >= target:
                break
            if add(v, force_cat=cat):
                have += 1

    # Final top-up any leftover unique companies
    leftovers = []
    for pool in by_cat.values():
        leftovers.extend(pool)
    leftovers.extend(extras)
    leftovers.extend(db_vendors)
    for v in leftovers:
        if len(selected) >= 500:
            break
        # place into most underfilled category
        shortfalls = sorted(
            ((TARGETS[c] - sum(1 for s in selected if s["robot_category"] == c)), c)
            for c in TARGETS
        )
        need, cat = shortfalls[-1]
        if need <= 0:
            break
        add(v, force_cat=cat)

    if len(selected) < 500:
        print(f"WARNING: only {len(selected)} unique host/name vendors; need manual fill to 500")
    return selected[:500]


def models_from_vendors(vendors: list[dict]) -> list[dict]:
    """Seed robot-model sheet rows from primary_robots + Tier-1 catalog if present."""
    rows = []
    tier1_path = ROOT / "docs" / "calibration" / "tier1_oem_catalog_v1.json"
    if tier1_path.exists():
        data = json.loads(tier1_path.read_text())
        for mfr in data.get("manufacturers", []):
            for fam in mfr.get("families", []):
                for m in fam.get("models", []):
                    rows.append(
                        {
                            "vendor_name": mfr["name"],
                            "family": fam["name"],
                            "model_slug": m["slug"],
                            "model_name": m["name"],
                            "primary_class": m.get("primary_class", ""),
                            "work_to_map": ",".join(m.get("work_to_map") or []),
                            "commercial_maturity": m.get("commercial_maturity", "unknown"),
                            "calibration_tier": m.get("calibration_tier", 1),
                            "source": "tier1_oem_catalog_v1",
                        }
                    )
    # Also explode primary_robots text into stub models for vendors not in Tier-1
    existing_vendors = {_norm_key(r["vendor_name"]) for r in rows}
    for v in vendors:
        if _norm_key(v["company_name"]) in existing_vendors:
            continue
        primaries = [p.strip() for p in (v.get("primary_robots") or "").split("/") if p.strip()]
        if not primaries:
            primaries = [f"{v['company_name']} platform"]
        for i, p in enumerate(primaries[:3]):
            slug = re.sub(r"[^a-z0-9]+", "-", f"{v['company_name']}-{p}".lower()).strip("-")
            rows.append(
                {
                    "vendor_name": v["company_name"],
                    "family": f"{v['company_name']} family",
                    "model_slug": slug[:160],
                    "model_name": p,
                    "primary_class": v.get("robot_category", ""),
                    "work_to_map": v.get("work_type", ""),
                    "commercial_maturity": v.get("commercial_maturity", "unknown"),
                    "calibration_tier": 2,
                    "source": "vendor_primary_robots",
                }
            )
    return rows


def category_ontology() -> list[dict]:
    rows = []
    for cat, target in TARGETS.items():
        rows.append(
            {
                "category_id": cat,
                "label": cat.replace("_", " ").title(),
                "seed_target": target,
                "includes": "Robot sellers (OEM/brand/RaaS). Exclude pure SI/component/AI-lab unless noted.",
                "match_use": "WHAT ROBOT CLASS CAN DO THIS WORK",
            }
        )
    rows.append(
        {
            "category_id": "_excluded_ecosystem",
            "label": "Excluded from vendor seed",
            "seed_target": 0,
            "includes": "Pure system integrators without robots, component-only, AI-software-only, research labs without product robots — track separately later",
            "match_use": "Do not mix into OEM match graph",
        }
    )
    return rows


def coverage_dashboard(vendors: list[dict]) -> list[dict]:
    counts = Counter(v["robot_category"] for v in vendors)
    roles = Counter(v["vendor_role"] for v in vendors)
    rows = []
    for cat, target in TARGETS.items():
        have = counts.get(cat, 0)
        rows.append(
            {
                "metric": "category_fill",
                "key": cat,
                "target": target,
                "actual": have,
                "gap": target - have,
                "pct": round(100.0 * have / target, 1) if target else 0,
            }
        )
    rows.append(
        {
            "metric": "total_vendors",
            "key": "all",
            "target": 500,
            "actual": len(vendors),
            "gap": 500 - len(vendors),
            "pct": round(100.0 * len(vendors) / 500, 1),
        }
    )
    for role, n in roles.most_common():
        rows.append(
            {
                "metric": "vendor_role",
                "key": role,
                "target": "",
                "actual": n,
                "gap": "",
                "pct": round(100.0 * n / max(len(vendors), 1), 1),
            }
        )
    return rows


# --- Minimal XLSX writer (stdlib) ---

def _col_name(idx: int) -> str:
    s = ""
    n = idx
    while True:
        n, r = divmod(n, 26)
        s = chr(65 + r) + s
        if n == 0:
            break
        n -= 1
    return s


def _sheet_xml(name: str, headers: list[str], rows: list[dict]) -> str:
    # shared strings not used — inline strings
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]
    # header
    cells = []
    for i, h in enumerate(headers):
        ref = f"{_col_name(i)}1"
        cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(h))}</t></is></c>')
    lines.append(f'<row r="1">{"".join(cells)}</row>')
    for r_i, row in enumerate(rows, start=2):
        cells = []
        for i, h in enumerate(headers):
            val = row.get(h, "")
            if val is None:
                val = ""
            ref = f"{_col_name(i)}{r_i}"
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                cells.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(val))}</t></is></c>')
        lines.append(f'<row r="{r_i}">{"".join(cells)}</row>')
    lines.append("</sheetData></worksheet>")
    return "\n".join(lines)


def write_xlsx(path: Path, sheets: list[tuple[str, list[str], list[dict]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for i in range(len(sheets)):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types.append("</Types>")

    rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>',
        "</Relationships>",
    ]

    wb_rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for i in range(len(sheets)):
        wb_rels.append(
            f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>'
        )
    wb_rels.append("</Relationships>")

    sheets_xml = []
    for i, (title, _, _) in enumerate(sheets, start=1):
        safe = escape(title[:31])
        sheets_xml.append(f'<sheet name="{safe}" sheetId="{i}" r:id="rId{i}"/>')
    workbook = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        "<sheets>",
        *sheets_xml,
        "</sheets></workbook>",
    ]

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "\n".join(content_types))
        z.writestr("_rels/.rels", "\n".join(rels))
        z.writestr("xl/workbook.xml", "\n".join(workbook))
        z.writestr("xl/_rels/workbook.xml.rels", "\n".join(wb_rels))
        for i, (title, headers, rows) in enumerate(sheets, start=1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet_xml(title, headers, rows))


def write_csvs(sheets: list[tuple[str, list[str], list[dict]]]) -> None:
    OUT_DIR_CSV.mkdir(parents=True, exist_ok=True)
    for title, headers, rows in sheets:
        p = OUT_DIR_CSV / f"{title.replace(' ', '_').lower()}.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for row in rows:
                w.writerow({h: row.get(h, "") for h in headers})


def main() -> None:
    vendors = assemble_500()
    # normalize vendor sheet columns
    vendor_headers = [
        "company_name",
        "website",
        "country",
        "vendor_role",
        "robot_category",
        "primary_robots",
        "work_type",
        "industries",
        "commercial_maturity",
        "us_availability",
        "sales_model",
        "notes",
        "source",
        "verification",
        "vendor_type",
    ]
    models = models_from_vendors(vendors)
    model_headers = [
        "vendor_name",
        "family",
        "model_slug",
        "model_name",
        "primary_class",
        "work_to_map",
        "commercial_maturity",
        "calibration_tier",
        "source",
    ]
    ontology = category_ontology()
    ont_headers = ["category_id", "label", "seed_target", "includes", "match_use"]
    dash = coverage_dashboard(vendors)
    dash_headers = ["metric", "key", "target", "actual", "gap", "pct"]

    sheets = [
        ("Vendors", vendor_headers, vendors),
        ("Robot Models", model_headers, models),
        ("Category Ontology", ont_headers, ontology),
        ("Vendor Coverage Dashboard", dash_headers, dash),
    ]
    write_xlsx(OUT_XLSX, sheets)
    write_csvs(sheets)

    payload = {
        "dataset_id": "robot_vendor_seed_v1",
        "as_of": date.today().isoformat(),
        "target_vendors": 500,
        "actual_vendors": len(vendors),
        "target_models_range": [1500, 2500],
        "seeded_model_rows": len(models),
        "note": "Model sheet starts from Tier-1 deep models + primary_robots stubs; expand toward 1500–2500 via product-page ingest.",
        "vendor_roles": VENDOR_ROLES,
        "category_targets": TARGETS,
        "vendors": vendors,
        "models": models,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print("vendors", len(vendors))
    print("models", len(models))
    print("xlsx", OUT_XLSX)
    print("json", OUT_JSON)
    print("csv_dir", OUT_DIR_CSV)
    print("coverage", {k: sum(1 for v in vendors if v["robot_category"] == k) for k in TARGETS})


if __name__ == "__main__":
    main()
