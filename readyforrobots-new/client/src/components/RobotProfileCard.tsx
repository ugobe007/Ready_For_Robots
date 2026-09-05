/**
 * Robot Profile — first trust checkpoint (Understanding v1).
 * Generated from structured objects, not free prose.
 */
import { useState } from "react";
import {
  formatFactLine,
  profileConfidenceCopy,
  sourceTypeLabel,
  type RobotProfileResult,
} from "@/lib/robotProfile";

const eyebrow =
  "font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500";

export default function RobotProfileCard({
  profile,
  compact = false,
}: {
  profile: RobotProfileResult;
  compact?: boolean;
}) {
  const [showSources, setShowSources] = useState(false);
  const product = profile.selected_product;
  const company = profile.company.name;
  const tier = profile.profile_confidence;
  const classLabel = (product?.display_class || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());

  const confirmed = profile.facts.filter(
    f => f.epistemic === "explicit" || f.epistemic === "strongly_inferred"
  );
  const byPred = new Map<string, (typeof confirmed)[0]>();
  for (const f of confirmed) {
    const prev = byPred.get(f.predicate);
    if (!prev || f.confidence > prev.confidence) byPred.set(f.predicate, f);
  }
  const factLines = [...byPred.values()]
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, compact ? 8 : 12);

  const unknownFacts = profile.facts.filter(f => f.epistemic === "unknown");
  const conflictFacts = profile.facts.filter(
    f => f.epistemic === "contradicted"
  );
  const sourceTypes = [...new Set(profile.sources.map(s => s.source_type))];

  const groundingPct = Math.round(profile.source_grounding_rate * 100);
  const coveragePct = Math.round((profile.coverage_rate ?? 0) * 100);
  const qualityPct = Math.round((profile.source_quality_rate ?? 0) * 100);

  return (
    <div
      className={
        compact
          ? "flex min-h-0 flex-col border border-emerald-500/25 bg-[#081126] p-3"
          : "flex min-h-0 flex-col border border-emerald-500/25 bg-[#081126] p-4"
      }
    >
      <p className={eyebrow}>Your robot</p>
      <h2 className="mt-1 font-display text-2xl font-bold tracking-tight text-slate-100 sm:text-[1.85rem]">
        {product?.name || "Robot"}
        <span className="font-normal text-slate-400"> · {company}</span>
      </h2>
      {classLabel ? (
        <p className="mt-0.5 text-sm text-slate-500">{classLabel}</p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
          Profile confidence
        </span>
        <span
          className={
            tier === "A"
              ? "font-mono text-lg font-bold text-emerald-400"
              : tier === "B"
                ? "font-mono text-lg font-bold text-amber-300"
                : "font-mono text-lg font-bold text-slate-400"
          }
        >
          {tier}
        </span>
      </div>
      <p className="mt-1.5 font-mono text-[9px] uppercase tracking-[0.08em] text-slate-500">
        Grounding {groundingPct}% · Coverage {profile.coverage_level || "—"} (
        {coveragePct}
        %) · Sources {profile.source_quality_level || "—"} ({qualityPct}%)
      </p>
      <p className="mt-1 text-[12px] leading-snug text-slate-500">
        {profileConfidenceCopy(tier)}
      </p>
      {tier !== "A" ? (
        <p className="mt-1 text-[11px] leading-snug text-amber-200/70">
          Not a complete profile — unknowns below matter as much as confirmed
          facts.
        </p>
      ) : null}

      <p className={`${eyebrow} mt-5`}>Confirmed facts</p>
      {factLines.length ? (
        <ul className="mt-2 space-y-1.5">
          {factLines.map(f => (
            <li key={f.id} className="text-[13px] leading-snug text-slate-300">
              <span className="text-emerald-400/80">✓</span> {formatFactLine(f)}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-[12px] text-slate-500">
          Identity resolved; no hard constraints extracted yet.
        </p>
      )}

      {unknownFacts.length || conflictFacts.length ? (
        <>
          <p className={`${eyebrow} mt-4`}>
            {tier === "C"
              ? "Incomplete coverage — unknowns"
              : "Unknowns / contradictions"}
          </p>
          <ul className="mt-2 space-y-1">
            {conflictFacts.slice(0, 4).map(f => (
              <li
                key={f.id}
                className="text-[12px] leading-snug text-amber-200/90"
              >
                CONFLICTED — {formatFactLine(f)}
              </li>
            ))}
            {unknownFacts.slice(0, compact ? 5 : 8).map(f => (
              <li
                key={f.id}
                className="text-[12px] leading-snug text-amber-200/80"
              >
                {formatFactLine(f)}
              </li>
            ))}
          </ul>
        </>
      ) : tier !== "A" ? (
        <p className="mt-4 text-[12px] leading-snug text-amber-200/80">
          Some technical constraints may still be unknown even when not listed
          here — verify before relying on this profile.
        </p>
      ) : null}

      <p className={`${eyebrow} mt-4`}>Sources reviewed</p>
      <p className="mt-1 text-[12px] text-slate-400">
        {profile.sources.length.toString().padStart(2, "0")} sources
        {sourceTypes.length
          ? ` · ${sourceTypes.map(sourceTypeLabel).slice(0, 4).join(", ")}`
          : ""}
      </p>
      <button
        type="button"
        onClick={() => setShowSources(v => !v)}
        className="mt-2 text-left font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-emerald-400"
      >
        {showSources ? "Hide sources ←" : "View sources →"}
      </button>
      {showSources ? (
        <div className="mt-2 max-h-56 space-y-3 overflow-y-auto border border-slate-700 p-2">
          <ul className="space-y-2">
            {profile.sources.map(s => {
              const cited = factLines.filter(f => f.source_id === s.id);
              return (
                <li key={s.id} className="text-[11px] leading-snug">
                  <span className="font-mono uppercase tracking-[0.08em] text-slate-500">
                    {sourceTypeLabel(s.source_type)}
                  </span>
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-0.5 block text-slate-300 underline decoration-slate-600 hover:text-emerald-400"
                  >
                    {s.title || s.url}
                  </a>
                  {cited.length ? (
                    <p className="mt-0.5 text-[10px] text-slate-600">
                      Supports: {cited.map(f => formatFactLine(f)).join("; ")}
                    </p>
                  ) : null}
                </li>
              );
            })}
          </ul>
          <p className="border-t border-slate-800 pt-2 text-[10px] leading-snug text-slate-600">
            Open a source to verify the claim on the manufacturer page. Profile
            facts are grounded; job matches use a separate corpus.
          </p>
        </div>
      ) : null}
    </div>
  );
}
