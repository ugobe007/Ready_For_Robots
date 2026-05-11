import React, { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Mail, Radio, RefreshCw, Send, Zap } from "lucide-react";
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
};

type IndustryBrief = {
  executive_take?: string;
  macro_trends?: string[];
  strategic_implications?: string[];
  watch_next?: string[];
};

type NewsletterEdition = {
  latestEdition?: {
    date?: string;
    edition?: string;
    headline?: string;
    subheadline?: string;
  };
  industryBrief?: IndustryBrief;
  topStories?: NewsletterStory[];
  summary?: {
    total_leads?: number;
    generated_at?: string;
  };
};

const fallbackStories: NewsletterStory[] = [
  {
    category: "Signal",
    headline: "Daily robot demand signals are updating",
    snippet: "SCOUT watches labor pressure, expansion plans, CapEx hints, automation hiring, and deployment news for robotics vendors.",
  },
  {
    category: "Market",
    headline: "Logistics, hospitality, and healthcare remain active",
    snippet: "The daily brief packages where demand is moving and which signals are turning into sales or partnership opportunities.",
  },
  {
    category: "Action",
    headline: "Use the brief to activate SCOUT",
    snippet: "Every daily edition points toward accounts and signal types worth turning into outreach, research, or partnership motion.",
  },
];

function shortDate(value?: string) {
  if (!value) return "Updated daily";
  return value;
}

export default function Newsletter() {
  const [edition, setEdition] = useState<NewsletterEdition | null>(null);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/newsletter/edition?limit=8`, liveFetchInit())
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data?.topStories) setEdition(data);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  async function subscribe(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("submitting");
    try {
      const res = await fetch(`${getApiBase()}/api/newsletter/subscribe`, liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, source: "newsletter_page" }),
      }));
      if (!res.ok) throw new Error("Subscribe failed");
      setStatus("success");
      setEmail("");
    } catch {
      setStatus("error");
    }
  }

  const stories = (edition?.topStories?.length ? edition.topStories : fallbackStories).slice(0, 8);
  const brief = edition?.industryBrief;
  const headline = cleanScrapedText(edition?.latestEdition?.headline) || "Daily robot demand intelligence.";
  const subheadline = cleanScrapedText(edition?.latestEdition?.subheadline) || "A daily digest of buying signals, deployment stories, vendor movement, and sales timing for robotics teams.";

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 px-6 pb-20 pt-28">
        <div className="mx-auto max-w-6xl">
          <section className="relative mb-10 overflow-hidden rounded-3xl border border-white/10 p-6 lg:p-9" style={{ background: "linear-gradient(135deg, rgba(3,218,197,0.08), rgba(124,58,237,0.08), rgba(255,176,0,0.05))" }}>
            <div className="pointer-events-none absolute right-0 top-0 h-56 w-56 rounded-full blur-3xl" style={{ background: "rgba(3,218,197,0.12)" }} />
            <div className="relative grid grid-cols-1 gap-8 lg:grid-cols-[1fr_340px] lg:items-end">
              <div>
                <p className="mb-4 inline-flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#03DAC5" }}>
                  <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
                  Robot Intelligence Brief
                </p>
                <h1 className="max-w-3xl text-4xl font-extrabold leading-tight text-white lg:text-6xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  {headline}
                </h1>
                <p className="mt-5 max-w-2xl text-base leading-relaxed text-white/48">
                  {subheadline}
                </p>
              </div>
              <form onSubmit={subscribe} className="rounded-2xl border border-white/10 p-5" style={{ background: "rgba(13,5,32,0.62)" }}>
                <Mail className="mb-4 h-5 w-5" style={{ color: "#03DAC5" }} />
                <p className="text-sm font-bold text-white">Subscribe free</p>
                <p className="mt-2 text-xs leading-relaxed text-white/35">Get the signal brief when the daily edition updates.</p>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  placeholder="work email"
                  className="mt-4 w-full rounded-xl border border-white/10 px-4 py-3 text-sm text-white placeholder-white/25 outline-none focus:border-teal-300/50"
                  style={{ background: "rgba(255,255,255,0.04)" }}
                />
                <button type="submit" disabled={status === "submitting"} className="mt-3 w-full rounded-xl px-4 py-3 text-sm font-bold transition-all hover:bg-amber-400/6 disabled:opacity-50" style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}>
                  {status === "submitting" ? "Subscribing..." : "Subscribe Free"}
                </button>
                {status === "success" && <p className="mt-3 text-xs" style={{ color: "#03DAC5" }}>Subscribed.</p>}
                {status === "error" && <p className="mt-3 text-xs text-red-300">Could not subscribe. Try again.</p>}
              </form>
            </div>
          </section>

          <section className="mb-10 grid grid-cols-1 gap-3 md:grid-cols-4">
            {[
              ["Edition", edition?.latestEdition?.edition || "Daily"],
              ["Updated", shortDate(edition?.latestEdition?.date)],
              ["Stories", String(edition?.summary?.total_leads || stories.length)],
              ["Cadence", "Every day"],
            ].map(([label, value], index) => (
              <div key={label} className="rounded-2xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-white/30">{label}</p>
                <p className="mt-2 font-mono text-lg font-black" style={{ color: index === 2 ? "#FFB000" : "#03DAC5", fontFamily: "'JetBrains Mono', monospace" }}>{value}</p>
              </div>
            ))}
          </section>

          {brief?.executive_take && (
            <section className="mb-10 rounded-3xl border border-white/10 p-6 lg:p-7" style={{ background: "rgba(255,255,255,0.035)" }}>
              <div className="grid grid-cols-1 gap-7 lg:grid-cols-[1fr_360px]">
                <div>
                  <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#a78bfa" }}>Strategic take</p>
                  <p className="break-words text-lg leading-relaxed text-white/70">{cleanScrapedText(brief.executive_take)}</p>
                </div>
                <div className="space-y-3">
                  {(brief.watch_next || brief.macro_trends || []).slice(0, 3).map((item, index) => (
                    <div key={`${item}-${index}`} className="flex items-start gap-3 rounded-2xl border border-white/8 p-4" style={{ background: "rgba(13,5,32,0.5)" }}>
                      <Radio className="mt-0.5 h-4 w-4 shrink-0" style={{ color: index === 0 ? "#FFB000" : "#03DAC5" }} />
                      <p className="break-words text-sm leading-relaxed text-white/50">{cleanScrapedText(item)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {stories.map((story, index) => (
              <article key={`${story.company || story.headline || index}`} className="rounded-3xl border border-white/8 p-5 transition-colors hover:border-teal-300/25" style={{ background: "rgba(255,255,255,0.03)" }}>
                <div className="mb-4 flex items-center justify-between gap-3">
                  <span className="rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest" style={{ color: index % 2 ? "#FFB000" : "#03DAC5", borderColor: index % 2 ? "rgba(255,176,0,0.28)" : "rgba(3,218,197,0.28)", background: index % 2 ? "rgba(255,176,0,0.06)" : "rgba(3,218,197,0.06)" }}>
                    {cleanScrapedText(story.category) || "Signal"}
                  </span>
                  {story.signalStrength && (
                    <span className="font-mono text-xs font-bold text-white/35" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                      {story.signalStrength}/10 strength
                    </span>
                  )}
                </div>
                <h2 className="text-xl font-extrabold leading-snug text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  {cleanScrapedText(story.headline || story.company) || "Signal story"}
                </h2>
                <p className="mt-3 break-words text-sm leading-relaxed text-white/45">
                  {cleanScrapedText(story.snippet || story.summary) || "Fresh signal intelligence from ReadyForRobots."}
                </p>
                <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
                  {[story.roi, story.economics, story.impact].map((item) => cleanScrapedText(item)).filter(Boolean).map((item) => (
                    <div key={item} className="rounded-xl border border-white/8 px-3 py-2" style={{ background: "rgba(13,5,32,0.45)" }}>
                      <p className="text-[11px] font-bold text-white/48">{item}</p>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </section>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-5 text-sm">
            <Link href="/results?url=" className="inline-flex items-center gap-2 font-bold" style={{ color: "#FFB000" }}>
              Activate SCOUT from today&apos;s brief <Zap className="h-4 w-4" />
            </Link>
            <Link href="/signals" className="inline-flex items-center gap-2 font-bold text-white/50 hover:text-white/80">
              Watch live signals <BarChart3 className="h-4 w-4" />
            </Link>
            <Link href="/intelligence" className="inline-flex items-center gap-2 font-bold text-white/50 hover:text-white/80">
              Read the report <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
