/**
 * CalLearningPanel — live per-angle scoreboard for Cal's outreach.
 *
 * Reads GET /api/admin/communication-learning and shows which trust-first angle
 * (and which industry) is actually earning replies. This is the loop that turns
 * "let's see how this works" into a scoreboard: every send is tagged with its
 * angle, every reply is classified, and this panel rolls it up.
 *
 * Honest framing: at our volume this is a *directional* read, not a p-value.
 */
import { useCallback, useEffect, useState } from "react";
import { BarChart3, RefreshCw } from "lucide-react";

type VariantRow = {
  variant_id: string;
  sent: number;
  replied: number;
  positive: number;
  negative: number;
  reply_rate: number;
  positive_rate: number;
  subject_sample: string | null;
};

type IndustryRow = {
  industry: string;
  sent: number;
  replied: number;
  positive: number;
  positive_rate: number;
};

type LearningReport = {
  period_hours: number;
  generated_at: string;
  totals: {
    sent: number;
    replied: number;
    positive: number;
    negative: number;
    reply_rate: number;
    positive_rate: number;
  };
  variants: VariantRow[];
  industries: IndustryRow[];
};

const ANGLE_LABELS: Record<string, string> = {
  what_survives: "Still running at 6 months",
  workflow_first: "Wrong workflow first",
  bottleneck_first: "Start with the bottleneck",
  unknown: "Untagged",
};

const WINDOWS: Array<{ label: string; hours: number }> = [
  { label: "7d", hours: 168 },
  { label: "30d", hours: 720 },
  { label: "90d", hours: 2160 },
];

function angleLabel(id: string): string {
  return ANGLE_LABELS[id] ?? id;
}

export default function CalLearningPanel({
  adminFetch,
}: {
  adminFetch: (path: string, init?: RequestInit) => Promise<Response>;
}) {
  const [hours, setHours] = useState(168);
  const [report, setReport] = useState<LearningReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(
    async (windowHours: number) => {
      setLoading(true);
      setError("");
      try {
        const res = await adminFetch(
          `/api/admin/communication-learning?period_hours=${windowHours}`
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setReport((await res.json()) as LearningReport);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    },
    [adminFetch]
  );

  useEffect(() => {
    void load(hours);
  }, [load, hours]);

  const totals = report?.totals;
  const variants = (report?.variants ?? []).filter(v => v.sent > 0);
  const industries = (report?.industries ?? []).filter(i => i.sent > 0);
  const anyReplies = (totals?.replied ?? 0) > 0;
  const scored = variants.filter(v => v.sent >= 3);
  const leader = anyReplies && scored.length ? scored[0] : null;

  return (
    <section className="mb-6 rounded-2xl border border-slate-700/60 bg-[#0a1226] p-4 text-slate-100 shadow-xl">
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-violet-400" />
          <div>
            <h2 className="text-base font-extrabold text-slate-100">
              Cal learning — which voice earns replies
            </h2>
            <p className="text-[11px] text-slate-400">
              Per-angle reply rates from tagged sends. Directional signal, not a
              verdict.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="inline-flex overflow-hidden rounded-lg border border-slate-700/60 bg-[#060c1c]">
            {WINDOWS.map(w => (
              <button
                key={w.hours}
                type="button"
                onClick={() => setHours(w.hours)}
                className={`px-2.5 py-1 font-medium transition ${
                  hours === w.hours
                    ? "bg-violet-600 text-white"
                    : "bg-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                {w.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => void load(hours)}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-700/60 bg-[#060c1c] px-2.5 py-1 text-slate-300 hover:bg-[#0b162f]"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
            />{" "}
            Refresh
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-amber-500/30 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
          Couldn&apos;t load the report ({error}).
        </div>
      ) : null}

      {/* Totals */}
      <div className="mb-3 grid grid-cols-3 gap-2">
        <div className="rounded-xl border border-slate-700/40 bg-[#060c1c] px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
            Tagged sends
          </p>
          <p className="text-xl font-black text-slate-100">
            {totals?.sent?.toLocaleString() ?? "—"}
          </p>
        </div>
        <div className="rounded-xl border border-slate-700/40 bg-[#060c1c] px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
            Replied
          </p>
          <p className="text-xl font-black text-slate-100">
            {totals?.replied?.toLocaleString() ?? "—"}
            <span className="ml-1 text-xs font-semibold text-slate-400">
              {totals ? `${totals.reply_rate}%` : ""}
            </span>
          </p>
        </div>
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-400">
            Positive
          </p>
          <p className="text-xl font-black text-emerald-400">
            {totals?.positive?.toLocaleString() ?? "—"}
            <span className="ml-1 text-xs font-semibold text-emerald-300">
              {totals ? `${totals.positive_rate}%` : ""}
            </span>
          </p>
        </div>
      </div>

      {leader ? (
        <p className="mb-3 rounded-lg border border-emerald-500/30 bg-emerald-950/30 px-3 py-2 text-xs text-emerald-200">
          Leading angle so far: <strong>{angleLabel(leader.variant_id)}</strong>{" "}
          — {leader.positive_rate}% positive on {leader.sent} sends. Keep an eye
          on it before retiring the others.
        </p>
      ) : (
        <p className="mb-3 rounded-lg border border-slate-700/60 bg-[#060c1c] px-3 py-2 text-xs text-slate-300">
          {(totals?.sent ?? 0) === 0
            ? "No tagged sends in this window yet."
            : anyReplies
              ? "Replies are landing — need ~3+ per angle before calling a winner."
              : "Sends are out; no replies yet. This fills in as buyers respond (a reply cools fast — check the inbox)."}
        </p>
      )}

      {/* Per-angle table */}
      {variants.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-700/60 text-[11px] uppercase tracking-wide text-slate-400">
                <th className="py-1.5 pr-2 font-bold">Angle</th>
                <th className="px-2 py-1.5 text-right font-bold">Sent</th>
                <th className="px-2 py-1.5 text-right font-bold">Replied</th>
                <th className="px-2 py-1.5 text-right font-bold">Positive</th>
              </tr>
            </thead>
            <tbody>
              {variants.map(v => (
                <tr
                  key={v.variant_id}
                  className="border-b border-slate-800/60 last:border-0"
                >
                  <td className="py-2 pr-2">
                    <div className="font-semibold text-slate-100">
                      {angleLabel(v.variant_id)}
                    </div>
                    {v.subject_sample ? (
                      <div
                        className="truncate text-[11px] text-slate-400"
                        title={v.subject_sample}
                      >
                        “{v.subject_sample}”
                      </div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums text-slate-300">
                    {v.sent.toLocaleString()}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums text-slate-300">
                    {v.replied.toLocaleString()}
                    <span className="ml-1 text-[11px] text-slate-500">
                      {v.reply_rate}%
                    </span>
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums font-semibold text-emerald-400">
                    {v.positive.toLocaleString()}
                    <span className="ml-1 text-[11px] text-emerald-500">
                      {v.positive_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {/* Industry slice */}
      {industries.length > 0 ? (
        <div className="mt-3">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-400">
            By industry (top by volume)
          </p>
          <div className="flex flex-wrap gap-1.5">
            {industries.map(i => (
              <span
                key={i.industry}
                className="rounded-full border border-slate-700/60 bg-[#060c1c] px-2 py-0.5 text-[11px] text-slate-300"
              >
                {i.industry}: <strong>{i.sent}</strong> sent
                {i.positive > 0 ? (
                  <span className="text-emerald-400">
                    {" "}
                    · {i.positive} positive ({i.positive_rate}%)
                  </span>
                ) : null}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
