import React, { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Mail, Radio, Zap, TrendingUp, AlertTriangle, Eye } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { cleanScrapedText } from "@/lib/text";

type NewsletterStory = {
  category?: string;
  company?: string;
  headline?: string;
  snippet?: string;
  summary?: string;
  roi?: string;
  economics?: string;
  impact?: string;
  signalStrength?: number;
  fullText?: string;
  company_id?: number;
};

type ResearchFinding = {
  company_id?: number;
  company?: string;
  industry?: string;
  category?: string;
  title?: string;
  summary?: string;
  source_domain?: string | null;
  detected_at?: string | null;
  significance_score?: number;
  pipeline_url?: string;
  scout_url?: string;
  action_label?: string;
};

type BriefTextItem = string | {
  title?: string;
  detail?: string;
  audience?: string;
  insight?: string;
};

type IndustryBrief = {
  executive_take?: string;
  macro_trends?: BriefTextItem[];
  strategic_implications?: BriefTextItem[];
  risks_and_unknowns?: BriefTextItem[];
  watch_next?: BriefTextItem[];
};

type NewsletterEdition = {
  latestEdition?: {
    date?: string;
    edition?: string;
    headline?: string;
    subheadline?: string;
  };
  industryBrief?: IndustryBrief;
  researchFindings?: ResearchFinding[];
  topStories?: NewsletterStory[];
  summary?: {
    total_leads?: number;
    research_findings?: number;
    generated_at?: string;
  };
};

function briefTextTitle(item: BriefTextItem | undefined): string {
  if (!item) return "";
  if (typeof item === "string") return cleanScrapedText(item);
  return cleanScrapedText(item.title || item.audience || "");
}

function briefTextDetail(item: BriefTextItem | undefined): string {
  if (!item) return "";
  if (typeof item === "string") return "";
  return cleanScrapedText(item.detail || item.insight || "");
}

function signalBullets(fullText: string | undefined): string[] {
  if (!fullText) return [];
  const lines = fullText.split("\n");
  const bullets: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
      const clean = trimmed.replace(/^[•\-]\s*/, "").replace(/\*\*/g, "").trim();
      if (clean && !clean.includes("<img") && !clean.includes("<a href") && clean.length > 20) {
        const withoutHtml = clean.replace(/<[^>]*>/g, "").trim();
        if (withoutHtml.length > 20) bullets.push(withoutHtml.slice(0, 160));
      }
    }
    if (bullets.length >= 3) break;
  }
  return bullets;
}

function tierColor(tier: string | undefined): string {
  if (!tier) return "#03DAC5";
  const t = tier.toLowerCase();
  if (t.includes("labor") || t.includes("shortage")) return "#f87171";
  if (t.includes("fund") || t.includes("round")) return "#a78bfa";
  if (t.includes("expansion") || t.includes("hire")) return "#FFB000";
  if (t.includes("capex") || t.includes("budget")) return "#34d399";
  return "#03DAC5";
}

const TEAL = "#03DAC5";
const AMBER = "#FFB000";
const PURPLE = "#a78bfa";

export default function Newsletter() {
  const [edition, setEdition] = useState<NewsletterEdition | null>(null);
  const [loadStatus, setLoadStatus] = useState<"loading" | "ready" | "error">("loading");
  const [loadSec, setLoadSec] = useState(0);
  const [email, setEmail] = useState("");
  const [subStatus, setSubStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  // Tick the loading counter so the user sees progress, not a frozen spinner
  useEffect(() => {
    if (loadStatus !== "loading") return;
    const id = setInterval(() => setLoadSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [loadStatus]);

  useEffect(() => {
    let cancelled = false;
    let retryTimer: number | undefined;

    const load = (attempt: number) => {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 25_000);
      fetch(`${getApiBase()}/api/newsletter/edition?limit=15&cb=${Date.now()}`, liveFetchInit({
        signal: controller.signal,
      }))
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (cancelled) return;
          if (data?.latestEdition) {
            setEdition(data);
            const storyCount = Array.isArray(data.topStories) ? data.topStories.length : 0;
            if (storyCount > 0) {
              setLoadStatus("ready");
              return;
            }
          }
          if (attempt < 4) {
            setLoadStatus("loading");
            retryTimer = window.setTimeout(() => load(attempt + 1), 4000);
            return;
          }
          setLoadStatus("error");
        })
        .catch(() => {
          if (cancelled) return;
          if (attempt < 4) {
            retryTimer = window.setTimeout(() => load(attempt + 1), 4000);
            return;
          }
          setLoadStatus("error");
        })
        .finally(() => window.clearTimeout(timeout));
    };

    setLoadStatus("loading");
    load(0);

    return () => {
      cancelled = true;
      if (retryTimer) window.clearTimeout(retryTimer);
    };
  }, []);

  async function subscribe(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) return;
    setSubStatus("submitting");
    try {
      const res = await fetch(`${getApiBase()}/api/newsletter/subscribe`, liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, source: "newsletter_page" }),
      }));
      if (!res.ok) throw new Error("Subscribe failed");
      setSubStatus("success");
      setEmail("");
    } catch {
      setSubStatus("error");
    }
  }

  const stories = (edition?.topStories || []).slice(0, 14);
  const researchFindings = (edition?.researchFindings || []).slice(0, 6);
  const brief = edition?.industryBrief;

  // ── Benchmark report state ──────────────────────────────────────────────
  const [benchReport, setBenchReport] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    fetch(`${getApiBase()}/api/humanoid/report`, liveFetchInit())
      .then(r => r.ok ? r.json() : null)
      .then(d => d?.report ? setBenchReport(d.report) : null)
      .catch(() => null);
  }, []);
  const headline = cleanScrapedText(edition?.latestEdition?.headline) || "Daily robot demand intelligence.";
  const subheadline = cleanScrapedText(edition?.latestEdition?.subheadline) || "Buying signals, deployment moves, funding events, and strategic hires — curated daily for robotics sales teams.";
  const macroItems = (brief?.macro_trends || []).slice(0, 4);
  const stratItems = (brief?.strategic_implications || []).slice(0, 4);
  const riskItems = (brief?.risks_and_unknowns || []).map((r) => (typeof r === "string" ? r : "")).filter(Boolean).slice(0, 3);
  const watchItems = (brief?.watch_next || []).map((w) => (typeof w === "string" ? w : "")).filter(Boolean).slice(0, 3);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 px-4 pb-24 pt-28 lg:px-6">
        <div className="mx-auto max-w-6xl">

          {/* ── Hero ─────────────────────────────────────────────────── */}
          <section
            className="relative mb-8 overflow-hidden rounded-3xl border border-white/10 p-6 lg:p-10"
            style={{ background: "linear-gradient(135deg,rgba(3,218,197,0.07),rgba(124,58,237,0.07),rgba(255,176,0,0.04))" }}
          >
            <div className="pointer-events-none absolute right-0 top-0 h-64 w-64 rounded-full blur-3xl" style={{ background: "rgba(3,218,197,0.10)" }} />
            <div className="relative grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px] lg:items-end">
              <div>
                <p className="mb-4 inline-flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
                  <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: TEAL }} />
                  Robot Intelligence Brief · {edition?.latestEdition?.edition || "Daily"} · {edition?.latestEdition?.date || "Updated daily"}
                </p>
                <h1 className="max-w-3xl text-3xl font-extrabold leading-tight text-white lg:text-5xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  {headline}
                </h1>
                <p className="mt-4 max-w-2xl text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.50)" }}>
                  {subheadline}
                </p>
              </div>
              <form onSubmit={subscribe} className="rounded-2xl border border-white/10 p-5" style={{ background: "rgba(13,5,32,0.65)" }}>
                <Mail className="mb-3 h-4 w-4" style={{ color: TEAL }} />
                <p className="text-sm font-bold text-white">Subscribe free</p>
                <p className="mt-1 text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.35)" }}>Signal brief in your inbox when the edition updates.</p>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  placeholder="work email"
                  className="mt-4 w-full rounded-xl border border-white/10 px-4 py-2.5 text-sm text-white placeholder-white/25 outline-none focus:border-teal-300/50"
                  style={{ background: "rgba(255,255,255,0.04)" }}
                />
                <button
                  type="submit"
                  disabled={subStatus === "submitting"}
                  className="mt-3 w-full rounded-xl px-4 py-2.5 text-sm font-bold transition-all disabled:opacity-50"
                  style={{ color: AMBER, border: `1.5px solid ${AMBER}`, background: "transparent" }}
                >
                  {subStatus === "submitting" ? "Subscribing…" : "Subscribe Free"}
                </button>
                {subStatus === "success" && <p className="mt-2 text-xs" style={{ color: TEAL }}>You're subscribed.</p>}
                {subStatus === "error" && <p className="mt-2 text-xs text-red-300">Could not subscribe — try again.</p>}
              </form>
            </div>
          </section>

          {/* ── Stats bar ────────────────────────────────────────────── */}
          <section className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              { label: "Edition", value: edition?.latestEdition?.edition || "—" },
              { label: "Updated", value: edition?.latestEdition?.date || "Daily" },
              { label: "Hot leads", value: String(edition?.summary?.total_leads ?? stories.length), accent: AMBER },
              { label: "Stories", value: String(stories.length || (loadStatus === "loading" ? "…" : "—")), accent: TEAL },
            ].map(({ label, value, accent }) => (
              <div key={label} className="rounded-2xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-white/30">{label}</p>
                <p className="mt-2 font-mono text-xl font-black" style={{ color: accent || TEAL, fontFamily: "'JetBrains Mono', monospace" }}>{value}</p>
              </div>
            ))}
          </section>

          {/* ── Loading state ─────────────────────────────────────────── */}
          {loadStatus === "loading" && (
            <section className="mb-8 rounded-3xl border border-white/10 p-8 text-center" style={{ background: "rgba(255,255,255,0.025)" }}>
              <div className="mx-auto mb-4 h-10 w-10 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: `${TEAL} transparent transparent transparent` }} />
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] mb-2" style={{ color: TEAL }}>Building your intelligence brief</p>
              <p className="text-sm text-white/40">Pulling signals from 4,000+ companies… {loadSec > 5 ? `${loadSec}s` : ""}</p>
              {loadSec > 20 && <p className="mt-2 text-xs text-white/25">AI analysis is generating — this takes about 60 seconds on first load.</p>}
            </section>
          )}

          {loadStatus === "error" && (
            <section className="mb-8 rounded-3xl border border-white/10 p-6 text-center" style={{ background: "rgba(255,176,0,0.04)" }}>
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] mb-2" style={{ color: AMBER }}>Brief is refreshing</p>
              <p className="text-sm text-white/40">SCOUT is rebuilding today&apos;s edition. Subscribe above, or reload in a moment for the full brief.</p>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="mt-4 inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-bold"
                style={{ color: TEAL, borderColor: "rgba(3,218,197,0.35)" }}
              >
                Reload page
              </button>
            </section>
          )}

          {/* ── AI Executive Brief ───────────────────────────────────── */}
          {brief?.executive_take && (
            <section className="mb-8 rounded-3xl border border-white/10 p-6 lg:p-8" style={{ background: "rgba(124,58,237,0.06)" }}>
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: PURPLE }}>AI market analysis</p>
              <p className="text-base leading-relaxed text-white/75 lg:text-lg">{cleanScrapedText(brief.executive_take)}</p>

              {/* Macro trends + Strategic implications side by side */}
              <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                {macroItems.length > 0 && (
                  <div>
                    <div className="mb-3 flex items-center gap-2">
                      <TrendingUp className="h-3.5 w-3.5" style={{ color: TEAL }} />
                      <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: TEAL }}>Macro trends</p>
                    </div>
                    <div className="space-y-2">
                      {macroItems.map((item, i) => {
                        const title = briefTextTitle(item);
                        const detail = briefTextDetail(item);
                        return (
                          <div key={i} className="rounded-xl border border-white/8 p-3" style={{ background: "rgba(3,218,197,0.04)" }}>
                            {title && <p className="text-sm font-semibold text-white">{title}</p>}
                            {detail && <p className="mt-1 text-xs leading-relaxed text-white/50">{detail}</p>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                {stratItems.length > 0 && (
                  <div>
                    <div className="mb-3 flex items-center gap-2">
                      <Radio className="h-3.5 w-3.5" style={{ color: AMBER }} />
                      <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: AMBER }}>Strategic implications</p>
                    </div>
                    <div className="space-y-2">
                      {stratItems.map((item, i) => {
                        const title = briefTextTitle(item);
                        const detail = briefTextDetail(item);
                        return (
                          <div key={i} className="rounded-xl border border-white/8 p-3" style={{ background: "rgba(255,176,0,0.04)" }}>
                            {title && <p className="text-xs font-bold uppercase tracking-wider" style={{ color: AMBER }}>{title}</p>}
                            {detail && <p className="mt-1 text-xs leading-relaxed text-white/55">{detail}</p>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Risks + Watch next */}
              {(riskItems.length > 0 || watchItems.length > 0) && (
                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  {riskItems.length > 0 && (
                    <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(248,113,113,0.04)" }}>
                      <div className="mb-2 flex items-center gap-2">
                        <AlertTriangle className="h-3.5 w-3.5 text-red-400/70" />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-red-400/70">Risks to watch</p>
                      </div>
                      <ul className="space-y-1.5">
                        {riskItems.map((r, i) => (
                          <li key={i} className="text-xs leading-relaxed text-white/45 before:mr-1.5 before:content-['·']">{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {watchItems.length > 0 && (
                    <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(3,218,197,0.03)" }}>
                      <div className="mb-2 flex items-center gap-2">
                        <Eye className="h-3.5 w-3.5" style={{ color: TEAL }} />
                        <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: TEAL }}>Watch next</p>
                      </div>
                      <ul className="space-y-1.5">
                        {watchItems.map((w, i) => (
                          <li key={i} className="text-xs leading-relaxed text-white/45 before:mr-1.5 before:content-['·']">{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}

          {/* ── SCOUT research findings ───────────────────────────────── */}
          {researchFindings.length > 0 && (
            <section className="mb-8 rounded-3xl border border-white/10 p-6 lg:p-7" style={{ background: "rgba(255,176,0,0.04)" }}>
              <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: AMBER }}>SCOUT research findings</p>
                  <h2 className="text-xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>Account changes worth actioning today</h2>
                </div>
                <Link href="/pipeline" className="inline-flex items-center gap-2 text-xs font-bold" style={{ color: AMBER }}>Open pipeline <ArrowRight className="h-3.5 w-3.5" /></Link>
              </div>
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                {researchFindings.map((finding, index) => (
                  <article key={`${finding.company_id || finding.company}-${index}`} className="rounded-2xl border border-amber-300/12 p-4" style={{ background: "rgba(13,5,32,0.55)" }}>
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <span className="rounded-full border border-amber-300/22 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest" style={{ color: AMBER, background: "rgba(255,176,0,0.06)" }}>
                        {cleanScrapedText(finding.category) || "Research"}
                      </span>
                      {typeof finding.significance_score === "number" && (
                        <span className="font-mono text-[11px] font-bold" style={{ color: AMBER }}>{Math.round(finding.significance_score * 100)} signal</span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-white">{cleanScrapedText(finding.company) || "Lead"}</h3>
                    <p className="mt-1.5 text-xs leading-relaxed" style={{ color: AMBER }}>{cleanScrapedText(finding.summary || finding.title)}</p>
                    {finding.industry && <p className="mt-2 text-[11px] text-white/25">{cleanScrapedText(finding.industry)}</p>}
                    <Link href={finding.pipeline_url || "/pipeline"} className="mt-3 inline-flex items-center gap-1.5 text-xs font-bold" style={{ color: AMBER }}>
                      {finding.action_label || "Act now"} <Zap className="h-3 w-3" />
                    </Link>
                  </article>
                ))}
              </div>
            </section>
          )}

          {/* ── Humanoid benchmark report ─────────────────────────────── */}
          {benchReport && (
            <section className="mb-12">
              <div className="mb-5 flex items-center justify-between flex-wrap gap-3">
                <div>
                  <p className="mb-1.5 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#a78bfa" }}>Robot Intelligence · Benchmark</p>
                  <h2 className="text-xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    {String(benchReport.title ?? "Humanoid Robot Benchmark")}
                  </h2>
                </div>
                <Link href="/robots" className="inline-flex items-center gap-2 text-xs font-bold text-white/40 hover:text-white/70">
                  Full index <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>

              {/* Top 3 */}
              <div className="grid gap-3 sm:grid-cols-3 mb-5">
                {((benchReport.top_3 as Array<{name: string; vendor: string; score: number; status: string}>) ?? []).map((r, i) => (
                  <div key={r.name} className="rounded-2xl border border-white/8 p-4" style={{ background: "rgba(124,58,237,0.06)" }}>
                    <p className="text-[10px] text-white/30 mb-1">{["🥇 Leader", "🥈 2nd", "🥉 3rd"][i]}</p>
                    <p className="font-bold text-white text-sm">{r.name}</p>
                    <p className="text-[11px] text-white/40">{r.vendor}</p>
                    <p className="text-2xl font-black mt-2" style={{ color: i === 0 ? "#34d399" : i === 1 ? "#a78bfa" : "#fbbf24" }}>{r.score}</p>
                    <p className="text-[9px] text-white/25 uppercase tracking-wider">/ 100</p>
                  </div>
                ))}
              </div>

              {/* Key findings */}
              <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.02)" }}>
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-3">Key findings</p>
                <ul className="space-y-2">
                  {((benchReport.key_findings as string[]) ?? []).map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-[13px] text-white/55">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 bg-violet-400" />
                      {f}
                    </li>
                  ))}
                </ul>
                <div className="mt-4 pt-4 border-t border-white/7 flex flex-wrap gap-4 text-[11px] text-white/35">
                  <span>{String(benchReport.total_robots ?? 0)} robots scored</span>
                  <span>{String(benchReport.available_count ?? 0)} commercially available</span>
                  <span>{String(benchReport.pilot_count ?? 0)} in pilot</span>
                </div>
              </div>
            </section>
          )}

          {/* ── Top stories ───────────────────────────────────────────── */}
          {stories.length > 0 && (
            <>
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="mb-1.5 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>Signal intelligence · {stories.length} accounts</p>
                  <h2 className="text-xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>Companies moving toward automation now</h2>
                </div>
                <Link href="/pipeline" className="hidden md:inline-flex items-center gap-2 text-xs font-bold text-white/40 hover:text-white/70">
                  Full pipeline <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>

              <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {stories.map((story, index) => {
                  const bullets = signalBullets(story.fullText);
                  const color = tierColor(story.category);
                  return (
                    <article
                      key={`${story.company || story.headline || index}`}
                      className="flex flex-col rounded-3xl border border-white/8 p-5 transition-colors hover:border-white/16"
                      style={{ background: "rgba(255,255,255,0.025)" }}
                    >
                      {/* Header row */}
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <span
                          className="inline-block rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest"
                          style={{ color, borderColor: `${color}44`, background: `${color}0d` }}
                        >
                          {cleanScrapedText(story.category) || "Signal"}
                        </span>
                        {story.signalStrength && (
                          <span className="font-mono text-xs font-bold text-white/30" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                            {story.signalStrength}/10
                          </span>
                        )}
                      </div>

                      {/* Company + headline */}
                      <h2 className="text-lg font-extrabold leading-snug text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                        {cleanScrapedText(story.company || story.headline)}
                      </h2>
                      <p className="mt-2 text-sm leading-relaxed text-white/50">
                        {cleanScrapedText(story.snippet || story.summary || "").slice(0, 200)}
                      </p>

                      {/* Signal evidence bullets */}
                      {bullets.length > 0 && (
                        <ul className="mt-3 space-y-1.5">
                          {bullets.map((b, bi) => (
                            <li key={bi} className="flex items-start gap-2 text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.45)" }}>
                              <span className="mt-1 h-1 w-1 shrink-0 rounded-full" style={{ background: color }} />
                              {b}
                            </li>
                          ))}
                        </ul>
                      )}

                      {/* Meta chips */}
                      <div className="mt-auto pt-4 flex flex-wrap items-center gap-2">
                        {[story.economics, story.impact].map((chip) => cleanScrapedText(chip)).filter(Boolean).map((chip) => (
                          <span key={chip} className="rounded-lg border border-white/8 px-2.5 py-1 text-[11px] font-medium text-white/35" style={{ background: "rgba(13,5,32,0.5)" }}>
                            {chip}
                          </span>
                        ))}
                        {story.roi && (
                          <span className="rounded-lg border px-2.5 py-1 text-[11px] font-bold" style={{ color, borderColor: `${color}33`, background: `${color}0a` }}>
                            {cleanScrapedText(story.roi)}
                          </span>
                        )}
                      </div>

                      {/* CTA */}
                      <div className="mt-3 border-t border-white/6 pt-3">
                        <Link
                          href={story.company_id ? `/pipeline#${story.company_id}` : "/pipeline"}
                          className="inline-flex items-center gap-1.5 text-xs font-bold transition-colors hover:opacity-80"
                          style={{ color }}
                        >
                          Open in pipeline <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </div>
                    </article>
                  );
                })}
              </section>
            </>
          )}

          {/* ── Footer CTA ───────────────────────────────────────────── */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-5 text-sm">
            <Link href="/results?url=" className="inline-flex items-center gap-2 font-bold" style={{ color: AMBER }}>
              Activate SCOUT from today&apos;s brief <Zap className="h-4 w-4" />
            </Link>
            <Link href="/signals" className="inline-flex items-center gap-2 font-bold text-white/40 hover:text-white/70">
              Live signals <BarChart3 className="h-4 w-4" />
            </Link>
            <Link href="/intelligence" className="inline-flex items-center gap-2 font-bold text-white/40 hover:text-white/70">
              Intelligence report <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

        </div>
      </main>
    </div>
  );
}
