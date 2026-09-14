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
    email: "karen.mcguigan@aimbridgehospitality.com",
    confidence: 85,
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

  const subject = `Automation Feasibility Assessment for ${company}`;
  const body = `Dear ${name},

Nice to meet you. I'm reaching out directly regarding ${company}'s operational footprint and current front-line staffing demands across your locations.

As peak operational load rises, operators are increasingly turning to ${robotCategories} to handle repetitive physical movement and facility tasks. This allows on-site teams to focus entirely on core operations while eliminating 30–40% of physical transport strain.

ReadyForRobots provides vendor-neutral automation feasibility assessments comparing the leading commercial robotics platforms. We evaluate payload, battery cycle times, floor navigation, and net ROI before capital is committed. I have attached our Humanoid Report for review. More information available here: https://readyforrobots.com/robot-ready

My own background—> I led robotics at Panasonic and built 3 robot companies.

Would you be open to a brief 10-minute introduction this week to review our comparative benchmarking report for your automation roadmap?

Best regards,
Bob

Bob Christopher
President
ReadyForRobots
bob@readyforrobots.com`;

  return { subject, body };
}

export default function AdminTopLeadsPanel() {
  const [leads, setLeads] = useState<TopLeadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | number | null>(null);

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
    const companyKey = lead.company_name.toLowerCase().trim();
    const hunterMatch = HUNTER_EXECUTIVE_MAP[companyKey];
    const decisionMakers = lead.hermes_decision_makers || [];
    const dmName = hunterMatch?.name || decisionMakers[0]?.name;
    const emailData = buildBobExecutiveEmail({
      companyName: lead.company_name,
      dmName,
      robotTypes: lead.robot_types_needed,
    });
    const fullText = `Subject: ${emailData.subject}\n\nTo: ${hunterMatch?.email || lead.inferred_contact_email || ""}\n\n${emailData.body}`;
    void navigator.clipboard.writeText(fullText);
    setCopiedId(lead.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <section
      id="admin-top-leads"
      className="mb-8 rounded-2xl border border-emerald-500/30 bg-[#081329] p-6 text-slate-100 shadow-2xl backdrop-blur-md"
    >
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/20 px-2.5 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/40">
              <ShieldAlert className="h-3.5 w-3.5" />
              ADMIN ONLY
            </span>
            <h2 className="text-xl font-bold tracking-tight text-white">
              Top 10 High-Priority Customer Automation Projects
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Exclusive Hermes pipeline intelligence, verified decision-makers,
            and direct phone/email contact triggers for executive outreach.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void fetchTopLeads()}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl border border-emerald-500/40 bg-emerald-950/40 px-3.5 py-2 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-900/60 hover:text-white disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Refreshing..." : "Refresh Top 10"}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-950/40 p-3 text-xs text-rose-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-3 sm:grid-cols-1 lg:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-36 animate-pulse rounded-xl border border-slate-800 bg-slate-900/50 p-4"
            />
          ))}
        </div>
      ) : leads.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-8 text-center text-sm text-slate-400">
          No high-priority leads currently returned. Check server connection.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
          {leads.map((lead, idx) => {
            const rank = idx + 1;
            const score = lead.priority_score ?? 100;
            const companyKey = lead.company_name.toLowerCase().trim();
            const hunterMatch = HUNTER_EXECUTIVE_MAP[companyKey];

            const decisionMakers = lead.hermes_decision_makers || [];
            const primaryDm = decisionMakers[0];

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

            return (
              <div
                key={lead.id || idx}
                className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0d1836] p-4 transition hover:border-emerald-500/50 hover:bg-[#101e42] shadow-md"
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
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-emerald-300"
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
                          className="rounded-md bg-slate-800/80 px-2 py-0.5 text-[10px] font-semibold text-slate-300 border border-slate-700/60"
                        >
                          {rt}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Decision Maker & Contact Info */}
                  <div className="mt-3 space-y-1.5 rounded-lg bg-slate-900/60 p-2.5 text-xs text-slate-300 border border-slate-800">
                    <div className="flex items-center gap-1.5 font-medium text-emerald-300">
                      <UserCheck className="h-3.5 w-3.5 text-emerald-400" />
                      <span>{dmText}</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
                      <a
                        href={`mailto:${email}`}
                        className="inline-flex items-center gap-1 font-mono text-emerald-400 hover:underline"
                      >
                        <Mail className="h-3 w-3" />
                        {email}
                      </a>

                      {phone && (
                        <a
                          href={`tel:${phone}`}
                          className="inline-flex items-center gap-1 font-mono text-sky-400 hover:underline"
                        >
                          <Phone className="h-3 w-3" />
                          {phone}
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Why Now Rationale */}
                  <p className="mt-3 text-[11px] leading-relaxed text-slate-300 line-clamp-2">
                    <strong className="text-emerald-400">Why Now: </strong>
                    {whyNow}
                  </p>
                </div>

                {/* Actions Footer */}
                <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3">
                  <button
                    type="button"
                    onClick={() => copyPitch(lead)}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white"
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
                    {(() => {
                      const emailData = buildBobExecutiveEmail({
                        companyName: lead.company_name,
                        dmName,
                        robotTypes: lead.robot_types_needed,
                      });
                      return (
                        <a
                          href={`mailto:${email}?subject=${encodeURIComponent(
                            emailData.subject
                          )}&body=${encodeURIComponent(emailData.body)}`}
                          className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 border border-emerald-500 px-3 py-1 text-[11px] font-semibold text-white hover:bg-emerald-500 transition shadow-sm"
                        >
                          <Mail className="h-3 w-3" />
                          Email Lead
                        </a>
                      );
                    })()}
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
