import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { cleanAndClampText } from "@/lib/text";

type SupplyCompany = {
  robot_company: {
    id: number;
    company_name: string;
    robot_type?: string | null;
    target_market?: string | null;
    website?: string | null;
    contact_email?: string | null;
    lead_score?: number | null;
    vendor_list_score?: number | null;
  };
  contact_strategy: {
    primary?: { role?: string; contact?: string | null };
    research_notes?: string[];
  };
  lead_matches: Array<{
    id: number;
    company_name: string;
    industry?: string | null;
    score?: number;
    signal?: string | null;
    why_match?: string | null;
  }>;
  email: { subject: string; body: string };
  cta: { signup: string; meeting: string };
};

export default function SupplyPipeline() {
  const [rows, setRows] = useState<SupplyCompany[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const response = await fetch(`${getApiBase()}/api/robot-companies/agent/supply-side?limit=12`, liveFetchInit());
        if (!response.ok) throw new Error(await response.text());
        const payload = await response.json();
        const companies = Array.isArray(payload.companies) ? payload.companies : [];
        setRows(companies);
        setSelectedId(companies[0]?.robot_company?.id ?? null);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Could not load supply pipeline");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const selected = rows.find((row) => row.robot_company.id === selectedId) ?? rows[0];

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 px-4 pb-12 pt-24">
        <div className="mx-auto max-w-6xl">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
            Marketplace supply pipeline
          </p>
          <h1 className="text-2xl font-black text-white" style={{ fontFamily: "'Sora', system-ui" }}>
            Robot company outreach agent
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/45">
            SCOUT researches robot companies, identifies who to contact, shows three matched buyer leads, and drafts a signup plus meeting email for review.
          </p>
          {err && <p className="mt-4 rounded-lg border border-red-500/30 p-3 text-sm text-red-200">{err}</p>}

          <div className="mt-6 grid gap-4 lg:grid-cols-[360px_1fr]">
            <aside className="rounded-2xl border border-white/10 bg-white/[0.025]">
              <div className="border-b border-white/8 px-4 py-3">
                <p className="text-xs font-bold text-white/75">{loading ? "Loading..." : `${rows.length} robot companies`}</p>
                <p className="mt-1 text-[11px] text-white/35">Review only. No emails send automatically.</p>
              </div>
              <div className="max-h-[680px] overflow-y-auto p-2">
                {rows.map((row) => {
                  const company = row.robot_company;
                  const active = company.id === selected?.robot_company.id;
                  return (
                    <button
                      key={company.id}
                      type="button"
                      onClick={() => setSelectedId(company.id)}
                      className="mb-2 w-full rounded-xl border px-3 py-2.5 text-left"
                      style={active ? { borderColor: "rgba(255,176,0,0.45)", background: "rgba(255,176,0,0.08)" } : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-sm font-bold text-white/85">{company.company_name}</p>
                        <span className="font-mono text-[11px]" style={{ color: "#FFB000" }}>
                          {Math.round(company.vendor_list_score ?? company.lead_score ?? 0)}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-[11px] text-white/35">
                        {company.robot_type || "robotics"} · {company.target_market || "market TBD"}
                      </p>
                    </button>
                  );
                })}
              </div>
            </aside>

            {selected && (
              <section className="grid gap-4">
                <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <h2 className="text-xl font-black text-white">{selected.robot_company.company_name}</h2>
                      <p className="mt-1 text-sm text-white/42">
                        {selected.robot_company.robot_type || "Robotics"} for {selected.robot_company.target_market || "target market review"}
                      </p>
                    </div>
                    {selected.robot_company.website && (
                      <a href={selected.robot_company.website} target="_blank" rel="noreferrer" className="text-xs font-bold text-amber-300 underline">
                        Website
                      </a>
                    )}
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
                      <p className="text-[10px] uppercase tracking-widest text-white/30">Who to contact</p>
                      <p className="mt-1 text-sm font-bold text-white/80">{selected.contact_strategy.primary?.role || "Partnerships"}</p>
                      <p className="mt-1 break-all text-xs text-white/45">{selected.contact_strategy.primary?.contact || selected.robot_company.contact_email || "Research contact first"}</p>
                    </div>
                    <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3 md:col-span-2">
                      <p className="text-[10px] uppercase tracking-widest text-white/30">Research checklist</p>
                      <p className="mt-1 text-xs leading-relaxed text-white/45">
                        {(selected.contact_strategy.research_notes || []).join(" ")}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
                  <p className="text-[10px] uppercase tracking-widest text-white/30">3 buyer lead matches for email</p>
                  <div className="mt-3 grid gap-3 md:grid-cols-3">
                    {selected.lead_matches.slice(0, 3).map((lead) => (
                      <div key={lead.id} className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="truncate text-sm font-bold text-white/82">{lead.company_name}</p>
                          <span className="font-mono text-[10px] text-emerald-300">{Math.round(lead.score || 0)}</span>
                        </div>
                        <p className="mt-1 text-[11px] text-white/35">{lead.industry || "industry unknown"}</p>
                        <p className="mt-2 text-[11px] leading-relaxed text-white/48">{cleanAndClampText(lead.why_match, 150)}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-[10px] uppercase tracking-widest text-white/30">Draft email for review</p>
                    <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-2 py-1 text-[10px] font-bold text-amber-100">
                      Review before send
                    </span>
                  </div>
                  <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 p-3">
                    <p className="text-[10px] uppercase tracking-widest text-white/30">Subject</p>
                    <p className="mt-1 text-sm font-bold text-amber-100">{selected.email.subject}</p>
                  </div>
                  <pre className="mt-3 whitespace-pre-wrap rounded-xl border border-white/8 bg-black/15 p-4 font-sans text-sm leading-relaxed text-white/68">
                    {selected.email.body}
                  </pre>
                  <div className="mt-4 grid gap-2 md:grid-cols-2">
                    <p className="rounded-xl border border-white/8 bg-white/[0.025] p-3 text-xs text-white/45">{selected.cta.signup}</p>
                    <p className="rounded-xl border border-white/8 bg-white/[0.025] p-3 text-xs text-white/45">{selected.cta.meeting}</p>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
