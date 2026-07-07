/**
 * /preview — shareable Cal lead drops (public candy).
 */
import { useEffect, useState } from "react";
import { Link } from "wouter";
import { ArrowRight, ExternalLink, Loader2 } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import CalLeadDrop, { type CalLeadDropData } from "@/components/pipeline/CalLeadDrop";
import { getApiBase, fetchWithTimeoutRetry, liveFetchInit } from "@/lib/apiBase";
import {
  LINKEDIN_ORG_URN,
  linkedInShareUrl,
  usePageMeta,
} from "@/lib/pageMeta";

type CalDropsResponse = {
  headline?: string;
  subhead?: string;
  drops?: CalLeadDropData[];
  count?: number;
  cache_pending?: boolean;
  built_at?: string;
};

const PREVIEW_TITLE = "Cal's pipeline brief";
const PREVIEW_SUBHEAD =
  "Priority accounts with Cal's read, robot fit, and send-ready outreach.";

export default function Preview() {
  const [data, setData] = useState<CalDropsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const shareUrl =
    typeof window !== "undefined" ? `${window.location.origin}/preview` : "https://readyforrobots.com/preview";

  usePageMeta({
    title: `${PREVIEW_TITLE} | Ready For Robots`,
    description: PREVIEW_SUBHEAD,
    path: "/preview",
    imageAlt: "Cal pipeline brief — priority sales accounts",
  });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetchWithTimeoutRetry(
          `${getApiBase()}/api/leads/cal-drops`,
          liveFetchInit(),
          12_000,
          { retries: 1 },
        );
        if (!res.ok) throw new Error(`Could not load preview (${res.status})`);
        const json = (await res.json()) as CalDropsResponse;
        if (!cancelled) setData(json);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Preview failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const drops = data?.drops ?? [];
  const heroDrop = drops[0];
  const shareSummary =
    heroDrop?.cal_observation ||
    "Cal surfaces priority accounts with real signals and send-ready outreach drafts.";

  const linkedInHref = linkedInShareUrl({
    url: shareUrl,
    title: PREVIEW_TITLE,
    summary: shareSummary,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <PageHeroDark
        eyebrow="Monday · sales pipeline"
        title={PREVIEW_TITLE}
        subtitle={data?.subhead || PREVIEW_SUBHEAD}
      />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 pb-16 -mt-6 relative z-10">
        <section className="mb-6 rounded-xl border border-gray-200 bg-white p-4 sm:p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row gap-4 sm:gap-5 items-start">
            <figure className="shrink-0 mx-auto sm:mx-0">
              <img
                src="/marketing/cal-meme-monday.gif"
                alt="Cal pipeline preview animation"
                className="w-[min(100%,200px)] max-w-[200px] rounded-lg border border-gray-200 shadow-sm"
                width={200}
                height={114}
                loading="lazy"
              />
              <figcaption className="mt-1.5 text-[9px] text-center text-gray-400">
                8-sec loop · thumbnail
              </figcaption>
            </figure>

            <div className="flex-1 min-w-0 w-full">
              <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-700 mb-2">
                Cal&apos;s read
              </p>
              {heroDrop?.cal_observation ? (
                <p className="text-sm text-gray-800 leading-relaxed">
                  <span className="font-semibold text-emerald-800">Cal: </span>
                  {heroDrop.cal_observation}
                </p>
              ) : (
                <p className="text-sm text-gray-600 leading-relaxed">
                  Live priority accounts with signal-backed outreach — loading…
                </p>
              )}

              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white hover:bg-emerald-700"
                  onClick={() => {
                    const text = `${shareSummary}\n\n${shareUrl}`;
                    void navigator.clipboard?.writeText(text);
                  }}
                >
                  Copy share text
                </button>
                <a
                  href={linkedInHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[#0a66c2] px-3 py-2 text-xs font-bold text-[#0a66c2] hover:bg-blue-50"
                >
                  Share on LinkedIn
                  <ExternalLink className="h-3 w-3" />
                </a>
                <Link
                  href="/pipeline"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-bold text-gray-700 hover:bg-gray-50"
                >
                  Pipeline
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              <p className="mt-3 text-[10px] text-gray-400 leading-relaxed">
                LinkedIn company URN:{" "}
                <code className="text-gray-500">{LINKEDIN_ORG_URN}</code>
                {" · "}
                <Link href="/privacy" className="text-emerald-700 underline hover:text-emerald-800">
                  Privacy Policy
                </Link>
              </p>
            </div>
          </div>
        </section>

        <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500 mb-4">
          Live Cal drops
        </h2>
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-20 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Cal is pulling live matches…
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-6 text-sm text-amber-950">
            {error}.{" "}
            <Link href="/pipeline" className="font-semibold underline">
              Browse the pipeline
            </Link>{" "}
            instead.
          </div>
        ) : drops.length === 0 ? (
          <div className="rounded-2xl border border-gray-200 bg-white px-4 py-8 text-center text-sm text-gray-600">
            Preview cache is warming.{" "}
            <Link href="/pipeline" className="font-semibold text-emerald-700">
              Open the live pipeline
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {drops.map((drop) => (
              <CalLeadDrop key={drop.id} drop={drop} variant="full" showDraft />
            ))}
          </div>
        )}

        <section className="mt-8 rounded-xl border border-gray-200 bg-white p-4 sm:p-5">
          <h2 className="text-sm font-bold text-gray-900">Email preview loop</h2>
          <p className="mt-1 text-xs text-gray-600">
            Compact footer animation in Cal outreach emails.
          </p>
          <img
            src="/marketing/cal-pipeline-demo.gif"
            alt="Email pipeline preview"
            className="mt-3 max-w-[200px] rounded-md border border-gray-200"
            width={200}
            height={68}
            loading="lazy"
          />
        </section>

        {data?.built_at && (
          <p className="mt-6 text-center text-[10px] text-gray-400">
            Live data refreshed {new Date(data.built_at).toLocaleString()}
          </p>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
