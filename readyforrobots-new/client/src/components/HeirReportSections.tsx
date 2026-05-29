import type { ReactNode } from "react";
import { Download, FileText } from "lucide-react";
import {
  CAPABILITY_PYRAMID,
  DEMO_VS_DEPLOYMENT,
  ENGINEERING_SCHOOLS,
  HEIF_BENCHMARK,
  HEIR_PULL_QUOTES,
  HEIR_REPORTS,
  READINESS_FUNNEL,
  STRATEGIC_INSIGHTS,
} from "@/content/heir2026";

const VIOLET = "#a78bfa";
const TEAL = "#03DAC5";

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: VIOLET }}>
      {children}
    </p>
  );
}

function Prose({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <p className={`text-sm leading-relaxed text-white/42 ${className}`}>{children}</p>;
}

function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-3xl border border-white/10 p-6 lg:p-8 ${className}`}
      style={{ background: "rgba(255,255,255,0.035)" }}
    >
      {children}
    </div>
  );
}

export default function HeirReportSections() {
  return (
    <div className="mx-auto max-w-5xl px-4 space-y-6 pb-10">
      {/* Intro + downloads */}
      <Panel>
        <SectionLabel>HEIR 2026 · May 2026</SectionLabel>
        <h2 className="max-w-3xl text-2xl font-extrabold leading-tight text-white sm:text-3xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
          Measuring humanoids by engineering maturity — not demo choreography.
        </h2>
        <Prose className="mt-4 max-w-3xl">
          Public perception of humanoids has been shaped by staged videos: dancing, balancing, and choreographed motion.
          Those demos prove bounded behaviors under controlled assumptions. Deployment requires repeatability, manipulation,
          safety, maintainability, and operational economics.
        </Prose>
        <Prose className="mt-3 max-w-3xl">
          HEIR introduces the Humanoid Engineering Intelligence Framework (HEIF) — a comparative benchmark across mobility,
          manipulation, cognition, safety, data pipeline, and production readiness. No company currently dominates every category.
        </Prose>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {HEIR_REPORTS.map((report) => (
            <a
              key={report.href}
              href={report.href}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-start gap-4 rounded-2xl border border-white/8 p-4 transition-colors hover:border-white/15 hover:bg-white/[0.02]"
              style={{ background: "rgba(13,5,32,0.45)" }}
            >
              <div className="rounded-xl border border-white/10 p-2.5 text-white/50">
                <FileText className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-bold text-white/90">{report.title}</p>
                  <Download className="h-3.5 w-3.5 shrink-0 text-white/30 group-hover:text-white/60" />
                </div>
                <p className="mt-1 text-xs leading-relaxed text-white/38">{report.description}</p>
              </div>
            </a>
          ))}
        </div>
      </Panel>

      {/* Pull quotes */}
      <div className="grid gap-3 md:grid-cols-3">
        {HEIR_PULL_QUOTES.map((quote) => (
          <div
            key={quote}
            className="rounded-2xl border border-white/8 px-5 py-4"
            style={{ background: "rgba(13,5,32,0.45)" }}
          >
            <p className="text-sm leading-relaxed text-white/72">&ldquo;{quote}&rdquo;</p>
          </div>
        ))}
      </div>

      {/* Demo vs deployment */}
      <Panel>
        <SectionLabel>Demo culture vs deployment reality</SectionLabel>
        <h3 className="text-lg font-bold text-white">What demos prove — and what they don&apos;t</h3>
        <Prose className="mt-2 max-w-3xl">
          Humanoids are entering the same transition autonomous vehicles faced: visible demos captured attention, but the
          bottlenecks emerged in reliability, safety validation, and deployment economics.
        </Prose>
        <div className="mt-6 overflow-hidden rounded-2xl border border-white/8">
          <div className="grid grid-cols-2 border-b border-white/8 bg-white/[0.02] text-[10px] font-bold uppercase tracking-[0.18em] text-white/35">
            <div className="px-4 py-3">Demo culture</div>
            <div className="px-4 py-3 border-l border-white/8">Deployment reality</div>
          </div>
          {DEMO_VS_DEPLOYMENT.map((row) => (
            <div key={row.before} className="grid grid-cols-2 border-b border-white/6 last:border-b-0 text-[13px]">
              <div className="px-4 py-3 text-white/45">{row.before}</div>
              <div className="px-4 py-3 border-l border-white/6 text-white/70">{row.after}</div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Capability pyramid */}
      <Panel>
        <SectionLabel>Capability hierarchy</SectionLabel>
        <h3 className="text-lg font-bold text-white">Where most vendors sit today</h3>
        <Prose className="mt-2 max-w-3xl">
          Most companies operate in the lower half of the pyramid (Levels 1–3): elite mobility, early manipulation.
          The market often mistakes lower-layer locomotion for upper-layer operational maturity.
        </Prose>
        <ol className="mt-6 space-y-0">
          {[...CAPABILITY_PYRAMID].reverse().map((item) => (
            <li
              key={item.level}
              className="flex items-start gap-4 border-b border-white/6 py-3 last:border-b-0"
            >
              <span className="w-8 shrink-0 font-mono text-[11px] text-white/25">L{item.level}</span>
              <div>
                <p className="text-sm text-white/80">{item.label}</p>
                {item.note && <p className="mt-0.5 text-[11px] text-white/35">{item.note}</p>}
              </div>
            </li>
          ))}
        </ol>
      </Panel>

      {/* HEIF table */}
      <Panel>
        <SectionLabel>HEIF cross-company benchmark</SectionLabel>
        <h3 className="text-lg font-bold text-white">Research assessment · scores out of 4.0</h3>
        <Prose className="mt-2 max-w-3xl">
          HEIF scores reflect engineering maturity from public evidence — not live lab tests. The live index below uses
          published specs on a separate 0–100 scale.
        </Prose>
        <div className="mt-6 overflow-x-auto rounded-2xl border border-white/8">
          <table className="w-full min-w-[640px] text-left text-[12px]">
            <thead>
              <tr className="border-b border-white/8 bg-white/[0.02] text-[10px] font-bold uppercase tracking-[0.16em] text-white/35">
                <th className="px-4 py-3 font-bold">Company</th>
                <th className="px-3 py-3">Mobility</th>
                <th className="px-3 py-3">Manipulation</th>
                <th className="px-3 py-3">Cognition</th>
                <th className="px-3 py-3">Safety</th>
                <th className="px-3 py-3">Data</th>
                <th className="px-3 py-3">Production</th>
              </tr>
            </thead>
            <tbody>
              {HEIF_BENCHMARK.map((row) => (
                <tr key={row.company} className="border-b border-white/6 last:border-b-0">
                  <td className="px-4 py-3 font-medium text-white/80">{row.company}</td>
                  <td className="px-3 py-3 font-mono text-white/55">{row.mobility.toFixed(1)}</td>
                  <td className="px-3 py-3 font-mono text-white/55">{row.manipulation.toFixed(1)}</td>
                  <td className="px-3 py-3 font-mono text-white/55">{row.cognition.toFixed(1)}</td>
                  <td className="px-3 py-3 font-mono text-white/55">{row.safety.toFixed(1)}</td>
                  <td className="px-3 py-3 font-mono text-white/55">{row.dataPipeline.toFixed(1)}</td>
                  <td className="px-3 py-3 font-mono text-white/55">{row.production.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Readiness funnel + schools */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <SectionLabel>Operational readiness</SectionLabel>
          <h3 className="text-lg font-bold text-white">Deployment funnel</h3>
          <ul className="mt-5 space-y-0">
            {READINESS_FUNNEL.map((step) => (
              <li key={step.stage} className="border-b border-white/6 py-3 last:border-b-0">
                <div className="flex items-baseline gap-3">
                  <span className="font-mono text-[10px] text-white/30">Stage {step.stage}</span>
                  <p className="text-sm font-medium text-white/80">{step.title}</p>
                </div>
                <p className="mt-1 pl-12 text-[12px] text-white/38">{step.examples}</p>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel>
          <SectionLabel>Five engineering schools</SectionLabel>
          <h3 className="text-lg font-bold text-white">Companies optimize different layers</h3>
          <Prose className="mt-2">Humanoid vendors are not in the same race — they prioritize different parts of the stack.</Prose>
          <ul className="mt-5 space-y-4">
            {ENGINEERING_SCHOOLS.map((s) => (
              <li key={s.school}>
                <p className="text-sm font-bold text-white/85">{s.school}</p>
                <p className="mt-1 text-[12px] leading-relaxed text-white/40">
                  {s.focus}. Strength: {s.strength}. Risk: {s.risk}.
                </p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      {/* Strategic insights */}
      <Panel>
        <SectionLabel>Strategic conclusions</SectionLabel>
        <h3 className="text-lg font-bold text-white">Six hypotheses for the humanoid decade</h3>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {STRATEGIC_INSIGHTS.map((item, i) => (
            <div key={item.title} className="rounded-2xl border border-white/8 p-4" style={{ background: "rgba(13,5,32,0.45)" }}>
              <p className="text-[10px] font-mono text-white/30">0{i + 1}</p>
              <p className="mt-1 text-sm font-bold text-white/85">{item.title}</p>
              <p className="mt-2 text-[12px] leading-relaxed text-white/40">{item.body}</p>
            </div>
          ))}
        </div>
        <Prose className="mt-6 max-w-3xl">
          Humanoid economics are systems economics — not simple labor replacement. True operational cost includes hardware,
          energy, maintenance, battery wear, oversight, software licensing, and downtime risk. The first economically successful
          platforms will reduce friction around difficult, repetitive, or labor-constrained tasks — not achieve full autonomy on day one.
        </Prose>
      </Panel>

      {/* Live index divider */}
      <div className="flex items-center gap-4 pt-2">
        <div className="h-px flex-1 bg-white/10" />
        <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
          Live spec-based index
        </p>
        <div className="h-px flex-1 bg-white/10" />
      </div>
    </div>
  );
}
