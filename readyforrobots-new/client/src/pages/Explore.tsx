/**
 * /explore — research doors. Card copy is static. Brief rows and any
 * count come from the API; missing figures stay off the page.
 */
import { FormEvent, useEffect, useState } from "react";
import { Eyebrow, SiteFooter, SiteHeader } from "@/components/editorial";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { usePageMeta } from "@/lib/pageMeta";

const DOORS = [
  {
    kicker: "Index",
    title: "Robot index",
    body: "Service, warehouse and humanoid robots, classified by form, work and the buyers they fit. Scored on published specs.",
    cta: "Browse robots",
    href: "/robot-ready",
  },
  {
    kicker: "Weekly",
    title: "The robot jobs brief",
    body: "The strongest new buying signals of the week: RFPs, pilots, budgets and expansions, each with its source.",
    note: "Every Monday",
    cta: "Read this week",
    href: "/newsletter",
  },
  {
    kicker: "Tool",
    title: "RaaS ROI calculator",
    body: "Payback, year-one return and three-year savings for buying or renting a robot. Flags inputs that buyers will question.",
    note: "Buy, lease or robots-as-a-service",
    cta: "Run the numbers",
    href: "/roi-calculator",
  },
  {
    kicker: "Reports",
    title: "Industry reports",
    body: "Where automation is moving in each of our nine industries: which work, which signals, which robots fit.",
    note: "Updated monthly",
    cta: "Read reports",
    href: "/reports/benchmarking",
  },
] as const;

const SUBNAV = [
  { label: "Overview", href: "/explore" },
  { label: "Robot index", href: "/robot-ready" },
  { label: "The robot jobs brief", href: "/newsletter" },
  { label: "RaaS ROI calculator", href: "/roi-calculator" },
  { label: "Industry reports", href: "/reports/benchmarking" },
] as const;

type BriefItem = {
  headline: string;
  tier: string | null;
  meta: string;
};

type EditionStory = {
  headline?: string;
  tier?: string;
  industry?: string;
  category?: string;
};

function briefItems(stories: EditionStory[] | undefined): BriefItem[] {
  const items: BriefItem[] = [];
  for (const story of stories || []) {
    const headline = (story.headline || "").trim();
    if (!headline) continue;
    const tier = (story.tier || "").trim().toUpperCase();
    const meta = [story.industry, story.category]
      .map((part) => (part || "").trim())
      .filter(Boolean)
      .join(" · ");
    items.push({
      headline,
      tier: /^[A-D]$/.test(tier) ? tier : null,
      meta,
    });
    if (items.length >= 3) break;
  }
  return items;
}

export default function Explore() {
  usePageMeta({
    title: "Explore — Ready For Robots",
    description:
      "Research and tools for robot sellers. Free to use, no sign-in. Every number comes from our database or a cited source.",
    path: "/explore",
  });
  const [items, setItems] = useState<BriefItem[]>([]);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");

  useEffect(() => {
    let cancelled = false;
    void fetch(
      `${getApiBase()}/api/newsletter/edition?limit=3`,
      liveFetchInit()
    )
      .then((res) => (res.ok ? res.json() : null))
      .then((data: { topStories?: EditionStory[] } | null) => {
        if (!cancelled) setItems(briefItems(data?.topStories));
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function subscribe(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = email.trim();
    if (!trimmed || status === "sending") return;
    setStatus("sending");
    try {
      const res = await fetch(
        `${getApiBase()}/api/newsletter/subscribe`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: trimmed, source: "explore" }),
        })
      );
      setStatus(res.ok ? "done" : "error");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="rfr-editorial rfr-explore-page">
      <SiteHeader />
      <nav className="rfr-explore-sub" aria-label="Explore">
        <div>
          {SUBNAV.map((link) => (
            <a
              key={link.href}
              href={link.href}
              aria-current={link.href === "/explore" ? "page" : undefined}
            >
              {link.label}
            </a>
          ))}
        </div>
      </nav>
      <section className="rfr-explore-hero">
        <Eyebrow label="Explore" />
        <h1>Go deeper on the robot market.</h1>
        <p>
          Research and tools for robot sellers. Free to use, no sign-in. Every number comes from our database or a cited source.
        </p>
      </section>
      <section className="rfr-explore-cards" aria-label="Research and tools">
        {DOORS.map((door) => (
          <a key={door.href} className="rfr-explore-card" href={door.href}>
            <span>{door.kicker}</span>
            <strong>{door.title}</strong>
            <p>{door.body}</p>
            {"note" in door ? <em>{door.note}</em> : <em />}
            <b>
              {door.cta} →
            </b>
          </a>
        ))}
      </section>
      <section className="rfr-explore-week">
        {items.length > 0 ? (
          <div>
            <div className="rfr-explore-week-head">
              <h2>This week in the brief</h2>
            </div>
            {items.map((item) => (
              <article key={item.headline}>
                {item.tier ? <span className={item.tier === "A" ? "is-a" : undefined}>{item.tier}</span> : null}
                <div>
                  <strong>{item.headline}</strong>
                  {item.meta ? <em>{item.meta}</em> : null}
                </div>
              </article>
            ))}
            <a className="rfr-explore-more" href="/newsletter">
              Read the brief →
            </a>
          </div>
        ) : null}
        <form onSubmit={subscribe}>
          <span>Weekly</span>
          <strong>Get the robot jobs brief.</strong>
          <p>Which companies are moving to automate, which work, and which robots fit. One email a week.</p>
          <label htmlFor="explore-email">Work email</label>
          <input
            id="explore-email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@company.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <button type="submit" disabled={status === "sending" || status === "done"}>
            {status === "done" ? "Subscribed" : status === "sending" ? "Subscribing…" : "Subscribe →"}
          </button>
          {status === "error" ? <p className="rfr-explore-form-error">Could not subscribe. Try again in a moment.</p> : null}
        </form>
      </section>
      <SiteFooter />
    </div>
  );
}
