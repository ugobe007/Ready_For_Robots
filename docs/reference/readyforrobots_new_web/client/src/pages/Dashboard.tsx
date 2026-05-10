import SiteShell from "@/components/SiteShell";
import { LEADS_PUBLIC_FETCH_LIMIT } from "@/lib/leadsApiConstants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import LeadDetailPanel from "@/components/leads/LeadDetailPanel";
import SignupLeadsBlur from "@/components/leads/SignupLeadsBlur";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import type { LeadRow, LeadSignal } from "@/lib/leadTypes";
import { scoreNum, signalDisplayExcerpt } from "@/lib/leadTypes";
import { cn } from "@/lib/utils";
import { ArrowRight, RefreshCw, Search } from "lucide-react";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "wouter";

type PipelineSummary = {
  total?: number;
  hot?: number;
  warm?: number;
  cold?: number;
  junk_filtered?: number;
  total_signals?: number;
  signals_in_database?: number;
  companies_in_database?: number;
  summary_tier_slice_size?: number;
  leads_list_max_per_request?: number;
};

const EMERALD = "oklch(0.527 0.154 162.5)";

/** Coerce API summary numbers (handles stringified JSON or stale caches). */
function summaryNum(v: unknown): number | undefined {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
  return undefined;
}

function tierBadgeVariant(_tier: string | undefined): "default" | "secondary" | "outline" | "destructive" {
  return "outline";
}

function tierBadgeClass(tier: string | undefined): string {
  if (tier === "HOT") return "border-orange-400 text-orange-950 bg-orange-50 shrink-0 text-xs font-semibold";
  if (tier === "WARM") return "border-sky-400 text-sky-950 bg-sky-50 shrink-0 text-xs font-semibold";
  return "border-gray-400 text-gray-900 bg-gray-50 shrink-0 text-xs font-semibold";
}

function groupLeadsByIndustry(leads: LeadRow[]): Record<string, LeadRow[]> {
  const m: Record<string, LeadRow[]> = {};
  for (const l of leads) {
    const k = (l.industry || "Other").trim() || "Other";
    if (!m[k]) m[k] = [];
    m[k].push(l);
  }
  for (const arr of Object.values(m)) {
    arr.sort((a, b) => scoreNum(b, "overall_score") - scoreNum(a, "overall_score"));
  }
  return m;
}

function industryKeysSorted(grouped: Record<string, LeadRow[]>): string[] {
  return Object.keys(grouped).sort((a, b) => grouped[b].length - grouped[a].length);
}

function formatLocation(lead: LeadRow): string {
  const city = (lead.location_city || "").trim();
  const st = (lead.location_state || "").trim();
  if (city && st) return `${city}, ${st}`;
  if (st) return st;
  if (city) return city;
  return "Location TBD";
}

function formatEmployees(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n) || n <= 0) return "Size unknown";
  if (n >= 50_000) return "50,000+ employees";
  if (n >= 10_000) return "10,000+ employees";
  if (n >= 5_000) return "5,000–10,000 employees";
  if (n >= 1_000) return "1,000–5,000 employees";
  if (n >= 500) return "500–1,000 employees";
  if (n >= 200) return "200–500 employees";
  return "Under 200 employees";
}

function signalBullet(s: LeadSignal): string {
  const t = signalDisplayExcerpt(s);
  if (t.length > 72) return t.slice(0, 69) + "…";
  if (t) return t;
  const lab = s.signal_label || s.signal_type || "";
  return lab || "Signal";
}

/** Collapse same headline ingested under multiple signal_type rows (API may lag cache). */
function signalPreviewDedupeKey(s: LeadSignal): string {
  const raw = signalDisplayExcerpt(s)
    .replace(/<[^>]+>/g, "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
  if (raw.length >= 16) return raw.slice(0, 220);
  return `${s.signal_type || "sig"}:${raw.slice(0, 96)}`;
}

function distinctPreviewSignals(signals: LeadSignal[] | undefined, max: number): LeadSignal[] {
  const seen = new Set<string>();
  const out: LeadSignal[] = [];
  for (const s of signals || []) {
    const k = signalPreviewDedupeKey(s);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(s);
    if (out.length >= max) break;
  }
  return out;
}

function estDealLabel(lead: LeadRow): string | null {
  const top = lead.crm_metadata?.budget?.top_amount;
  if (typeof top === "string" && top.trim()) return top.trim();
  const lv = scoreNum(lead, "lead_value_score");
  if (lv <= 0) return null;
  const lowK = Math.max(200, Math.round(lv * 8)) * 1000;
  const highK = Math.max(lowK, Math.round(lv * 22)) * 1000;
  const fmt = (n: number) =>
    n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` : `$${Math.round(n / 1000)}K`;
  return `${fmt(lowK)}–${fmt(highK)}`;
}

function readIndustryFromUrl(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("industry")?.trim() || "";
}

function LeadAvatar({ name }: { name: string }) {
  const ch = (name || "?").trim().charAt(0).toUpperCase() || "?";
  const hue = ((name || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0) % 360) || 162;
  return (
    <div
      className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-lg font-bold text-white shadow-inner"
      style={{ backgroundColor: `oklch(0.52 0.14 ${hue})` }}
      aria-hidden
    >
      {ch}
    </div>
  );
}

export default function Dashboard() {
  const [leads, setLeads] = useState<LeadRow[]>([]);
  const [summary, setSummary] = useState<PipelineSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState<string>("");
  const [industrySearchInput, setIndustrySearchInput] = useState(() => readIndustryFromUrl());
  const [appliedIndustry, setAppliedIndustry] = useState(() => readIndustryFromUrl());

  useEffect(() => {
    const t = setTimeout(() => setAppliedIndustry(industrySearchInput.trim()), 420);
    return () => clearTimeout(t);
  }, [industrySearchInput]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const u = new URL(window.location.href);
    if (appliedIndustry) u.searchParams.set("industry", appliedIndustry);
    else u.searchParams.delete("industry");
    const qs = u.searchParams.toString();
    const next = `${u.pathname}${qs ? `?${qs}` : ""}`;
    const cur = `${window.location.pathname}${window.location.search}`;
    if (next !== cur) window.history.replaceState({}, "", next);
  }, [appliedIndustry]);

  const load = useCallback(async () => {
    const API = getApiBase();
    setError(null);
    setLoadingSummary(true);
    setLoadingLeads(true);
    setLeads([]);
    setExpandedId(null);

    const controller = new AbortController();
    const p = new URLSearchParams();
    p.set("limit", LEADS_PUBLIC_FETCH_LIMIT);
    p.set("exclude_junk", "true");
    p.set("min_score", "0");
    p.set("sort", "score");
    p.set("tier", "HOT");
    const ind = appliedIndustry.trim();
    if (ind) p.set("industry", ind);

    const fetchLeads = async (params: URLSearchParams) =>
      fetch(`${API}/api/leads?${params}`, liveFetchInit({ signal: controller.signal }));

    try {
      const [summaryRes, leadsResFirst] = await Promise.all([
        fetch(`${API}/api/leads/summary?exclude_junk=true&cb=${Date.now()}`, liveFetchInit({ signal: controller.signal })),
        fetchLeads(p),
      ]);

      if (summaryRes.ok) {
        const st = await summaryRes.text();
        if (!st.trimStart().startsWith("<")) {
          try {
            setSummary(JSON.parse(st) as PipelineSummary);
          } catch {
            setSummary(null);
          }
        }
      } else {
        setSummary(null);
      }
      setLoadingSummary(false);

      let leadsRes = leadsResFirst;
      if (!leadsRes.ok) {
        setError("We couldn’t load leads right now. Please try Refresh in a moment.");
        setLeads([]);
      } else {
        const raw = await leadsRes.text();
        if (raw.trimStart().startsWith("<")) {
          setError("We couldn’t reach the data service. Please try again shortly.");
          setLeads([]);
        } else {
          let list = JSON.parse(raw) as LeadRow[];
          if (list.length === 0 && p.get("tier") === "HOT") {
            const pAll = new URLSearchParams(p);
            pAll.delete("tier");
            leadsRes = await fetchLeads(pAll);
            if (leadsRes.ok) {
              const rawAll = await leadsRes.text();
              if (!rawAll.trimStart().startsWith("<")) {
                try {
                  list = JSON.parse(rawAll) as LeadRow[];
                } catch {
                  /* keep [] */
                }
              }
            }
          }
          setLeads(list);
          setError(null);
        }
      }
    } catch {
      setSummary(null);
      setError("Network error while loading. Check your connection and try Refresh.");
      setLeads([]);
    } finally {
      setLoadingSummary(false);
      setLoadingLeads(false);
    }
  }, [appliedIndustry]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (typeof window === "undefined" || !leads.length) return;
    const sp = new URLSearchParams(window.location.search);
    const raw = sp.get("analyze");
    if (!raw) return;
    const id = Number(raw);
    if (!Number.isFinite(id) || id <= 0) return;
    const preview = leads.slice(0, 5);
    if (preview.some((l) => l.id === id)) {
      setExpandedId(id);
    }
  }, [leads]);

  const grouped = useMemo(() => groupLeadsByIndustry(leads), [leads]);
  const industries = useMemo(() => industryKeysSorted(grouped), [grouped]);

  useEffect(() => {
    if (!industries.length) {
      setSelectedIndustry("");
      return;
    }
    setSelectedIndustry((prev) => (prev && industries.includes(prev) ? prev : industries[0]));
  }, [industries]);

  const industryLeads = selectedIndustry ? grouped[selectedIndustry] || [] : [];
  const previewLimit = 3;
  const previewLeads = industryLeads.slice(0, previewLimit);
  const busy = loadingSummary || loadingLeads;

  const hotLeadCount =
    summaryNum(summary?.hot) ??
    (leads.length ? leads.filter((l) => l.priority_tier === "HOT").length : undefined) ??
    0;
  const warmLeadCount =
    summaryNum(summary?.warm) ??
    (leads.length ? leads.filter((l) => l.priority_tier === "WARM").length : undefined) ??
    0;
  const companiesStat = summaryNum(summary?.companies_in_database);
  const signalStat =
    summaryNum(summary?.signals_in_database) ??
    summaryNum(summary?.total_signals) ??
    (leads.length ? leads.reduce((a, l) => a + (l.signal_count || 0), 0) : undefined) ??
    0;

  return (
    <SiteShell>
      <div className="pb-20">
        <section
          className="relative overflow-hidden border-b border-emerald-100/60"
          style={{ background: "linear-gradient(145deg, #ffffff 0%, #ecfdf5 38%, #f0f9ff 100%)" }}
        >
          <div
            className="pointer-events-none absolute inset-0 opacity-40"
            style={{
              backgroundImage:
                "radial-gradient(ellipse 70% 50% at 10% 0%, oklch(0.9 0.06 162.5), transparent), radial-gradient(ellipse 60% 40% at 90% 20%, oklch(0.93 0.04 250), transparent)",
            }}
          />
          <div className="container relative py-10 md:py-14">
            <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
              <div className="max-w-3xl space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-xs font-semibold uppercase tracking-widest text-emerald-800/90">
                    Live database
                  </span>
                  <span className="text-xs text-gray-400">·</span>
                  <span className="text-xs font-medium text-gray-500">Updated daily</span>
                </div>
                <h1
                  className="text-4xl md:text-5xl lg:text-[3.25rem] font-extrabold text-gray-900 leading-[1.06] tracking-tight"
                  style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.03em" }}
                >
                  Automation projects{" "}
                  <span style={{ color: EMERALD }}>ready for robots.</span>
                </h1>
                <p className="text-base md:text-lg text-gray-600 leading-relaxed max-w-2xl">
                  Sample leads across live industries — real companies, real signals, real buying intent. Sign up to
                  unlock scores, contacts, and your full CRM pipeline.
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                className="shrink-0 self-start border-emerald-200 text-emerald-900 hover:bg-white/90 gap-2"
                onClick={() => void load()}
                disabled={busy}
              >
                <RefreshCw className={cn("h-4 w-4", busy && "animate-spin")} aria-hidden />
                {busy ? "Refreshing…" : "Refresh"}
              </Button>
            </div>

            <div className="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
              {(loadingSummary && !summary) || (loadingLeads && !leads.length && !error) ? (
                <>
                  <Skeleton className="h-28 rounded-lg" />
                  <Skeleton className="h-28 rounded-lg" />
                  <Skeleton className="h-28 rounded-lg" />
                  <Skeleton className="h-28 rounded-lg" />
                </>
              ) : (
                [
                  { label: "HOT leads (scored window)", value: hotLeadCount },
                  { label: "WARM leads (scored window)", value: warmLeadCount },
                  { label: "Companies in database", value: companiesStat !== undefined ? companiesStat : "—" },
                  { label: "Signal rows in database", value: signalStat },
                ].map((s) => (
                  <div
                    key={s.label}
                    className="rounded-lg border border-gray-200 bg-white px-5 py-5 shadow-sm"
                  >
                    <p className="text-3xl md:text-4xl font-bold tabular-nums tracking-tight text-gray-900">
                      {typeof s.value === "number" ? s.value.toLocaleString() : s.value}
                    </p>
                    <p className="text-sm font-semibold text-gray-500 mt-1 leading-snug">{s.label}</p>
                  </div>
                ))
              )}
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {[
                {
                  t: "Evidence-linked",
                  d: "Each lead carries real signal excerpts (news, hiring, CapEx, labor) — not generic firmographics alone.",
                },
                {
                  t: "Scored for motion",
                  d: "SIG / VAL / INTENT summarize signal strength, deal quality, and buying urgency so reps know who to call first.",
                },
                {
                  t: "Refreshed daily",
                  d: "The HOT window rotates on a rolling schedule so you see active intent, not a frozen snapshot.",
                },
              ].map((x) => (
                <div
                  key={x.t}
                  className="rounded-xl border border-emerald-200/80 bg-white/90 px-4 py-4 shadow-sm text-sm leading-snug"
                >
                  <p className="font-bold text-gray-950 mb-1.5">{x.t}</p>
                  <p className="text-gray-700">{x.d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="container py-10 md:py-12 space-y-10">
          {error ? (
            <Card className="border-amber-200 bg-amber-50/80 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-amber-900 text-lg">Could not load leads</CardTitle>
                <CardDescription className="text-amber-900/90 whitespace-pre-wrap">{error}</CardDescription>
              </CardHeader>
            </Card>
          ) : null}

          {!error ? (
            <div className="space-y-6">
              <div className="rounded-2xl border-2 border-emerald-200/90 bg-gradient-to-br from-emerald-50/95 via-white to-sky-50/70 p-4 md:p-5 shadow-md ring-1 ring-emerald-900/5">
                <label htmlFor="dashboard-industry-search" className="text-sm font-bold text-emerald-950 block mb-2">
                  Search by industry
                </label>
                <div className="relative max-w-xl">
                  <Search
                    className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-700/80 pointer-events-none"
                    aria-hidden
                  />
                  <Input
                    id="dashboard-industry-search"
                    type="search"
                    autoComplete="off"
                    placeholder="e.g. Hospitality, Logistics, Healthcare…"
                    value={industrySearchInput}
                    onChange={(e) => setIndustrySearchInput(e.target.value)}
                    className="pl-10 h-11 border-2 border-sky-200/90 bg-white text-gray-900 shadow-inner placeholder:text-gray-500 focus-visible:ring-2 focus-visible:ring-emerald-500/35 focus-visible:border-emerald-600"
                  />
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-3">
                  <p className="text-xs text-gray-600 max-w-2xl">
                    Narrows the HOT sample via the API (partial match on industry). Use the chips below to switch
                    verticals in the current result set.
                  </p>
                  {industrySearchInput ? (
                    <button
                      type="button"
                      className="text-xs font-semibold text-emerald-800 hover:underline"
                      onClick={() => setIndustrySearchInput("")}
                    >
                      Clear filter
                    </button>
                  ) : null}
                </div>
              </div>

              {industries.length > 0 ? (
                <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin">
                  {industries.map((ind) => {
                    const n = grouped[ind].length;
                    const active = ind === selectedIndustry;
                    return (
                      <button
                        key={ind}
                        type="button"
                        onClick={() => {
                          setSelectedIndustry(ind);
                          setExpandedId(null);
                        }}
                        className={cn(
                          "shrink-0 rounded-md border px-4 py-2 text-sm font-semibold transition-all whitespace-nowrap bg-transparent",
                          active
                            ? "border-emerald-600 text-emerald-900"
                            : "border-gray-300 text-gray-700 hover:border-gray-400 hover:text-gray-900"
                        )}
                      >
                        {ind}
                        <span className={cn("ml-1.5 tabular-nums", active ? "text-emerald-800" : "text-gray-400")}>
                          {n}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : !loadingLeads ? (
                <p className="text-sm text-gray-700 rounded-xl border border-amber-200 bg-amber-50/80 px-4 py-3">
                  No leads match this industry in the current window. Try a shorter term (e.g. <strong>Hotel</strong>)
                  or clear the search to reload the full HOT sample.
                </p>
              ) : null}

              {industries.length > 0 ? (
                <>
                  <div>
                    <h2
                      className="text-2xl md:text-3xl font-bold text-gray-900"
                      style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.02em" }}
                    >
                      {selectedIndustry}
                    </h2>
                    <p className="text-sm md:text-base text-gray-600 mt-2">
                      Live signals in this vertical · Showing {Math.min(previewLimit, industryLeads.length)} of{" "}
                      {industryLeads.length} active leads
                    </p>
                    <Link
                      href="/login"
                      className="inline-flex items-center gap-1 mt-3 text-sm font-semibold hover:underline"
                      style={{ color: EMERALD }}
                    >
                      See all {industryLeads.length} leads
                      <ArrowRight className="h-4 w-4" aria-hidden />
                    </Link>
                  </div>

                  <div className="rounded-xl border border-gray-100 bg-gray-50/50 px-4 py-3 text-xs text-gray-600">
                    <span className="font-semibold text-gray-800">Score key:</span>{" "}
                    <span className="font-mono text-[11px]">SIG</span> — signal strength ·{" "}
                    <span className="font-mono text-[11px]">VAL</span> — deal quality ·{" "}
                    <span className="font-mono text-[11px]">INTENT</span> — buying intent
                  </div>

                  {loadingLeads ? (
                    <div className="space-y-4">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <Skeleton key={i} className="h-48 rounded-2xl" />
                      ))}
                    </div>
                  ) : industryLeads.length === 0 ? (
                    <p className="text-sm text-gray-500">No leads in this industry for the current window.</p>
                  ) : (
                    <div className="space-y-4">
                      {previewLeads.map((lead) => {
                        const open = expandedId === lead.id;
                        const sig = Math.round(scoreNum(lead, "signal_score"));
                        const val = Math.round(scoreNum(lead, "lead_value_score"));
                        const intent = Math.round(scoreNum(lead, "overall_score"));
                        const bullets = distinctPreviewSignals(lead.signals, 3).map(signalBullet);
                        const deal = estDealLabel(lead);
                        return (
                          <Fragment key={lead.id}>
                            <Card
                              className={cn(
                                "overflow-hidden rounded-2xl border-gray-200/90 shadow-md transition-shadow",
                                open && "ring-2 ring-emerald-200/80 shadow-lg"
                              )}
                            >
                              <CardContent className="p-0">
                                <div className="flex flex-col md:flex-row md:items-stretch">
                                  <div className="flex gap-4 p-5 md:p-6 md:pr-4 flex-1 min-w-0">
                                    <LeadAvatar name={lead.company_name || "?"} />
                                    <div className="min-w-0 flex-1 space-y-3">
                                      <div className="flex flex-wrap items-start justify-between gap-2">
                                        <div>
                                          <h3 className="text-lg font-bold text-gray-900 truncate">
                                            {lead.company_name || "—"}
                                          </h3>
                                          <p className="text-sm text-gray-500 mt-0.5">
                                            {formatLocation(lead)} ·{" "}
                                            {formatEmployees(lead.employee_estimate ?? undefined)}
                                          </p>
                                        </div>
                                        <Badge
                                          variant={tierBadgeVariant(lead.priority_tier)}
                                          className={tierBadgeClass(lead.priority_tier)}
                                        >
                                          {lead.priority_tier === "HOT" ? "🔥 HOT" : lead.priority_tier || "—"}
                                        </Badge>
                                      </div>
                                      <ul className="space-y-1.5 text-sm text-gray-700">
                                        {bullets.length ? (
                                          bullets.map((b, i) => (
                                            <li key={i} className="flex gap-2">
                                              <span className="text-emerald-600 shrink-0">·</span>
                                              <span className="leading-snug">{b}</span>
                                            </li>
                                          ))
                                        ) : (
                                          <li className="text-gray-500">No signal snippets in preview.</li>
                                        )}
                                      </ul>
                                      <div className="flex flex-wrap gap-3 pt-1">
                                        {[
                                          { k: "SIG", v: sig },
                                          { k: "VAL", v: val },
                                          { k: "INTENT", v: intent },
                                        ].map((col) => (
                                          <div
                                            key={col.k}
                                            className="rounded-lg border border-gray-100 bg-gray-50/80 px-3 py-2 min-w-[4.5rem]"
                                          >
                                            <p className="text-[10px] font-bold uppercase tracking-wide text-gray-500">
                                              {col.k}
                                            </p>
                                            <p
                                              className="text-lg font-mono font-bold tabular-nums"
                                              style={{ color: EMERALD }}
                                            >
                                              {col.v || "—"}
                                            </p>
                                          </div>
                                        ))}
                                      </div>
                                      {deal ? (
                                        <p className="text-sm">
                                          <span className="text-gray-500">Est. deal </span>
                                          <span className="font-semibold text-gray-900">{deal}</span>
                                        </p>
                                      ) : null}
                                      <button
                                        type="button"
                                        className="inline-flex items-center gap-1 text-sm font-semibold hover:underline"
                                        style={{ color: EMERALD }}
                                        onClick={() => setExpandedId(open ? null : lead.id)}
                                      >
                                        {open ? "Hide analysis" : "Analyze this lead"}
                                        <ArrowRight className={cn("h-4 w-4 transition-transform", open && "rotate-90")} />
                                      </button>
                                    </div>
                                  </div>
                                </div>
                                {open ? (
                                  <div className="border-t border-gray-100 bg-gray-50/60 p-4 md:p-6 max-h-[min(75vh,28rem)] overflow-y-auto">
                                    <LeadDetailPanel lead={lead} density="default" />
                                  </div>
                                ) : null}
                              </CardContent>
                            </Card>
                          </Fragment>
                        );
                      })}

                      {!loadingLeads && industryLeads.length > previewLimit ? (
                        <SignupLeadsBlur leads={industryLeads} previewLimit={previewLimit} />
                      ) : null}
                    </div>
                  )}

                  <section
                    className="rounded-3xl border border-emerald-100/80 px-6 py-10 md:px-12 md:py-12 text-center space-y-5"
                    style={{ background: "linear-gradient(180deg, oklch(0.99 0.02 162.5) 0%, #fff 55%)" }}
                  >
                    <h2
                      className="text-2xl md:text-3xl font-bold text-gray-900"
                      style={{ fontFamily: "'Bricolage Grotesque', sans-serif" }}
                    >
                      Ready to build your pipeline?
                    </h2>
                    <p className="text-gray-600 max-w-xl mx-auto text-sm md:text-base leading-relaxed">
                      Sign up to unlock every HOT lead, full signal data, contact insights, and your personal CRM
                      pipeline — refreshed on a rolling window.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center items-center pt-1">
                      <Link
                        href="/login"
                        className="inline-flex items-center justify-center gap-2 rounded-md border px-8 py-3 text-sm font-semibold bg-transparent hover:opacity-90 transition-opacity"
                        style={{ borderColor: EMERALD, color: EMERALD }}
                      >
                        Get started free
                        <ArrowRight className="h-4 w-4" aria-hidden />
                      </Link>
                      <Link
                        href="/pipeline"
                        className="inline-flex items-center justify-center gap-2 rounded-md border border-gray-300 px-8 py-3 text-sm font-semibold text-gray-900 bg-transparent hover:border-gray-400"
                      >
                        HOT pipeline
                      </Link>
                      <Link href="/" className="text-sm font-semibold text-gray-600 hover:text-gray-900">
                        ← Back to home
                      </Link>
                    </div>
                    <p className="text-xs text-gray-500">No credit card required · Free trial · Cancel anytime</p>
                  </section>
                </>
              ) : null}
            </div>
          ) : !loadingLeads && !error && leads.length === 0 ? (
            <p className="text-center text-gray-500 py-12">No leads returned for this view.</p>
          ) : null}
        </div>
      </div>
    </SiteShell>
  );
}
