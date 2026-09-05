"""Seed NIMO beta-host target accounts into the special project's outreach queue.

Structured from nimo-gtm/02_target_accounts.md. Idempotent by (project, company):
reruns refresh fields + regenerate the review-first draft, but never re-send.
Nothing is sent here — drafts land in the queue for admin approval.

Run locally with DATABASE_URL set, or on Fly:

    fly ssh console -a ready-2-robot -C "python3 scripts/seed_special_project_nimo_targets.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.special_project import SpecialProject, SpecialProjectTarget  # noqa: E402
from app.services.special_projects import (  # noqa: E402
    build_target_draft,
    recompute_project_rollup,
)

SLUG = "nimo-technology"

# company, website, segment, best_fit_task, persona, sequence(A/B/C), fit(H/W/C), signal
TARGETS: list[tuple] = [
    # Tier 1A — Ghost / cloud kitchens & virtual brands
    ("CloudKitchens", "cloudkitchens.com", "Ghost / cloud kitchens", "Assembly + prep", "Founder / Head of Ops", "A", "H", "Nationwide dark-kitchen network with controlled, automation-forward sites"),
    ("Wonder Group", "wonder.com", "Ghost / cloud kitchens", "Multi-step meal assembly", "VP Ops / Culinary", "C", "H", "Rolled up Blue Apron / Grubhub / Tastemade and scaling meal assembly"),
    ("Reef Technology", "reeftechnology.com", "Ghost / cloud kitchens", "Portioning + assembly", "Head of Kitchen Ops", "A", "H", "Mobile / ghost kitchen footprint under unit-economics pressure"),
    ("Kitchen United", "kitchenunited.com", "Ghost / cloud kitchens", "Prep + assembly", "GM / Ops", "A", "W", "Shared commissary model consolidating kitchens"),
    ("Local Kitchens", "localkitchens.com", "Ghost / cloud kitchens", "Assembly", "Founder", "A", "H", "CA multi-brand micro-kitchens, tech-native, exposed to CA wage law"),
    ("Franklin Junction", "franklinjunction.com", "Ghost / cloud kitchens", "Assembly", "Ops lead", "A", "W", "Host-kitchen virtual brand distribution scaling"),
    ("Nextbite", "nextbite.io", "Ghost / cloud kitchens", "Assembly", "Culinary Ops", "B", "W", "Virtual restaurant brands at volume"),
    ("ClusterTruck", "clustertruck.com", "Ghost / cloud kitchens", "Cook prep + assembly", "Founder / CTO", "A", "H", "Owns delivery-only kitchens end-to-end with strong tech DNA"),
    ("C3 (Creative Culinary Concepts)", None, "Ghost / cloud kitchens", "Assembly", "Culinary innovation", "B", "W", "Multi-brand digital kitchens"),
    ("Zuul", None, "Ghost / cloud kitchens", "Assembly", "Ops", "A", "C", "Ghost-kitchen software plus ops"),
    # Tier 1B — QSR innovation labs / high-volume franchisors
    ("Chipotle", "chipotle.com", "QSR innovation labs", "Portioning + prep (produce, guac)", "VP Culinary / Innovation", "B", "H", "Cultivate Next fund invests in kitchen robotics (Autocado, Hyphen) amid acute labor pain"),
    ("Sweetgreen", "sweetgreen.com", "QSR innovation labs", "Bowl assembly + portioning", "VP Innovation", "B", "H", "Acquired Spyce and building the Infinite Kitchen assembly-line concept"),
    ("White Castle", "whitecastle.com", "QSR innovation labs", "Griddle prep + assembly", "Innovation lead", "B", "H", "Longtime automation adopter with Flippy pilots — proven appetite"),
    ("Wendy's", "wendys.com", "QSR innovation labs", "Assembly + prep", "Chief Innovation / Ops", "B", "W", "Tested underground automation (Pipedream) and vocal on labor"),
    ("CKE (Carl's Jr / Hardee's)", "ckr.com", "QSR innovation labs", "Burger assembly", "Ops / franchise innovation", "C", "W", "Franchise-heavy with sharp labor-cost focus"),
    ("Jack in the Box", "jackinthebox.com", "QSR innovation labs", "Assembly + prep", "Innovation lead", "B", "W", "Public interest in labor automation"),
    ("Chick-fil-A", "chick-fil-a.com", "QSR innovation labs", "Prep + assembly", "Innovation / R&D", "B", "W", "High-volume, quality-obsessed, active R&D"),
    ("Panera Bread", "panerabread.com", "QSR innovation labs", "Assembly + prep", "Culinary R&D", "B", "W", "Menu simplification and automation trials"),
    ("Domino's", "dominos.com", "QSR innovation labs", "Pizza assembly", "Ops innovation", "C", "W", "Pizza assembly at massive scale"),
    ("Little Caesars", "littlecaesars.com", "QSR innovation labs", "Pizza assembly", "Ops", "C", "C", "High-volume pizza production"),
    ("Jersey Mike's", "jerseymikes.com", "QSR innovation labs", "Sandwich assembly", "Franchise ops", "C", "W", "Rapid expansion with repetitive sandwich assembly"),
    ("Firehouse Subs", "firehousesubs.com", "QSR innovation labs", "Assembly", "RBI innovation", "B", "W", "Under the RBI innovation umbrella"),
    ("Shake Shack", "shakeshack.com", "QSR innovation labs", "Burger assembly", "Innovation / Ops", "B", "W", "Premium QSR, tech-forward with kiosks"),
    ("In-N-Out", "in-n-out.com", "QSR innovation labs", "Prep", "Ops", "C", "C", "High-volume consistency culture"),
    ("Raising Cane's", "raisingcanes.com", "QSR innovation labs", "Prep + assembly", "Ops", "C", "W", "Rapid expansion on a limited, automatable menu"),
    # Tier 2A — Fast-casual assembly concepts
    ("CAVA", "cava.com", "Fast-casual assembly", "Bowl assembly + portioning", "VP Ops / Innovation", "B", "H", "Fast growth and IPO capital fueling operations investment"),
    ("Qdoba", "qdoba.com", "Fast-casual assembly", "Burrito rolling + assembly", "Ops", "C", "W", "Burrito / bowl assembly at volume"),
    ("Moe's Southwest Grill", "moes.com", "Fast-casual assembly", "Burrito rolling", "Franchise ops", "C", "W", "Franchise burrito assembly"),
    ("Freshii", "freshii.com", "Fast-casual assembly", "Assembly", "Ops", "C", "C", "Bowl / wrap assembly"),
    ("Dig", "diginn.com", "Fast-casual assembly", "Portioning + assembly", "Founder / Ops", "A", "W", "Seasonal bowls, tech-forward"),
    ("Just Salad", "justsalad.com", "Fast-casual assembly", "Portioning + assembly", "Ops", "C", "W", "High-volume salad assembly"),
    ("MOD Pizza", "modpizza.com", "Fast-casual assembly", "Pizza assembly", "Ops innovation", "C", "W", "Assembly-line pizza"),
    ("Blaze Pizza", "blazepizza.com", "Fast-casual assembly", "Pizza assembly", "Ops", "C", "W", "Fast-fire assembly line"),
    # Tier 2B — Contract & institutional food service
    ("Compass Group", "compass-group.com", "Contract / institutional", "Prep + assembly", "Innovation / Ops director", "C", "W", "Largest contract caterer with central kitchens and heavy labor spend"),
    ("Aramark", "aramark.com", "Contract / institutional", "Prep + assembly", "Innovation", "B", "W", "Stadiums, campuses, and healthcare kitchens"),
    ("Sodexo", "sodexo.com", "Contract / institutional", "Prep", "Innovation", "B", "W", "Institutional volume across sites"),
    ("HMSHost", "hmshost.com", "Contract / institutional", "Assembly + prep", "Ops innovation", "C", "H", "Airport concessions, 24/7, notoriously staffing-hard"),
    ("Levy Restaurants", "levyrestaurants.com", "Contract / institutional", "Assembly", "Ops", "C", "W", "Stadium / venue food at peak volume"),
    ("Delaware North", "delawarenorth.com", "Contract / institutional", "Assembly", "Innovation", "B", "C", "Venues plus travel hospitality"),
    ("Guckenheimer (ISS)", "guckenheimer.com", "Contract / institutional", "Prep", "Ops", "C", "C", "Corporate dining accounts"),
    # Tier 2C — Commissaries / central prep
    ("Factor (HelloFresh RTE)", "factor75.com", "Commissary / central prep", "Portioning + assembly", "Ops / automation lead", "C", "H", "Ready-to-eat meal assembly at scale"),
    ("Fresh N Lean", "freshnlean.com", "Commissary / central prep", "Portioning + assembly", "Founder / Ops", "A", "W", "Meal-prep subscription kitchens"),
    ("Territory Foods", "territoryfoods.com", "Commissary / central prep", "Assembly", "Ops", "C", "W", "Chef-driven meal prep"),
    ("Snap Kitchen", "snapkitchen.com", "Commissary / central prep", "Portioning", "Ops", "C", "C", "Prepared-meal commissary"),
    ("Amazon Fresh / Whole Foods prepared foods", "amazon.com", "Commissary / central prep", "Prep + assembly", "Ops innovation", "C", "W", "Central prep with automation budget"),
    ("Sysco (culinary centers)", "sysco.com", "Commissary / central prep", "Prep", "Innovation", "B", "C", "Distribution plus prep innovation"),
    ("Regional hospital system central kitchen", None, "Commissary / central prep", "Portioning + assembly", "Foodservice director", "C", "W", "Standardized trays, labor-hard"),
    ("University dining (large state system)", None, "Commissary / central prep", "Assembly", "Dining services director", "C", "W", "High-volume, repetitive assembly"),
    ("Casino / resort buffet central kitchen", None, "Commissary / central prep", "Prep + assembly", "F&B director", "C", "C", "High-volume prep"),
    ("Royal Caribbean (cruise commissary)", "royalcaribbean.com", "Commissary / central prep", "Portioning + assembly", "F&B innovation", "B", "C", "Massive standardized prep across ships"),
    # ── Tier 3 — expansion batch (net-new ICP, adds pipeline depth) ──────────────
    # Ghost / cloud kitchens
    ("DoorDash Kitchens", "doordash.com", "Ghost / cloud kitchens", "Assembly + prep", "Head of Kitchen Ops", "A", "W", "Operates shared delivery-only kitchen facilities"),
    ("Ghost Kitchen Brands", "ghostkitchenbrands.com", "Ghost / cloud kitchens", "Multi-brand assembly", "Ops lead", "A", "W", "Multi-brand delivery kitchens embedded in retail footprints"),
    ("Butler Hospitality", "butlerhospitality.com", "Ghost / cloud kitchens", "Prep + assembly", "Founder / Ops", "A", "C", "Hotel-based virtual kitchens serving room service at scale"),
    ("Everytable", "everytable.com", "Commissary / central prep", "Portioning + assembly", "Founder / Ops", "A", "H", "Central-kitchen model powering high-volume grab-and-go"),
    # QSR innovation labs / high-volume franchisors
    ("Taco Bell", "tacobell.com", "QSR innovation labs", "Assembly + portioning", "VP Innovation (Yum)", "B", "H", "Yum Brands innovation labs actively testing kitchen automation"),
    ("Burger King", "bk.com", "QSR innovation labs", "Burger assembly", "RBI innovation", "B", "W", "RBI reimaging kitchens under its multi-year capital plan"),
    ("Wingstop", "wingstop.com", "QSR innovation labs", "Fry + sauce portioning", "Ops innovation", "B", "H", "Rapid unit growth on a simple, automatable menu with a restaurant-of-the-future program"),
    ("Panda Express", "pandaexpress.com", "QSR innovation labs", "Wok prep + portioning", "R&D / Ops", "B", "W", "Largest Asian QSR investing in kitchen innovation"),
    ("Popeyes", "popeyes.com", "QSR innovation labs", "Prep + assembly", "RBI innovation", "B", "W", "RBI brand scaling with heavy fried-chicken prep labor"),
    ("Del Taco", "deltaco.com", "QSR innovation labs", "Assembly", "Ops innovation", "C", "W", "Value QSR under margin and labor pressure"),
    ("El Pollo Loco", "elpolloloco.com", "QSR innovation labs", "Prep + assembly", "Ops / R&D", "B", "W", "Publicly signaled automation interest for back-of-house"),
    # Fast-casual assembly
    ("Chopt", "choptsalad.com", "Fast-casual assembly", "Bowl + salad assembly", "Ops innovation", "B", "W", "High-volume salad assembly across urban units"),
    ("Mendocino Farms", "mendocinofarms.com", "Fast-casual assembly", "Sandwich + bowl assembly", "Culinary Ops", "B", "W", "Chef-driven fast casual scaling nationally"),
    ("Salad and Go", "saladandgo.com", "Fast-casual assembly", "Bowl assembly + portioning", "Ops", "A", "H", "Drive-thru salad concept built on a central-kitchen model"),
    ("Honeygrow", "honeygrow.com", "Fast-casual assembly", "Stir-fry + bowl assembly", "Founder / Ops", "A", "W", "Tech-forward build-your-own concept"),
    # Contract / institutional
    ("Chartwells", "chartwellsk12.com", "Contract / institutional", "Prep + assembly", "Innovation (Compass)", "B", "W", "Compass division cooking at institutional volume"),
    ("Bon Appétit Management", "bamco.com", "Contract / institutional", "Prep + assembly", "Culinary innovation", "B", "C", "Compass premium sector carrying a scratch-cooking labor load"),
    ("SSP America", "foodtravelexperts.com", "Contract / institutional", "Assembly + prep", "Ops innovation", "C", "H", "Airport dining operator with brutal 24/7 staffing"),
    # Commissary / meal service / grocery prepared foods
    ("CookUnity", "cookunity.com", "Commissary / central prep", "Portioning + assembly", "Ops / automation", "A", "H", "Chef-marketplace meal service scaling central production"),
    ("Thistle", "thistle.co", "Commissary / central prep", "Portioning + assembly", "Ops", "A", "W", "Plant-forward meal delivery from central kitchens"),
    ("Daily Harvest", "daily-harvest.com", "Commissary / central prep", "Portioning + assembly", "Ops", "C", "W", "Frozen prepared-food production at scale"),
    ("Home Chef", "homechef.com", "Commissary / central prep", "Portioning + assembly", "Ops (Kroger)", "C", "W", "Kroger-owned meal service with central assembly"),
    ("Kroger (Kitchen 1883)", "kroger.com", "Commissary / central prep", "Prep + assembly", "Prepared-foods innovation", "B", "W", "Grocery prepared-foods program with an automation budget"),
    ("Mosaic Foods", "mosaicfoods.com", "Commissary / central prep", "Portioning + assembly", "Founder / Ops", "A", "W", "Frozen plant-based meals from a central kitchen"),
]


def main() -> None:
    db = SessionLocal()
    try:
        project = db.query(SpecialProject).filter(SpecialProject.slug == SLUG).first()
        if project is None:
            raise SystemExit(f"NIMO project not found (slug={SLUG}). Run seed_special_project_nimo.py first.")

        existing = {
            (t.company or "").strip().lower(): t for t in (project.targets or [])
        }
        created = 0
        refreshed = 0
        for order, row in enumerate(TARGETS, start=1):
            company, website, segment, task, persona, seq, fit, signal = row
            key = company.strip().lower()
            target = existing.get(key)
            if target is None:
                target = SpecialProjectTarget(company=company)
                # Append to the loaded collection so recompute counts it.
                project.targets.append(target)
                created += 1
            else:
                refreshed += 1
            target.website = website
            target.segment = segment
            target.best_fit_task = task
            target.persona = persona
            target.sequence = seq
            target.fit = fit
            target.signal = signal
            target.sort_order = order
            # Never overwrite a sent draft; refresh the rest from the playbook.
            if target.sent_at is None:
                subject, body = build_target_draft(project, target)
                target.draft_subject, target.draft_body = subject, body

        db.flush()
        recompute_project_rollup(project)
        db.commit()
        db.refresh(project)
        print(f"NIMO targets: {created} created, {refreshed} refreshed (total {len(project.targets)})")
        print(f"Funnel: {project.pipeline}")
        print(f"Client portal path: /p/{project.share_token}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
