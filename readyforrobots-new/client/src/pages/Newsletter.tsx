import React, { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Zap } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import {
  fetchWithTimeout,
  getApiBase,
  liveFetchInit,
  publicFetchInit,
  readSessionCache,
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
const NEWSLETTER_SESSION_KEY = "newsletter_edition_v1";
const NEWSLETTER_SESSION_TTL_MS = 30 * 60 * 1000;

/** Supabase-style section chrome — label + flow, no padded panels */
function NlSection({
  kicker,
  title,
  kickerColor = TEAL,
  action,
  children,
  className = "",
}: {
  kicker: string;
  title?: string;
  kickerColor?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`border-b border-white/[0.08] pb-8 mb-8 last:border-b-0 ${className}`}>
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em]" style={{ color: kickerColor }}>{kicker}</p>
          {title ? (
            <h2 className="mt-1 text-base font-semibold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>{title}</h2>
          ) : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function NlDividerList({ children }: { children: React.ReactNode }) {
  return <ul className="divide-y divide-white/[0.06]">{children}</ul>;
}

function NlRow({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <li className={`py-3 first:pt-0 last:pb-0 ${className}`}>{children}</li>;
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

    const cached = readSessionCache<NewsletterEdition>(NEWSLETTER_SESSION_KEY, NEWSLETTER_SESSION_TTL_MS);
    if (cached?.latestEdition && (cached.topStories?.length ?? 0) > 0) {
      setEdition(cached);
      setLoadStatus("ready");
    }

    const applyEdition = (data: NewsletterEdition | null) => {
      if (!data?.latestEdition) return false;
      const storyCount = Array.isArray(data.topStories) ? data.topStories.length : 0;
      if (storyCount > 0) {
        setEdition(data);
        setLoadStatus("ready");
        writeSessionCache(NEWSLETTER_SESSION_KEY, data);
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

    void load(0);

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
  const [benchReport, setBenchReport] = useState<Record<string, unknown> | null>(null);
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
        .then((d) => (d?.report ? setBenchReport(d.report) : null))
        .catch(() => null);
    }, 400);
    return () => window.clearTimeout(timer);
  }, [loadStatus]);
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
        <div className="mx-auto max-w-3xl">

          {/* ── Hero ─────────────────────────────────────────────────── */}
          <header className="mb-8 border-b border-white/[0.08] pb-8">
            <p className="mb-3 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em]" style={{ color: TEAL }}>
              <span className="h-1 w-1 rounded-full" style={{ background: TEAL }} />
              Robot Intelligence Brief · {edition?.latestEdition?.edition || "Daily"} · {edition?.latestEdition?.date || "Updated daily"}
            </p>
            <h1 className="text-2xl font-semibold leading-snug text-white lg:text-3xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              {headline}
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-white/55">{subheadline}</p>

            <dl className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-xs text-white/40">
              {[
                { label: "Edition", value: edition?.latestEdition?.edition || "—" },
                { label: "Updated", value: edition?.latestEdition?.date || "Daily" },
                { label: "Hot leads", value: String(edition?.summary?.total_leads ?? stories.length) },
                { label: "Stories", value: String(stories.length || (loadStatus === "loading" ? "…" : "—")) },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-baseline gap-2">
                  <dt className="uppercase tracking-wider text-white/30">{label}</dt>
                  <dd className="font-mono font-medium text-white/70" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{value}</dd>
                </div>
              ))}
            </dl>

            <form onSubmit={subscribe} className="mt-6 flex flex-col gap-2 sm:flex-row sm:items-center">
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                placeholder="work email"
                className="min-w-0 flex-1 border border-white/10 bg-transparent px-3 py-2 text-sm text-white placeholder-white/30 outline-none focus:border-white/25"
              />
              <button
                type="submit"
                disabled={subStatus === "submitting"}
                className="shrink-0 border px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-50"
                style={{ color: AMBER, borderColor: `${AMBER}66` }}
              >
                {subStatus === "submitting" ? "Subscribing…" : "Subscribe"}
              </button>
            </form>
            {subStatus === "success" && <p className="mt-2 text-xs" style={{ color: TEAL }}>Subscribed.</p>}
            {subStatus === "error" && <p className="mt-2 text-xs text-red-300">Could not subscribe — try again.</p>}
          </header>

          {loadStatus === "loading" && (
            <p className="mb-8 border-b border-white/[0.08] pb-8 text-sm text-white/45">
              Loading today&apos;s brief… {loadSec > 3 ? `${loadSec}s` : ""}
            </p>
          )}

          {loadStatus === "error" && (
            <div className="mb-8 border-b border-white/[0.08] pb-8 text-sm text-white/45">
              <p>Brief is refreshing — reload in a moment.</p>
              <button type="button" onClick={() => window.location.reload()} className="mt-3 text-xs font-semibold" style={{ color: TEAL }}>
                Reload
              </button>
            </div>
          )}

          {brief?.executive_take && (
            <NlSection kicker="AI market analysis" kickerColor={PURPLE}>
              <p className="text-sm leading-relaxed text-white/70">{cleanScrapedText(brief.executive_take)}</p>

              {macroItems.length > 0 && (
                <div className="mt-6">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">Macro trends</p>
                  <NlDividerList>
                    {macroItems.map((item, i) => {
                      const title = briefTextTitle(item);
                      const detail = briefTextDetail(item);
                      return (
                        <NlRow key={i}>
                          {title && <p className="text-sm font-medium text-white/90">{title}</p>}
                          {detail && <p className="mt-1 text-sm leading-relaxed text-white/50">{detail}</p>}
                        </NlRow>
                      );
                    })}
                  </NlDividerList>
                </div>
              )}

              {stratItems.length > 0 && (
                <div className="mt-6">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">Strategic implications</p>
                  <NlDividerList>
                    {stratItems.map((item, i) => {
                      const title = briefTextTitle(item);
                      const detail = briefTextDetail(item);
                      return (
                        <NlRow key={i}>
                          {title && <p className="text-sm font-medium text-white/90">{title}</p>}
                          {detail && <p className="mt-1 text-sm leading-relaxed text-white/50">{detail}</p>}
                        </NlRow>
                      );
                    })}
                  </NlDividerList>
                </div>
              )}

              {riskItems.length > 0 && (
                <div className="mt-6">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-red-400/80">Risks to watch</p>
                  <ul className="space-y-1.5 text-sm leading-relaxed text-white/50">
                    {riskItems.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {watchItems.length > 0 && (
                <div className="mt-6">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">Watch next</p>
                  <ul className="space-y-1.5 text-sm leading-relaxed text-white/50">
                    {watchItems.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </NlSection>
          )}

          {researchFindings.length > 0 && (
            <NlSection
              kicker="SCOUT research findings"
              title="Account changes worth actioning today"
              kickerColor={AMBER}
              action={(
                <Link href="/pipeline" className="text-xs font-semibold text-white/45 hover:text-white/70">
                  Pipeline <ArrowRight className="inline h-3 w-3" />
                </Link>
              )}
            >
              <NlDividerList>
                {researchFindings.map((finding, index) => (
                  <NlRow key={`${finding.company_id || finding.company}-${index}`}>
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                      <span className="text-sm font-medium text-white">{cleanScrapedText(finding.company) || "Lead"}</span>
                      <span className="text-[10px] uppercase tracking-wider text-white/35">
                        {cleanScrapedText(finding.category) || "Research"}
                        {finding.industry ? ` · ${cleanScrapedText(finding.industry)}` : ""}
                      </span>
                    </div>
                    <p className="mt-1 text-sm leading-relaxed text-white/55">
                      {cleanScrapedText(finding.summary || finding.title)}
                    </p>
                    <Link href={finding.pipeline_url || "/pipeline"} className="mt-2 inline-block text-xs font-semibold text-white/45 hover:text-white/70">
                      {finding.action_label || "Open in pipeline"} →
                    </Link>
                  </NlRow>
                ))}
              </NlDividerList>
            </NlSection>
          )}

          {benchReport && (
            <NlSection
              kicker="Robot intelligence benchmark"
              title={String(benchReport.title ?? "Humanoid robot benchmark")}
              kickerColor={PURPLE}
              action={(
                <Link href="/robots" className="text-xs font-semibold text-white/45 hover:text-white/70">
                  Full index <ArrowRight className="inline h-3 w-3" />
                </Link>
              )}
            >
              {((benchReport.top_3 as Array<{ name: string; vendor: string; score: number; status: string }>) ?? []).length > 0 && (
                <div className="mb-6">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">Top ranked</p>
                  <NlDividerList>
                    {((benchReport.top_3 as Array<{ name: string; vendor: string; score: number; status: string }>) ?? []).map((r, i) => (
                      <NlRow key={r.name}>
                        <div className="flex items-baseline justify-between gap-4">
                          <div>
                            <span className="text-[10px] uppercase tracking-wider text-white/30 mr-2">
                              {["1", "2", "3"][i]}
                            </span>
                            <span className="text-sm font-medium text-white">{r.name}</span>
                            <span className="ml-2 text-sm text-white/40">{r.vendor}</span>
                          </div>
                          <span className="font-mono text-sm font-medium text-white/70" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                            {r.score}
                          </span>
                        </div>
                      </NlRow>
                    ))}
                  </NlDividerList>
                </div>
              )}

              {((benchReport.key_findings as string[]) ?? []).length > 0 && (
                <div>
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">Key findings</p>
                  <ul className="space-y-2 text-sm leading-relaxed text-white/60">
                    {((benchReport.key_findings as string[]) ?? []).map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              <p className="mt-4 text-xs text-white/35">
                {String(benchReport.total_robots ?? 0)} robots scored · {String(benchReport.available_count ?? 0)} commercially available · {String(benchReport.pilot_count ?? 0)} in pilot
              </p>
            </NlSection>
          )}

          {loadStatus === "ready" && stories.length === 0 && (
            <p className="mb-8 text-sm text-white/45">Stories are still syncing — reload in a moment.</p>
          )}

          {stories.length > 0 && (
            <NlSection
              kicker={`Signal intelligence · ${stories.length} accounts`}
              title="Companies moving toward automation now"
              action={(
                <Link href="/pipeline" className="text-xs font-semibold text-white/45 hover:text-white/70">
                  Pipeline <ArrowRight className="inline h-3 w-3" />
                </Link>
              )}
            >
              <NlDividerList>
                {stories.map((story, index) => {
                  const bullets = signalBullets(story.fullText);
                  const color = tierColor(story.category);
                  const meta = [story.economics, story.impact, story.roi]
                    .map((chip) => cleanScrapedText(chip))
                    .filter(Boolean)
                    .join(" · ");
                  return (
                    <NlRow key={`${story.company || story.headline || index}`}>
                      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                        <span className="text-sm font-medium text-white">{cleanScrapedText(story.company || story.headline)}</span>
                        <span className="text-[10px] uppercase tracking-wider" style={{ color: `${color}cc` }}>
                          {cleanScrapedText(story.category) || "Signal"}
                        </span>
                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-white/55">
                        {leadPreviewSentences(story.summary || story.snippet, 3, 480)
                          || "SCOUT is tracking automation signals for this account."}
                      </p>
                      {bullets.length > 0 && (
                        <ul className="mt-2 space-y-1 text-sm text-white/45">
                          {bullets.map((b, bi) => (
                            <li key={bi}>{b}</li>
                          ))}
                        </ul>
                      )}
                      {meta && <p className="mt-2 text-xs text-white/35">{meta}</p>}
                      <Link
                        href={story.company_id ? `/pipeline#${story.company_id}` : "/pipeline"}
                        className="mt-2 inline-block text-xs font-semibold text-white/45 hover:text-white/70"
                      >
                        Open in pipeline →
                      </Link>
                    </NlRow>
                  );
                })}
              </NlDividerList>
            </NlSection>
          )}

          <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 border-t border-white/[0.08] pt-6 text-sm text-white/40">
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
