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
  "harvard maintenance": {
    name: "Max Lapierre",
    title: "Director of Facilities & Maintenance",
    email: "max.lapierre@abm.com",
    confidence: 85,
  },
  "diversified maintenance systems": {
    name: "Ralph Sica",
    title: "VP Operations & Facility Management",
    email: "ralph.sica@abm.com",
    confidence: 85,
  },
};

export function buildBobExecutiveEmail(opts: {
  companyName: string;
  dmName?: string;
  robotTypes?: string[];
}): { subject: string; body: string } {
  const name = opts.dmName ? opts.dmName.split(" ")[0] : "there";
  const company = opts.companyName;
  const robotCategories =
    (opts.robotTypes || []).slice(0, 2).join(" and ") ||
    "collaborative service robots and mobile manipulators";

  const subject = `Robotics feasibility at ${company}?`;
  const body = `Dear ${name},

I’m reaching out with a simple question regarding ${company}’s operational roadmap: Are you currently evaluating collaborative service robots or AMRs for your facilities this year?

Having spent years in commercial robotics—leading teams at Panasonic and building 3 robot companies—I founded ReadyForRobots to help enterprise operators navigate a complex market: customer interest in automation is high, but vendor claims on payload, floor navigation, and net ROI vary wildly.

We publish independent, vendor-neutral feasibility benchmarks comparing leading commercial platforms (${robotCategories}) across duty cycles, integration friction, and real-world payback targets.

If you’re currently looking into automation options or planning for upcoming peak operational loads, I’d be glad to share our latest 2-page benchmark report.

Either way, I’d be curious to hear where you see the biggest operational bottlenecks across your facilities right now.

Best regards,

Bob

Bob Christopher
President | ReadyForRobots
bob@readyforrobots.com
https://readyforrobots.com/robot-ready`;

  return { subject, body };
}

export default function AdminTopLeadsPanel() {
  const [leads, setLeads] = useState<TopLeadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | number | null>(null);
  const [previewEmailId, setPreviewEmailId] = useState<string | number | null>(null);

  const fetchTopLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const base = getPublicReadApiBase();
      const res = await fetch(
        `${base}/api/leads?limit=10&tier=HOT&sort=score&exclude_junk=true`,
        liveFetchInit()
      );
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Failed to load admin leads.`);
      }
      const data = await res.json();
      setLeads(Array.isArray(data) ? data.slice(0, 10) : []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to retrieve top leads."
      );
    } finally {
      setLoading(false);
    }
  }, []);

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

        <button
          type="button"
          onClick={() => void fetchTopLeads()}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600/90 hover:bg-emerald-500 px-4 py-2 text-xs font-bold text-white transition disabled:opacity-50 shadow-md"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Pipeline
        </button>
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
