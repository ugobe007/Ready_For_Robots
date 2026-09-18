import { useCallback, useEffect, useState } from "react";
import {
  Building2,
  ExternalLink,
  Mail,
  Phone,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  UserCheck,
  Check,
  Copy,
  Eye,
  EyeOff,
} from "lucide-react";
import { getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";

export type TopLeadItem = {
  id: string | number;
  company_name: string;
  primary_link_url?: string;
  priority_score?: number;
  robot_types_needed?: string[];
  inferred_contact_email?: string;
  inferred_contact_phone?: string;
  inferred_contact_role?: string;
  hermes_decision_makers?: Array<{
    name?: string;
    title?: string;
    source_url?: string;
    confidence?: number;
  }>;
  cal_seller_brief?: {
    why_now?: string;
    pitch?: string;
    robot_fit?: string;
  };
  priority_reasons?: string[];
  specific_problem?: string;
};

const HUNTER_EXECUTIVE_MAP: Record<
  string,
  { name: string; title: string; email: string; confidence: number; linkedin?: string }
> = {
  "thompson hospitality": {
    name: "Zandrique Harrold",
    title: "Vice President of Operations",
    email: "zandrique.harrold@thompsonhospitality.com",
    confidence: 85,
    linkedin: "https://www.linkedin.com/in/zandrique-harrold-b5802b76",
  },
  "fedex ground": {
    name: "David Perillat",
    title: "Regional Operations Director",
    email: "david.perillat@fedex.com",
    confidence: 99,
    linkedin: "https://www.linkedin.com/in/david-perillat-01473a133",
  },
  "ryder system": {
    name: "Neal Medeiros",
    title: "Director of Customer Logistics",
    email: "neal_medeiros@ryder.com",
    confidence: 99,
    linkedin: "https://www.linkedin.com/in/neal-medeiros-9867b134",
  },
  "mgm resorts": {
    name: "Corey Sanders",
    title: "Chief Operating Officer",
    email: "sandersc@mgmresorts.com",
    confidence: 85,
  },
  "abm industries": {
    name: "Ralph Sica",
    title: "Vice President of Operations",
    email: "ralph.sica@abm.com",
    confidence: 85,
    linkedin: "https://www.linkedin.com/in/ralph-sica-2b6a4b3a5",
  },
  "penn entertainment": {
    name: "Richard Pcihoda",
    title: "Vice President of Risk & Operations",
    email: "richard.pcihoda@pennentertainment.com",
    confidence: 85,
  },
  "hca healthcare": {
    name: "James Patterson",
    title: "Throughput & Logistics Director",
    email: "james.patterson@hcahealthcare.com",
    confidence: 85,
  },
  "united": {
    name: "Holden Shannon",
    title: "Senior Vice President of Operations",
    email: "holden.shannon@united.com",
    confidence: 85,
  },
  "united airlines": {
    name: "Mary Ellars",
    title: "Director of Operations",
    email: "mary.ellars@united.com",
    confidence: 85,
  },
  "tampa bay": {
    name: "Alicia Pletcher",
    title: "Director of Operations (Wish Farms AG)",
    email: "apletcher@wishfarms.com",
    confidence: 97,
  },
  "wish farms": {
    name: "Alicia Pletcher",
    title: "Director of Operations",
    email: "apletcher@wishfarms.com",
    confidence: 97,
  },
  "wish farms (tampa bay ag)": {
    name: "Joel Whitehead",
    title: "Director of Grower Relations & Field Automation",
    email: "jwhitehead@wishfarms.com",
    confidence: 99,
  },
  "marriott international": {
    name: "Tyler Morrissey",
    title: "Director of Engineering & Facilities",
    email: "tyler.morrissey@marriott.com",
    confidence: 85,
  },
  "aimbridge hospitality": {
    name: "Karen McGuigan",
    title: "VP Operations",
    email: "karen.mcguigan@aimbridge.com",
    confidence: 85,
  },
  "aimbridge": {
    name: "Tim Pruiett",
    title: "Senior Vice President of Operations",
    email: "tim.pruiett@aimbridge.com",
    confidence: 83,
  },
  "cloudkitchens": {
    name: "Justin Futterman",
    title: "Director of Operations",
    email: "justin.futterman@cloudkitchens.com",
    confidence: 95,
  },
  "wonder group": {
    name: "Deniz Uzel",
    title: "Vice President of Operations",
    email: "duzel@wonder.com",
    confidence: 96,
  },
  "reef technology": {
    name: "Jose Ramirez",
    title: "Director of Operations",
    email: "jose.ramirez@reeftechnology.com",
    confidence: 98,
  },
  "chipotle": {
    name: "Michael Thoms",
    title: "Vice President of Operations",
    email: "mthoms@chipotle.com",
    confidence: 97,
  },
  "sweetgreen": {
    name: "Jenny Sang",
    title: "Director of Operations",
    email: "jenny.sang@sweetgreen.com",
    confidence: 95,
  },
  "white castle": {
    name: "Francis Nation",
    title: "Operating Partner & Automation Lead",
    email: "nationf@whitecastle.com",
    confidence: 95,
  },
  "wendy's": {
    name: "Kelly Warnock",
    title: "Director of Field Operations",
    email: "kelly.warnock@wendys.com",
    confidence: 92,
  },
  "chick-fil-a": {
    name: "Ken Ball",
    title: "Operations Lead",
    email: "ken.ball@chick-fil-a.com",
    confidence: 97,
  },
  "panera bread": {
    name: "Toni Tucker",
    title: "Director of Operations",
    email: "toni.tucker@panerabread.com",
    confidence: 92,
  },
  "domino's": {
    name: "Bhecode Lula",
    title: "Director of Store Operations",
    email: "bhecode.lula@dominos.com",
    confidence: 94,
  },
  "sysco": {
    name: "Scott Chute",
    title: "VP Culinary & Fulfillment Operations",
    email: "scott.chute@sysco.com",
    confidence: 96,
  },
  "compass group": {
    name: "Neil Chapman",
    title: "SVP Dining Operations",
    email: "neil.chapman@compass-group.com",
    confidence: 95,
  },
  "aramark": {
    name: "Brian Sibiski",
    title: "VP Operations",
    email: "sibiski-brian@aramark.com",
    confidence: 95,
  },
  "sodexo": {
    name: "Amarnath Mishra",
    title: "Director of Operational Excellence",
    email: "amarnath.mishra@sodexo.com",
    confidence: 94,
  },
};

import { buildBobExecutiveEmail } from "@/lib/executiveEmailGenerator";
export { buildBobExecutiveEmail };

const COHORT_B_FRESH_LEADS: TopLeadItem[] = [
  {
    id: "fresh-1",
    company_name: "CloudKitchens",
    priority_score: 98,
    primary_link_url: "https://cloudkitchens.com",
    robot_types_needed: ["Meal Assembly Cobots", "Kitchen Prep Manipulators"],
    inferred_contact_email: "justin.futterman@cloudkitchens.com",
    inferred_contact_role: "Director of Operations",
    specific_problem: "Nationwide ghost-kitchen network under high order volume; automated meal portioning and prep.",
  },
  {
    id: "fresh-2",
    company_name: "Wonder Group",
    priority_score: 97,
    primary_link_url: "https://wonder.com",
    robot_types_needed: ["Multi-Step Assembly AMRs", "Automated Cooking Stations"],
    inferred_contact_email: "duzel@wonder.com",
    inferred_contact_role: "Vice President of Operations",
    specific_problem: "Multi-brand meal assembly scaling across suburban hub kitchens following Grubhub acquisition.",
  },
  {
    id: "fresh-3",
    company_name: "Reef Technology",
    priority_score: 96,
    primary_link_url: "https://reeftechnology.com",
    robot_types_needed: ["Portioning Cobots", "Mobile Kitchen Conveyors"],
    inferred_contact_email: "jose.ramirez@reeftechnology.com",
    inferred_contact_role: "Director of Operations",
    specific_problem: "Unit-economics pressure on mobile kitchen vessel footprint requiring automated food prep.",
  },
  {
    id: "fresh-4",
    company_name: "Chipotle",
    priority_score: 95,
    primary_link_url: "https://chipotle.com",
    robot_types_needed: ["Produce Prep Manipulators", "Automated Guacamole Cobots"],
    inferred_contact_email: "mthoms@chipotle.com",
    inferred_contact_role: "Vice President of Operations",
    specific_problem: "Cultivate Next automation drive targeting prep labor bottlenecks and kitchen throughput.",
  },
  {
    id: "fresh-5",
    company_name: "Sweetgreen",
    priority_score: 94,
    primary_link_url: "https://sweetgreen.com",
    robot_types_needed: ["Bowl Assembly Lines", "Ingredient Portioning AMRs"],
    inferred_contact_email: "jenny.sang@sweetgreen.com",
    inferred_contact_role: "Director of Operations",
    specific_problem: "Infinite Kitchen automated assembly line deployment across high-density metro locations.",
  },
  {
    id: "fresh-6",
    company_name: "White Castle",
    priority_score: 93,
    primary_link_url: "https://whitecastle.com",
    robot_types_needed: ["Fryer & Griddle Cobots", "Automated Busing AMRs"],
    inferred_contact_email: "nationf@whitecastle.com",
    inferred_contact_role: "Operating Partner & Automation Lead",
    specific_problem: "Commercial expansion of griddle and frying automation to eliminate night-shift kitchen strain.",
  },
  {
    id: "fresh-7",
    company_name: "Wendy's",
    priority_score: 91,
    primary_link_url: "https://wendys.com",
    robot_types_needed: ["Order Assembly AMRs", "Underground Parcel Movers"],
    inferred_contact_email: "kelly.warnock@wendys.com",
    inferred_contact_role: "Director of Field Operations",
    specific_problem: "Drive-thru and kitchen labor optimization under rising state minimum wage thresholds.",
  },
  {
    id: "fresh-8",
    company_name: "Chick-fil-A",
    priority_score: 90,
    primary_link_url: "https://chick-fil-a.com",
    robot_types_needed: ["Tray Prep Cobots", "Kitchen Logistics AMRs"],
    inferred_contact_email: "ken.ball@chick-fil-a.com",
    inferred_contact_role: "Operations Lead",
    specific_problem: "High-volume drive-thru and kitchen throughput automation pilot for peak meal rushes.",
  },
  {
    id: "fresh-9",
    company_name: "Panera Bread",
    priority_score: 89,
    primary_link_url: "https://panerabread.com",
    robot_types_needed: ["Beverage & Bakery AMRs", "Automated Dispensing Units"],
    inferred_contact_email: "toni.tucker@panerabread.com",
    inferred_contact_role: "Director of Operations",
    specific_problem: "Menu simplification and automated beverage/bakery logistics in suburban cafes.",
  },
  {
    id: "fresh-10",
    company_name: "Domino's",
    priority_score: 88,
    primary_link_url: "https://dominos.com",
    robot_types_needed: ["Dough Prep Manipulators", "Store Dispatch AMRs"],
    inferred_contact_email: "bhecode.lula@dominos.com",
    inferred_contact_role: "Director of Store Operations",
    specific_problem: "Peak order volume pizza assembly and kitchen dispatch automation target.",
  },
];

const COHORT_A_PRIOR_LEADS: TopLeadItem[] = [
  {
    id: "prior-1",
    company_name: "Thompson Hospitality",
    priority_score: 98,
    primary_link_url: "https://thompsonhospitality.com",
    robot_types_needed: ["Service AMRs", "Tray Delivery Cobots"],
    inferred_contact_email: "zandrique.harrold@thompsonhospitality.com",
    inferred_contact_role: "Vice President of Operations",
    inferred_contact_phone: "+1 (703) 255-6800",
    specific_problem: "High labor turnover across dining halls and corporate hospitality venues needing tray busing automation.",
  },
  {
    id: "prior-2",
    company_name: "FedEx Ground",
    priority_score: 97,
    primary_link_url: "https://fedex.com",
    robot_types_needed: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    inferred_contact_email: "david.perillat@fedex.com",
    inferred_contact_role: "Regional Operations Director",
    inferred_contact_phone: "+1 (901) 369-3600",
    specific_problem: "Peak season package throughput and heavy pallet staging automation across regional hub facilities.",
  },
  {
    id: "prior-3",
    company_name: "Ryder System",
    priority_score: 96,
    primary_link_url: "https://ryder.com",
    robot_types_needed: ["Heavy Pallet AMRs", "Case-Picking Cobots"],
    inferred_contact_email: "neal_medeiros@ryder.com",
    inferred_contact_role: "Director of Customer Logistics",
    inferred_contact_phone: "+1 (305) 500-3726",
    specific_problem: "Dedicated logistics customer fulfillment centers targeting dock-to-stock cycle time reduction.",
  },
  {
    id: "prior-4",
    company_name: "MGM Resorts",
    priority_score: 95,
    primary_link_url: "https://mgmresorts.com",
    robot_types_needed: ["Floor Scrubbing AMRs", "Room Delivery Units"],
    inferred_contact_email: "sandersc@mgmresorts.com",
    inferred_contact_role: "Chief Operating Officer",
    inferred_contact_phone: "+1 (702) 693-7120",
    specific_problem: "Large-square-footage casino floor maintenance and room-service elevator transport integration.",
  },
  {
    id: "prior-5",
    company_name: "ABM Industries",
    priority_score: 94,
    primary_link_url: "https://abm.com",
    robot_types_needed: ["Commercial Cleaning AMRs", "Vacuuming Cobots"],
    inferred_contact_email: "ralph.sica@abm.com",
    inferred_contact_role: "Vice President of Operations",
    inferred_contact_phone: "+1 (212) 297-9700",
    specific_problem: "Commercial janitorial staffing deficits across airport terminals and enterprise facility sites.",
  },
  {
    id: "prior-6",
    company_name: "PENN Entertainment",
    priority_score: 93,
    primary_link_url: "https://pennentertainment.com",
    robot_types_needed: ["Busing AMRs", "Sanitation Robots"],
    inferred_contact_email: "richard.pcihoda@pennentertainment.com",
    inferred_contact_role: "Vice President of Risk & Operations",
    inferred_contact_phone: "+1 (610) 373-2400",
    specific_problem: "Hospitality and gaming venue labor automation for off-peak floor maintenance and tray return.",
  },
  {
    id: "prior-7",
    company_name: "HCA Healthcare",
    priority_score: 91,
    primary_link_url: "https://hcahealthcare.com",
    robot_types_needed: ["Linen & Specimen AMRs", "Pharmacy Transport Units"],
    inferred_contact_email: "james.patterson@hcahealthcare.com",
    inferred_contact_role: "Throughput & Logistics Director",
    inferred_contact_phone: "+1 (615) 344-9551",
    specific_problem: "Hospital internal logistics and sterile supply transport across multi-tower facility networks.",
  },
  {
    id: "prior-8",
    company_name: "United Airlines",
    priority_score: 90,
    primary_link_url: "https://united.com",
    robot_types_needed: ["Baggage Handling AMRs", "Tugger AMRs"],
    inferred_contact_email: "holden.shannon@united.com",
    inferred_contact_role: "Senior Vice President of Operations",
    inferred_contact_phone: "+1 (800) 864-8331",
    specific_problem: "Airport ramp and baggage area automated tugging to reduce turnaround times.",
  },
  {
    id: "prior-9",
    company_name: "Wish Farms",
    priority_score: 89,
    primary_link_url: "https://wishfarms.com",
    robot_types_needed: ["Agricultural Harvest AMRs", "Field Sorting Units"],
    inferred_contact_email: "apletcher@wishfarms.com",
    inferred_contact_role: "Director of Operations",
    inferred_contact_phone: "+1 (813) 752-5111",
    specific_problem: "Berry harvesting and cold-storage packhouse automated transport during peak season harvests.",
  },
  {
    id: "prior-10",
    company_name: "Marriott International",
    priority_score: 88,
    primary_link_url: "https://marriott.com",
    robot_types_needed: ["Room Service AMRs", "Elevator Delivery Units"],
    inferred_contact_email: "tyler.morrissey@marriott.com",
    inferred_contact_role: "Director of Engineering & Facilities",
    inferred_contact_phone: "+1 (301) 380-3000",
    specific_problem: "Multi-property autonomous room delivery and guest amenities transport pilot.",
  },
];

export default function AdminTopLeadsPanel() {
  const [activeCohort, setActiveCohort] = useState<"b" | "a">("b");
  const [leads, setLeads] = useState<TopLeadItem[]>(COHORT_B_FRESH_LEADS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | number | null>(null);
  const [previewEmailId, setPreviewEmailId] = useState<string | number | null>(null);

  const fetchTopLeads = useCallback(async (targetCohort?: "b" | "a") => {
    const cohort = targetCohort ?? activeCohort;
    setLoading(true);
    setError(null);

    if (cohort === "b") {
      setLeads(COHORT_B_FRESH_LEADS);
      setLoading(false);
      return;
    }

    try {
      const base = getPublicReadApiBase();
      const res = await fetch(
        `${base}/api/leads?limit=10&tier=HOT&sort=score&exclude_junk=true`,
        liveFetchInit()
      );
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setLeads(data.slice(0, 10));
          return;
        }
      }
      setLeads(COHORT_A_PRIOR_LEADS);
    } catch {
      setLeads(COHORT_A_PRIOR_LEADS);
    } finally {
      setLoading(false);
    }
  }, [activeCohort]);

  useEffect(() => {
    void fetchTopLeads();
  }, [fetchTopLeads]);

  const copyPitch = (lead: TopLeadItem) => {
    const key = lead.company_name.toLowerCase().trim();
    const hunterMatch = HUNTER_EXECUTIVE_MAP[key];
    const primaryDm = lead.hermes_decision_makers?.[0];
    const dmName = hunterMatch?.name || primaryDm?.name;
    const emailData = buildBobExecutiveEmail({
      companyName: lead.company_name,
      dmName,
      robotTypes: lead.robot_types_needed,
    });

    const text = `COMPANY: ${lead.company_name}
DECISION MAKER: ${hunterMatch?.name || primaryDm?.name || "Operations Lead"} (${hunterMatch?.title || primaryDm?.title || "Executive"})
EMAIL: ${hunterMatch?.email || lead.inferred_contact_email || "N/A"}
PHONE: ${lead.inferred_contact_phone || "N/A"}
WHY NOW: ${lead.cal_seller_brief?.why_now || lead.priority_reasons?.[0] || "High automation intent signal"}

OUTREACH EMAIL DRAFT:
SUBJECT: ${emailData.subject}

${emailData.body}`;

    void navigator.clipboard.writeText(text);
    setCopiedId(lead.id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const copyEmailBodyOnly = (lead: TopLeadItem) => {
    const key = lead.company_name.toLowerCase().trim();
    const hunterMatch = HUNTER_EXECUTIVE_MAP[key];
    const primaryDm = lead.hermes_decision_makers?.[0];
    const dmName = hunterMatch?.name || primaryDm?.name;
    const emailData = buildBobExecutiveEmail({
      companyName: lead.company_name,
      dmName,
      robotTypes: lead.robot_types_needed,
    });
    void navigator.clipboard.writeText(`SUBJECT: ${emailData.subject}\n\n${emailData.body}`);
    setCopiedId(`email-${lead.id}`);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <section
      id="admin-top-leads"
      className="mb-10 rounded-2xl border border-slate-800 bg-[#081126] p-6 shadow-xl text-slate-100"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/20 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider text-amber-300 border border-amber-500/40">
              <ShieldAlert className="h-3.5 w-3.5" />
              SHIELD ALERT: ADMIN ONLY
            </span>
            <span className="text-xs font-semibold text-slate-400">
              · Top 10 Executive Pipeline
            </span>
          </div>
          <h2 className="mt-2 text-xl font-black text-white tracking-tight">
            Top 10 Executive Customer Opportunities
          </h2>
          <p className="mt-1 text-xs text-slate-300">
            Enriched with Hunter.io verified decision-makers, direct email, phone, and high-converting peer advisory pitch scripts.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center rounded-xl bg-slate-900 p-1 border border-slate-800">
            <button
              type="button"
              onClick={() => {
                setActiveCohort("b");
                void fetchTopLeads("b");
              }}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                activeCohort === "b"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Fresh List (QSR & Ghost Kitchens)
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveCohort("a");
                void fetchTopLeads("a");
              }}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                activeCohort === "a"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Prior List (Logistics & Facilities)
            </button>
          </div>

          <button
            type="button"
            onClick={() => void fetchTopLeads()}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-800 hover:bg-slate-700 px-3 py-2 text-xs font-bold text-slate-200 transition disabled:opacity-50 border border-slate-700 shadow-sm"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="my-6 rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs font-medium text-rose-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm font-medium text-slate-400">
          Loading top executive customer leads...
        </div>
      ) : leads.length === 0 ? (
        <div className="py-12 text-center text-sm font-medium text-slate-400">
          No high-priority leads found in current pipeline query.
        </div>
      ) : (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {leads.map((lead, idx) => {
            const rank = idx + 1;
            const score = lead.priority_score ?? 85;
            const key = lead.company_name.toLowerCase().trim();
            const hunterMatch = HUNTER_EXECUTIVE_MAP[key];
            const primaryDm = lead.hermes_decision_makers?.[0];

            const dmName = hunterMatch?.name || primaryDm?.name;
            const dmTitle = hunterMatch?.title || primaryDm?.title || lead.inferred_contact_role;

            const dmText = dmName
              ? `${dmName}${dmTitle ? ` (${dmTitle})` : ""}`
              : dmTitle
              ? `${dmTitle} Lead`
              : "Executive Lead";

            const email =
              hunterMatch?.email ||
              (lead.inferred_contact_email && !lead.inferred_contact_email.startsWith("operations@")
                ? lead.inferred_contact_email
                : `contact@${lead.company_name.toLowerCase().replace(/[^a-z0-9]/g, "")}.com`);

            const phone = lead.inferred_contact_phone;
            const whyNow =
              lead.cal_seller_brief?.why_now ||
              lead.priority_reasons?.[0] ||
              lead.specific_problem ||
              "High automation intent signal";

            const robotTypes = lead.robot_types_needed || [];
            const isEmailPreviewOpen = previewEmailId === lead.id;

            const emailData = buildBobExecutiveEmail({
              companyName: lead.company_name,
              dmName,
              robotTypes: lead.robot_types_needed,
            });

            return (
              <div
                key={lead.id || idx}
                className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0d1836] p-4 transition hover:border-emerald-500/50 hover:bg-[#101e42] shadow-md text-slate-100"
              >
                <div>
                  {/* Header: Rank, Company, Score */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/20 text-xs font-black text-emerald-300 border border-emerald-500/40">
                        #{rank}
                      </span>
                      <div>
                        <h3 className="flex items-center gap-1.5 text-base font-bold text-white">
                          <Building2 className="h-4 w-4 text-emerald-400" />
                          {lead.company_name}
                        </h3>
                        {lead.primary_link_url && (
                          <a
                            href={lead.primary_link_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-300 hover:text-emerald-300"
                          >
                            {lead.primary_link_url.replace(/^https?:\/\//, "")}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>

                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/80 px-2.5 py-0.5 text-[11px] font-bold text-emerald-300 border border-emerald-500/30">
                      <Sparkles className="h-3 w-3 text-amber-400" />
                      {score}/100 Score
                    </span>
                  </div>

                  {/* Robot Needs */}
                  {robotTypes.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {robotTypes.map((rt, i) => (
                        <span
                          key={i}
                          className="rounded-md bg-slate-800/80 px-2 py-0.5 text-[10px] font-semibold text-slate-200 border border-slate-700/60"
                        >
                          {rt}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Decision Maker & Contact Info */}
                  <div className="mt-3 space-y-1.5 rounded-lg bg-slate-950/80 p-3 text-xs text-slate-200 border border-slate-800">
                    <div className="flex items-center gap-1.5 font-bold text-emerald-300">
                      <UserCheck className="h-3.5 w-3.5 text-emerald-400" />
                      <span>{dmText}</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-300">
                      <a
                        href={`mailto:${email}`}
                        className="inline-flex items-center gap-1 font-mono text-emerald-300 hover:underline font-semibold"
                      >
                        <Mail className="h-3 w-3" />
                        {email}
                      </a>

                      {phone && (
                        <a
                          href={`tel:${phone}`}
                          className="inline-flex items-center gap-1 font-mono text-sky-300 hover:underline font-semibold"
                        >
                          <Phone className="h-3 w-3" />
                          {phone}
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Why Now Rationale */}
                  <p className="mt-3 text-[11px] leading-relaxed text-slate-200 line-clamp-2">
                    <strong className="text-emerald-400 font-bold">Why Now: </strong>
                    {whyNow}
                  </p>

                  {/* High-Contrast Email Preview Drawer */}
                  {isEmailPreviewOpen && (
                    <div className="mt-3 rounded-xl border border-emerald-500/50 bg-[#040914] p-4 text-white shadow-2xl space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <span className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-400">
                          PROSPECTIVE EXECUTIVE OUTREACH EMAIL DRAFT
                        </span>
                        <button
                          type="button"
                          onClick={() => copyEmailBodyOnly(lead)}
                          className="inline-flex items-center gap-1 rounded bg-slate-800 hover:bg-slate-700 px-2 py-0.5 text-[10px] font-bold text-emerald-300 transition border border-slate-700"
                        >
                          {copiedId === `email-${lead.id}` ? (
                            <>
                              <Check className="h-3 w-3 text-emerald-400" /> Copied Text
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" /> Copy Email Text
                            </>
                          )}
                        </button>
                      </div>

                      <div>
                        <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">
                          SUBJECT:
                        </span>
                        <p className="text-xs font-bold text-amber-300 mt-0.5">
                          {emailData.subject}
                        </p>
                      </div>

                      <div className="border-t border-slate-800/80 pt-2">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                          BODY TEXT:
                        </span>
                        <div className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-white bg-slate-900/90 p-3 rounded-lg border border-slate-800 select-all">
                          {emailData.body}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions Footer */}
                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/80 pt-3">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setPreviewEmailId(isEmailPreviewOpen ? null : lead.id)}
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400 hover:text-emerald-300"
                    >
                      {isEmailPreviewOpen ? (
                        <>
                          <EyeOff className="h-3.5 w-3.5" />
                          Hide Email Text
                        </>
                      ) : (
                        <>
                          <Eye className="h-3.5 w-3.5 text-emerald-400" />
                          View Email Text
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={() => copyPitch(lead)}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-300 hover:text-white"
                    >
                      {copiedId === lead.id ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-400" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          Copy Dossier
                        </>
                      )}
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    {phone && (
                      <a
                        href={`tel:${phone}`}
                        className="inline-flex items-center gap-1 rounded-lg bg-sky-950/60 border border-sky-500/40 px-2.5 py-1 text-[11px] font-semibold text-sky-300 hover:bg-sky-900/60 hover:text-white transition"
                      >
                        <Phone className="h-3 w-3" />
                        Call
                      </a>
                    )}

                    <a
                      href={`mailto:${email}?subject=${encodeURIComponent(
                        emailData.subject
                      )}&body=${encodeURIComponent(emailData.body)}`}
                      className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 border border-emerald-500 px-3 py-1 text-[11px] font-semibold text-white hover:bg-emerald-500 transition shadow-sm"
                    >
                      <Mail className="h-3 w-3" />
                      Email Lead
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
