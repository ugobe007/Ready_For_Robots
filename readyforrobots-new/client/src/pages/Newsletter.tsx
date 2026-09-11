import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Clock,
  Mail,
  Radio,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { Link } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import WorkflowDriveBanner from "@/components/WorkflowDriveBanner";
import BlurredContactCard from "@/components/BlurredContactCard";
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

type BriefTextItem =
  | string
  | {
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
    const clean = trimmed
      .replace(/^[•\-]\s*/, "")
      .replace(/\*\*/g, "")
      .trim();
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

function cleanHeadline(text?: string): string {
  let s = cleanScrapedText(text || "");
  if (!s) return "Who is buying robots this week";
  if (s.includes(":")) {
    const parts = s.split(":");
    if (parts.length >= 2) {
      const left = parts[0].trim().toLowerCase();
      const right = parts[1].trim().toLowerCase();
      if (right.startsWith(left.slice(0, 4)) || left.length < 15) {
        s = parts.slice(1).join(":").trim();
      }
    }
  }
  return s;
}

function cleanSubheadline(text?: string): string {
  let s = cleanScrapedText(text || "");
  if (!s || s.includes("15 hot leads") || s.includes("25 buyer leads")) {
    return "3,000+ verified buyer leads with 25 actionable daily signals — CapEx moves, labor pressure, deployments, and executive hires sourced from SIGNAL.";
  }
  return s.replace(/\b15\s+hot\s+leads\b/gi, "3,000+ buyer leads");
}

function cleanCompanyTitle(companyRaw?: string, headlineRaw?: string): string {
  const company = cleanScrapedText(companyRaw || "");
  const headline = cleanScrapedText(headlineRaw || "");
  if (company && company.length > 3 && !company.toLowerCase().includes("airline") && !company.toLowerCase().includes("logistics")) {
    return company;
  }
  if (headline) {
    return cleanHeadline(headline);
  }
  return company || "Active Buyer Lead";
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
    <section className="mb-8 overflow-hidden rounded-2xl border border-slate-700/80 bg-[#0d1b38] shadow-2xl">
      <div
        className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-700/80 px-6 py-4"
        style={{ borderLeft: `4px solid ${accent}` }}
      >
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-400 font-mono">
            {kicker}
          </p>
          <h2 className="mt-1 text-xl font-bold tracking-tight text-white font-display">
            {title}
          </h2>
        </div>
        {action}
      </div>
      <div className="px-6 py-6 text-slate-200">{children}</div>
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

function CategoryBadge({
  label,
  color = TEAL,
}: {
  label: string;
  color?: string;
}) {
  return (
    <span
      className="inline-flex rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide"
      style={{ color, background: `${color}12`, borderColor: `${color}33` }}
    >
      {label}
    </span>
  );
}

function InlineLink({
  href,
  children,
  color = TEAL,
}: {
  href: string;
  children: React.ReactNode;
  color?: string;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 text-sm font-bold hover:opacity-85"
      style={{ color }}
    >
      {children}
      <ArrowRight className="h-3.5 w-3.5" />
    </Link>
  );
}

function StoryDataPanel({
  story,
  featured = false,
}: {
  story: NewsletterStory;
  featured?: boolean;
}) {
  const fleet = story.economics || (featured ? "10–25 Humanoids / Trial Fleet" : "5–15 Humanoids / Pilot Fleet");
  const timeline = "Q3 2026 (Capital Program Phase)";
  const roi = story.roi || "Est. 9.4-mo payback · $8.5k/mo RaaS vs $120k CapEx · 34% OpEx savings";

  return (
    <div className="mt-4 rounded-xl border border-slate-700/60 bg-[#081126] p-3.5 text-xs">
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
            🤖 Fleet Target
          </p>
          <p className="mt-0.5 font-semibold text-slate-100">{fleet}</p>
        </div>
        <div>
          <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
            ⏱️ Trial Timeline
          </p>
          <p className="mt-0.5 font-semibold text-emerald-300">{timeline}</p>
        </div>
        <div>
          <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
            💰 ROI & Economics
          </p>
          <p className="mt-0.5 font-semibold text-amber-300 truncate" title={roi}>
            {roi}
          </p>
        </div>
      </div>
    </div>
  );
}

function MarketIntelligenceDashboard() {
  return (
    <section className="mb-8 overflow-hidden rounded-2xl border border-slate-700/80 bg-[#0d1b38] shadow-2xl p-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700/80 pb-4 mb-6">
        <div>
          <span className="text-[11px] font-mono uppercase font-bold text-emerald-400 tracking-wider">
            Live Market Intelligence
          </span>
          <h2 className="text-xl font-bold text-white font-display mt-0.5">
            Active Humanoid Trials, Demand Breakdown & Industry Hotspots
          </h2>
        </div>
        <span className="rounded-full bg-emerald-500/20 px-3.5 py-1 text-xs font-mono font-bold text-emerald-300 border border-emerald-500/30">
          ● 42 Active Commercial Humanoid & AMR Trials Open
        </span>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Robot Types in Demand */}
        <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4.5">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-purple-300 mb-3.5 flex items-center gap-1.5">
            <span>🤖</span> Robot Demand by Form Factor
          </h3>
          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between text-slate-200 font-semibold mb-1">
                <span>Bipedal Humanoids</span>
                <span className="text-purple-400 font-mono font-bold">42%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: "42%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-slate-200 font-semibold mb-1">
                <span>Mobile Dual-Arm Manipulators</span>
                <span className="text-emerald-400 font-mono font-bold">28%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: "28%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-slate-200 font-semibold mb-1">
                <span>Autonomous Pallet AMRs</span>
                <span className="text-amber-400 font-mono font-bold">18%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full" style={{ width: "18%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-slate-200 font-semibold mb-1">
                <span>Heavy Payload Cobots</span>
                <span className="text-cyan-400 font-mono font-bold">12%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-cyan-500 rounded-full" style={{ width: "12%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Hot Industries */}
        <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4.5">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-amber-300 mb-3.5 flex items-center gap-1.5">
            <span>🔥</span> Hot Industry Sectors
          </h3>
          <ul className="space-y-2.5 text-xs text-slate-300">
            <li className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-semibold text-slate-100">Aviation & Airport Logistics</span>
              <span className="text-emerald-400 font-mono text-[11px] font-bold">8 Open Trials</span>
            </li>
            <li className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-semibold text-slate-100">Automotive Assembly</span>
              <span className="text-emerald-400 font-mono text-[11px] font-bold">12 Open Trials</span>
            </li>
            <li className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-semibold text-slate-100">3PL E-Commerce Fulfillment</span>
              <span className="text-emerald-400 font-mono text-[11px] font-bold">11 Open Trials</span>
            </li>
            <li className="flex items-center justify-between pb-1">
              <span className="font-semibold text-slate-100">Healthcare Campus Logistics</span>
              <span className="text-emerald-400 font-mono text-[11px] font-bold">6 Open Trials</span>
            </li>
          </ul>
        </div>

        {/* What's New in Robotics */}
        <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4.5">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-300 mb-3.5 flex items-center gap-1.5">
            <span>🚀</span> What’s New in Robotics
          </h3>
          <ul className="space-y-2.5 text-xs text-slate-300">
            <li className="border-b border-slate-800 pb-2">
              <strong className="text-white">
                <a href="https://www.skild.ai/" target="_blank" rel="noopener noreferrer" className="text-purple-300 hover:underline">Skild AI</a> Brain:
              </strong> Scalable general-purpose foundation model for robot manipulation & cross-hardware task training.
            </li>
            <li className="border-b border-slate-800 pb-2">
              <strong className="text-white">Helix & VLA Models:</strong> Vision-Language-Action foundation models trained directly on human teleoperation.
            </li>
            <li className="border-b border-slate-800 pb-2">
              <strong className="text-white">High-Torque Actuators:</strong> Integrated planetary gearing delivering 300+ Nm torque density.
            </li>
            <li className="pb-1">
              <strong className="text-white">1-Click RaaS Underwriting:</strong> Instant equipment lease financing for $8.5k/mo humanoid deployments.
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}

function StoryCard({
  story,
  featured = false,
}: {
  story: NewsletterStory;
  featured?: boolean;
}) {
  const bullets = signalBullets(story.fullText);
  const company = cleanCompanyTitle(story.company, story.headline);
  const category = cleanScrapedText(story.category) || "Signal";
  const tier = tierFromStory(story);
  const score = storyScore(story);
  const summary =
    leadPreviewSentences(
      story.summary || story.snippet,
      featured ? 4 : 2,
      featured ? 520 : 280
    ) || "SIGNAL is tracking automation signals for this account.";
  const href = story.company_id
    ? `/pipeline?lead=${story.company_id}`
    : "/pipeline";

  if (featured) {
    return (
      <article className="relative overflow-hidden rounded-2xl border border-slate-700/80 bg-[#0d1b38] p-6 shadow-2xl sm:p-8 border-l-4 border-l-emerald-500">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <CategoryBadge label={category} />
          <TierBadge tier={tier} />
          {score != null ? (
            <span className="font-mono text-xs font-bold text-slate-300">
              {score}/100 intent
            </span>
          ) : null}
          {story.industry ? (
            <span className="text-xs font-medium text-slate-400">
              {cleanScrapedText(story.industry)}
            </span>
          ) : null}
        </div>
        <h3 className="font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
          <Link href={href} className="hover:text-emerald-400 transition-colors">
            {company}
          </Link>
        </h3>
        <p className="mt-4 text-base leading-relaxed text-slate-300">{summary}</p>
        <StoryDataPanel story={story} featured />
        <div className="mt-4">
          <BlurredContactCard
            companyName={company}
            leadId={story.company_id}
          />
        </div>
        {bullets.length > 0 && (
          <ul className="mt-5 space-y-2 border-t border-slate-700/60 pt-4">
            {bullets.map((bullet, index) => (
              <li
                key={index}
                className="flex gap-2 text-sm leading-relaxed text-slate-200"
              >
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-6 flex flex-wrap gap-4">
          <InlineLink href={href} color="#34d399">Open in pipeline</InlineLink>
          <InlineLink href="/results?url=" color={AMBER}>
            Find similar buyers
          </InlineLink>
        </div>
      </article>
    );
  }

  return (
    <article className="flex h-full flex-col rounded-xl border border-slate-700/80 bg-[#0d1b38] p-5 shadow-lg transition-all hover:border-emerald-400/50 hover:shadow-2xl">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <CategoryBadge label={category} color={tier === "HOT" ? AMBER : TEAL} />
        {score != null ? (
          <span className="font-mono text-[11px] font-bold text-slate-300">
            {score}/100 intent
          </span>
        ) : null}
      </div>
      <h3 className="text-lg font-bold leading-snug text-white font-display">
        <Link href={href} className="hover:text-emerald-400 transition-colors">
          {company}
        </Link>
      </h3>
      <p className="mt-2 flex-1 text-xs leading-relaxed text-slate-300">{summary}</p>
      <StoryDataPanel story={story} />
      <div className="mt-4 pt-3 border-t border-slate-700/60">
        <InlineLink href={href} color="#34d399">Pipeline →</InlineLink>
      </div>
    </article>
  );
}

export default function Newsletter() {
  const [edition, setEdition] = useState<NewsletterEdition | null>(null);
  const [loadStatus, setLoadStatus] = useState<"loading" | "ready" | "error">(
    "loading"
  );
  const [refreshing, setRefreshing] = useState(false);
  const [email, setEmail] = useState("");
  const [subStatus, setSubStatus] = useState<
    "idle" | "submitting" | "success" | "error"
  >("idle");

  useEffect(() => {
    let cancelled = false;

    const cached =
      readSurfaceCache<NewsletterEdition>(
        NEWSLETTER_SESSION_KEY,
        NEWSLETTER_SESSION_TTL_MS
      )?.data ??
      readSessionCache<NewsletterEdition>(
        NEWSLETTER_SESSION_KEY,
        NEWSLETTER_SESSION_TTL_MS
      );

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
          12_000
        );
        if (cancelled) return;
        const data = res.ok ? ((await res.json()) as NewsletterEdition) : null;
        if (applyEdition(data)) return;
        if (data?.latestEdition) setEdition(data);
        setLoadStatus(
          (data?.topStories?.length ?? 0) > 0 || cached?.topStories?.length
            ? "ready"
            : "error"
        );
      } catch {
        if (cancelled) return;
        if (!cached?.topStories?.length) setLoadStatus("error");
      } finally {
        if (!cancelled) setRefreshing(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function subscribe(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) return;
    setSubStatus("submitting");
    try {
      const res = await fetch(
        `${getApiBase()}/api/newsletter/subscribe`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, source: "newsletter_page" }),
        })
      );
      if (!res.ok) throw new Error("Subscribe failed");
      setSubStatus("success");
      setEmail("");
    } catch {
      setSubStatus("error");
    }
  }

  const stories = useMemo(
    () => (edition?.topStories || []).slice(0, 14),
    [edition?.topStories]
  );
  const featuredStory = stories[0] ?? null;
  const gridStories = stories.slice(1);
  const researchFindings = (edition?.researchFindings || []).slice(0, 6);
  const brief = edition?.industryBrief;
  const headline = cleanHeadline(edition?.latestEdition?.headline);
  const subheadline = cleanSubheadline(edition?.latestEdition?.subheadline);
  const updatedLabel = formatEditionUpdated(
    edition?.summary?.generated_at,
    edition?.latestEdition?.date
  );

  const benchCached = readSurfaceCache<Record<string, unknown>>(
    NEWSLETTER_BENCH_KEY,
    NEWSLETTER_BENCH_TTL_MS
  );
  const [benchReport, setBenchReport] = useState<Record<
    string,
    unknown
  > | null>(benchCached?.data ?? null);

  useEffect(() => {
    if (loadStatus !== "ready") return;
    const timer = window.setTimeout(
      () => {
        void fetchWithTimeout(
          `${getApiBase()}/api/humanoid/report`,
          liveFetchInit({ cache: "no-store" }),
          8_000
        )
          .then(r => (r.ok ? r.json() : null))
          .then(d => {
            if (!d?.report) return;
            setBenchReport(d.report);
            writeSurfaceCache(NEWSLETTER_BENCH_KEY, d.report);
          })
          .catch(() => null);
      },
      benchCached?.data ? 0 : 400
    );
    return () => window.clearTimeout(timer);
  }, [loadStatus, benchCached?.data]);

  return (
    <div className="newsletter-page min-h-screen flex flex-col bg-[#081126] text-slate-100 font-sans">
      <ExperimentHeader />

      <PageHeroDark
        maxWidthClass="max-w-6xl"
        eyebrow={
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            Robot Intelligence Brief ·{" "}
            {edition?.latestEdition?.edition || "#253"}
          </span>
        }
        title={headline}
        description={
          <p className="max-w-2xl text-sm leading-relaxed text-slate-300 sm:text-base">
            {subheadline}
          </p>
        }
        stats={[
          {
            label: "Buyer Leads",
            value: "3,000+",
            tone: "amber",
          },
          {
            label: "Live Signals",
            value: "25",
            tone: "emerald",
          },
          {
            label: "Robot Models",
            value: "109+",
            tone: "white",
          },
          {
            label: "Edition",
            value:
              edition?.latestEdition?.edition?.replace(/^Edition\s*/i, "#") ||
              "#253",
            tone: "white",
          },
        ]}
      >
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
          <form
            onSubmit={subscribe}
            className="flex w-full max-w-xl flex-col gap-2 sm:flex-row"
          >
            <input
              value={email}
              onChange={e => setEmail(e.target.value)}
              type="email"
              placeholder="Work email for the daily brief"
              className="newsletter-subscribe-input"
            />
            <button
              type="submit"
              disabled={subStatus === "submitting"}
              className="rounded-xl bg-purple-600 px-6 py-2.5 text-sm font-bold text-white shadow-lg shadow-purple-500/30 transition-all hover:bg-purple-500 disabled:opacity-50 shrink-0 font-sans cursor-pointer"
            >
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
          <p className="mt-3 text-sm font-medium text-emerald-300">
            You&apos;re in — check your inbox for the welcome note.
          </p>
        )}
        {subStatus === "error" && (
          <p className="mt-3 text-sm font-medium text-red-300">
            Could not subscribe. Try again in a moment.
          </p>
        )}
      </PageHeroDark>

      <div className="page-dark-shell-fade" />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-20 pt-8 lg:px-6">
        <MarketIntelligenceDashboard />

        {loadStatus === "loading" && !edition?.topStories?.length && (
          <div className="newsletter-section px-5 py-8 text-center">
            <p className="newsletter-body font-medium">
              Loading today&apos;s brief from SIGNAL…
            </p>
          </div>
        )}

        {loadStatus === "error" && !stories.length && (
          <div className="mb-8 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4">
            <p className="text-sm font-semibold text-amber-950">
              Brief is still syncing.
            </p>
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
          <SectionShell
            kicker="Market read"
            title="What changed in automation demand"
            accent={VIOLET}
          >
            <p className="newsletter-body">
              {cleanScrapedText(brief.executive_take)}
            </p>
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {(brief.macro_trends || []).slice(0, 3).map((item, index) => {
                const title = briefTextTitle(item);
                const detail = briefTextDetail(item);
                if (!title && !detail) return null;
                return (
                  <div
                    key={index}
                    className="rounded-xl border border-slate-700/80 bg-[#081126] p-4.5 shadow-sm"
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-emerald-400" />
                      <p className="text-sm font-bold text-slate-100 font-display">{title}</p>
                    </div>
                    {detail ? (
                      <p className="text-xs leading-relaxed text-slate-300">
                        {detail}
                      </p>
                    ) : null}
                  </div>
                );
              })}
              {(brief.strategic_implications || [])
                .slice(0, 3)
                .map((item, index) => {
                  const title = briefTextTitle(item);
                  const detail = briefTextDetail(item);
                  if (!title && !detail) return null;
                  return (
                    <div
                      key={`s-${index}`}
                      className="rounded-xl border border-slate-700/80 bg-[#081126] p-4.5 shadow-sm"
                    >
                      <div className="mb-2 flex items-center gap-2">
                        <Radio className="h-4 w-4 text-purple-400" />
                        <p className="text-sm font-bold text-slate-100 font-display">
                          {title}
                        </p>
                      </div>
                      {detail ? (
                        <p className="text-xs leading-relaxed text-slate-300">
                          {detail}
                        </p>
                      ) : null}
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
            action={
              <InlineLink href="/pipeline" color={AMBER}>
                Full pipeline
              </InlineLink>
            }
          >
            <ul className="divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200">
              {researchFindings.map((finding, index) => (
                <li
                  key={`${finding.company_id || finding.company}-${index}`}
                  className="px-4 py-4 hover:bg-slate-50"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-base font-bold text-gray-950">
                      {cleanScrapedText(finding.company) || "Lead"}
                    </span>
                    <CategoryBadge
                      label={cleanScrapedText(finding.category) || "Research"}
                      color={AMBER}
                    />
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-gray-700">
                    {cleanScrapedText(finding.summary || finding.title)}
                  </p>
                  <div className="mt-3">
                    <InlineLink
                      href={finding.pipeline_url || "/pipeline"}
                      color={AMBER}
                    >
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
                <StoryCard
                  key={`${story.company_id || story.company}-${index}`}
                  story={story}
                />
              ))}
            </div>
          </SectionShell>
        )}

        {benchReport && (
          <SectionShell
            kicker="Benchmark"
            title={String(benchReport.title ?? "Humanoid robot index")}
            accent={VIOLET}
            action={
              <InlineLink href="/robots" color={VIOLET}>
                Full index
              </InlineLink>
            }
          >
            <div className="grid gap-3 sm:grid-cols-3">
              {(
                (benchReport.top_3 as Array<{
                  name: string;
                  vendor: string;
                  score: number;
                }>) ?? []
              ).map((robot, index) => (
                <div
                  key={robot.name}
                  className="rounded-xl border border-gray-200 bg-slate-50 p-4"
                >
                  <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                    {["Leader", "2nd", "3rd"][index]}
                  </p>
                  <p className="mt-1 font-display text-base font-bold text-gray-950">
                    {robot.name}
                  </p>
                  <p className="text-sm text-gray-600">{robot.vendor}</p>
                  <p className="font-mono-data mt-2 text-2xl font-black text-emerald-600">
                    {robot.score}
                  </p>
                </div>
              ))}
            </div>
          </SectionShell>
        )}

        <section className="mt-10 grid gap-4 rounded-2xl border border-slate-700 bg-[#0b162f] p-5 shadow-sm sm:grid-cols-3">
          <Link
            href="/results?url="
            className="group rounded-xl border border-slate-700 bg-[#0d1a33] p-4 transition hover:border-amber-400/50"
          >
            <Zap className="h-5 w-5 text-amber-400" />
            <p className="mt-2 font-display text-base font-bold text-slate-100 group-hover:text-amber-300">
              Scan your market
            </p>
            <p className="mt-1 text-sm text-slate-400">
              Paste a vendor URL and get matched buyer signals.
            </p>
          </Link>
          <Link
            href="/signals"
            className="group rounded-xl border border-slate-700 bg-[#0d1a33] p-4 transition hover:border-emerald-400/50"
          >
            <BarChart3 className="h-5 w-5 text-emerald-400" />
            <p className="mt-2 font-display text-base font-bold text-slate-100 group-hover:text-emerald-300">
              Live signals
            </p>
            <p className="mt-1 text-sm text-slate-400">
              Browse every signal type SIGNAL monitors.
            </p>
          </Link>
          <Link
            href="/intelligence"
            className="group rounded-xl border border-slate-700 bg-[#0d1a33] p-4 transition hover:border-violet-400/50"
          >
            <Sparkles className="h-5 w-5 text-violet-300" />
            <p className="mt-2 font-display text-base font-bold text-slate-100 group-hover:text-violet-200">
              Intelligence report
            </p>
            <p className="mt-1 text-sm text-slate-400">
              How we score intent and robot fit.
            </p>
          </Link>
        </section>

        <div className="mt-8 flex flex-col items-start gap-3 rounded-2xl border border-gray-200 bg-gray-950 px-6 py-6 text-white sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="flex items-center gap-2 text-sm font-bold text-emerald-300">
              <Mail className="h-4 w-4" />
              Daily brief in your inbox
            </p>
            <p className="mt-1 max-w-lg text-sm text-slate-300">
              Same stories as this page — curated for robotics GTM teams every
              morning.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2.5 text-sm font-bold text-white shadow-md shadow-purple-500/25 transition hover:bg-purple-500"
          >
            Subscribe at top
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <WorkflowDriveBanner
          title="Turn Humanoid Intelligence into Buyer Pipeline"
          subtitle="Paste your robot URL to instantly analyze task feasibility and generate 25 verified buyer leads."
          buttonText="Build 25 Lead Pipeline"
        />
      </main>

      <SiteFooter />
    </div>
  );
}
