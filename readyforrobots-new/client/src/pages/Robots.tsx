import { useEffect, useState } from "react";
import { Link } from "wouter";
import { ArrowRight, ExternalLink, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import Header from "@/components/Header";
import HeirResearchAppendix from "@/components/HeirResearchAppendix";
import RobotAvatar from "@/components/RobotAvatar";
import { HEIR_REPORTS } from "@/content/heir2026";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

// ── Types ────────────────────────────────────────────────────────────────────

type RobotRow = {
  id: number;
  name: string;
  vendor: string;
  model_slug: string;
  product_url?: string;
  image_url?: string | null;
  status: "available" | "pilot" | "research" | "discontinued";
  specs: Record<string, unknown>;
  score_mobility: number;
  score_manipulation: number;
  score_autonomy: number;
  score_cognition?: number;
  score_safety: number;
  score_endurance: number;
  score_data_pipeline?: number;
  score_market_readiness: number;
  score_production?: number;
  score_total: number;
  heif_mobility?: number;
  heif_manipulation?: number;
  heif_cognition?: number;
  heif_safety?: number;
  heif_data_pipeline?: number;
  heif_production?: number;
  heif_total?: number;
  last_scraped_at?: string;
};

const HEIF_DIMS = ["mobility", "manipulation", "cognition", "safety", "data_pipeline", "production"] as const;

const HEIF_LABELS: Record<(typeof HEIF_DIMS)[number], string> = {
  mobility: "Mobility",
  manipulation: "Manipulation",
  cognition: "Cognition",
  safety: "Safety",
  data_pipeline: "Data",
  production: "Prod",
};

const HEIF_COLORS: Record<(typeof HEIF_DIMS)[number], string> = {
  mobility: "#93c5fd",
  manipulation: "#a78bfa",
  cognition: "#34d399",
  safety: "#fbbf24",
  data_pipeline: "#6ee7b7",
  production: "#f9a8d4",
};

const INDEX_DIMS = ["mobility", "manipulation", "cognition", "safety", "data_pipeline", "production"] as const;

const INDEX_LABELS: Record<(typeof INDEX_DIMS)[number], string> = {
  mobility: "Mobility",
  manipulation: "Manipulation",
  cognition: "Cognition",
  safety: "Safety",
  data_pipeline: "Data pipeline",
  production: "Production",
};

const INDEX_COLORS = HEIF_COLORS;

const TEAL = "#03DAC5";

function heifValue(robot: RobotRow, dim: (typeof HEIF_DIMS)[number]): number {
  const key = `heif_${dim}` as keyof RobotRow;
  const direct = robot[key];
  if (typeof direct === "number") return direct;
  const scoreKey =
    dim === "cognition"
      ? "score_autonomy"
      : dim === "data_pipeline"
        ? "score_endurance"
        : dim === "production"
          ? "score_market_readiness"
          : (`score_${dim}` as keyof RobotRow);
  const score = robot[scoreKey];
  return typeof score === "number" ? score / 25 : 0;
}

function indexValue(robot: RobotRow, dim: (typeof INDEX_DIMS)[number]): number {
  const scoreKey =
    dim === "cognition"
      ? robot.score_cognition ?? robot.score_autonomy
      : dim === "data_pipeline"
        ? robot.score_data_pipeline ?? robot.score_endurance
        : dim === "production"
          ? robot.score_production ?? robot.score_market_readiness
          : (robot[`score_${dim}` as keyof RobotRow] as number | undefined);
  return Number(scoreKey ?? 0);
}

function HeifBar({ value, dim }: { value: number; dim: (typeof HEIF_DIMS)[number] }) {
  const color = HEIF_COLORS[dim];
  const pct = (value / 4) * 100;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/8 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono text-white/45 w-8 text-right">{value.toFixed(1)}</span>
    </div>
  );
}

function ScoreBar({ value, dim }: { value: number; dim: (typeof INDEX_DIMS)[number] }) {
  const color = INDEX_COLORS[dim];
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/8 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono text-white/45 w-7 text-right">{Math.round(value)}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { label: string; color: string; bg: string }> = {
    available: { label: "Available", color: "#34d399", bg: "rgba(52,211,153,0.12)" },
    pilot: { label: "Pilot", color: "#fbbf24", bg: "rgba(251,191,36,0.12)" },
    research: { label: "Research", color: "#93c5fd", bg: "rgba(96,165,250,0.12)" },
    discontinued: { label: "Discontinued", color: "#f87171", bg: "rgba(248,113,113,0.12)" },
  };
  const s = cfg[status] ?? cfg.research;
  return (
    <span className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider" style={{ color: s.color, background: s.bg }}>
      {s.label}
    </span>
  );
}

function RobotCard({ robot, rank }: { robot: RobotRow; rank: number }) {
  const [open, setOpen] = useState(false);
  const heifTotal = robot.heif_total ?? robot.score_total / 25;
  const specs = robot.specs;

  return (
    <div
      className="rounded-xl border overflow-hidden transition-colors"
      style={{
        borderColor: open ? "rgba(3,218,197,0.2)" : "rgba(255,255,255,0.08)",
        background: open ? "rgba(3,218,197,0.04)" : "rgba(255,255,255,0.02)",
      }}
    >
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full grid gap-4 px-5 py-4 text-left items-center"
        style={{ gridTemplateColumns: "2rem 2.25rem 1fr 4.5rem 4.5rem 3rem" }}
      >
        <span className="text-xl font-black text-white/15">#{rank}</span>
        <RobotAvatar
          vendor={robot.vendor}
          name={robot.name}
          modelSlug={robot.model_slug}
          productUrl={robot.product_url}
          imageUrl={robot.image_url}
          size="md"
        />
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-bold text-white text-base leading-tight">{robot.name}</p>
            <StatusBadge status={robot.status} />
          </div>
          <p className="text-[11px] text-white/35 mt-0.5">{robot.vendor}</p>
          <div className="mt-2 grid grid-cols-3 gap-x-3 gap-y-1 max-w-md">
            {HEIF_DIMS.map((d) => (
              <div key={d}>
                <p className="text-[8px] text-white/25 mb-0.5 uppercase tracking-wider">{HEIF_LABELS[d]}</p>
                <HeifBar value={heifValue(robot, d)} dim={d} />
              </div>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-center justify-center">
          <span className="text-[9px] text-white/30 uppercase tracking-widest">HEIF</span>
          <span
            className="text-2xl font-black"
            style={{
              color: heifTotal >= 2.8 ? "#34d399" : heifTotal >= 2.0 ? "#fbbf24" : "#f87171",
            }}
          >
            {heifTotal.toFixed(1)}
          </span>
          <span className="text-[9px] text-white/30">/ 4.0</span>
        </div>
        <div className="flex flex-col items-center justify-center">
          <span className="text-[9px] text-white/30 uppercase tracking-widest">Index</span>
          <span
            className="text-2xl font-black"
            style={{
              color: robot.score_total >= 65 ? "#34d399" : robot.score_total >= 45 ? "#fbbf24" : "#f87171",
            }}
          >
            {Math.round(robot.score_total)}
          </span>
          <span className="text-[9px] text-white/30">/ 100</span>
        </div>
        <div className="flex items-center justify-center gap-2">
          {robot.product_url ? (
            <a
              href={robot.product_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-white/25 hover:text-white/60 transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
          {open ? <ChevronUp className="h-4 w-4 text-white/25" /> : <ChevronDown className="h-4 w-4 text-white/25" />}
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-white/7 pt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">HEIF · 0–4</p>
            <div className="space-y-2">
              {HEIF_DIMS.map((d) => (
                <div key={d} className="flex items-center gap-3">
                  <span className="text-[11px] text-white/45 w-24 shrink-0">{INDEX_LABELS[d]}</span>
                  <div className="flex-1">
                    <HeifBar value={heifValue(robot, d)} dim={d} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">Live index · 0–100</p>
            <div className="space-y-2">
              {INDEX_DIMS.map((d) => (
                <div key={d} className="flex items-center gap-3">
                  <span className="text-[11px] text-white/45 w-24 shrink-0">{INDEX_LABELS[d]}</span>
                  <div className="flex-1">
                    <ScoreBar value={indexValue(robot, d)} dim={d} />
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
              ]
                .filter(([, v]) => v !== null)
                .map(([label, value]) => (
                  <div key={String(label)} className="rounded-lg px-2.5 py-1.5 bg-white/[0.03] border border-white/6">
                    <p className="text-[9px] text-white/30 mb-0.5">{String(label)}</p>
                    <p className="text-[11px] font-semibold text-white/70">{String(value)}</p>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Robots() {
  const [robots, setRobots] = useState<RobotRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "available" | "pilot" | "research">("all");
  const [sortDim, setSortDim] = useState<string>("total");
  const api = getApiBase();

  useEffect(() => {
    document.title = "Humanoid Index | Ready For Robots";
  }, []);

  useEffect(() => {
    setLoading(true);
    fetch(`${api}/api/humanoid/robots`, liveFetchInit())
      .then((r) => (r.ok ? r.json() : Promise.reject(r)))
      .then((d) => setRobots(d.robots ?? []))
      .catch(() => setRobots([]))
      .finally(() => setLoading(false));
  }, [api]);

  const filtered = robots
    .filter((r) => filter === "all" || r.status === filter)
    .sort((a, b) => {
      if (sortDim === "total") {
        return (b.score_total ?? 0) - (a.score_total ?? 0);
      }
      if (sortDim === "heif_total") {
        return (b.heif_total ?? b.score_total / 25) - (a.heif_total ?? a.score_total / 25);
      }
      const heifKey = `heif_${sortDim}` as keyof RobotRow;
      const scoreKey =
        sortDim === "cognition"
          ? "score_autonomy"
          : sortDim === "data_pipeline"
            ? "score_endurance"
            : sortDim === "production"
              ? "score_market_readiness"
              : (`score_${sortDim}` as keyof RobotRow);
      const bv = (b[heifKey] as number | undefined) ?? ((b[scoreKey] as number | undefined) ?? 0) / 25;
      const av = (a[heifKey] as number | undefined) ?? ((a[scoreKey] as number | undefined) ?? 0) / 25;
      return bv - av;
    });

  const sortOptions = [
    { value: "total", label: "Index total" },
    { value: "heif_total", label: "HEIF total" },
    ...HEIF_DIMS.map((d) => ({ value: d, label: HEIF_LABELS[d] })),
  ];

  return (
    <div className="min-h-screen" style={{ background: "#0a0118", color: "#fff" }}>
      <Header />

      {/* Compact page header */}
      <section className="mx-auto max-w-5xl px-4 pt-24 pb-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              Humanoid Robot Index
            </h1>
            <p className="mt-2 max-w-xl text-sm text-white/42">
              HEIF engineering maturity (HEIR 2026) plus a live 0–100 index from published specs — same six dimensions, two scales.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] shrink-0">
            {HEIR_REPORTS.map((r) => (
              <a
                key={r.href}
                href={r.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/40 hover:text-white/70 underline underline-offset-4 decoration-white/15"
              >
                HEIR 2026 · {r.title} ↗
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* HEIR research — expandable, above live index */}
      <HeirResearchAppendix />

      {/* ── Live spec-based index (primary) ── */}
      <section id="live-index" className="mx-auto max-w-5xl px-4 pb-12 pt-10">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
              Live humanoid index
            </p>
            <h2 className="mt-1 text-xl font-bold text-white">Ranked by HEIF · dual 0–4 and 0–100</h2>
            <p className="mt-1 text-[13px] text-white/38">
              Known vendors use HEIR 2026 research scores; others infer from datasheets. Index = HEIF × 25.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 rounded-lg border border-white/10 p-0.5">
              {(["all", "available", "pilot", "research"] as const).map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setFilter(f)}
                  className="px-3 py-1 rounded-md text-[11px] font-bold capitalize transition-colors"
                  style={
                    filter === f
                      ? { background: "rgba(3,218,197,0.12)", color: TEAL }
                      : { color: "rgba(255,255,255,0.35)" }
                  }
                >
                  {f}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-white/35">
              <span>Sort</span>
              <select
                value={sortDim}
                onChange={(e) => setSortDim(e.target.value)}
                className="rounded-md border border-white/10 bg-transparent px-2 py-1 text-white/55 text-[11px] outline-none"
              >
                {sortOptions.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>
            <span className="text-[11px] text-white/25">{filtered.length} robots</span>
          </div>
        </div>

        <div className="space-y-2">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-20 text-white/30">
              <RefreshCw className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : filtered.length === 0 ? (
            <p className="py-20 text-center text-white/30">No robots match this filter.</p>
          ) : (
            filtered.map((robot, i) => <RobotCard key={robot.model_slug} robot={robot} rank={i + 1} />)
          )}
        </div>
      </section>

      {/* Footer CTA — inline, no panel */}
      <section className="mx-auto max-w-5xl px-4 pb-16 text-sm text-white/40">
        <p>
          Need help matching a robot to your operation?{" "}
          <Link href="/" className="text-violet-300/90 hover:text-violet-200 underline underline-offset-4">
            Scan your operation
          </Link>
          {" · "}
          <Link href="/benchmark" className="text-white/50 hover:text-white/75 underline underline-offset-4">
            Evaluation criteria
          </Link>
          <ArrowRight className="inline h-3.5 w-3.5 ml-1 opacity-40" />
        </p>
      </section>
    </div>
  );
}
