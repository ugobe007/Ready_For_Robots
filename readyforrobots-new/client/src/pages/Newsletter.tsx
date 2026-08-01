import React, { useEffect, useMemo, useState } from "react";
import { ArrowRight, BarChart3, Clock, Mail, Radio, Sparkles, TrendingUp, Zap } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import {
  fetchWithTimeout,
  getApiBase,
  liveFetchInit,
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
  tier?: string;
  industry?: string;
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

const TEAL = "#059669";
const AMBER = "#FFB000";
const VIOLET = "#7c3aed";
const NEWSLETTER_SESSION_KEY = "newsletter_edition_v3";
const NEWSLETTER_SESSION_TTL_MS = 30 * 60 * 1000;
const NEWSLETTER_BENCH_KEY = "newsletter_humanoid_report_v2";
const NEWSLETTER_BENCH_TTL_MS = 30 * 60 * 1000;

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
  const bullets: string[] = [];
  for (const line of fullText.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed.startsWith("•") && !trimmed.startsWith("-")) continue;
    const clean = trimmed.replace(/^[•\-]\s*/, "").replace(/\*\*/g, "").trim();
    if (!clean || clean.includes("<img") || clean.includes("<a href")) continue;
    const withoutHtml = clean.replace(/<[^>]*>/g, "").trim();
    if (withoutHtml.length > 24) bullets.push(withoutHtml.slice(0, 180));
    if (bullets.length >= 3) break;
  }
  return bullets;
}

function formatEditionUpdated(iso?: string, fallback?: string): string {
  if (iso) {
    try {
      return new Intl.DateTimeFormat("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short",
      }).format(new Date(iso));
    } catch {
      /* fall through */
    }
  }
  return fallback || "Today";
}

function storyScore(story: NewsletterStory): number | null {
  const impact = story.impact || "";
  const match = impact.match(/(\d+)\s*\/\s*100/);
  if (match) return Number(match[1]);
  if (story.signalStrength) return Math.min(100, story.signalStrength * 10);
  return null;
}

function tierFromStory(story: NewsletterStory): "HOT" | "WARM" | null {
  const tier = (story.tier || "").toUpperCase();
  if (tier === "HOT" || tier === "WARM") return tier;
  const score = storyScore(story);
  if (score == null) return null;
  if (score >= 80) return "HOT";
  if (score >= 60) return "WARM";
  return null;
}

function SectionShell({
  kicker,
  title,
  action,
  children,
  accent = TEAL,
}: {
  kicker: string;
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <section className="newsletter-section">
      <div className="newsletter-section-head" style={{ borderLeft: `4px solid ${accent}` }}>
        <div>
          <p className="newsletter-kicker">{kicker}</p>
          <h2 className="newsletter-section-title">{title}</h2>
        </div>
        {action}
      </div>
      <div className="px-5 py-5">{children}</div>
    </section>
  );
}

function TierBadge({ tier }: { tier: "HOT" | "WARM" | null }) {
  if (!tier) return null;
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
        tier === "HOT" ? "newsletter-tier-hot" : "newsletter-tier-warm"
      }`}
    >
      {tier}
    </span>
  );
}

function CategoryBadge({ label, color = TEAL }: { label: string; color?: string }) {
  return (
    <span
      className="inline-flex rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide"
      style={{ color, background: `${color}12`, borderColor: `${color}33` }}
    >
      {label}
    </span>
  );
}

function InlineLink({ href, children, color = TEAL }: { href: string; children: React.ReactNode; color?: string }) {
  return (
    <Link href={href} className="inline-flex items-center gap-1 text-sm font-bold hover:opacity-85" style={{ color }}>
      {children}
      <ArrowRight className="h-3.5 w-3.5" />
    </Link>
  );
}

function StoryCard({ story, featured = false }: { story: NewsletterStory; featured?: boolean }) {
  const bullets = signalBullets(story.fullText);
  const company = cleanScrapedText(story.company || story.headline) || "Lead";
  const category = cleanScrapedText(story.category) || "Signal";
  const tier = tierFromStory(story);
  const score = storyScore(story);
  const summary =
    leadPreviewSentences(story.summary || story.snippet, featured ? 4 : 2, featured ? 520 : 280)
    || "SIGNAL is tracking automation signals for this account.";
  const href = story.company_id ? `/pipeline?lead=${story.company_id}` : "/pipeline";

  if (featured) {
    return (
      <article className="newsletter-featured">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <CategoryBadge label={category} />
          <TierBadge tier={tier} />
          {score != null ? (
            <span className="font-mono-data text-xs font-bold text-gray-500">{score}/100 intent</span>
          ) : null}
          {story.industry ? (
            <span className="newsletter-meta">{cleanScrapedText(story.industry)}</span>
          ) : null}
        </div>
        <h3 className="font-display text-2xl font-bold tracking-tight text-gray-950 sm:text-3xl">
          <Link href={href} className="hover:text-emerald-700">{company}</Link>
        </h3>
        <p className="newsletter-body mt-4">{summary}</p>
        {bullets.length > 0 && (
          <ul className="mt-5 space-y-2 border-t border-gray-100 pt-4">
            {bullets.map((bullet, index) => (
              <li key={index} className="flex gap-2 text-sm leading-relaxed text-gray-800">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-6 flex flex-wrap gap-4">
          <InlineLink href={href}>Open in pipeline</InlineLink>
          <InlineLink href="/results?url=" color={AMBER}>Find similar buyers</InlineLink>
        </div>
      </article>
    );
  }

  return (
    <article className="newsletter-story-card">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <CategoryBadge label={category} color={tier === "HOT" ? AMBER : TEAL} />
        {score != null ? (
          <span className="font-mono-data text-[10px] font-bold text-gray-500">{score}</span>
        ) : null}
      </div>
      <h3 className="newsletter-story-title">
        <Link href={href} className="hover:text-emerald-700">{company}</Link>
      </h3>
      <p className="newsletter-story-copy">{summary}</p>
      <div className="mt-3 pt-2">
        <InlineLink href={href}>Pipeline</InlineLink>
      </div>
    </article>
  );
}

export default function Newsletter() {
  const [edition, setEdition] = useState<NewsletterEdition | null>(null);
  const [loadStatus, setLoadStatus] = useState<"loading" | "ready" | "error">("loading");
  const [refreshing, setRefreshing] = useState(false);
  const [email, setEmail] = useState("");
  const [subStatus, setSubStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  useEffect(() => {
    let cancelled = false;

    const cached =
      readSurfaceCache<NewsletterEdition>(NEWSLETTER_SESSION_KEY, NEWSLETTER_SESSION_TTL_MS)?.data
      ?? readSessionCache<NewsletterEdition>(NEWSLETTER_SESSION_KEY, NEWSLETTER_SESSION_TTL_MS);

    if (cached?.latestEdition && (cached.topStories?.length ?? 0) > 0) {
      setEdition(cached);
      setLoadStatus("ready");
    }

    const applyEdition = (data: NewsletterEdition | null) => {
      if (!data?.latestEdition || !(data.topStories?.length ?? 0)) return false;
      setEdition(data);
      setLoadStatus("ready");
      writeSurfaceCache(NEWSLETTER_SESSION_KEY, data);
      writeSessionCache(NEWSLETTER_SESSION_KEY, data);
      return true;
    };

    const load = async () => {
      if (!cached?.topStories?.length) setLoadStatus("loading");
      else setRefreshing(true);
      try {
        const res = await fetchWithTimeout(
          `${getApiBase()}/api/newsletter/edition?limit=15&_=${Date.now()}`,
          liveFetchInit({ cache: "no-store" }),
          12_000,
        );
        if (cancelled) return;
        const data = res.ok ? ((await res.json()) as NewsletterEdition) : null;
        if (applyEdition(data)) return;
        if (data?.latestEdition) setEdition(data);
        setLoadStatus((data?.topStories?.length ?? 0) > 0 || cached?.topStories?.length ? "ready" : "error");
      } catch {
        if (cancelled) return;
        if (!cached?.topStories?.length) setLoadStatus("error");
      } finally {
        if (!cancelled) setRefreshing(false);
      }
    };

    void load();
    return () => { cancelled = true; };
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

  const stories = useMemo(() => (edition?.topStories || []).slice(0, 14), [edition?.topStories]);
  const featuredStory = stories[0] ?? null;
  const gridStories = stories.slice(1);
  const researchFindings = (edition?.researchFindings || []).slice(0, 6);
  const brief = edition?.industryBrief;
  const headline = cleanScrapedText(edition?.latestEdition?.headline) || "Who is buying robots this week";
  const subheadline =
    cleanScrapedText(edition?.latestEdition?.subheadline)
    || "Daily brief for robotics sales teams — CapEx moves, labor pressure, deployments, and executive hires sourced from SIGNAL.";
  const updatedLabel = formatEditionUpdated(
    edition?.summary?.generated_at,
    edition?.latestEdition?.date,
  );

  const benchCached = readSurfaceCache<Record<string, unknown>>(NEWSLETTER_BENCH_KEY, NEWSLETTER_BENCH_TTL_MS);
  const [benchReport, setBenchReport] = useState<Record<string, unknown> | null>(benchCached?.data ?? null);

  useEffect(() => {
    if (loadStatus !== "ready") return;
    const timer = window.setTimeout(() => {
      void fetchWithTimeout(`${getApiBase()}/api/humanoid/report`, liveFetchInit({ cache: "no-store" }), 8_000)
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

  return (
    <div className="newsletter-page min-h-screen flex flex-col">
      <Header />

      <PageHeroDark
        maxWidthClass="max-w-6xl"
        eyebrow={
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            Robot Intelligence Brief · {edition?.latestEdition?.edition || "Daily edition"}
          </span>
        }
        title={headline}
        description={<p className="max-w-2xl text-sm leading-relaxed text-slate-300 sm:text-base">{subheadline}</p>}
        stats={[
          { label: "Hot leads", value: edition?.summary?.total_leads ?? stories.length ?? "—", tone: "amber" },
          { label: "Stories", value: stories.length || "…", tone: "emerald" },
          { label: "Research", value: researchFindings.length || "0", tone: "white" },
          { label: "Edition", value: edition?.latestEdition?.edition?.replace(/^Edition\s*/i, "#") || "—", tone: "white" },
        ]}
      >
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
          <form onSubmit={subscribe} className="flex w-full max-w-xl flex-col gap-2 sm:flex-row">
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              placeholder="Work email for the daily brief"
              className="newsletter-subscribe-input"
            />
            <button type="submit" disabled={subStatus === "submitting"} className="newsletter-subscribe-btn">
              {subStatus === "submitting" ? "Subscribing…" : "Subscribe free"}
            </button>
          </form>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Clock className="h-3.5 w-3.5 shrink-0" />
            <span>
              Updated {updatedLabel}
              {refreshing ? " · refreshing…" : ""}
            </span>
          </div>
        </div>
        {subStatus === "success" && (
          <p className="mt-3 text-sm font-medium text-emerald-300">You&apos;re in — check your inbox for the welcome note.</p>
        )}
        {subStatus === "error" && (
          <p className="mt-3 text-sm font-medium text-red-300">Could not subscribe. Try again in a moment.</p>
        )}
      </PageHeroDark>

      <div className="page-dark-shell-fade" />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-20 pt-8 lg:px-6">
        {loadStatus === "loading" && !edition?.topStories?.length && (
          <div className="newsletter-section px-5 py-8 text-center">
            <p className="newsletter-body font-medium">Loading today&apos;s brief from SIGNAL…</p>
          </div>
        )}

        {loadStatus === "error" && !stories.length && (
          <div className="mb-8 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4">
            <p className="text-sm font-semibold text-amber-950">Brief is still syncing.</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-2 text-sm font-bold text-emerald-700"
            >
              Reload page
            </button>
          </div>
        )}

        {featuredStory && (
          <div className="mb-8">
            <p className="newsletter-kicker mb-3">Lead story</p>
            <StoryCard story={featuredStory} featured />
          </div>
        )}

        {brief?.executive_take && (
          <SectionShell kicker="Market read" title="What changed in automation demand" accent={VIOLET}>
            <p className="newsletter-body">{cleanScrapedText(brief.executive_take)}</p>
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {(brief.macro_trends || []).slice(0, 3).map((item, index) => {
                const title = briefTextTitle(item);
                const detail = briefTextDetail(item);
                if (!title && !detail) return null;
                return (
                  <div key={index} className="rounded-xl border border-gray-100 bg-slate-50 p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-emerald-600" />
                      <p className="text-sm font-bold text-gray-950">{title}</p>
                    </div>
                    {detail ? <p className="text-sm leading-relaxed text-gray-700">{detail}</p> : null}
                  </div>
                );
              })}
              {(brief.strategic_implications || []).slice(0, 3).map((item, index) => {
                const title = briefTextTitle(item);
                const detail = briefTextDetail(item);
                if (!title && !detail) return null;
                return (
                  <div key={`s-${index}`} className="rounded-xl border border-gray-100 bg-slate-50 p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <Radio className="h-4 w-4 text-amber-600" />
                      <p className="text-sm font-bold text-gray-950">{title}</p>
                    </div>
                    {detail ? <p className="text-sm leading-relaxed text-gray-700">{detail}</p> : null}
                  </div>
                );
              })}
            </div>
          </SectionShell>
        )}

        {researchFindings.length > 0 && (
          <SectionShell
            kicker="SIGNAL research"
            title="Account moves worth actioning today"
            accent={AMBER}
            action={<InlineLink href="/pipeline" color={AMBER}>Full pipeline</InlineLink>}
          >
            <ul className="divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200">
              {researchFindings.map((finding, index) => (
                <li key={`${finding.company_id || finding.company}-${index}`} className="px-4 py-4 hover:bg-slate-50">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-base font-bold text-gray-950">{cleanScrapedText(finding.company) || "Lead"}</span>
                    <CategoryBadge label={cleanScrapedText(finding.category) || "Research"} color={AMBER} />
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-gray-700">
                    {cleanScrapedText(finding.summary || finding.title)}
                  </p>
                  <div className="mt-3">
                    <InlineLink href={finding.pipeline_url || "/pipeline"} color={AMBER}>
                      {finding.action_label || "Run in SIGNAL"}
                    </InlineLink>
                  </div>
                </li>
              ))}
            </ul>
          </SectionShell>
        )}

        {gridStories.length > 0 && (
          <SectionShell
            kicker={`${gridStories.length + (featuredStory ? 1 : 0)} accounts`}
            title="More companies moving toward automation"
            accent={TEAL}
            action={<InlineLink href="/pipeline">Pipeline</InlineLink>}
          >
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {gridStories.map((story, index) => (
                <StoryCard key={`${story.company_id || story.company}-${index}`} story={story} />
              ))}
            </div>
          </SectionShell>
        )}

        {benchReport && (
          <SectionShell
            kicker="Benchmark"
            title={String(benchReport.title ?? "Humanoid robot index")}
            accent={VIOLET}
            action={<InlineLink href="/robots" color={VIOLET}>Full index</InlineLink>}
          >
            <div className="grid gap-3 sm:grid-cols-3">
              {((benchReport.top_3 as Array<{ name: string; vendor: string; score: number }>) ?? []).map((robot, index) => (
                <div key={robot.name} className="rounded-xl border border-gray-200 bg-slate-50 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                    {["Leader", "2nd", "3rd"][index]}
                  </p>
                  <p className="mt-1 font-display text-base font-bold text-gray-950">{robot.name}</p>
                  <p className="text-sm text-gray-600">{robot.vendor}</p>
                  <p className="font-mono-data mt-2 text-2xl font-black text-emerald-600">{robot.score}</p>
                </div>
              ))}
            </div>
          </SectionShell>
        )}

        <section className="mt-10 grid gap-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:grid-cols-3">
          <Link href="/results?url=" className="group rounded-xl border border-amber-200 bg-amber-50 p-4 transition hover:border-amber-300">
            <Zap className="h-5 w-5 text-amber-600" />
            <p className="mt-2 font-display text-base font-bold text-gray-950 group-hover:text-amber-900">Scan your market</p>
            <p className="mt-1 text-sm text-gray-700">Paste a vendor URL and get matched buyer signals.</p>
          </Link>
          <Link href="/signals" className="group rounded-xl border border-emerald-200 bg-emerald-50 p-4 transition hover:border-emerald-300">
            <BarChart3 className="h-5 w-5 text-emerald-700" />
            <p className="mt-2 font-display text-base font-bold text-gray-950 group-hover:text-emerald-900">Live signals</p>
            <p className="mt-1 text-sm text-gray-700">Browse every signal type SIGNAL monitors.</p>
          </Link>
          <Link href="/intelligence" className="group rounded-xl border border-violet-200 bg-violet-50 p-4 transition hover:border-violet-300">
            <Sparkles className="h-5 w-5 text-violet-700" />
            <p className="mt-2 font-display text-base font-bold text-gray-950 group-hover:text-violet-900">Intelligence report</p>
            <p className="mt-1 text-sm text-gray-700">How we score intent and robot fit.</p>
          </Link>
        </section>

        <div className="mt-8 flex flex-col items-start gap-3 rounded-2xl border border-gray-200 bg-gray-950 px-6 py-6 text-white sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="flex items-center gap-2 text-sm font-bold text-emerald-300">
              <Mail className="h-4 w-4" />
              Daily brief in your inbox
            </p>
            <p className="mt-1 max-w-lg text-sm text-slate-300">
              Same stories as this page — curated for robotics GTM teams every morning.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-bold text-gray-950"
          >
            Subscribe at top
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
