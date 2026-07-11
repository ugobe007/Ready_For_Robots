"""Shared wording for agent-authored Ready For Robots communication."""
from __future__ import annotations

# ── Cal voice: veteran sherpa for robot companies ─────────────────────────────
# Wise, abbreviated, in-the-know. Engineer-led teams, PoC → deployment reality.
# Honesty and trust over hype. Draws on deep robotics industry experience.

CAL_INTRO = "Hi — I'm Cal, with Ready For Robots."

CAL_VENDOR_IDENTITY = (
    "I've spent years inside robot deployments — Anybots, Omron, Panasonic, Mitsubishi, Locus Robotics — "
    "and I've seen the same pattern: great hardware, hard PoCs, harder conversions to paying accounts."
)

CAL_VENDOR_SHERPA_LINE = (
    "Most robot companies are engineer-led, not sales-led. I act as a guide through trials and deployments — "
    "honest readouts, no theater."
)

# Plain, honest, first-person. Say what I do and why I'm writing — no slogans.
BUYER_SIGNAL_EXPLANATION = (
    "I help operations teams figure out which robots would actually fit the way they run, "
    "and which ones aren't worth the trouble. A lot of what I do is talk people out of a pilot "
    "that was never going to work."
)

# Quiet credibility — a plain observation about what makes robots pay off, no bravado.
BUYER_ROI_PROOF = (
    "The teams that get real value out of it usually aren't the ones who bought the most impressive "
    "robot. They're the ones who matched a specific machine to the one job that was actually costing "
    "them. When the fit is right, it tends to pay for itself inside a year or two."
)

BUYER_OUTREACH_CTA = (
    "If it's useful, I'm happy to put together a short list of vendors that have actually deployed in "
    "operations like yours — and flag the couple I'd be careful about. No call, no pitch; just reply "
    "and I'll send it over."
)

# Honest closing beat — builds trust rather than performing confidence.
BUYER_CAL_PERSONALITY = (
    "And if I don't think a robot is the right answer for you yet, I'll tell you that too."
)

VENDOR_SIGNAL_EXPLANATION = (
    "We map buyer demand signals and match them to robot capabilities — "
    "the accounts showing real intent, not list noise."
)

CAL_VENDOR_PIPELINE_EXPLANATION = (
    "I've reviewed your robots and specs against what buyers are asking for right now. "
    "The fit isn't always obvious on paper — ROI, proof points, PoC availability, technical support, "
    "and how your team shows up all factor in."
)

CAL_VENDOR_PIPELINE_LOGIC_LINE = (
    "PoCs fail when capabilities don't match buyer requirements. "
    "Deployments happen when positioning, support, and follow-through align."
)

VEGAS_DISTRIBUTION_LINE = (
    "For teams pushing hospitality or West Coast expansion, we also map buyers across Las Vegas — "
    "hotels, casinos, logistics hubs — where robot trials actually get evaluated."
)

CAL_VENDOR_OFFRAMP_LINE = (
    "If the signal is weak or the fit isn't there, I'll say so. "
    "The point is fewer wasted PoCs, not more pipeline noise."
)

CAL_VENDOR_STRATEGY_CALL_CTA = "Worth 15 minutes to walk through the matches?"

CAL_VENDOR_BUYER_MATCH_CTA = "Want me to send the buyer profiles? I'll flag what fits and what doesn't."

# Customer-facing rep voice (robot sales rep → buyer ops). No Ready For Robots branding.
REP_OUTREACH_CTA = "Worth a quick reply if you're the right person to explore this?"


def rep_outreach_signature() -> str:
    return "Best,\n[Your name]"


def buyer_company_hook(name: str, *, industry: str = "your industry") -> str:
    """One grounded, human line about the real problem teams like theirs run into."""
    n = (name or "your team").strip()
    ind = (industry or "your industry").strip().lower()
    if ind in ("logistics", "warehousing"):
        return (
            f"For an operation like {n}, the hard part usually isn't deciding to automate — it's knowing "
            f"which robots still hold up once they're out of a demo and into your real aisles, at your "
            f"real volume. That's the part I can help with."
        )
    if ind in ("hospitality", "hotels", "casinos & gaming"):
        return (
            f"For a property like {n}, it usually comes down to overnight coverage and turnover — where "
            f"service or cleaning robots start earning their keep instead of sitting in the lobby. "
            f"Knowing which ones actually work in a real building is the tricky part."
        )
    if ind in ("healthcare", "medical technology"):
        return (
            f"Teams like {n} tend to look at robots when demand grows faster than they can hire — usually "
            f"internal transport and delivery first, since that's where the hours quietly go. Working out "
            f"which systems fit your floors is where I can help."
        )
    if ind in ("food service", "food processing & manufacturing"):
        return (
            f"In an operation like {n}, it's usually throughput and back-of-house strain that make the "
            f"case — one robot aimed at the real bottleneck, not a shelf of machines you'll never run. "
            f"Picking the right one is the hard part."
        )
    return (
        f"Teams in {industry.strip()} like {n} usually get to robots the same way: one job gets expensive "
        f"or hard to staff, and a focused pilot starts to look smarter than hiring against it. Knowing "
        f"which robot actually fits is where I come in."
    )


def cal_signature() -> str:
    return "— Cal\nReady For Robots"


def max_signature() -> str:
    return "— Max\nReady For Robots"


# ── Trust-first buyer variants ────────────────────────────────────────────────
# Three genuinely different openers — different premises, not reworded twins.
# All are humble and non-presumptuous: Cal names a real reason for writing, admits
# he doesn't know their context, leaves room for "we already tried robots and it
# flopped," and asks with low commitment plus explicit permission to say no.
# Every variant must (a) mention the company name (assembly gate) and (b) end with
# the Cal sign-off (draft-completeness gate).

BUYER_VARIANTS: tuple[str, ...] = ("workflow_first", "what_survives", "bottleneck_first")


def _buyer_sector(industry: str) -> str:
    """Lowercase, parenthetical-stripped sector that reads naturally after "in ...".

    Falls back to a neutral phrase for missing/junk industries so we never emit
    "in Unknown" or "in your industry teams".
    """
    ind = (industry or "").strip()
    # Drop trailing qualifiers like "Food Service (Restaurants)" -> "food service".
    if "(" in ind:
        ind = ind.split("(", 1)[0].strip()
    low = ind.lower()
    if not low or low in (
        "unknown", "general", "general robotics", "other", "n/a", "none", "your industry",
    ):
        return "your line of work"
    return low


# Cal is a vendor-neutral deployment advisor, not a salesperson. Each vertical
# gets: `glam` = the workflow everyone automates first (and over-focuses on),
# `hidden` = where labor hours actually disappear, and `opinion` = one strong,
# memorable, deployment-earned point of view. The voice teaches; it doesn't pitch.
_GENERIC_INSIGHT = {
    "glam": "the most visible task",
    "hidden": "the repetitive back-of-house work — moving material and handling the same exceptions over and over",
    "opinion": "The coolest robot in the room is rarely the one that pays for itself.",
}

_INDUSTRY_INSIGHT: tuple[tuple[tuple[str, ...], dict[str, str]], ...] = (
    (
        ("logistic", "warehous", "supply chain", "fulfil", "distribution", "3pl"),
        {
            "glam": "Picking",
            "hidden": "receiving, replenishment, pallet moves, inventory exceptions, and returns",
            "opinion": "The fastest AMR on the floor is rarely the one that survives real peak volume.",
        },
    ),
    (
        ("hospitality", "hotel", "casino", "gaming", "resort"),
        {
            "glam": "The lobby delivery robot",
            "hidden": "linen runs, housekeeping carts, overnight floor cleaning, and room-service logistics",
            "opinion": "A robot that shines in an empty lobby usually stalls the first busy weekend.",
        },
    ),
    (
        ("health", "medical", "hospital", "clinic", "elder", "senior living"),
        {
            "glam": "The robot that gets posted on LinkedIn",
            "hidden": "moving supplies, meds, lab samples, linen, and waste between floors",
            "opinion": "In a hospital the ROI is almost never the flashy robot — it's the miles staff walk every shift.",
        },
    ),
    (
        ("food", "restaurant", "kitchen", "beverage", "grocery"),
        {
            "glam": "The cooking robot",
            "hidden": "prep, portioning, dishwashing, packaging, and product changeovers",
            "opinion": "Most kitchen automation dies on changeover, not on the cook.",
        },
    ),
    (
        ("manufactur", "industrial", "automotive", "assembly", "factory", "cnc", "metal"),
        {
            "glam": "The six-axis arm on the line",
            "hidden": "machine tending, moving material between cells, and end-of-line packaging",
            "opinion": "A cell that only runs one part number looks great until your mix changes.",
        },
    ),
    (
        ("retail", "store", "e-commerce", "ecommerce", "apparel", "consumer goods"),
        {
            "glam": "The shelf-scanning robot",
            "hidden": "backroom sortation, replenishment, and inventory exceptions",
            "opinion": "A robot that just produces another dashboard rarely changes what staff actually do.",
        },
    ),
)


def _buyer_insight(industry: str) -> dict[str, str]:
    """Return Cal's deployment read for an industry (substring match, generic fallback)."""
    ind = (industry or "").strip()
    if "(" in ind:
        ind = ind.split("(", 1)[0].strip()
    low = ind.lower()
    for keys, insight in _INDUSTRY_INSIGHT:
        if any(k in low for k in keys):
            return insight
    return _GENERIC_INSIGHT


# ── Relationship ladder: teaching follow-ups ──────────────────────────────────
# The follow-up cadence isn't "just bumping this." Each touch teaches ONE thing
# in Cal's advisor voice: a deployment lesson (teach), a market pattern/mistake
# (trend), then an easy, genuine question that invites the buyer's expertise
# (question). No pitch, no AI tells. Company name is added by the wrapper's close
# so every touch clears the assembly gate.
LADDER_TOUCHES: tuple[str, ...] = ("teach", "trend", "question")

_GENERIC_LADDER = {
    "teach_subject": "the workflow most teams automate last",
    "teach": (
        "The projects with the fastest payback rarely start with the most visible task. They start with "
        "the quiet process upstream that backs everything else up — less glamorous, and usually the "
        "easiest place to prove a robot earns its keep.\n\n"
        "Most teams do the opposite: automate the flashy part first, then wonder why the ROI never showed."
    ),
    "trend_subject": 'why "evaluating five robots" is usually the wrong question',
    "trend": (
        "A pattern I see constantly: a team lines up five vendors, runs a bake-off, and picks the fastest. "
        "Six months later it's parked.\n\n"
        "The robots that survive aren't the fastest — they're the ones matched to one specific bottleneck, "
        "with the integration and software actually resourced. Speed is the easiest thing to demo and the "
        "least predictive of ROI."
    ),
    "question_subject": "one question about your operation",
    "question": (
        "No agenda here — one question tells me more than a whole discovery call.\n\n"
        "If you automated one workflow tomorrow, which would it be? Most teams name the busiest one. The "
        "one that actually pays back is usually the process quietly creating work everywhere else."
    ),
}

_LADDER_CONTENT: tuple[tuple[tuple[str, ...], dict[str, str]], ...] = (
    (
        ("logistic", "warehous", "supply chain", "fulfil", "distribution", "3pl"),
        {
            "teach_subject": "the workflow most warehouses automate last",
            "teach": (
                "The warehouses with the fastest payback rarely start at picking. They start at receiving "
                "— a slow dock backs up replenishment, putaway, and every downstream pick, and it's the "
                "easiest place to prove a robot earns its keep.\n\n"
                "Most teams do the opposite: automate the flashy pick line first, then wonder why the ROI "
                "never showed."
            ),
            "trend_subject": 'why "evaluating five robots" is usually the wrong question',
            "trend": (
                "A pattern I see constantly: a team lines up five AMRs, runs a bake-off, and picks the "
                "fastest. Six months later it's parked in a corner.\n\n"
                "The ones that survive aren't the fastest — they're matched to one specific bottleneck, "
                "with integration and software actually resourced. Speed is the easiest spec to demo and "
                "the least predictive of payback."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "No agenda here — one question tells me more than a discovery call.\n\n"
                "If you automated one workflow tomorrow, which would it be? Most teams say picking. The one "
                "that usually pays back is the process quietly creating work everywhere else — receiving, "
                "replenishment, or returns."
            ),
        },
    ),
    (
        ("hospitality", "hotel", "casino", "gaming", "resort"),
        {
            "teach_subject": "the automation most hotels overlook",
            "teach": (
                "The properties that get real value from robots rarely start in the lobby. They start with "
                "the runs nobody sees — linen, housekeeping carts, and overnight floor cleaning — because "
                "that's where the labor hours and turnover actually pile up.\n\n"
                "The lobby delivery robot photographs well and moves the needle least."
            ),
            "trend_subject": "the robot that demos well and stalls by the weekend",
            "trend": (
                "A pattern worth knowing: the service robot that glides across an empty showroom floor "
                "often stalls the first busy Saturday — crowded elevators, guests, tight corridors.\n\n"
                "The ones that last are chosen for how they handle a full building on a bad day, not how "
                "they look in the demo."
            ),
            "question_subject": "one question about your property",
            "question": (
                "No agenda here — one question tells me more than a tour.\n\n"
                "If you automated one task across your property tomorrow, which would it be? Most teams say "
                "delivery. The one that usually pays back is the repetitive run quietly eating overnight "
                "hours — linen, cleaning, or room service."
            ),
        },
    ),
    (
        ("health", "medical", "hospital", "clinic", "elder", "senior living"),
        {
            "teach_subject": "where hospital automation actually pays back",
            "teach": (
                "In most hospitals the ROI isn't the robot that makes the news. It's the miles clinical "
                "staff walk every shift — moving supplies, meds, samples, linen, and waste between "
                "floors.\n\n"
                "Automate that transport and you give nurses time back. Chase the flashy robot and you "
                "usually get a press release, not payback."
            ),
            "trend_subject": "the part of a robot pilot everyone underestimates",
            "trend": (
                "A mistake I see often in healthcare: teams evaluate the robot and skip the integration — "
                "elevators, badge access, EVS workflow, EHR hooks.\n\n"
                "That's the part that decides whether a transport robot actually runs or sits charging. "
                "The hardware is rarely the reason a pilot stalls."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "No agenda here — one question tells me more than a long call.\n\n"
                "If you automated one workflow tomorrow, which would it be? Most teams name a clinical task. "
                "The one that usually pays back first is the internal transport quietly pulling staff away "
                "from patients."
            ),
        },
    ),
    (
        ("food", "restaurant", "kitchen", "beverage", "grocery"),
        {
            "teach_subject": "where kitchen automation usually breaks",
            "teach": (
                "Most kitchen automation doesn't fail on the cook — it fails on changeover. A cell that "
                "runs one product beautifully falls apart when the menu shifts three times a day.\n\n"
                "The deployments that last are built around prep, portioning, and fast changeovers, not the "
                "one hero task that films well."
            ),
            "trend_subject": "the robot that looks great and never scales",
            "trend": (
                "A pattern I see in food operations: the cooking robot demos beautifully, then can't keep "
                "up with real throughput or sanitation between products.\n\n"
                "The ones that earn their spot handle the repetitive, food-safe work — portioning, tray "
                "loading, packaging — and flex across products without a teardown."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "No agenda here — one question tells me more than a walkthrough.\n\n"
                "If you automated one station tomorrow, which would it be? Most teams point at the cook "
                "line. The one that usually pays back is the high-turnover station you can never keep "
                "staffed — prep, portioning, or dish."
            ),
        },
    ),
    (
        ("manufactur", "industrial", "automotive", "assembly", "factory", "cnc", "metal"),
        {
            "teach_subject": "the automation that survives a mix change",
            "teach": (
                "On most lines the value isn't the six-axis arm everyone photographs. It's the unglamorous "
                "work between cells — machine tending, material movement, and end-of-line packaging — where "
                "labor quietly goes.\n\n"
                "And a cell that only runs one part number looks great until your product mix changes."
            ),
            "trend_subject": "why the flexible robot beats the fast one",
            "trend": (
                "A pattern worth knowing: teams buy for peak speed on one part, then get burned when the "
                "mix shifts and the cell can't flex.\n\n"
                "The deployments that last are chosen for changeover and reconfiguration, not top-end cycle "
                "time. In high-mix work, flexibility pays back longer than speed."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "No agenda here — one question tells me more than a plant tour.\n\n"
                "If you automated one job tomorrow, which would it be? Most teams name the bottleneck cell. "
                "The one that usually pays back is the repetitive tending and material movement nobody "
                "wants."
            ),
        },
    ),
    (
        ("retail", "store", "e-commerce", "ecommerce", "apparel", "consumer goods"),
        {
            "teach_subject": "the retail robot that changes nothing",
            "teach": (
                "A hard truth: a shelf-scanning robot that just produces another dashboard rarely changes "
                "what staff actually do. The value shows up when automation touches the work behind the "
                "shelf — backroom sortation, replenishment, and inventory exceptions.\n\n"
                "Data is easy. Changing the labor is the part that pays back."
            ),
            "trend_subject": "why inventory robots stall after the pilot",
            "trend": (
                "A pattern I see in retail: the inventory robot nails accuracy in the pilot, then nothing "
                "changes because no workflow was rebuilt around the data.\n\n"
                "The deployments that last close the loop — the scan triggers replenishment or a task, not "
                "just a report. Otherwise it's a very expensive dashboard."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "No agenda here — one question tells me more than a call.\n\n"
                "If you automated one workflow tomorrow, which would it be? Most teams say shelf scanning. "
                "The one that usually pays back is the backroom labor behind it — sortation, replenishment, "
                "exceptions."
            ),
        },
    ),
)


def _ladder_content(industry: str) -> dict[str, str]:
    """Return the teaching content for an industry (substring match, generic fallback)."""
    ind = (industry or "").strip()
    if "(" in ind:
        ind = ind.split("(", 1)[0].strip()
    low = ind.lower()
    for keys, content in _LADDER_CONTENT:
        if any(k in low for k in keys):
            return content
    return _GENERIC_LADDER


def ladder_touch_subject(touch: str, name: str, industry: str) -> str:
    """Insight-led subject for a follow-up touch (teach / trend / question)."""
    content = _ladder_content(industry)
    key = f"{touch}_subject"
    return content.get(key, _GENERIC_LADDER.get(key, "a quick note"))


def build_ladder_touch_body(touch: str, name: str, industry: str) -> str:
    """Assemble a teaching follow-up body. Each touch teaches one thing and ends
    with a company-named close (assembly gate) plus Cal's sign-off."""
    n = (name or "your team").strip()
    content = _ladder_content(industry)
    core = content.get(touch, _GENERIC_LADDER.get(touch, ""))
    if touch == "teach":
        close = f"If {n} ever maps this out, that's where I'd start."
    elif touch == "trend":
        close = f"If {n} is weighing vendors, I'm glad to share what separates the ones that last. No pitch."
    else:  # question
        close = f"Curious what you'd pick for {n} — no wrong answer, and no agenda on my end."
    return "\n".join(["Hi,", "", core, "", close, "", cal_signature()])


def pick_buyer_variant(company_id, *, allowed=None) -> str:
    """Deterministic round-robin so a company's draft and send agree on the angle."""
    pool = [v for v in (allowed or BUYER_VARIANTS) if v in BUYER_VARIANTS]
    if not pool:
        pool = list(BUYER_VARIANTS)
    try:
        idx = int(company_id or 0) % len(pool)
    except (TypeError, ValueError):
        idx = 0
    return pool[idx]


def resolve_buyer_variant(company, acct=None) -> str | None:
    """The angle a send should be tagged with.

    Prefers the variant stashed at draft time (``crm_metadata['cal_variant_id']``)
    so the tag matches the copy that actually shipped; otherwise falls back to the
    deterministic round-robin. Returns ``None`` for vendors / StageGate accounts,
    which don't use the trust-first buyer angles.
    """
    account_type = getattr(acct, "account_type", None)
    if account_type and account_type != "buyer":
        return None
    meta = getattr(company, "crm_metadata", None) or {}
    if meta.get("outreach_pipeline") == "stagegate":
        return None
    stored = meta.get("cal_variant_id")
    if stored in BUYER_VARIANTS:
        return stored
    return pick_buyer_variant(getattr(company, "id", None))


def _variant_workflow_first(name: str, industry: str) -> str:
    """Flagship teach: most projects automate the wrong workflow first."""
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        "Hi,",
        "",
        "I spend my days looking at where robot deployments actually work — and where they quietly fall apart.",
        "",
        f"One pattern keeps showing up in {sector}.",
        "",
        "Most projects don't struggle because the robot can't do the job. They struggle because the wrong "
        "workflow got automated first.",
        "",
        f"{ins['glam']} gets all the attention. Meanwhile {ins['hidden']} quietly consume thousands of "
        f"labor hours a month. That's usually where I'd start with {name}.",
        "",
        "Ready For Robots isn't tied to any manufacturer. We spend our time working out where automation "
        "creates real ROI — and, just as often, where the answer is \"not yet.\"",
        "",
        f"If robotics is on the roadmap at {name} this year, I'll share what we're seeing across the "
        "market. No presentation, just a practical conversation.",
        "",
        cal_signature(),
    ])


def _variant_what_survives(name: str, industry: str) -> str:
    """Pattern-recognition teach: which deployments are still running at 6 months."""
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        "Hi,",
        "",
        "Part of my job surprises people: I don't track which robots demo well. I track which ones are "
        "still running six months after install.",
        "",
        f"In {sector}, that list is shorter than the sales decks suggest.",
        "",
        ins["opinion"],
        "",
        "What decides it usually isn't the hardware — it's integration, the software layer, and whether the "
        "robot was aimed at the right job in the first place. We're vendor-neutral, so I care about fit, not "
        "about moving any particular box. Sometimes the right call is \"not yet.\"",
        "",
        f"If {name} is weighing robotics this year, I'll tell you what's actually holding up in the field — "
        "and what I'd stay away from. No pitch.",
        "",
        cal_signature(),
    ])


def _variant_bottleneck_first(name: str, industry: str) -> str:
    """Opinionated + curious: start with the bottleneck, not the robot."""
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        "Hi,",
        "",
        f"A question I'd ask before {name} looks at a single robot: which job is actually eating your hours "
        "right now?",
        "",
        f"Most teams start with the coolest machine. I start with the bottleneck — because in {sector} the "
        f"hours usually disappear into {ins['hidden'].lower()}, not {ins['glam'].lower()}.",
        "",
        ins["opinion"],
        "",
        "I'm not tied to any manufacturer. My job is helping teams avoid buying the wrong robot — and "
        "sometimes that means \"not yet.\"",
        "",
        "If it's worth a short exchange, tell me where the hours go and I'll tell you whether a robot is "
        "even the right answer.",
        "",
        cal_signature(),
    ])


def build_buyer_variant_body(name: str, industry: str, variant_id: str) -> str:
    """Assemble the full buyer email body for a given advisor angle."""
    n = (name or "your team").strip()
    builders = {
        "workflow_first": _variant_workflow_first,
        "what_survives": _variant_what_survives,
        "bottleneck_first": _variant_bottleneck_first,
    }
    fn = builders.get(variant_id, _variant_workflow_first)
    return fn(n, industry or "your industry")


def buyer_variant_subject(name: str, industry: str, variant_id: str) -> str:
    """Insight-led subject — a topic Cal is about to teach, not a pitch."""
    sector = _buyer_sector(industry)
    generic_sector = sector == "your line of work"
    if variant_id == "what_survives":
        return (
            "the robots still running six months in"
            if generic_sector
            else f"the {sector} robots still running six months in"
        )
    if variant_id == "bottleneck_first":
        return "start with the bottleneck, not the robot"
    # workflow_first (default)
    return (
        "where automation projects usually go sideways"
        if generic_sector
        else f"where {sector} automation usually goes sideways"
    )


def cal_opening(*, audience: str = "buyer") -> str:
    explanation = VENDOR_SIGNAL_EXPLANATION if audience == "vendor" else BUYER_SIGNAL_EXPLANATION
    return f"{CAL_INTRO}\n\n{explanation}"


def cal_vendor_opening() -> str:
    return (
        f"{CAL_INTRO}\n\n"
        f"{CAL_VENDOR_IDENTITY}\n\n"
        f"{CAL_VENDOR_SHERPA_LINE}\n\n"
        f"{VENDOR_SIGNAL_EXPLANATION}"
    )


def cal_vendor_match_paragraph(company_name: str, *, industry: str = "your space") -> str:
    """Core vendor outreach block — opportunities + PoC realism."""
    name = (company_name or "your team").strip()
    ind = (industry or "your space").strip()
    return (
        f"I've looked at {name}'s robots against active buyer signals in {ind}. "
        f"A few opportunities align with your capabilities — not generic leads, accounts with timing behind them.\n\n"
        f"{CAL_VENDOR_PIPELINE_LOGIC_LINE}"
    )
