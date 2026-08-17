/**
 * Terminal research console — perceived progress via completed stages, not fake %.
 */
import { dotsBar, researchStages, researchStatusLine } from "@/lib/submitWorkflow";

export default function JobsResearchConsole({
  elapsedMs,
  composing,
  robotName,
  companyName,
  jobCount,
  sourceCount,
}: {
  elapsedMs: number;
  composing: boolean;
  robotName?: string | null;
  companyName?: string | null;
  jobCount?: number | null;
  sourceCount?: number | null;
}) {
  const stages = researchStages(elapsedMs, composing);
  const done = stages.filter((s) => s.done).length;
  const who = (robotName || companyName || "ROBOT").toUpperCase();
  const company = (companyName || "—").toUpperCase();

  return (
    <div className="mt-4 min-h-0 flex-1 font-mono text-[11px] uppercase tracking-[0.08em] text-slate-400">
      <p className="font-semibold tracking-[0.14em] text-emerald-400">Looking for jobs…</p>
      <ul className="mt-4 space-y-2">
        {stages.map((s) => (
          <li
            key={s.n}
            className={s.done ? "text-emerald-400" : s.active ? "text-slate-200" : "text-slate-600"}
          >
            {s.n} {s.label} {s.done ? "✓" : s.active ? "…" : ""}
          </li>
        ))}
      </ul>
      <p className="mt-5 text-[12px] normal-case tracking-normal text-slate-300">
        {researchStatusLine({ robotName, companyName, composing, jobCount })}
      </p>
      <pre className="mt-6 whitespace-pre-wrap text-[10px] leading-5 text-slate-500">
        {`READYFORROBOTS JOB SEARCH

ROBOT ........... ${who}
COMPANY ......... ${company}
PROFILE ......... ${composing ? "READY" : "BUILDING"}
SOURCES ......... ${sourceCount != null ? String(sourceCount).padStart(2, "0") : "—"} FOUND
MATCHING ........ ROBOT JOBS

[${dotsBar(composing ? 3 : done)}]`}
      </pre>
      {composing ? (
        <p className="mt-4 font-semibold tracking-[0.12em] text-emerald-400">
          Displaying best matches…
        </p>
      ) : null}
    </div>
  );
}
