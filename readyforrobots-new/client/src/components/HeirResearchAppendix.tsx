import { ChevronDown } from "lucide-react";
import { HEIF_BENCHMARK, HEIR_PULL_QUOTES, HEIR_REPORTS } from "@/content/heir2026";

/** Collapsed-by-default HEIR appendix — full detail stays in the PDFs. */
export default function HeirResearchAppendix() {
  return (
    <section className="mx-auto max-w-5xl px-4 pb-8 border-b border-white/10 pt-2">
      <details className="group">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 [&::-webkit-details-marker]:hidden">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-white/35">HEIR 2026 research</p>
            <h2 className="mt-1 text-lg font-bold text-white/90" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              Engineering maturity framework
            </h2>
            <p className="mt-1 text-sm text-white/40">
              Demo culture vs deployment reality — HEIF scores, readiness funnel, and vendor analysis in the PDF.
            </p>
          </div>
          <ChevronDown className="h-5 w-5 shrink-0 text-white/30 transition-transform group-open:rotate-180" />
        </summary>

        <div className="mt-8 space-y-8 text-sm leading-relaxed text-white/42">
          <p className="max-w-3xl">
            HEIR measures humanoids by engineering maturity, not demo choreography. The Humanoid Engineering
            Intelligence Framework (HEIF) scores mobility, manipulation, cognition, safety, data pipeline, and
            production readiness from public evidence. No vendor leads every category today.
          </p>

          <ul className="space-y-2 max-w-3xl">
            {HEIR_PULL_QUOTES.map((q) => (
              <li key={q} className="flex gap-2 text-white/55">
                <span className="text-white/25">—</span>
                <span>&ldquo;{q}&rdquo;</span>
              </li>
            ))}
          </ul>

          <div className="flex flex-wrap gap-x-6 gap-y-2 text-[13px]">
            {HEIR_REPORTS.map((r) => (
              <a
                key={r.href}
                href={r.href}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-violet-300/90 hover:text-violet-200 underline underline-offset-4 decoration-white/20"
              >
                Download {r.title} ↗
              </a>
            ))}
          </div>

          <div>
            <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.18em] text-white/30">
              HEIF snapshot · scores out of 4.0 · May 2026
            </p>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-left text-[12px] border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-[10px] uppercase tracking-wider text-white/35">
                    <th className="py-2 pr-4 font-medium">Company</th>
                    <th className="py-2 px-2 font-medium">Mob</th>
                    <th className="py-2 px-2 font-medium">Manip</th>
                    <th className="py-2 px-2 font-medium">Cog</th>
                    <th className="py-2 px-2 font-medium">Safety</th>
                    <th className="py-2 px-2 font-medium">Data</th>
                    <th className="py-2 px-2 font-medium">Prod</th>
                  </tr>
                </thead>
                <tbody>
                  {HEIF_BENCHMARK.map((row) => (
                    <tr key={row.company} className="border-b border-white/6 last:border-0">
                      <td className="py-2.5 pr-4 text-white/75">{row.company}</td>
                      <td className="py-2.5 px-2 font-mono text-white/45">{row.mobility.toFixed(1)}</td>
                      <td className="py-2.5 px-2 font-mono text-white/45">{row.manipulation.toFixed(1)}</td>
                      <td className="py-2.5 px-2 font-mono text-white/45">{row.cognition.toFixed(1)}</td>
                      <td className="py-2.5 px-2 font-mono text-white/45">{row.safety.toFixed(1)}</td>
                      <td className="py-2.5 px-2 font-mono text-white/45">{row.dataPipeline.toFixed(1)}</td>
                      <td className="py-2.5 px-2 font-mono text-white/45">{row.production.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-[11px] text-white/30">
              HEIF is a research assessment. The live index below uses published specs on a separate 0–100 scale.
            </p>
          </div>
        </div>
      </details>
    </section>
  );
}
