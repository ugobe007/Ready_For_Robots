import { ChevronDown } from "lucide-react";
import { HEIF_BENCHMARK, HEIR_PULL_QUOTES, HEIR_REPORTS } from "@/content/heir2026";

const TEAL = "#03DAC5";

/** Collapsed-by-default HEIR appendix — full detail stays in the PDFs. */
export default function HeirResearchAppendix() {
  return (
    <section className="mx-auto max-w-5xl px-4 pb-8 pt-2">
      <details className="group rounded-xl border overflow-hidden transition-colors" style={{ borderColor: "rgba(124,58,237,0.35)", background: "linear-gradient(135deg, rgba(124,58,237,0.12) 0%, rgba(3,218,197,0.06) 50%, rgba(10,1,24,0.9) 100%)" }}>
        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 sm:px-6 sm:py-5 [&::-webkit-details-marker]:hidden hover:bg-white/[0.03]">
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-bold uppercase tracking-[0.28em]" style={{ color: TEAL }}>
              HEIR 2026 research
            </p>
            <h2
              className="mt-1.5 text-xl font-extrabold tracking-tight text-white sm:text-2xl"
              style={{ fontFamily: "'Sora', system-ui, sans-serif", textShadow: "0 0 40px rgba(124,58,237,0.35)" }}
            >
              Engineering maturity framework
            </h2>
            <p className="mt-2 text-sm sm:text-[15px] leading-relaxed text-white/55 max-w-none">
              Demo culture vs deployment reality — HEIF scores, readiness funnel, and vendor analysis in the PDF.
            </p>
          </div>
          <span
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/15"
            style={{ background: "rgba(124,58,237,0.2)" }}
          >
            <ChevronDown className="h-5 w-5 text-white/70 transition-transform group-open:rotate-180" />
          </span>
        </summary>

        <div className="border-t border-white/10 px-5 pb-8 pt-6 sm:px-6 space-y-8 text-[15px] sm:text-base leading-[1.7] text-white/48">
          <p className="w-full max-w-none text-white/55">
            HEIR measures humanoids by engineering maturity, not demo choreography. The Humanoid Engineering
            Intelligence Framework (HEIF) scores mobility, manipulation, cognition, safety, data pipeline, and
            production readiness from public evidence. No vendor leads every category today.
          </p>

          <ul className="w-full max-w-none space-y-3">
            {HEIR_PULL_QUOTES.map((q) => (
              <li key={q} className="flex gap-3 text-white/60">
                <span className="text-white/25 shrink-0">—</span>
                <span>&ldquo;{q}&rdquo;</span>
              </li>
            ))}
          </ul>

          <div className="flex flex-wrap gap-x-6 gap-y-2 text-[14px]">
            {HEIR_REPORTS.map((r) => (
              <a
                key={r.href}
                href={r.href}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-violet-300 hover:text-violet-100 underline underline-offset-4 decoration-violet-400/40"
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
              HEIF snapshot below matches HEIR 2026 research for seven vendors. The live index applies the same framework to all robots in the ranking.
            </p>
          </div>
        </div>
      </details>
    </section>
  );
}
