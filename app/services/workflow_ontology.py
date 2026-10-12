"""Workflow ontology — where robots can be hired.

A Robot Job is **human work a robot could be hired to do**. An operational job
posting (order picker, dishwasher, EVS tech) is the *evidence* that the work
exists at a named employer. It is the opportunity, not contamination.

Three evidence layers, scored independently:

    FIT     — the work maps to a workflow family that commercial robots do today
    PAIN    — the employer is struggling to staff it (volume, turnover, bonuses,
              24/7 shifts, heavy/repetitive/hazardous work)
    INTENT  — the employer is already moving toward automation (robot / AMR /
              automation named in the posting, automation or CI hires at an
              operator, RFPs/tenders, deployment news)

Tier (stored on ``robot_jobs.opportunity_tier``):

    1  AUTOMATION_INTENT   intent evidence + fit       → daily email first
    2  AUTOMATION_READY    fit + pain, or high-automatability fit
    3  AUTOMATABLE_WORK    fit only                    → pipeline / nurture
    0  NOT_AN_OPPORTUNITY  robot builders at OEMs, desk work with no physical
                           workflow — the ONLY thing we drop

Nothing a robot could do is ever rejected for "looking like a human job".
That is the whole market.

Robot categories match ``docs/calibration/vendor_seed_sheets/vendors.csv``
(``robot_category``) so example vendors come from the curated seed.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

_ROOT = Path(__file__).resolve().parents[2]
_VENDORS_CSV = _ROOT / "docs" / "calibration" / "vendor_seed_sheets" / "vendors.csv"


# ─── Workflow families ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorkflowFamily:
    key: str                      # job_function key stored on requirements.job_function
    label: str
    product_class: str            # FIND product class (existing + new)
    industries: tuple[str, ...]
    title_terms: tuple[str, ...]  # regex fragments matched on the TITLE
    task_terms: tuple[str, ...]   # regex fragments matched on the DESCRIPTION
    robot_categories: tuple[str, ...]
    automatability: float         # 0..1 — commercial readiness of robots for this work
    capabilities: tuple[str, ...] = ()
    notes: str = ""
    exclude_title: tuple[str, ...] = ()

    @property
    def title_re(self) -> re.Pattern:
        return _compile(self.title_terms)

    @property
    def task_re(self) -> re.Pattern:
        return _compile(self.task_terms, stem=True)


@lru_cache(maxsize=None)
def _compile_cached(terms: tuple[str, ...], stem: bool) -> re.Pattern:
    tail = "" if stem else r"\b"
    return re.compile(r"\b(?:" + "|".join(terms) + r")" + tail, re.I)


def _compile(terms: tuple[str, ...], stem: bool = False) -> re.Pattern:
    """Titles match whole words; task language matches stems (palletiz → palletizing)."""
    if not terms:
        return re.compile(r"(?!x)x")
    return _compile_cached(terms, stem)


FAMILIES: tuple[WorkflowFamily, ...] = (
    # ── WAREHOUSE / LOGISTICS ────────────────────────────────────────────────
    WorkflowFamily(
        "picking", "Order picking", "warehouse", ("Logistics", "Retail", "Grocery", "E-commerce"),
        (rf"order pickers?", rf"pickers?", rf"pick(?:ing)? associates?", rf"selectors?",
         rf"order selectors?", rf"order fillers?", rf"order pullers?", rf"fulfillment (?:associate|specialist|worker)s?",
         rf"e-?commerce associates?", rf"personal shoppers?", rf"grocery pickers?", rf"pick ?& ?pack"),
        (r"pick(?:ing)? orders?", r"pick(?:ing)?, pack", r"rf scanners?", r"pick (?:to|by) (?:light|voice)",
         r"voice pick(?:ing)?", r"units per hour", r"cases per hour", r"pick rates?", r"order fulfillment",
         r"goods[- ]to[- ]person", r"pick ?modules?", r"pick ?faces?", r"each pick(?:ing)?"),
        ("picking_manipulation_palletizing", "amr_agv_material_transport"), 0.80,
        ("pick_pack", "tote_transport"),
    ),
    WorkflowFamily(
        "packing", "Packing / pack-out", "warehouse", ("Logistics", "E-commerce", "Manufacturing", "Food Processing"),
        (r"packers?", r"pack(?:ing)? (?:associate|operator|line worker)s?", r"packag(?:ing|er)s? (?:associate|operator|worker|tech)s?",
         r"kitting (?:associate|operator)s?", r"kitters?", r"box(?:ing)? (?:associate|operator)s?", r"bagg(?:ers?|ing)",
         r"pack[- ]?out", r"case packers?", r"wrappers?"),
        (r"pack(?:ing)? (?:orders|boxes|cases|cartons|product)", r"carton erect", r"case pack", r"kitting",
         r"box(?:ing)? product", r"seal(?:ing)? (?:boxes|cartons)", r"bagging", r"labeling (?:boxes|cartons|packages)"),
        ("picking_manipulation_palletizing", "industrial_robot_arms", "cobots"), 0.75,
        ("pick_pack",),
    ),
    WorkflowFamily(
        "palletizing", "Palletizing / depalletizing", "factory", ("Manufacturing", "Food & Beverage", "Logistics", "CPG"),
        (r"palleti[sz]ers?", r"palleti[sz]ing", r"depalleti[sz]", r"stackers?", r"case stackers?", r"end[- ]of[- ]line (?:operator|associate)s?"),
        (r"build(?:ing)? pallets?", r"stack(?:ing)? (?:cases|boxes|bags|cartons) on(?:to)? pallets?", r"palleti[sz]",
         r"mixed[- ]case pallets?", r"stretch[- ]wrap", r"end of line", r"end-of-line"),
        ("picking_manipulation_palletizing", "industrial_robot_arms", "cobots"), 0.90,
        ("load_unload", "palletize"),
    ),
    WorkflowFamily(
        "truck_unloading", "Truck / container (un)loading", "logistics", ("Logistics", "Parcel", "Retail DC"),
        (r"(?:truck|trailer|container) (?:un)?loaders?", r"unloaders?", r"loaders?", r"dock (?:worker|associate|hand)s?",
         r"freight handlers?", r"package handlers?", r"parcel handlers?", r"lumpers?", r"ramp agents?", r"baggage handlers?"),
        (r"(?:un)?load(?:ing)? (?:trucks|trailers|containers|freight)", r"floor[- ]loaded", r"floor loaded",
         r"(?:un)?load(?:ing)? packages", r"lift (?:up to )?\d{2,3} ?(?:lbs|pounds)", r"sort(?:ing)? packages",
         r"conveyor", r"inbound freight", r"outbound freight", r"live unload"),
        ("picking_manipulation_palletizing", "industrial_robot_arms"), 0.65,
        ("load_unload",),
    ),
    WorkflowFamily(
        "material_handling", "Material handling / intralogistics transport", "warehouse",
        ("Logistics", "Manufacturing", "Healthcare", "Automotive"),
        (r"material handlers?", r"warehouse (?:worker|associate|clerk|operator|team member|handler)s?",
         r"distribution (?:center )?(?:associate|worker)s?", r"stock (?:handler|associate)s?", r"tuggers?",
         r"tugger (?:driver|operator)s?", r"water ?spiders?", r"line feeders?", r"parts (?:runner|delivery|chaser)s?",
         r"material (?:runner|driver|coordinator|associate)s?", r"inventory associates?", r"put[- ]?away (?:associate|driver)s?",
         r"replenishment (?:associate|driver)s?", r"warehouse"),
        (r"move (?:material|product|parts|inventory|totes|carts)", r"deliver(?:ing)? (?:parts|material|totes)",
         r"line[- ]side", r"replenish(?:ing|ment)?", r"put[- ]?away", r"tote", r"carts? to", r"kanban",
         r"stage (?:material|product)", r"transport(?:ing)? (?:material|product|parts)", r"pallet jack"),
        ("amr_agv_material_transport", "autonomous_forklift_pallet"), 0.85,
        ("tote_transport", "transport"),
    ),
    WorkflowFamily(
        "forklift", "Forklift / pallet movement", "logistics", ("Logistics", "Manufacturing", "Retail DC", "Food & Beverage"),
        (r"forklift (?:operator|driver|associate)s?", r"forklift", r"reach (?:truck )?(?:operator|driver)s?",
         r"(?:pallet|electric pallet) jack (?:operator|driver)s?", r"cherry ?picker operators?", r"order picker operators?",
         r"lift truck (?:operator|driver)s?", r"sit[- ]down forklift", r"stand[- ]up forklift", r"clamp (?:truck )?operators?",
         r"yard (?:jockey|driver|hostler)s?", r"hostlers?", r"spotters?"),
        (r"forklift", r"reach truck", r"pallet jack", r"lift truck", r"move pallets", r"yard trucks?", r"move trailers",
         r"double[- ]stack", r"high[- ]bay", r"rack(?:ing)? pallets"),
        ("autonomous_forklift_pallet", "amr_agv_material_transport"), 0.80,
        ("pallet_transport",),
    ),
    WorkflowFamily(
        "receiving", "Receiving / inventory control", "warehouse", ("Logistics", "Retail", "Healthcare"),
        (r"receiving (?:associate|clerk|lead)s?", r"receivers?", r"inventory (?:control|clerk|counter|specialist)s?",
         r"cycle counters?", r"stock clerks?", r"shipping (?:and|&) receiving", r"shipping clerks?", r"shipping associates?"),
        (r"cycle count", r"count(?:ing)? inventory", r"scan(?:ning)? (?:barcodes|inventory|product)", r"inventory accuracy",
         r"physical inventory", r"receive (?:freight|product|shipments)", r"check in (?:shipments|deliveries)"),
        ("amr_agv_material_transport", "inspection_security_quadrupeds", "specialty_commercial"), 0.60,
        ("inventory_scan",),
    ),
    WorkflowFamily(
        "sortation", "Parcel / mail sortation", "logistics", ("Parcel", "Postal", "Logistics", "Recycling"),
        (r"sort(?:er|ers|ing) (?:associate|operator)s?", r"sorters?", r"mail (?:handler|sorter|processor)s?",
         r"parcel (?:sorter|associate)s?", r"induct(?:er|ion) (?:associate|operator)s?"),
        (r"sort(?:ing)? (?:packages|parcels|mail|items)", r"induct(?:ing)? packages", r"sortation"),
        ("picking_manipulation_palletizing", "amr_agv_material_transport"), 0.80,
        ("pick_pack",),
    ),
    WorkflowFamily(
        "cold_storage", "Cold storage / freezer work", "warehouse", ("Cold Chain", "Food & Beverage", "Grocery"),
        (r"freezer (?:associate|selector|worker|order picker)s?", r"cooler (?:associate|selector|worker)s?",
         r"cold storage (?:associate|worker)s?"),
        (r"freezer", r"-\d{1,2} ?(?:°|degrees)", r"below zero", r"cold storage", r"refrigerated (?:warehouse|environment)"),
        ("autonomous_forklift_pallet", "amr_agv_material_transport", "picking_manipulation_palletizing"), 0.80,
        ("pallet_transport", "pick_pack"),
        "Freezer work is hard to staff and hazardous — strong pain by default.",
    ),
    # ── MANUFACTURING ────────────────────────────────────────────────────────
    WorkflowFamily(
        "machine_tending", "Machine tending", "factory", ("Manufacturing", "Automotive", "Aerospace", "Metal Fabrication"),
        (r"cnc (?:operator|machinist|tender|setup operator)s?", r"machine (?:operator|tender)s?", r"press (?:operator|brake operator)s?",
         r"lathe operators?", r"mill(?:ing)? operators?", r"injection mold(?:ing)? (?:operator|tech)s?", r"molding operators?",
         r"stamping operators?", r"punch press operators?", r"grinder operators?", r"saw operators?", r"extrusion operators?",
         r"die ?cast (?:operator)s?", r"production (?:line )?operators?", r"production (?:worker|associate|team member)s?"),
        (r"load(?:ing)? (?:and|&) unload(?:ing)? (?:machines|parts|cnc)", r"machine tending", r"cnc", r"press brake",
         r"injection mold", r"run (?:multiple )?machines", r"parts? (?:in|into) (?:the )?machine", r"monitor machines"),
        ("cobots", "industrial_robot_arms"), 0.85,
        ("load_unload",),
    ),
    WorkflowFamily(
        "assembly", "Assembly", "factory", ("Manufacturing", "Electronics", "Automotive", "Medical Devices"),
        (r"assemblers?", r"assembly (?:operator|technician|associate|worker|line worker)s?", r"line workers?",
         r"electronic assemblers?", r"mechanical assemblers?", r"production assemblers?", r"solderers?",
         r"wire harness (?:assembler|operator)s?", r"screwdriving"),
        (r"assembl(?:e|ing) (?:parts|components|products|units)", r"screw(?:ing)?", r"fasten(?:ing)?", r"insert(?:ing)? components",
         r"solder(?:ing)?", r"torque", r"repetitive (?:assembly|tasks)", r"assembly line"),
        ("cobots", "industrial_robot_arms", "humanoids_general_purpose"), 0.60,
        ("assembly",),
    ),
    WorkflowFamily(
        "welding", "Welding / cutting", "factory", ("Manufacturing", "Metal Fabrication", "Shipbuilding", "Construction"),
        (r"welders?", r"welding (?:operator|technician)s?", r"mig welders?", r"tig welders?", r"robotic weld(?:ing)? operators?",
         r"fabricators?", r"plasma (?:cutter|operator)s?", r"laser (?:cutter|operator)s?", r"brazers?", r"solder(?:er)?s?"),
        (r"weld(?:ing)?", r"mig", r"tig", r"flux[- ]core", r"plasma cut", r"laser cut", r"fabricat(?:e|ion)"),
        ("industrial_robot_arms", "cobots"), 0.80,
        ("weld",),
    ),
    WorkflowFamily(
        "finishing", "Painting / coating / sanding / deburring", "factory",
        ("Manufacturing", "Aerospace", "Automotive", "Furniture"),
        (r"painters?", r"paint (?:line )?(?:operator|tech)s?", r"spray (?:painter|operator)s?", r"powder coat(?:er|ing)? (?:operator)?s?",
         r"coaters?", r"sanders?", r"deburr(?:er|ing)s?", r"polishers?", r"grinders?", r"blasters?", r"sandblasters?", r"finishers?"),
        (r"spray (?:paint|coat)", r"powder coat", r"sand(?:ing)?", r"deburr", r"polish(?:ing)?", r"grind(?:ing)?", r"blast(?:ing)?"),
        ("industrial_robot_arms", "cobots"), 0.75,
        ("finish",),
    ),
    WorkflowFamily(
        "quality_inspection", "Visual / dimensional inspection", "factory",
        ("Manufacturing", "Food Processing", "Electronics", "Pharma"),
        (r"(?:quality|qc|qa) (?:inspector|technician|associate|auditor)s?", r"inspectors?", r"visual inspectors?",
         r"quality control", r"sorters? (?:and|&) inspectors?", r"cmm (?:operator|programmer)s?"),
        (r"inspect(?:ing)? (?:parts|products|units)", r"visual inspection", r"measure (?:parts|dimensions)", r"defects?",
         r"calipers", r"micrometers?", r"go/no[- ]go"),
        ("industrial_robot_arms", "cobots", "inspection_security_quadrupeds"), 0.65,
        ("inspect",),
    ),
    WorkflowFamily(
        "food_processing", "Food & meat processing lines", "factory",
        ("Food Processing", "Meat & Poultry", "Bakery", "CPG"),
        (r"(?:meat|poultry|food|seafood|plant) (?:processor|packer|production worker|line worker)s?", r"production (?:sanitation|worker)s?",
         r"deboners?", r"meat cutters?", r"trimmers?", r"butchers?", r"bakery (?:production|line) (?:worker|associate)s?",
         r"sanitation (?:worker|associate|crew)s?", r"line attendants?"),
        (r"processing (?:plant|line)", r"debon(?:e|ing)", r"trim(?:ming)? (?:meat|product)", r"cut(?:ting)? (?:meat|poultry)",
         r"sanitation", r"wash ?down", r"usda", r"haccp", r"cold, wet"),
        ("industrial_robot_arms", "cobots", "picking_manipulation_palletizing"), 0.55,
        ("food_handling",),
    ),
    WorkflowFamily(
        "lab_automation", "Laboratory sample handling", "lab",
        ("Healthcare", "Pharma", "Biotech", "Clinical Labs"),
        (r"lab(?:oratory)? (?:assistant|technician|aide|associate)s?", r"specimen (?:processor|accessioner|handler)s?",
         r"accessioners?", r"phlebotomy processors?", r"sample (?:handler|processor|prep technician)s?", r"lab tech"),
        (r"pipett(?:e|ing)", r"specimen(?:s)? (?:processing|receipt|accessioning)", r"centrifug", r"aliquot", r"plate (?:handling|prep)",
         r"sample prep", r"liquid handl", r"high[- ]throughput"),
        ("industrial_robot_arms", "cobots", "healthcare_hospital_service"), 0.70,
        ("lab_handling",),
    ),
    # ── FOOD SERVICE ─────────────────────────────────────────────────────────
    WorkflowFamily(
        "food_prep", "Cooking / food prep", "food_prep",
        ("Food Service", "Restaurants", "Hospitality", "Casinos", "Corporate Dining", "Healthcare"),
        (r"(?:line|prep|fry|grill|sous|breakfast|banquet|short[- ]order|pantry|pizza|sushi|saute|wok|dietary) cooks?", r"cooks?",
         r"kitchen (?:staff|helper|worker|associate|team member)s?", r"food prep(?:arer)?s?", r"prep (?:worker|associate)s?",
         r"pizza makers?", r"sandwich (?:maker|artist)s?", r"salad makers?", r"fry(?:er)? (?:station|operator|cook)s?",
         r"tortilla makers?", r"bowl (?:assembly|makers?)", r"make[- ]line", r"chefs?", r"commissary (?:worker|associate)s?",
         r"food production (?:worker|associate)s?", r"bakers?", r"crew members?"),
        (r"fry(?:ing|er)", r"grill(?:ing)?", r"prep(?:ping)? (?:food|ingredients|vegetables)", r"chop(?:ping)?", r"portion(?:ing)?",
         r"assembl(?:e|ing) (?:orders|bowls|sandwiches|salads|pizzas)", r"line station", r"food safety", r"servsafe",
         r"high[- ]volume kitchen", r"tickets? per hour"),
        ("hospitality_foodservice_delivery", "industrial_robot_arms", "cobots"), 0.55,
        ("food_prep",),
    ),
    WorkflowFamily(
        "beverage", "Coffee / beverage prep", "food_prep",
        ("Food Service", "Retail", "Airports", "Corporate Dining", "Convenience"),
        (r"baristas?", r"bartenders?", r"beverage (?:attendant|server|associate)s?", r"drink makers?", r"smoothie (?:maker|associate)s?"),
        (r"espresso", r"brew(?:ing)?", r"blend(?:ing)? drinks", r"pour(?:ing)? drinks", r"beverage station"),
        ("hospitality_foodservice_delivery", "cobots"), 0.55,
        ("beverage_prep",),
    ),
    WorkflowFamily(
        "warewash", "Dishwashing / warewashing", "food_prep",
        ("Food Service", "Restaurants", "Hospitality", "Healthcare", "Education", "Corporate Dining"),
        (r"dish ?washers?", r"dishwashing", r"stewards?", r"utility (?:worker|steward)s?", r"pot washers?", r"warewash(?:er|ing)?",
         r"kitchen porters?", r"kitchen stewards?"),
        (r"wash(?:ing)? dishes", r"dish (?:machine|pit|room)", r"pots and pans", r"scrape (?:and )?rack", r"sort(?:ing)? dishes"),
        ("hospitality_foodservice_delivery", "industrial_robot_arms"), 0.60,
        ("food_prep",),
    ),
    WorkflowFamily(
        "serving", "Food running / table service / bussing", "serving",
        ("Restaurants", "Hospitality", "Casinos", "Senior Living", "Healthcare", "Entertainment"),
        (r"food runners?", r"runners?", r"bussers?", r"bus (?:boy|person|staff)s?", r"servers?", r"waiters?", r"waitress(?:es)?",
         r"waitstaff", r"banquet (?:server|houseperson|captain)s?", r"cocktail (?:server|waitress)es?", r"room service (?:attendant|server)s?",
         r"dining (?:room )?(?:attendant|associate|aide)s?", r"tray passers?", r"hosts?", r"hostess(?:es)?", r"expos?", r"expeditors?"),
        (r"run(?:ning)? food", r"deliver(?:ing)? food (?:to|orders)", r"bus(?:sing)? tables", r"clear(?:ing)? tables",
         r"carry (?:trays|plates)", r"room service", r"tray delivery", r"meal delivery"),
        ("hospitality_foodservice_delivery",), 0.75,
        ("serving_task",),
        exclude_title=(r"(?:sql|windows|linux|web|application|cloud|file|mail|exchange|database|game|minecraft|discord|process) servers?",
                       r"servers? (?:administrator|admin|engineer|technician)", r"process servers?"),
    ),
    WorkflowFamily(
        "cashier_ordering", "Order taking / cashiering", "retail",
        ("Restaurants", "Retail", "QSR", "Convenience", "Grocery"),
        (r"cashiers?", r"front counter (?:associate|crew)s?", r"order takers?", r"drive[- ]thru (?:operator|associate|cashier)s?",
         r"checkout (?:associate|clerk)s?", r"self[- ]checkout (?:host|attendant)s?", r"ticket (?:taker|seller)s?"),
        (r"take (?:customer )?orders", r"drive[- ]thru", r"cash register", r"process (?:payments|transactions)", r"pos system"),
        ("specialty_commercial",), 0.45,
        ("order_taking",),
        "Kiosk / voice-AI drive-thru territory; still counts as automatable work.",
    ),
    # ── HOSPITALITY ──────────────────────────────────────────────────────────
    WorkflowFamily(
        "housekeeping", "Housekeeping / room cleaning", "hospitality",
        ("Hospitality", "Hotels", "Casinos", "Healthcare", "Senior Living", "Cruise"),
        (r"housekeep(?:er|ers|ing)", r"room attendants?", r"guest room attendants?", r"housepersons?", r"housemen", r"house ?men",
         r"turndown attendants?", r"public area attendants?", r"pa attendants?", r"suite attendants?"),
        (r"clean(?:ing)? (?:guest )?rooms", r"make beds", r"\d{1,2} rooms per (?:shift|day)", r"rooms per shift", r"vacuum(?:ing)?",
         r"restock(?:ing)? (?:amenities|linens|carts)", r"turndown"),
        ("cleaning_robots", "hospitality_foodservice_delivery", "humanoids_general_purpose"), 0.55,
        ("hospitality_task", "surface_clean"),
    ),
    WorkflowFamily(
        "laundry", "Laundry / linen", "hospitality",
        ("Hospitality", "Healthcare", "Industrial Laundry", "Senior Living"),
        (r"laundry (?:attendant|worker|associate|aide|operator|tech)s?", r"linen (?:attendant|runner|tech|associate|aide)s?",
         r"launderers?", r"folders?", r"pressers?", r"ironers?", r"textile (?:processor|worker)s?"),
        (r"fold(?:ing)? (?:linens|towels|laundry|sheets)", r"sort(?:ing)? (?:linens|laundry)", r"wash(?:ers)? and dryers",
         r"linen (?:delivery|carts|chute)", r"ironer", r"feed(?:ing)? (?:the )?ironer"),
        ("specialty_commercial", "amr_agv_material_transport", "humanoids_general_purpose"), 0.45,
        ("hospitality_task",),
    ),
    WorkflowFamily(
        "guest_delivery", "In-building delivery (rooms, amenities, packages)", "hospitality",
        ("Hotels", "Residential", "Offices", "Healthcare", "Casinos"),
        (r"bell(?:person|man|men|hop|staff|s)?", r"bell attendants?", r"porters?", r"luggage (?:attendant|porter)s?",
         r"runners? \(hotel\)", r"package (?:room )?(?:attendant|clerk)s?", r"mail ?room (?:clerk|associate)s?", r"couriers? \(internal\)",
         r"amenity (?:attendant|runner)s?", r"door ?(?:man|person|staff)"),
        (r"deliver(?:ing)? (?:amenities|packages|luggage|items) to (?:guest|rooms|residents)", r"luggage", r"package room",
         r"mail ?room", r"amenity delivery"),
        ("hospitality_foodservice_delivery", "amr_agv_material_transport"), 0.70,
        ("transport",),
    ),
    WorkflowFamily(
        "front_desk", "Front desk / check-in / concierge", "hospitality",
        ("Hotels", "Healthcare", "Offices", "Residential"),
        (r"front desk (?:agent|associate|clerk|attendant)s?", r"front desk", r"guest service (?:agent|associate|representative)s?",
         r"night auditors?", r"concierges?", r"receptionists?", r"lobby (?:ambassador|attendant)s?", r"greeters?"),
        (r"check[- ]?in", r"check[- ]?out", r"greet(?:ing)? guests", r"answer(?:ing)? phones", r"room keys"),
        ("humanoids_general_purpose", "specialty_commercial"), 0.35,
        ("hospitality_task",),
    ),
    WorkflowFamily(
        "parking", "Parking / valet", "hospitality", ("Hotels", "Casinos", "Airports", "Healthcare", "Parking"),
        (r"valets?", r"valet (?:attendant|driver|parker)s?", r"parking (?:attendant|lot attendant|cashier|enforcement)s?",
         r"lot attendants?", r"car jockeys?", r"shuttle drivers?"),
        (r"park(?:ing)? (?:cars|vehicles)", r"retriev(?:e|ing) vehicles", r"parking (?:garage|structure|lot)"),
        ("specialty_commercial",), 0.35,
        ("transport",),
    ),
    # ── CLEANING / FACILITIES ────────────────────────────────────────────────
    WorkflowFamily(
        "cleaning", "Commercial floor & surface cleaning", "cleaning",
        ("Facilities", "Retail", "Airports", "Healthcare", "Education", "Offices", "Casinos", "Logistics"),
        (r"janitors?", r"janitorial (?:worker|associate|tech|staff)s?", r"custodians?", r"custodial (?:worker|staff|technician)s?",
         r"cleaners?", r"cleaning (?:technician|associate|crew|specialist|staff)s?", r"floor (?:tech|technician|care|cleaner|scrubber)s?",
         r"porters?", r"day porters?", r"night porters?", r"utility porters?", r"restroom attendants?", r"facility attendants?",
         r"building attendants?", r"maintenance (?:aide|attendant)s?", r"sanitation (?:attendant|specialist)s?", r"cleaning"),
        (r"scrub(?:bing|ber)?", r"auto[- ]?scrubber", r"buff(?:ing|er)", r"burnish(?:ing|er)", r"mop(?:ping)?", r"sweep(?:ing)?",
         r"vacuum(?:ing)?", r"strip(?:ping)? (?:and|&) wax", r"floor care", r"(?:square|sq\.?) (?:feet|ft)", r"disinfect(?:ing|ion)?",
         r"trash removal", r"empty(?:ing)? trash"),
        ("cleaning_robots",), 0.85,
        ("surface_clean", "hard_floor_scrub"),
    ),
    WorkflowFamily(
        "environmental_services", "Hospital environmental services / disinfection", "cleaning",
        ("Healthcare", "Senior Living", "Labs"),
        (r"evs (?:tech|technician|aide|associate|worker)s?", r"evs", r"environmental services(?: (?:tech|technician|aide|associate|worker)s?)?",
         r"terminal cleaners?", r"disinfection (?:tech|technician)s?", r"hospital (?:housekeeper|cleaner)s?"),
        (r"terminal clean", r"isolation rooms", r"uv[- ]?c?", r"disinfect(?:ing|ion)", r"patient rooms", r"discharge clean",
         r"infection prevention"),
        ("cleaning_robots", "healthcare_hospital_service"), 0.80,
        ("surface_clean", "disinfect"),
    ),
    WorkflowFamily(
        "facade_cleaning", "Window / facade / solar panel cleaning", "cleaning_drone",
        ("Facilities", "Real Estate", "Energy", "Hospitality"),
        (r"window (?:washer|cleaner)s?", r"facade cleaners?", r"high[- ]rise window", r"pressure washers?", r"power washers?",
         r"solar panel (?:cleaner|technician)s?", r"drone (?:cleaner|cleaning (?:operator|technician))s?", r"building wash(?:er|ing)s?",
         r"rope access technicians?"),
        (r"high[- ]rise", r"swing stage", r"bosun chair", r"rope access", r"pressure wash", r"soft wash", r"solar (?:panel|array) clean"),
        ("cleaning_robots", "specialty_commercial"), 0.65,
        ("surface_clean", "drone_task"),
    ),
    WorkflowFamily(
        "pool_car_wash", "Car wash / pool / tank cleaning", "cleaning",
        ("Automotive", "Hospitality", "Industrial"),
        (r"car wash (?:attendant|associate|detailer)s?", r"detailers?", r"pool (?:attendant|cleaner|technician)s?",
         r"tank cleaners?", r"vessel cleaners?", r"hydro ?blasters?", r"vacuum truck operators?"),
        (r"detail(?:ing)? (?:cars|vehicles)", r"pool cleaning", r"tank cleaning", r"hydro ?blast", r"confined space"),
        ("cleaning_robots", "specialty_commercial", "inspection_security_quadrupeds"), 0.55,
        ("surface_clean",),
    ),
    WorkflowFamily(
        "waste_recycling", "Waste & recycling sorting", "factory",
        ("Recycling", "Waste Management", "Municipal"),
        (r"(?:recycling|mrf|material recovery) (?:sorter|worker|associate|line worker)s?", r"sorters? \(recycling\)",
         r"waste (?:sorter|handler)s?", r"line sorters?", r"pickers? \(recycling\)", r"refuse (?:collector|loader)s?",
         r"sanitation (?:worker|loader|driver)s?", r"garbage collectors?"),
        (r"recycl(?:ing|ables)", r"material recovery facility", r"\bmrf\b", r"sort(?:ing)? (?:trash|waste|recyclables)",
         r"contaminants?", r"pick(?:ing)? line"),
        ("picking_manipulation_palletizing", "industrial_robot_arms"), 0.75,
        ("pick_pack",),
    ),
    # ── SECURITY / INSPECTION ────────────────────────────────────────────────
    WorkflowFamily(
        "security_patrol", "Security patrol / monitoring", "security",
        ("Facilities", "Logistics", "Retail", "Data Centers", "Utilities", "Parking", "Campuses"),
        (r"security (?:officer|guard|patrol officer|patroller|associate|specialist)s?", r"security guards?", r"patrol (?:officer|guard)s?",
         r"loss prevention (?:officer|associate|detective)s?", r"asset protection (?:associate|specialist)s?", r"fire watch",
         r"gate (?:guard|attendant)s?", r"night watch(?:man|men)?", r"site security"),
        (r"patrol(?:ling)?", r"rounds", r"monitor(?:ing)? (?:cameras|cctv|perimeter)", r"fire watch", r"perimeter", r"access control"),
        ("inspection_security_quadrupeds", "specialty_commercial"), 0.70,
        ("patrol", "inspect"),
    ),
    WorkflowFamily(
        "industrial_inspection", "Industrial inspection / meter reading / rounds", "inspection",
        ("Energy", "Oil & Gas", "Utilities", "Chemicals", "Data Centers", "Mining"),
        (r"(?:field|plant|outside|process|area) operators?", r"operator rounds", r"(?:pipeline|tank|asset|ndt|line|tower) inspectors?",
         r"meter readers?", r"utility (?:inspector|locator)s?", r"ndt technicians?", r"data center (?:technician|operator)s?",
         r"critical facilities technicians?", r"substation (?:operator|technician)s?", r"gauger(?:s)?"),
        (r"operator rounds", r"gauge readings?", r"thermal (?:imaging|inspection)", r"leak detection", r"read(?:ing)? meters",
         r"inspect(?:ing)? (?:equipment|pipelines|tanks|assets|towers|lines)", r"hazardous (?:areas|environments)", r"h2s",
         r"confined space", r"rack(?:ing)? (?:servers|equipment)", r"remote hands"),
        ("inspection_security_quadrupeds", "specialty_commercial"), 0.65,
        ("inspect",),
    ),
    # ── HEALTHCARE ───────────────────────────────────────────────────────────
    WorkflowFamily(
        "patient_transport", "Patient & specimen transport", "healthcare",
        ("Healthcare", "Senior Living"),
        (r"patient transport(?:er|ers)?", r"transporters?", r"patient escorts?", r"transport (?:aide|associate|tech)s?",
         r"specimen (?:courier|runner)s?", r"hospital couriers?", r"lab couriers?"),
        (r"transport(?:ing)? patients", r"wheelchairs?", r"stretchers?", r"deliver(?:ing)? (?:specimens|meds|medications|supplies)",
         r"tube system"),
        ("healthcare_hospital_service", "amr_agv_material_transport"), 0.60,
        ("transport", "healthcare_task"),
    ),
    WorkflowFamily(
        "hospital_logistics", "Hospital supply / meal / linen delivery", "healthcare",
        ("Healthcare", "Senior Living"),
        (r"supply chain (?:tech|technician|associate)s?", r"materials management (?:tech|associate)s?", r"central supply (?:tech|associate)s?",
         r"distribution (?:tech|technician)s? \(hospital\)", r"dietary (?:aide|associate|worker|host)s?", r"tray (?:line|passer)s?",
         r"nutrition (?:services|aide|associate|host)s?", r"food service (?:aide|worker|associate)s?", r"par level (?:tech|associate)s?"),
        (r"par levels?", r"restock(?:ing)? (?:supplies|units|carts)", r"deliver(?:ing)? (?:supplies|meal trays|trays|linens)",
         r"tray line", r"meal trays", r"case carts?"),
        ("healthcare_hospital_service", "amr_agv_material_transport"), 0.75,
        ("transport", "healthcare_task"),
    ),
    WorkflowFamily(
        "pharmacy", "Pharmacy dispensing / fill", "healthcare",
        ("Healthcare", "Retail Pharmacy", "Mail-Order Pharmacy"),
        (r"pharmacy (?:technician|tech|assistant|clerk|fill tech)s?", r"pharmacy techs?", r"fill technicians?",
         r"central fill (?:tech|associate)s?", r"iv (?:room )?technicians?", r"compounding technicians?"),
        (r"fill(?:ing)? prescriptions", r"count(?:ing)? (?:pills|tablets)", r"dispens(?:e|ing)", r"compound(?:ing)?",
         r"iv (?:compounding|admixture)", r"blister pack", r"unit dose"),
        ("healthcare_hospital_service", "industrial_robot_arms"), 0.70,
        ("healthcare_task",),
    ),
    WorkflowFamily(
        "sterile_processing", "Sterile processing", "healthcare",
        ("Healthcare", "Surgery Centers"),
        (r"sterile processing (?:technician|tech|associate)s?", r"sterile processing", r"central sterile (?:tech|technician)s?",
         r"spd (?:tech|technician)s?", r"decontamination (?:tech|technician)s?", r"instrument (?:tech|technician)s?"),
        (r"decontaminat(?:e|ion)", r"sterili[sz](?:e|ation)", r"autoclave", r"instrument trays", r"case carts?"),
        ("healthcare_hospital_service", "industrial_robot_arms"), 0.50,
        ("healthcare_task",),
    ),
    WorkflowFamily(
        "patient_assist", "Patient lifting / sitting / companion", "healthcare",
        ("Healthcare", "Senior Living", "Home Care"),
        (r"patient (?:care )?(?:sitter|observer|companion|attendant)s?", r"sitters?", r"companions?", r"resident assistants?",
         r"caregivers?", r"lift (?:team|tech)s?"),
        (r"lift(?:ing)? patients", r"patient (?:lift|transfer)s?", r"fall risk", r"1:1 observation", r"companionship"),
        ("healthcare_hospital_service", "humanoids_general_purpose"), 0.30,
        ("healthcare_task",),
    ),
    # ── RETAIL / GROCERY ─────────────────────────────────────────────────────
    WorkflowFamily(
        "replenishment", "Shelf stocking / store replenishment", "retail",
        ("Retail", "Grocery", "Convenience", "Home Improvement"),
        (r"stockers?", r"(?:night|overnight|dairy|freezer|grocery) stockers?", r"shelf stockers?", r"stock (?:associate|clerk|team member)s?",
         r"merchandisers?", r"replenishment (?:associate|team member)s?", r"(?:overnight|night) (?:crew|associate|team member)s?",
         r"unloaders? \(retail\)", r"inventory (?:replenishment|stocking) associates?", r"backroom (?:associate|team member)s?"),
        (r"stock(?:ing)? shelves", r"face (?:product|shelves)", r"front(?:ing)? (?:and|&) fac", r"planograms?", r"price (?:changes|tags)",
         r"out[- ]of[- ]stocks?", r"shelf (?:audits?|scanning)", r"backroom"),
        ("specialty_commercial", "amr_agv_material_transport", "humanoids_general_purpose"), 0.55,
        ("inventory_scan", "replenish"),
    ),
    WorkflowFamily(
        "last_mile", "Last-mile & campus delivery", "delivery",
        ("Logistics", "Food Delivery", "Retail", "Campuses", "Healthcare"),
        (r"delivery (?:driver|associate|helper|rider|courier)s?", r"couriers?", r"bike couriers?", r"food delivery",
         r"route (?:driver|helper)s?", r"package delivery (?:driver)?s?", r"delivery drivers?", r"van drivers?"),
        (r"deliver(?:ing)? (?:packages|orders|food|parcels)", r"last[- ]mile", r"route", r"stops per (?:day|route)", r"\d{2,3} stops"),
        ("last_mile_outdoor_delivery", "amr_agv_material_transport"), 0.45,
        ("transport",),
    ),
    WorkflowFamily(
        "trucking", "Yard / middle-mile driving", "logistics",
        ("Logistics", "Trucking", "Ports", "Mining"),
        (r"cdl[- ]?a? drivers?", r"truck drivers?", r"(?:otr|regional|local|linehaul|yard|terminal) drivers?", r"tractor[- ]trailer drivers?",
         r"haul truck (?:operator|driver)s?", r"straddle carrier operators?", r"terminal tractor operators?"),
        (r"cdl", r"hours of service", r"linehaul", r"yard moves", r"terminal tractor", r"drayage", r"haul road"),
        ("autonomous_forklift_pallet", "specialty_commercial"), 0.35,
        ("transport",),
        "Autonomous trucking/yard tractors — longer sales cycle, still a real market.",
    ),
    # ── AGRICULTURE ──────────────────────────────────────────────────────────
    WorkflowFamily(
        "harvest", "Harvesting / picking produce", "agriculture",
        ("Agriculture", "Greenhouses", "Vineyards", "Orchards", "Nurseries"),
        (r"farm (?:worker|laborer|hand|associate)s?", r"harvest(?:ers?| workers?| crew| associates?| laborers?)", r"field (?:worker|laborer|hand)s?",
         r"(?:fruit|berry|strawberry|apple|vegetable|produce|crop|tree) pickers?", r"orchard (?:worker|laborer)s?",
         r"vineyard (?:worker|laborer)s?", r"greenhouse (?:worker|associate|grower|laborer)s?", r"nursery (?:worker|laborer)s?",
         r"agricultural (?:worker|laborer|equipment operator)s?", r"h-?2a"),
        (r"harvest(?:ing)?", r"pick(?:ing)? (?:fruit|berries|vegetables|apples|strawberries|produce|crops)", r"prun(?:e|ing)",
         r"thin(?:ning)?", r"transplant(?:ing)?", r"greenhouse", r"seedlings?", r"h-?2a"),
        ("agriculture",), 0.50,
        ("agriculture_task",),
    ),
    WorkflowFamily(
        "field_work", "Weeding / spraying / field operations", "agriculture",
        ("Agriculture", "Turf", "Landscaping"),
        (r"tractor (?:operator|driver)s?", r"equipment operators? \(farm\)", r"sprayer operators?", r"applicators?",
         r"pesticide applicators?", r"irrigators?", r"weeders?", r"hoe crew"),
        (r"weed(?:ing)?", r"spray(?:ing)? (?:crops|fields|herbicide|pesticide)", r"till(?:ing)?", r"plant(?:ing)? (?:seeds|crops)",
         r"irrigat(?:e|ion)", r"tractor"),
        ("agriculture",), 0.60,
        ("agriculture_task",),
    ),
    WorkflowFamily(
        "dairy_livestock", "Milking / livestock / poultry house", "agriculture",
        ("Dairy", "Livestock", "Poultry", "Egg Production"),
        (r"milkers?", r"dairy (?:worker|farm hand|technician)s?", r"herdsm[ae]n", r"livestock (?:worker|tech)s?",
         r"poultry (?:house )?(?:worker|tech|farm hand)s?", r"egg (?:packer|gatherer)s?", r"barn (?:worker|hand)s?"),
        (r"milk(?:ing)? (?:cows|parlor)", r"parlor", r"feed(?:ing)? (?:animals|livestock|calves)", r"barn cleaning",
         r"egg (?:collection|gathering)", r"poultry houses?"),
        ("agriculture",), 0.70,
        ("agriculture_task",),
    ),
    WorkflowFamily(
        "landscaping", "Mowing / grounds / snow", "landscaping",
        ("Landscaping", "Golf", "Campuses", "Municipal", "Facilities"),
        (r"landscapers?", r"landscape (?:laborer|technician|crew member)s?", r"groundskeepers?", r"grounds (?:worker|crew|keeper)s?",
         r"mowers?", r"mower operators?", r"lawn (?:care )?(?:technician|tech|worker)s?", r"golf course (?:maintenance|worker)s?",
         r"greenskeepers?", r"snow (?:removal|plow) (?:operator|worker|driver)s?"),
        (r"mow(?:ing)?", r"trim(?:ming)? (?:hedges|grass)", r"edg(?:e|ing)", r"leaf (?:blowing|removal)", r"snow removal", r"plow(?:ing)?"),
        ("specialty_commercial", "agriculture"), 0.60,
        ("outdoor_task",),
    ),
    # ── CONSTRUCTION / MINING ────────────────────────────────────────────────
    WorkflowFamily(
        "construction_labor", "Construction labor (drywall, layout, rebar, masonry)", "construction",
        ("Construction", "Homebuilding", "Infrastructure", "Solar"),
        (r"construction (?:laborer|worker|helper)s?", r"general laborers?", r"laborers?", r"drywall (?:finisher|hanger|installer|taper)s?",
         r"drywallers?", r"tapers?", r"(?:framing|rough) carpenters?", r"framers?", r"bricklayers?", r"masons?", r"rebar (?:worker|tier|ironworker)s?",
         r"ironworkers?", r"concrete (?:finisher|laborer)s?", r"layout (?:technician|surveyor)s?", r"tile (?:setter|installer)s?",
         r"painters? \(construction\)", r"demolition (?:laborer|worker)s?", r"solar (?:installer|module installer)s?", r"insulation installers?"),
        (r"hang(?:ing)? drywall", r"tape (?:and|&) mud", r"tie rebar", r"lay(?:ing)? (?:brick|block)", r"layout", r"demolition",
         r"install(?:ing)? (?:solar )?(?:panels|modules)", r"drill(?:ing)? (?:holes|anchors) (?:in|into) (?:ceilings|concrete)",
         r"overhead drilling", r"concrete (?:finishing|pour)"),
        ("construction", "humanoids_general_purpose"), 0.40,
        ("construction_task",),
    ),
    WorkflowFamily(
        "mining", "Mining & heavy equipment", "mining",
        ("Mining", "Quarries", "Oil & Gas"),
        (r"(?:underground )?miners?", r"mine (?:laborer|operator|worker)s?", r"haul truck (?:operator|driver)s?",
         r"heavy equipment operators?", r"loader operators?", r"dozer operators?", r"excavator operators?", r"drill(?:er)? operators?",
         r"blasters? \(mining\)", r"roustabouts?", r"floorhands?"),
        (r"haul truck", r"underground", r"open pit", r"blast(?:ing)?", r"drill rig", r"excavat(?:e|or|ion)"),
        ("specialty_commercial", "inspection_security_quadrupeds"), 0.45,
        ("mining_task",),
    ),
    # ── GENERAL PURPOSE ──────────────────────────────────────────────────────
    WorkflowFamily(
        "general_labor", "General repetitive physical labor", "general",
        ("Manufacturing", "Logistics", "Facilities", "Staffing"),
        (r"general (?:labor|laborer|warehouse|production|helper)s?", r"helpers?", r"utility (?:worker|associate|person)s?",
         r"handlers?", r"(?:production|plant|factory) helpers?", r"associates? \(production\)", r"temp to hire"),
        (r"repetitive (?:lifting|tasks|motions)", r"lift (?:up to )?\d{2,3} ?(?:lbs|pounds)", r"stand(?:ing)? for (?:\d+|long) hours",
         r"fast[- ]paced", r"physically demanding"),
        ("humanoids_general_purpose", "cobots", "amr_agv_material_transport"), 0.40,
        ("general_manipulation",),
    ),
)

FAMILY_BY_KEY: dict[str, WorkflowFamily] = {f.key: f for f in FAMILIES}

# New job_function → product_class pairs the legacy map doesn't know yet.
EXTRA_FUNCTION_PRODUCT_CLASS: dict[str, str] = {f.key: f.product_class for f in FAMILIES}


# ─── Intent / pain / exclusion vocab ─────────────────────────────────────────

# Robot / automation named as something the employer runs, buys, or deploys.
INTENT_PATTERNS: tuple[tuple[str, float, str], ...] = (
    # (regex, weight, label)
    (r"(?:implement|deploy|roll(?:ing)? out|pilot|introduc|install|integrat|scal)\w* (?:\w+ ){0,4}"
     r"(?:robots?|robotics|amrs?|agvs?|cobots?|automation|automated (?:systems?|solutions?|equipment)|asrs|as/rs|autonomous)",
     1.0, "deploying_automation"),
    (r"(?:robots?|robotics|amrs?|agvs?|cobots?|asrs|as/rs|autostore|goods[- ]to[- ]person|automated storage)"
     r" (?:\w+ ){0,3}(?:program|deployment|rollout|initiative|project|pilot|fleet|cell|system|implementation)",
     0.9, "automation_program"),
    (r"work(?:ing)? (?:alongside|with|next to) (?:robots?|cobots?|amrs?|automation|autonomous)", 0.8, "works_with_robots"),
    (r"(?:monitor|supervis|oversee|troubleshoot|maintain|operate|run)\w* (?:\w+ ){0,3}"
     r"(?:robots?|robotic|amrs?|agvs?|cobots?|autonomous (?:mobile )?robots?|automated (?:equipment|systems?|lines?)|palletizing robots?)",
     0.8, "operates_robots"),
    (r"(?:automation|robotics|autonomous systems|industry 4\.0|smart (?:factory|warehouse)|lights[- ]out)"
     r" (?:\w+ ){0,3}(?:strategy|roadmap|initiative|investment|transformation|journey|program)", 0.9, "automation_strategy"),
    (r"(?:new|greenfield|state[- ]of[- ]the[- ]art|highly) automated (?:facility|distribution center|dc|warehouse|plant|fulfillment center)",
     0.9, "automated_facility"),
    (r"(?:request for (?:proposals?|quotes?|information|qualifications)|rfp|rfq|rfi|invitation (?:to|for) bid|itb|solicitation|tender)"
     r"(?:\W+\w+){0,8}\W+(?:robot|robotic|automat|autonomous|amr|agv|conveyor|palletiz|scrubber|disinfection)", 1.0, "procurement"),
    (r"(?:cost to automate|automate (?:this|the|our)|looking to automate|seeking (?:an? )?automation|automation (?:partner|vendor|integrator))",
     1.0, "explicit_automation_ask"),
    (r"\b(?:robot|cobot|amr|agv) (?:operator|attendant|tender|technician|supervisor|wrangler)s?\b", 0.7, "robot_operator_role"),
)

# Operator-side automation roles: a company hiring these is a BUYER, not a builder.
BUYER_AUTOMATION_ROLE_RE = re.compile(
    r"\b(?:(?:head|director|vp|vice president|manager|lead|senior manager|chief)\b.{0,25}"
    r"(?:automation|robotics|mechani[sz]ation|innovation|continuous improvement|operational excellence|industrial engineering|"
    r"process improvement|lean|engineering (?:and|&) automation|warehouse technology|operations technology)"
    r"|(?:automation|robotics|controls|material handling|mhe|conveyor|asrs|as/rs) (?:engineer|technician|tech|specialist|mechanic|manager|lead|supervisor)s?"
    r"|industrial engineers?|(?:robotic|automated) (?:systems|equipment) (?:technician|tech|mechanic)s?"
    r"|(?:continuous improvement|ci|lean|six sigma|kaizen|operational excellence|opex) (?:manager|lead|specialist|engineer|director)s?"
    r"|(?:asrs|as/rs|amr|agv|robotics|automation) (?:technician|tech|operator|coordinator|specialist)s?)\b",
    re.I,
)

PAIN_PATTERNS: tuple[tuple[str, float, str], ...] = (
    (r"(?:sign(?:ing|-on)|hiring|retention|referral|attendance|stay) bonus", 0.35, "bonus"),
    (r"(?:hiring|start(?:ing)?) (?:immediately|now|asap|this week|today)|immediate (?:hire|start|openings?)|urgently hiring|hiring event|walk[- ]in interviews?|same[- ]day (?:offer|interview)s?|no experience (?:needed|required|necessary)", 0.3, "urgent"),
    (r"(?:multiple|many|several|\d{2,4}\+?) (?:openings|positions|associates|team members|hires)|now hiring (?:\d+|multiple)|mass hiring", 0.35, "volume"),
    (r"(?:labor|staffing|worker|workforce) (?:shortage|challenges?|gap|crisis)|high turnover|hard[- ]to[- ]fill|difficult to (?:staff|fill|recruit)", 0.5, "shortage"),
    (r"(?:night|overnight|graveyard|3rd|third|weekend|rotating) shifts?|24/7|24 hours|7 days a week|holidays? required|mandatory overtime|overtime (?:available|required)", 0.2, "shifts"),
    (r"(?:lift|carry|push|pull)\w* (?:up to |at least )?\d{2,3} ?(?:lbs|pounds|lb\b|kg)", 0.25, "heavy"),
    (r"repetitive (?:lifting|motion|tasks|movements|bending)|stand(?:ing)? (?:and walk(?:ing)? )?for (?:\d+|8|10|12|long|extended) hours|physically demanding|fast[- ]paced", 0.2, "repetitive"),
    (r"(?:freezer|cooler|-\d{1,2} ?(?:°|degrees)|extreme (?:heat|cold)|hot (?:environment|temperatures)|confined spaces?|hazardous (?:materials|environment|areas)|chemical exposure|loud noise|wet conditions)", 0.3, "hazard"),
    (r"(?:pick|case|unit|piece|room|tote|package|pallet)s? (?:per|an|/) ?(?:hour|hr|shift)|productivity (?:standards|rates?|goals)|production quotas?|rate (?:requirements|expectations)", 0.3, "throughput_quota"),
    (r"\$(?:1[5-9]|2[0-9])(?:\.\d{2})?\s*(?:-|–|to)\s*\$?(?:1[6-9]|2[0-9]|3[0-5])(?:\.\d{2})?\s*(?:/|an|per)\s*(?:hr|hour)", 0.1, "hourly_wage"),
)

# Builders: a robot OEM hiring engineers is supply side, not a buyer.
BUILDER_TITLE_RE = re.compile(
    r"\b(?:robotics (?:software|hardware|research|perception|controls|ml|machine learning|firmware)? ?(?:engineer|scientist|researcher|developer|intern)"
    r"|(?:perception|motion planning|slam|manipulation|locomotion|embodied ai|reinforcement learning|computer vision|ml|machine learning|deep learning|ai) "
    r"(?:engineer|scientist|researcher|developer|intern)"
    r"|firmware engineer|embedded (?:software )?engineer|mechatronics engineer|robot (?:software )?developer|simulation engineer"
    r"|(?:field (?:application|service) engineer|solutions engineer|sales engineer|account executive|business development) .{0,30}(?:robot|autonom|amr)"
    r")s?\b",
    re.I,
)

# Pure desk work with no physical workflow: not an opportunity unless intent says so.
DESK_ONLY_TITLE_RE = re.compile(
    r"\b(?:software (?:engineer|developer)|data (?:scientist|analyst|engineer)|accountant|attorney|lawyer|paralegal|"
    r"financial analyst|marketing (?:manager|specialist|coordinator)|recruiter|talent acquisition|hr (?:generalist|manager|business partner)|"
    r"product manager|ux designer|graphic designer|copywriter|account executive|sales (?:representative|executive)|"
    r"customer success|it support|help ?desk|underwriter|actuary|teacher|professor|therapist|psychologist|physician|"
    r"registered nurse|nurse practitioner|pharmacist|dentist|counselor|social worker)s?\b",
    re.I,
)

_INTENT_RE = tuple((re.compile(p, re.I), w, lbl) for p, w, lbl in INTENT_PATTERNS)
_PAIN_RE = tuple((re.compile(p, re.I), w, lbl) for p, w, lbl in PAIN_PATTERNS)


# ─── Vendor seed (OEM detection + example vendors) ───────────────────────────


@lru_cache(maxsize=1)
def _vendor_rows() -> tuple[dict[str, str], ...]:
    try:
        with open(_VENDORS_CSV, newline="", encoding="utf-8") as fh:
            return tuple(csv.DictReader(fh))
    except (OSError, csv.Error):
        return ()


def _norm_company(name: str) -> str:
    name = (name or "").lower()
    name = re.sub(r"\(.*?\)", " ", name)
    name = re.sub(r"\b(?:inc|llc|ltd|gmbh|co|corp|corporation|company|technologies|technology|robotics|robots|ai|systems|the)\b\.?", " ", name)
    return re.sub(r"[^a-z0-9]+", " ", name).strip()


@lru_cache(maxsize=1)
def _oem_names() -> frozenset[str]:
    names = set()
    for row in _vendor_rows():
        if (row.get("vendor_role") or "").strip() in {"robot_oem", "component_supplier", "system_integrator"}:
            n = _norm_company(row.get("company_name") or "")
            if len(n) >= 3:
                names.add(n)
    return frozenset(names)


def is_robot_vendor(company: str) -> bool:
    """True when the employer is itself a robot OEM / integrator (supply side)."""
    n = _norm_company(company)
    if not n:
        return False
    if n in _oem_names():
        return True
    return bool(re.search(r"\brobot(?:ic)?s?\b", (company or "").lower())) and "hotel" not in (company or "").lower()


@lru_cache(maxsize=64)
def example_vendors(category: str, limit: int = 4) -> tuple[str, ...]:
    out = []
    for row in _vendor_rows():
        if (row.get("robot_category") or "") == category and (row.get("us_availability") or "").lower().startswith("y"):
            out.append((row.get("company_name") or "").strip())
        if len(out) >= limit:
            break
    return tuple(o for o in out if o)


# ─── Analysis ────────────────────────────────────────────────────────────────


@dataclass
class FamilyHit:
    family: WorkflowFamily
    title_hit: bool
    task_hits: int
    score: float


@dataclass
class OpportunityAnalysis:
    tier: int
    score: float                      # 0..100 opportunity score
    families: list[FamilyHit] = field(default_factory=list)
    intent: list[str] = field(default_factory=list)
    pain: list[str] = field(default_factory=list)
    buyer_automation_role: bool = False
    builder: bool = False
    reason: str = ""

    @property
    def primary(self) -> Optional[WorkflowFamily]:
        return self.families[0].family if self.families else None

    def to_requirements(self) -> dict[str, Any]:
        fam = self.primary
        return {
            "opportunity_score": round(self.score, 1),
            "opportunity_reason": self.reason,
            "workflow_families": [h.family.key for h in self.families[:3]],
            "robot_categories": list(fam.robot_categories) if fam else [],
            "example_vendors": [v for c in (fam.robot_categories if fam else ()) for v in example_vendors(c, 3)][:6],
            "intent_evidence": self.intent,
            "pain_evidence": self.pain,
            "automatability": fam.automatability if fam else None,
        }


# Titles that say "physical work happens here" but not WHICH work. Description decides.
GENERIC_TITLE_RE = re.compile(
    r"\b(?:production|warehouse|general|plant|factory|distribution|operations|team|crew|store|utility|"
    r"entry[- ]level|seasonal|temp(?:orary)?|associate)\s*(?:associates?|workers?|members?|laborers?|helpers?|"
    r"operators?|team members?|staff)?\b",
    re.I,
)


def _title_is_generic(title: str) -> bool:
    words = re.sub(r"[^a-z ]", " ", (title or "").lower()).split()
    stripped = GENERIC_TITLE_RE.sub(" ", title or "")
    return len(words) <= 4 and not re.sub(r"[^A-Za-z]", "", stripped)


def match_families(title: str, description: str = "", *, min_task_hits: int = 2) -> list[FamilyHit]:
    t = title or ""
    d = f"{title or ''}\n{description or ''}"
    hits: list[FamilyHit] = []
    title_weight = 0.4 if _title_is_generic(t) else 1.0
    for fam in FAMILIES:
        if fam.exclude_title and _compile(fam.exclude_title).search(t):
            continue
        title_hit = bool(fam.title_re.search(t))
        task_hits = len({m.group(0).lower() for m in fam.task_re.finditer(d)}) if d else 0
        if not title_hit and task_hits < min_task_hits:
            continue
        score = (title_weight if title_hit else 0.0) + min(task_hits, 4) * 0.3
        hits.append(FamilyHit(fam, title_hit, task_hits, score))
    # Prefer title evidence; generic families sink.
    hits.sort(key=lambda h: (h.score - (0.6 if h.family.key == "general_labor" else 0.0), h.family.automatability), reverse=True)
    return hits


def _labels(compiled: Iterable[tuple[re.Pattern, float, str]], text: str) -> tuple[float, list[str]]:
    total = 0.0
    labels: list[str] = []
    for rx, weight, label in compiled:
        if rx.search(text):
            total += weight
            labels.append(label)
    return total, labels


def analyze_posting(title: str, description: str = "", company: str = "") -> OpportunityAnalysis:
    """Score a posting / headline / tender as a robot opportunity."""
    title = (title or "").strip()
    text = f"{title}\n{description or ''}"
    fams = match_families(title, description)
    intent_w, intent = _labels(_INTENT_RE, text)
    pain_w, pain = _labels(_PAIN_RE, text)
    if not fams and intent_w >= 0.7:
        # A tender or announcement names the workflow once; one task hit is enough.
        fams = match_families(title, description, min_task_hits=1)
    buyer_role = bool(BUYER_AUTOMATION_ROLE_RE.search(title))
    vendor = is_robot_vendor(company) if company else False
    builder = bool(BUILDER_TITLE_RE.search(title)) or (vendor and not fams)

    if builder and not fams:
        return OpportunityAnalysis(0, 0.0, [], intent, pain, buyer_role, True, "robot builder / supply side")
    if vendor and not intent:
        # An OEM hiring a field tech or cleaner is not buying robots.
        return OpportunityAnalysis(0, 0.0, fams, intent, pain, buyer_role, True, "employer is a robot vendor")

    if buyer_role and not fams:
        # Automation / CI / controls hire at an operator = they are investing in automation.
        score = min(100.0, 55 + intent_w * 15 + pain_w * 5)
        return OpportunityAnalysis(1 if intent else 2, score, [], intent, pain, True, False,
                                   "operator hiring automation/CI talent")

    if not fams:
        if intent_w >= 0.7:
            return OpportunityAnalysis(1, min(100.0, 50 + intent_w * 20), [], intent, pain, buyer_role, False,
                                       "explicit automation intent, workflow unspecified")
        if DESK_ONLY_TITLE_RE.search(title):
            return OpportunityAnalysis(0, 0.0, [], intent, pain, buyer_role, False, "desk work, no physical workflow")
        return OpportunityAnalysis(0, 0.0, [], intent, pain, buyer_role, False, "no robot-doable workflow found")

    top = fams[0].family
    fit = top.automatability * (1.0 if fams[0].title_hit else 0.8)
    score = 100 * (0.45 * fit + 0.30 * min(1.0, pain_w / 1.0) + 0.25 * min(1.0, intent_w))
    if buyer_role:
        score += 10
    score = max(0.0, min(100.0, score))

    if intent_w >= 0.7 or buyer_role:
        tier, reason = 1, f"{top.label}: employer already moving to automation"
    elif pain_w >= 0.5 or top.automatability >= 0.8:
        tier, reason = 2, f"{top.label}: automatable work under staffing pressure" if pain_w >= 0.5 else f"{top.label}: robots do this commercially today"
    else:
        tier, reason = 3, f"{top.label}: automatable work"
    return OpportunityAnalysis(tier, score, fams, intent, pain, buyer_role, False, reason)


def job_function_for(title: str, description: str = "") -> Optional[str]:
    fams = match_families(title, description)
    return fams[0].family.key if fams else None


# product_class → the industry labels the rest of the app already filters on.
LEGACY_INDUSTRY_BY_CLASS = {
    "food_prep": "Food Service",
    "serving": "Food Service",
    "retail": "Retail",
    "cleaning": "Cleaning",
    "cleaning_drone": "Hospitality",
    "hospitality": "Hospitality",
    "healthcare": "Healthcare",
    "lab": "Healthcare",
    "warehouse": "Logistics",
    "logistics": "Logistics",
    "delivery": "Logistics",
    "factory": "Factory",
    "agriculture": "Agriculture",
    "construction": "Construction",
    "mining": "Mining",
    "security": "Facilities",
    "inspection": "Facilities",
    "landscaping": "Facilities",
}


def industry_for(title: str, description: str = "") -> Optional[str]:
    fams = match_families(title, description)
    if not fams:
        return None
    return LEGACY_INDUSTRY_BY_CLASS.get(fams[0].family.product_class)


def search_terms(limit_per_family: int = 4) -> dict[str, list[str]]:
    """Human-readable job-board query terms per family (for building search URLs)."""
    out: dict[str, list[str]] = {}
    for fam in FAMILIES:
        terms = []
        for frag in fam.title_terms:
            plain = re.sub(r"\(\?:([^)]*)\)\??", lambda m: m.group(1).split("|")[0], frag)
            plain = re.sub(r"[\\?\[\]()+*^$]|s\?$", "", plain).replace("[- ]", " ").replace("- ", " ")
            plain = re.sub(r"\s+", " ", plain).strip()
            if plain and plain not in terms and len(plain) > 3:
                terms.append(plain)
            if len(terms) >= limit_per_family:
                break
        out[fam.key] = terms
    return out
