import { useEffect, useState } from "react";
import { Link } from "wouter";
import { ArrowRight, ExternalLink, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import Header from "@/components/Header";
import HumanoidBenchmarkMarquee from "@/components/HumanoidBenchmarkMarquee";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

// ── Types ────────────────────────────────────────────────────────────────────

type RobotRow = {
  id: number;
  name: string;
  vendor: string;
  model_slug: string;
  product_url?: string;
  status: "available" | "pilot" | "research" | "discontinued";
  specs: Record<string, unknown>;
  score_mobility: number;
  score_manipulation: number;
  score_autonomy: number;
  score_safety: number;
  score_endurance: number;
  score_market_readiness: number;
  score_total: number;
  last_scraped_at?: string;
};

// ── Score bar ────────────────────────────────────────────────────────────────

const DIM_COLORS: Record<string, string> = {
  mobility:         "#93c5fd",
  manipulation:     "#a78bfa",
  autonomy:         "#34d399",
  safety:           "#fbbf24",
  endurance:        "#6ee7b7",
  market_readiness: "#f9a8d4",
};

const DIM_LABELS: Record<string, string> = {
  mobility:         "Mobility",
  manipulation:     "Manipulation",
  autonomy:         "Autonomy",
  safety:           "Safety",
  endurance:        "Endurance",
  market_readiness: "Market Ready",
};

function ScoreBar({ value, dim }: { value: number; dim: string }) {
  const color = DIM_COLORS[dim] ?? "#a78bfa";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/8 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, background: color }}
        />
      </div>
      <span className="text-[10px] font-mono text-white/45 w-7 text-right">{Math.round(value)}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { label: string; color: string; bg: string }> = {
    available:    { label: "Available",   color: "#34d399", bg: "rgba(52,211,153,0.12)" },
    pilot:        { label: "Pilot",       color: "#fbbf24", bg: "rgba(251,191,36,0.12)" },
    research:     { label: "Research",    color: "#93c5fd", bg: "rgba(96,165,250,0.12)" },
    discontinued: { label: "Discontinued",color: "#f87171", bg: "rgba(248,113,113,0.12)" },
  };
  const s = cfg[status] ?? cfg.research;
  return (
    <span
      className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider"
      style={{ color: s.color, background: s.bg }}
    >
      {s.label}
    </span>
  );
}

// ── Robot card ───────────────────────────────────────────────────────────────

function RobotCard({ robot, rank }: { robot: RobotRow; rank: number }) {
  const [open, setOpen] = useState(false);
  const dims = ["mobility", "manipulation", "autonomy", "safety", "endurance", "market_readiness"] as const;
  const specs = robot.specs;

  return (
    <div
      className="rounded-2xl border overflow-hidden transition-colors"
      style={{
        borderColor: open ? "rgba(167,139,250,0.25)" : "rgba(255,255,255,0.07)",
        background: open ? "rgba(124,58,237,0.06)" : "rgba(13,5,32,0.55)",
      }}
    >
      {/* Main row */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full grid gap-4 px-5 py-4 text-left"
        style={{ gridTemplateColumns: "2rem 1fr 5rem 5rem 2rem" }}
      >
        {/* Rank */}
        <span className="text-xl font-black text-white/15 mt-0.5">#{rank}</span>

        {/* Name + vendor + status */}
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-bold text-white text-base leading-tight">{robot.name}</p>
            <StatusBadge status={robot.status} />
          </div>
          <p className="text-[11px] text-white/35 mt-0.5">{robot.vendor}</p>
          {/* Mini score bars */}
          <div className="mt-2 grid grid-cols-3 gap-x-3 gap-y-1 max-w-xs">
            {dims.slice(0, 6).map(d => (
              <div key={d}>
                <p className="text-[8px] text-white/25 mb-0.5 uppercase tracking-wider">{DIM_LABELS[d]}</p>
                <ScoreBar value={Number((robot as unknown as Record<string, unknown>)[`score_${d}`] ?? 0)} dim={d} />
              </div>
            ))}
          </div>
        </div>

        {/* Total score ring */}
        <div className="flex flex-col items-center justify-center">
          <span
            className="text-3xl font-black"
            style={{
              color: robot.score_total >= 65 ? "#34d399"
                   : robot.score_total >= 45 ? "#fbbf24"
                   : "#f87171",
            }}
          >
            {Math.round(robot.score_total)}
          </span>
          <span className="text-[9px] text-white/30 uppercase tracking-widest -mt-0.5">total</span>
        </div>

        {/* Product URL */}
        <div className="flex items-center justify-center">
          {robot.product_url ? (
            <a
              href={robot.product_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={e => e.stopPropagation()}
              className="text-white/25 hover:text-white/60 transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
        </div>

        <div className="flex items-center justify-center">
          {open ? <ChevronUp className="h-4 w-4 text-white/25" /> : <ChevronDown className="h-4 w-4 text-white/25" />}
        </div>
      </button>

      {/* Expanded specs */}
      {open && (
        <div className="px-5 pb-5 border-t border-white/7 pt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">Dimension scores</p>
            <div className="space-y-2">
              {dims.map(d => (
                <div key={d} className="flex items-center gap-3">
                  <span className="text-[11px] text-white/45 w-24 shrink-0">{DIM_LABELS[d]}</span>
                  <div className="flex-1">
                    <ScoreBar value={Number((robot as unknown as Record<string, unknown>)[`score_${d}`] ?? 0)} dim={d} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">Published specs</p>
            <div className="grid grid-cols-2 gap-1.5">
              {[
                ["Top speed", specs.top_speed_mps != null ? `${specs.top_speed_mps} m/s` : null],
                ["Payload", specs.payload_kg != null ? `${specs.payload_kg} kg` : null],
                ["Battery", specs.battery_life_h != null ? `${specs.battery_life_h} h` : null],
                ["Charge time", specs.charge_time_h != null ? `${specs.charge_time_h} h` : null],
                ["Height", specs.height_cm != null ? `${specs.height_cm} cm` : null],
                ["Weight", specs.weight_kg != null ? `${specs.weight_kg} kg` : null],
                ["Fingers", specs.finger_count != null ? String(specs.finger_count) : null],
                ["Price", specs.price_usd != null ? `$${Number(specs.price_usd).toLocaleString()}` : "undisclosed"],
                ["Stair climbing", specs.can_climb_stairs != null ? (specs.can_climb_stairs ? "Yes" : "No") : null],
                ["SDK", specs.has_sdk != null ? (specs.has_sdk ? "Available" : "No") : null],
              ].filter(([, v]) => v !== null).map(([label, value]) => (
                <div key={String(label)} className="rounded-lg px-2.5 py-1.5 bg-white/[0.03] border border-white/6">
                  <p className="text-[9px] text-white/30 mb-0.5">{String(label)}</p>
                  <p className="text-[11px] font-semibold text-white/70">{String(value)}</p>
                </div>
              ))}
            </div>

            {/* Feature flags */}
            <div className="mt-2 flex flex-wrap gap-1.5">
              {!!specs.can_climb_stairs && <span className="text-[9px] rounded px-2 py-0.5 bg-green-400/10 text-green-300 border border-green-400/20">Stair climbing</span>}
              {!!specs.can_navigate_rough_terrain && <span className="text-[9px] rounded px-2 py-0.5 bg-blue-400/10 text-blue-300 border border-blue-400/20">Rough terrain</span>}
              {!!specs.can_run && <span className="text-[9px] rounded px-2 py-0.5 bg-violet-400/10 text-violet-300 border border-violet-400/20">Can run</span>}
              {!!specs.has_dexterous_hands && <span className="text-[9px] rounded px-2 py-0.5 bg-purple-400/10 text-purple-300 border border-purple-400/20">Dexterous hands</span>}
              {!!specs.has_estop && <span className="text-[9px] rounded px-2 py-0.5 bg-yellow-400/10 text-yellow-300 border border-yellow-400/20">E-stop</span>}
              {!!specs.hot_swap_battery && <span className="text-[9px] rounded px-2 py-0.5 bg-teal-400/10 text-teal-300 border border-teal-400/20">Hot-swap battery</span>}
              {!!specs.has_sdk && <span className="text-[9px] rounded px-2 py-0.5 bg-pink-400/10 text-pink-300 border border-pink-400/20">SDK</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function Robots() {
  const [robots, setRobots] = useState<RobotRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "available" | "pilot" | "research">("all");
  const [sortDim, setSortDim] = useState<string>("total");
  const api = getApiBase();

  useEffect(() => {
    setLoading(true);
    fetch(`${api}/api/humanoid/robots`, liveFetchInit())
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(d => setRobots(d.robots ?? []))
      .catch(() => setRobots([]))
      .finally(() => setLoading(false));
  }, [api]);

  const filtered = robots
    .filter(r => filter === "all" || r.status === filter)
    .sort((a, b) => {
      const key = sortDim === "total" ? "score_total" : `score_${sortDim}`;
      return ((b as unknown as Record<string, number>)[key] ?? 0) - ((a as unknown as Record<string, number>)[key] ?? 0);
    });

  const dims = ["total", "mobility", "manipulation", "autonomy", "safety", "endurance", "market_readiness"];

  return (
    <div className="min-h-screen" style={{ background: "#0a0118", color: "#fff" }}>
      <Header />

      {/* ── Hero ── */}
      <section className="mx-auto max-w-5xl px-4 pt-24 pb-12 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-1.5 text-[11px] font-bold uppercase tracking-widest text-white/45">
          Humanoid Robot Index
        </div>
        <h1
          className="mb-4 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl"
          style={{ fontFamily: "'Sora', system-ui, sans-serif" }}
        >
          Benchmark every<br />
          <span style={{ color: "#a78bfa" }}>humanoid on the market</span>
        </h1>
        <p className="mx-auto max-w-2xl text-base text-white/45 leading-relaxed">
          Scored across 6 dimensions using published specs and the Fraunhofer IPA framework.
          Specs are scraped from manufacturer sites and updated automatically.
          Estimates used where live test data is unavailable.
        </p>
      </section>

      <HumanoidBenchmarkMarquee />

      {/* ── Controls ── */}
      <div className="mx-auto max-w-5xl px-4 pb-6 flex flex-wrap items-center gap-3">
        {/* Status filter */}
        <div className="flex items-center gap-1 rounded-xl border border-white/10 p-1">
          {(["all", "available", "pilot", "research"] as const).map(f => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className="px-3 py-1 rounded-lg text-[11px] font-bold capitalize transition-colors"
              style={
                filter === f
                  ? { background: "rgba(167,139,250,0.15)", color: "#c4b5fd" }
                  : { color: "rgba(255,255,255,0.3)" }
              }
            >
              {f}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div className="flex items-center gap-1.5 text-[11px] text-white/35">
          <span>Sort by:</span>
          <select
            value={sortDim}
            onChange={e => setSortDim(e.target.value)}
            className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-white/60 text-[11px] outline-none"
          >
            {dims.map(d => (
              <option key={d} value={d}>{d === "total" ? "Total score" : d.replace("_", " ")}</option>
            ))}
          </select>
        </div>

        <span className="ml-auto text-[11px] text-white/25">{filtered.length} robots</span>
      </div>

      {/* ── Robot list ── */}
      <section className="mx-auto max-w-5xl px-4 pb-16 space-y-3">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-white/30">
            <RefreshCw className="h-4 w-4 animate-spin" /> Loading benchmark data…
          </div>
        ) : filtered.length === 0 ? (
          <p className="text-center py-16 text-white/30">No robots match this filter.</p>
        ) : (
          filtered.map((robot, i) => (
            <RobotCard key={robot.model_slug} robot={robot} rank={i + 1} />
          ))
        )}
      </section>

      {/* ── Scoring methodology ── */}
      <section className="mx-auto max-w-5xl px-4 pb-16">
        <div
          className="rounded-2xl border p-7"
          style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}
        >
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-3">Scoring methodology</p>
          <div className="grid gap-3 sm:grid-cols-3 text-[12px] text-white/45 leading-relaxed">
            <div>
              <p className="font-bold text-white/70 mb-1">6 dimensions</p>
              Mobility (20%), Manipulation (20%), Autonomy (20%), Safety (15%), Endurance (15%), Market Readiness (10%).
            </div>
            <div>
              <p className="font-bold text-white/70 mb-1">Data sources</p>
              Manufacturer datasheets, press releases, third-party reviews, and the Fraunhofer IPA benchmark (May 2026).
              Specs are scraped and re-scored periodically.
            </div>
            <div>
              <p className="font-bold text-white/70 mb-1">Limitations</p>
              Where live test data is unavailable, published specs are used as estimates. Scores reflect reported capabilities, not independently verified results.
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="mx-auto max-w-5xl px-4 pb-24 text-center">
        <div
          className="rounded-2xl border px-8 py-10"
          style={{ background: "rgba(124,58,237,0.06)", borderColor: "rgba(167,139,250,0.2)" }}
        >
          <h2 className="text-xl font-extrabold text-white mb-2" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
            Need help matching a robot to your operation?
          </h2>
          <p className="text-sm text-white/40 mb-5">
            Ready For Robots matches buyer requirements to vendors with active deployments in your industry.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link href="/">
              <a
                className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold"
                style={{ background: "rgba(167,139,250,0.15)", border: "1px solid rgba(167,139,250,0.35)", color: "#c4b5fd" }}
              >
                Scan your operation <ArrowRight className="h-4 w-4" />
              </a>
            </Link>
            <Link href="/benchmark">
              <a
                className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold"
                style={{ border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.45)" }}
              >
                Evaluation criteria
              </a>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
