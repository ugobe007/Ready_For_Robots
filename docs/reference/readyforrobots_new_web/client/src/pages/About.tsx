import SiteShell from "@/components/SiteShell";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { useEffect, useState } from "react";
import { Link } from "wouter";

type Summary = {
  hot?: number;
  warm?: number;
  companies_in_database?: number;
  signals_in_database?: number;
};

const stroke = "oklch(0.527 0.154 162.5)";

export default function About() {
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    const API = getApiBase();
    (async () => {
      try {
        const r = await fetch(`${API}/api/leads/summary?exclude_junk=true`, liveFetchInit());
        if (r.ok) {
          const t = await r.text();
          if (!t.trimStart().startsWith("<")) setSummary(JSON.parse(t) as Summary);
        }
      } catch {
        setSummary(null);
      }
    })();
  }, []);

  const fmt = (n: number | undefined) =>
    n != null && Number.isFinite(n) ? n.toLocaleString() : "—";

  return (
    <SiteShell>
      <div className="pb-20">
        <section className="border-b border-gray-200 bg-white">
          <div className="container py-12 md:py-16 max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">About</p>
            <h1
              className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight"
              style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.03em" }}
            >
              Signal intelligence for robotics revenue teams
            </h1>
            <p className="mt-5 text-lg text-gray-600 leading-relaxed">
              Ready For Robots surfaces companies that are staffing, funding, expanding, and automating — then scores
              every account so reps spend time on conversations that can close, not cold lists.
            </p>
            <div className="mt-8 flex flex-wrap gap-2">
              <Link
                href="/dashboard"
                className="inline-flex items-center rounded-md border border-gray-300 bg-transparent px-4 py-2.5 text-sm font-semibold text-gray-900 hover:border-gray-400"
              >
                Live dashboard
              </Link>
              <Link
                href="/pipeline"
                className="inline-flex items-center rounded-md border bg-transparent px-4 py-2.5 text-sm font-semibold hover:opacity-90"
                style={{ borderColor: stroke, color: stroke }}
              >
                HOT pipeline
              </Link>
            </div>
          </div>
        </section>

        {summary ? (
          <div className="container py-10 max-w-5xl">
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">Live footprint</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                ["HOT leads (window)", summary.hot],
                ["WARM leads (window)", summary.warm],
                ["Companies tracked", summary.companies_in_database],
                ["Signal events stored", summary.signals_in_database],
              ].map(([k, v]) => (
                <div key={String(k)} className="rounded-lg border border-gray-200 px-4 py-4 bg-white">
                  <p className="text-2xl md:text-3xl font-bold tabular-nums text-gray-900">{fmt(v as number)}</p>
                  <p className="text-xs font-medium text-gray-500 mt-1.5 leading-snug">{k}</p>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-3 max-w-2xl">
              Tier counts use the same classification as the product API; row totals are full-table counts from the
              database.
            </p>
          </div>
        ) : null}

        <div className="container py-6 max-w-3xl space-y-10 text-gray-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900" style={{ fontFamily: "'Bricolage Grotesque', sans-serif" }}>
              What we monitor
            </h2>
            <p>
              Public signals across hospitality, logistics, healthcare, food service, manufacturing, and retail: news,
              facility and CapEx headlines, hiring pressure, executive moves, and automation language. Each company is
              deduplicated, named validated, and scored for intent, deal quality, and timing.
            </p>
          </div>
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900" style={{ fontFamily: "'Bricolage Grotesque', sans-serif" }}>
              Who it is for
            </h2>
            <p>
              Robot OEMs, integrators, and automation consultancies who sell into physical operations — teams that need
              a prioritized queue of accounts showing buying behavior, not another static TAM spreadsheet.
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 p-6 bg-gray-50/40">
            <p className="text-sm text-gray-600">
              This site runs the new Precision Craft front end (Vite + React) against the same production APIs as your
              FastAPI deployment. Questions or partnerships: newsletter signup or your existing team channel.
            </p>
          </div>
        </div>
      </div>
    </SiteShell>
  );
}
