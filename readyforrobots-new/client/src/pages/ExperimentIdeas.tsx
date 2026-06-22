/**
 * Experiment lab — sandbox for new product ideas.
 * Right: live sales-lead ticker. Left: placeholder workspace (TBD).
 */
import Header from "@/components/Header";
import ExperimentLeadTicker from "@/components/ExperimentLeadTicker";
import { FlaskConical } from "lucide-react";

export default function ExperimentIdeas() {
  return (
    <div className="min-h-screen text-white" style={{ background: "#0d0520" }}>
      <Header />

      <main className="mx-auto max-w-7xl px-4 pb-16 pt-24 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center gap-3">
          <span
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-violet-500/30"
            style={{ background: "rgba(124,58,237,0.15)" }}
          >
            <FlaskConical className="h-5 w-5 text-violet-300" aria-hidden />
          </span>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-violet-300/80">Lab</p>
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              Experiments
            </h1>
            <p className="mt-1 max-w-xl text-sm text-white/45">
              Prototype space for new ideas. The live lead ticker on the right is the first experiment.
            </p>
          </div>
        </div>

        <div className="grid min-h-[calc(100vh-12rem)] gap-6 lg:grid-cols-2 lg:gap-8">
          <section
            className="flex min-h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed border-white/12 px-6 py-12 text-center"
            style={{ background: "rgba(255,255,255,0.015)" }}
            aria-label="Experiment workspace placeholder"
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/30">Left panel</p>
            <p className="mt-3 text-lg font-medium text-white/50">Workspace placeholder</p>
            <p className="mt-2 max-w-sm text-sm leading-relaxed text-white/30">
              New experiment UI will live here — controls, prototypes, and comparisons against live pipeline data.
            </p>
          </section>

          <section className="min-h-[520px]" aria-label="Live sales lead ticker">
            <ExperimentLeadTicker />
          </section>
        </div>
      </main>
    </div>
  );
}
