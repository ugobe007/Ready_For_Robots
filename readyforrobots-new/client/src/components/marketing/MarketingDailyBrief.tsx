import { ArrowRight, Mail } from "lucide-react";
import { Link } from "wouter";
import { cleanScrapedText } from "@/lib/text";

type NewsletterStory = {
  category?: string;
  company?: string;
  headline?: string;
  snippet?: string;
  summary?: string;
};

type NewsletterEdition = {
  latestEdition?: { headline?: string; subheadline?: string };
  topStories?: NewsletterStory[];
};

type Props = {
  dailyBrief: NewsletterEdition | null;
  newsletterEmail: string;
  newsletterStatus: "idle" | "submitting" | "success" | "error";
  onEmailChange: (v: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
};

export default function MarketingDailyBrief({
  dailyBrief,
  newsletterEmail,
  newsletterStatus,
  onEmailChange,
  onSubmit,
}: Props) {
  const briefHeadline =
    cleanScrapedText(dailyBrief?.latestEdition?.headline) || "Fresh robot demand signals, updated daily.";
  const briefSubheadline =
    cleanScrapedText(dailyBrief?.latestEdition?.subheadline) ||
    "A daily scan of sales triggers, partnership motion, and automation buying intent from the ReadyForRobots signal engine.";

  return (
    <section className="py-20 bg-white border-t border-gray-100">
      <div className="container grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        <div className="rounded-3xl border border-emerald-100 p-6 lg:p-7 bg-gradient-to-br from-emerald-50/80 to-slate-50">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="section-eyebrow mb-3">Today&apos;s Robot Intelligence Brief</p>
              <h2 className="max-w-2xl text-3xl font-display font-bold leading-tight text-gray-900">
                {briefHeadline}
              </h2>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-gray-600">{briefSubheadline}</p>
            </div>
            <Link
              href="/newsletter"
              className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white transition-all hover:bg-emerald-700"
            >
              Read the brief
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {dailyBrief?.topStories?.length ? (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {dailyBrief.topStories.slice(0, 3).map((story, index) => {
                const headline = cleanScrapedText(story.headline || story.company) || "Signal story";
                const snippet =
                  cleanScrapedText(story.snippet || story.summary) ||
                  "Fresh signal intelligence from ReadyForRobots.";
                return (
                  <div key={`${story.company || story.headline || index}`} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
                    <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-emerald-600">
                      {cleanScrapedText(story.category) || "Signal"}
                    </p>
                    <p className="text-sm font-bold leading-snug text-gray-900">{headline}</p>
                    <p className="mt-2 line-clamp-4 text-xs leading-relaxed text-gray-600">{snippet}</p>
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>

        <div className="rounded-3xl border border-gray-100 bg-slate-50 p-6">
          <Mail className="mb-5 h-5 w-5 text-emerald-600" />
          <p className="text-lg font-display font-bold text-gray-900">Get the brief daily</p>
          <p className="mt-3 text-sm leading-relaxed text-gray-600">
            A short, signal-driven digest of robot demand, buyer timing, and where Signal sees sales or partnership motion.
          </p>
          <form onSubmit={onSubmit} className="mt-5 space-y-2">
            <input
              value={newsletterEmail}
              onChange={(e) => onEmailChange(e.target.value)}
              type="email"
              placeholder="work email"
              className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={newsletterStatus === "submitting"}
              className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-700 disabled:opacity-50"
            >
              {newsletterStatus === "submitting" ? "Subscribing..." : "Subscribe Free"}
            </button>
          </form>
          {newsletterStatus === "success" && <p className="mt-3 text-xs text-emerald-600">Subscribed.</p>}
          {newsletterStatus === "error" && <p className="mt-3 text-xs text-red-600">Could not subscribe. Try again.</p>}
        </div>
      </div>
    </section>
  );
}
