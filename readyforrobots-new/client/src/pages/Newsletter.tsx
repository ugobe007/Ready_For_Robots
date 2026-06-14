import React, { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Bot, Radio, Sparkles, TrendingUp, Zap } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import {
  fetchWithTimeout,
  getApiBase,
  liveFetchInit,
  publicFetchInit,
  readSurfaceCache,
  readSessionCache,
  writeSurfaceCache,
  writeSessionCache,
} from "@/lib/apiBase";
import { cleanScrapedText, leadPreviewSentences } from "@/lib/text";

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


const TEAL = "#03DAC5";
const AMBER = "#FFB000";
const EMERALD = "#34d399";
const PURPLE = "#a78bfa";
const NEWSLETTER_SESSION_KEY = "newsletter_edition_v2";
const NEWSLETTER_SESSION_TTL_MS = 24 * 60 * 60 * 1000;
const NEWSLETTER_BENCH_KEY = "newsletter_humanoid_report_v1";
const NEWSLETTER_BENCH_TTL_MS = 30 * 60 * 1000;

/** Supabase-style surface — accent rail, tight padding, clear border */
function NlSurface({
  accent,
  icon: Icon,
  kicker,
  title,
  action,
  children,
  className = "",
}: {
  accent: string;
  icon?: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  kicker: string;
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`mb-5 overflow-hidden rounded-lg border border-white/[0.09] shadow-[0_1px_0_rgba(255,255,255,0.04)_inset] ${className}`}
      style={{ background: "linear-gradient(180deg, rgba(255,255,255,0.035) 0%, rgba(255,255,255,0.015) 100%)" }}
    >
      <div className="flex">
        <div className="w-[3px] shrink-0" style={{ background: accent }} />
        <div className="min-w-0 flex-1 p-4 lg:p-5">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3 border-b border-white/[0.06] pb-3">
            <div className="flex items-start gap-2.5">
              {Icon ? (
                <span
                  className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border"
                  style={{ borderColor: `${accent}44`, background: `${accent}14`, color: accent }}
                >
                  <Icon className="h-3.5 w-3.5" />
                </span>
              ) : null}
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: accent }}>{kicker}</p>
                {title ? (
                  <h2 className="mt-0.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    {title}
                  </h2>
                ) : null}
              </div>
            </div>
            {action}
          </div>
          {children}
        </div>
      </div>
    </section>
  );
}

function NlBadge({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{ color, background: `${color}18`, border: `1px solid ${color}33` }}
    >
      {label}
    </span>
  );
}

function NlStatCell({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="border border-white/[0.08] bg-white/[0.02] px-3 py-2.5">
      <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-white/35">{label}</p>
      <p
        className="mt-1 font-mono text-lg font-semibold leading-none"
        style={{ color: accent || TEAL, fontFamily: "'JetBrains Mono', monospace" }}
      >
        {value}
      </p>
    </div>
  );
}

function NlDataRow({
  accent,
  children,
  className = "",
}: {
  accent?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <li
      className={`group border-b border-white/[0.06] px-3 py-3 transition-colors last:border-b-0 hover:bg-white/[0.03] ${className}`}
      style={accent ? { borderLeft: `2px solid ${accent}55` } : undefined}
    >
      {children}
    </li>
  );
}

function NlLink({ href, children, color = TEAL }: { href: string; children: React.ReactNode; color?: string }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 text-xs font-semibold transition-opacity hover:opacity-80"
      style={{ color }}
    >
      {children}
      <ArrowRight className="h-3 w-3" />
    </Link>
  );
}

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

    const cached =
      readSurfaceCache<NewsletterEdition>(NEWSLETTER_SESSION_KEY, NEWSLETTER_SESSION_TTL_MS)?.data
      ?? readSessionCache<NewsletterEdition>(NEWSLETTER_SESSION_KEY, NEWSLETTER_SESSION_TTL_MS);
    const hasCachedStories = (cached?.topStories?.length ?? 0) > 0;
    if (cached?.latestEdition && hasCachedStories) {
      setEdition(cached);
      setLoadStatus("ready");
    }

    const applyEdition = (data: NewsletterEdition | null) => {
      if (!data?.latestEdition) return false;
      const storyCount = Array.isArray(data.topStories) ? data.topStories.length : 0;
      if (storyCount > 0) {
        setEdition(data);
        setLoadStatus("ready");
        writeSurfaceCache(NEWSLETTER_SESSION_KEY, data);
        return true;
      }
      return false;
    };

    const load = async (attempt: number) => {
      try {
        const res = await fetchWithTimeout(
          `${getApiBase()}/api/newsletter/edition?limit=15`,
          publicFetchInit(),
          8_000,
          { publicCache: true },
        );
        if (cancelled) return;
        const data = res.ok ? ((await res.json()) as NewsletterEdition) : null;
        if (applyEdition(data)) return;
        if (data?.latestEdition) setEdition(data);
        if (attempt < 1) {
          retryTimer = window.setTimeout(() => void load(attempt + 1), 1500);
          return;
        }
        setLoadStatus((data?.topStories?.length ?? 0) > 0 ? "ready" : "error");
      } catch {
        if (cancelled) return;
        if (attempt < 1) {
          retryTimer = window.setTimeout(() => void load(attempt + 1), 1500);
          return;
        }
        if (!cached?.topStories?.length) setLoadStatus("error");
      }
    };

    if (!hasCachedStories) {
      void load(0);
    }

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

  // ── Benchmark report state (deferred — newsletter stories paint first) ───
  const benchCached = readSurfaceCache<Record<string, unknown>>(NEWSLETTER_BENCH_KEY, NEWSLETTER_BENCH_TTL_MS);
  const [benchReport, setBenchReport] = useState<Record<string, unknown> | null>(benchCached?.data ?? null);
  useEffect(() => {
    if (loadStatus !== "ready") return;
    const timer = window.setTimeout(() => {
      void fetchWithTimeout(
        `${getApiBase()}/api/humanoid/report`,
        publicFetchInit(),
        8_000,
        { publicCache: true },
      )
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => {
          if (!d?.report) return;
          setBenchReport(d.report);
          writeSurfaceCache(NEWSLETTER_BENCH_KEY, d.report);
        })
        .catch(() => null);
    }, benchCached?.data ? 0 : 400);
    return () => window.clearTimeout(timer);
  }, [loadStatus, benchCached?.data]);
  const headline = cleanScrapedText(edition?.latestEdition?.headline) || "Daily robot demand intelligence.";
  const subheadline = cleanScrapedText(edition?.latestEdition?.subheadline) || "Buying signals, deployment moves, funding events, and strategic hires — curated daily for robotics sales teams.";
  const macroItems = (brief?.macro_trends || []).slice(0, 4);
  const stratItems = (brief?.strategic_implications || []).slice(0, 4);
  const riskItems = (brief?.risks_and_unknowns || []).map((r) => (typeof r === "string" ? r : "")).filter(Boolean).slice(0, 3);
  const watchItems = (brief?.watch_next || []).map((w) => (typeof w === "string" ? w : "")).filter(Boolean).slice(0, 3);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 px-4 pb-20 pt-24 lg:px-6">
        <div className="mx-auto max-w-5xl">

          <header
            className="mb-6 overflow-hidden rounded-lg border border-white/[0.09]"
            style={{ background: "linear-gradient(135deg, rgba(3,218,197,0.06), rgba(124,58,237,0.05) 55%, rgba(255,176,0,0.03))" }}
          >
            <div className="flex">
              <div className="w-[3px] shrink-0" style={{ background: TEAL }} />
              <div className="flex-1 p-4 lg:p-6">
                <p className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: TEAL }}>
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full" style={{ background: TEAL }} />
                  Robot Intelligence Brief · {edition?.latestEdition?.edition || "Daily"}
                </p>
                <h1 className="text-2xl font-semibold leading-tight text-white lg:text-[1.75rem]" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  {headline}
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/55">{subheadline}</p>

                <div className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded-md border border-white/[0.08] bg-white/[0.08] md:grid-cols-4">
                  <NlStatCell label="Edition" value={edition?.latestEdition?.edition || "—"} />
                  <NlStatCell label="Updated" value={edition?.latestEdition?.date || "Daily"} accent={PURPLE} />
                  <NlStatCell label="Hot leads" value={String(edition?.summary?.total_leads ?? stories.length)} accent={AMBER} />
                  <NlStatCell label="Stories" value={String(stories.length || (loadStatus === "loading" ? "…" : "—"))} />
                </div>

                <form onSubmit={subscribe} className="mt-4 flex flex-col gap-2 sm:flex-row">
                  <input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    type="email"
                    placeholder="work email"
                    className="min-w-0 flex-1 rounded-md border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder-white/30 outline-none focus:border-teal-400/40"
                  />
                  <button
                    type="submit"
                    disabled={subStatus === "submitting"}
                    className="shrink-0 rounded-md px-4 py-2 text-sm font-semibold transition-opacity disabled:opacity-50"
                    style={{ color: "#0d0520", background: AMBER }}
                  >
                    {subStatus === "submitting" ? "Subscribing…" : "Subscribe"}
                  </button>
                </form>
                {subStatus === "success" && <p className="mt-2 text-xs" style={{ color: TEAL }}>Subscribed.</p>}
                {subStatus === "error" && <p className="mt-2 text-xs text-red-300">Could not subscribe — try again.</p>}
              </div>
            </div>
          </header>

          {loadStatus === "loading" && (
            <div className="mb-5 rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-3 text-sm text-white/50">
              Loading today&apos;s brief… {loadSec > 3 ? `${loadSec}s` : ""}
            </div>
          )}

          {loadStatus === "error" && (
            <div className="mb-5 rounded-lg border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-white/55">
              <p>Brief is refreshing — reload in a moment.</p>
              <button type="button" onClick={() => window.location.reload()} className="mt-2 text-xs font-semibold" style={{ color: TEAL }}>
                Reload
              </button>
            </div>
          )}

          {brief?.executive_take && (
            <NlSurface accent={PURPLE} icon={Sparkles} kicker="AI market analysis" title="Executive read">
              <p className="text-sm leading-relaxed text-white/75">{cleanScrapedText(brief.executive_take)}</p>

              {(macroItems.length > 0 || stratItems.length > 0) && (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  {macroItems.length > 0 && (
                    <div className="overflow-hidden rounded-md border border-white/[0.07] bg-black/15">
                      <div className="flex items-center gap-2 border-b border-white/[0.06] px-3 py-2">
                        <TrendingUp className="h-3.5 w-3.5" style={{ color: EMERALD }} />
                        <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: EMERALD }}>Macro trends</p>
                      </div>
                      <ul>
                        {macroItems.map((item, i) => {
                          const title = briefTextTitle(item);
                          const detail = briefTextDetail(item);
                          return (
                            <NlDataRow key={i} accent={EMERALD}>
                              {title && <p className="text-sm font-medium" style={{ color: EMERALD }}>{title}</p>}
                              {detail && <p className="mt-1 text-xs leading-relaxed text-white/50">{detail}</p>}
                            </NlDataRow>
                          );
                        })}
                      </ul>
                    </div>
                  )}
                  {stratItems.length > 0 && (
                    <div className="overflow-hidden rounded-md border border-white/[0.07] bg-black/15">
                      <div className="flex items-center gap-2 border-b border-white/[0.06] px-3 py-2">
                        <Radio className="h-3.5 w-3.5" style={{ color: AMBER }} />
                        <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: AMBER }}>Strategic implications</p>
                      </div>
                      <ul>
                        {stratItems.map((item, i) => {
                          const title = briefTextTitle(item);
                          const detail = briefTextDetail(item);
                          return (
                            <NlDataRow key={i} accent={AMBER}>
                              {title && <p className="text-sm font-medium" style={{ color: AMBER }}>{title}</p>}
                              {detail && <p className="mt-1 text-xs leading-relaxed text-white/50">{detail}</p>}
                            </NlDataRow>
                          );
                        })}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {(riskItems.length > 0 || watchItems.length > 0) && (
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {riskItems.length > 0 && (
                    <div className="rounded-md border border-red-400/15 bg-red-400/[0.04] px-3 py-2.5">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-red-400/80">Risks</p>
                      <ul className="mt-2 space-y-1 text-xs leading-relaxed text-white/55">
                        {riskItems.map((r, i) => <li key={i}>{r}</li>)}
                      </ul>
                    </div>
                  )}
                  {watchItems.length > 0 && (
                    <div className="rounded-md border border-teal-400/15 bg-teal-400/[0.04] px-3 py-2.5">
                      <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: TEAL }}>Watch next</p>
                      <ul className="mt-2 space-y-1 text-xs leading-relaxed text-white/55">
                        {watchItems.map((w, i) => <li key={i}>{w}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </NlSurface>
          )}

          {researchFindings.length > 0 && (
            <NlSurface
              accent={AMBER}
              icon={Zap}
              kicker="SIGNAL research"
              title="Account changes worth actioning"
              action={<NlLink href="/pipeline" color={AMBER}>Pipeline</NlLink>}
            >
              <ul className="overflow-hidden rounded-md border border-white/[0.07] bg-black/15">
                {researchFindings.map((finding, index) => (
                  <NlDataRow key={`${finding.company_id || finding.company}-${index}`} accent={AMBER}>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-white">{cleanScrapedText(finding.company) || "Lead"}</span>
                      <NlBadge label={cleanScrapedText(finding.category) || "Research"} color={AMBER} />
                      {finding.industry && (
                        <span className="text-[10px] text-white/35">{cleanScrapedText(finding.industry)}</span>
                      )}
                    </div>
                    <p className="mt-1.5 text-sm leading-relaxed text-white/60">
                      {cleanScrapedText(finding.summary || finding.title)}
                    </p>
                    <div className="mt-2">
                      <NlLink href={finding.pipeline_url || "/pipeline"} color={AMBER}>
                        {finding.action_label || "Open in pipeline"}
                      </NlLink>
                    </div>
                  </NlDataRow>
                ))}
              </ul>
            </NlSurface>
          )}

          {benchReport && (
            <NlSurface
              accent={PURPLE}
              icon={Bot}
              kicker="Robot intelligence benchmark"
              title={String(benchReport.title ?? "Humanoid robot benchmark")}
              action={<NlLink href="/robots" color={PURPLE}>Full index</NlLink>}
            >
              {((benchReport.top_3 as Array<{ name: string; vendor: string; score: number; status: string }>) ?? []).length > 0 && (
                <div className="mb-4 grid gap-2 sm:grid-cols-3">
                  {((benchReport.top_3 as Array<{ name: string; vendor: string; score: number; status: string }>) ?? []).map((r, i) => {
                    const rankColor = i === 0 ? "#34d399" : i === 1 ? PURPLE : AMBER;
                    return (
                      <div
                        key={r.name}
                        className="rounded-md border border-white/[0.08] bg-black/20 px-3 py-3"
                        style={{ borderTop: `2px solid ${rankColor}` }}
                      >
                        <p className="text-[9px] font-semibold uppercase tracking-widest text-white/35">
                          {["Leader", "2nd", "3rd"][i]}
                        </p>
                        <p className="mt-1 text-sm font-semibold text-white">{r.name}</p>
                        <p className="text-xs text-white/40">{r.vendor}</p>
                        <p className="mt-2 font-mono text-2xl font-bold leading-none" style={{ color: rankColor, fontFamily: "'JetBrains Mono', monospace" }}>
                          {r.score}
                        </p>
                      </div>
                    );
                  })}
                </div>
              )}

              {((benchReport.key_findings as string[]) ?? []).length > 0 && (
                <details className="group rounded-md border border-white/[0.07] bg-black/15">
                  <summary className="cursor-pointer list-none px-3 py-2.5 text-[10px] font-semibold uppercase tracking-wide text-white/40 transition-colors hover:text-white/55 [&::-webkit-details-marker]:hidden">
                    <span className="inline-flex items-center gap-2">
                      <span
                        className="inline-block text-[10px] transition-transform group-open:rotate-90"
                        style={{ color: PURPLE }}
                      >
                        ▸
                      </span>
                      Key findings
                      <span className="font-mono normal-case tracking-normal text-white/30">
                        ({((benchReport.key_findings as string[]) ?? []).length})
                      </span>
                    </span>
                  </summary>
                  <ul className="space-y-2 border-t border-white/[0.06] px-3 py-3">
                    {((benchReport.key_findings as string[]) ?? []).map((f, i) => (
                      <li key={i} className="flex gap-2 text-sm leading-relaxed text-white/65">
                        <span className="mt-2 h-1 w-1 shrink-0 rounded-full" style={{ background: PURPLE }} />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              )}

              <div className="mt-3 flex flex-wrap gap-3 text-[11px] font-mono text-white/40" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                <span>{String(benchReport.total_robots ?? 0)} scored</span>
                <span>{String(benchReport.available_count ?? 0)} available</span>
                <span>{String(benchReport.pilot_count ?? 0)} pilot</span>
              </div>
            </NlSurface>
          )}

          {loadStatus === "ready" && stories.length === 0 && (
            <div className="mb-5 rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-3 text-sm text-white/50">
              Stories are still syncing — reload in a moment.
            </div>
          )}

          {stories.length > 0 && (
            <NlSurface
              accent={EMERALD}
              icon={BarChart3}
              kicker={`Signal intelligence · ${stories.length}`}
              title="Companies moving toward automation"
              action={<NlLink href="/pipeline" color={EMERALD}>Pipeline</NlLink>}
            >
              <div className="grid gap-3 lg:grid-cols-2">
                {stories.map((story, index) => {
                  const bullets = signalBullets(story.fullText);
                  const color = index % 2 === 0 ? EMERALD : AMBER;
                  const category = cleanScrapedText(story.category) || "Signal";
                  return (
                    <article
                      key={`${story.company || story.headline || index}`}
                      className="group flex flex-col rounded-md border border-white/[0.08] bg-black/20 p-3 transition-colors hover:border-white/[0.14] hover:bg-black/30"
                      style={{ borderLeft: `3px solid ${color}` }}
                    >
                      <div className="mb-2 flex items-start justify-between gap-2">
                        <NlBadge label={category} color={color} />
                        {story.signalStrength ? (
                          <span className="font-mono text-[10px] text-white/35" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                            {story.signalStrength}/10
                          </span>
                        ) : null}
                      </div>
                      <h3 className="text-sm font-semibold leading-snug">
                        {story.company_id ? (
                          <Link
                            href={`/pipeline?lead=${story.company_id}`}
                            className="transition-opacity hover:opacity-85"
                            style={{ color }}
                          >
                            {cleanScrapedText(story.company || story.headline)}
                          </Link>
                        ) : (
                          <span style={{ color }}>{cleanScrapedText(story.company || story.headline)}</span>
                        )}
                      </h3>
                      <p className="mt-1.5 flex-1 text-xs leading-relaxed text-white/55">
                        {leadPreviewSentences(story.summary || story.snippet, 3, 420)
                          || "SIGNAL is tracking automation signals for this account."}
                      </p>
                      {bullets.length > 0 && (
                        <ul className="mt-2 space-y-1 border-t border-white/[0.06] pt-2 text-[11px] text-white/45">
                          {bullets.slice(0, 2).map((b, bi) => (
                            <li key={bi} className="flex gap-1.5">
                              <span className="text-white/25">·</span>
                              <span>{b}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                      <div className="mt-2 pt-1">
                        <NlLink href={story.company_id ? `/pipeline?lead=${story.company_id}` : "/pipeline"} color={color}>
                          Open in pipeline
                        </NlLink>
                      </div>
                    </article>
                  );
                })}
              </div>
            </NlSurface>
          )}

          <div className="mt-6 flex flex-wrap gap-4 rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-3 text-sm">
            <Link href="/results?url=" className="inline-flex items-center gap-2 font-bold" style={{ color: AMBER }}>
              Activate SIGNAL from today&apos;s brief <Zap className="h-4 w-4" />
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
