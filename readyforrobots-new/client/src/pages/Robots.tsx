import { useEffect, useState } from "react";
import { Link } from "wouter";
import { ArrowRight, ExternalLink, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import RobotsLeaderCards from "@/components/robots/RobotsLeaderCards";
import HeirResearchAppendix from "@/components/HeirResearchAppendix";
import HumanoidIndexSummaryIntro from "@/components/HumanoidIndexSummaryIntro";
import HumanoidIntelligenceReport from "@/components/HumanoidIntelligenceReport";
import RobotAvatar from "@/components/RobotAvatar";
import { HEIR_REPORTS } from "@/content/heir2026";
import {
  fetchWithTimeout,
  getApiBase,
  getPublicReadApiBase,
  publicFetchInit,
  readSurfaceCache,
  writeSurfaceCache,
} from "@/lib/apiBase";
import { useHumanoidIntelligenceReport } from "@/lib/humanoidIntelligenceReport";

// ── Types ────────────────────────────────────────────────────────────────────

type RobotRow = {
  id: number;
  name: string;
  vendor: string;
  model_slug: string;
  product_url?: string;
  image_url?: string | null;
  status: "available" | "pilot" | "research" | "discontinued";
  country?: string;
  created_at?: string;
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
  ai_stack?: AiStack;
  spec_provenance?: SpecProvenance;
  data_confidence?: number | null;
  confidence_label?: "high" | "medium" | "low" | "curated";
  verified_field_count?: number;
  official_field_count?: number;
  heif_total_adjusted?: number | null;
};

type SpecProvenanceEntry = {
  url?: string | null;
  quote?: string | null;
  tier: "official" | "third_party";
};

type SpecProvenance = Record<string, SpecProvenanceEntry>;

type AiStack = {
  primary_model?: string;
  model_family?: string;
  stack_layers?: string[];
  compute?: string;
  third_party?: string[];
  unique_claim?: string;
};

const MODEL_FAMILY_LABELS: Record<string, string> = {
  vla: "Vision-Language-Action (VLA)",
  world_model: "World model",
  physics_fm: "Physics foundation model",
  hybrid: "Hybrid cognitive stack",
  fleet_platform: "Fleet / ops platform",
  research_stack: "Research / open stack",
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
  manipulation: "#10b981",
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

const TEAL = "#059669";
const ROBOTS_SURFACE_KEY = "humanoid_robots_v2";
const ROBOTS_SURFACE_TTL_MS = 3 * 60 * 60 * 1000;

function isWithinDays(iso: string | undefined, days: number): boolean {
  if (!iso) return false;
  const ts = Date.parse(iso);
  if (!Number.isFinite(ts)) return false;
  const delta = Date.now() - ts;
  return delta >= 0 && delta <= days * 24 * 60 * 60 * 1000;
}

function policyTone(country?: string): { label: string; color: string; bg: string } {
  const key = (country || "").trim().toLowerCase();
  if (key === "china") {
    return { label: "Higher US risk", color: "#b45309", bg: "rgba(245,158,11,0.16)" };
  }
  if (key === "usa" || key === "united states" || key === "us") {
    return { label: "US-favored", color: "#047857", bg: "rgba(16,185,129,0.16)" };
  }
  return { label: "Policy-neutral", color: "#1d4ed8", bg: "rgba(59,130,246,0.14)" };
}

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
      <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono text-gray-500 w-8 text-right">{value.toFixed(1)}</span>
    </div>
  );
}

function ScoreBar({ value, dim }: { value: number; dim: (typeof INDEX_DIMS)[number] }) {
  const color = INDEX_COLORS[dim];
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono text-gray-500 w-7 text-right">{Math.round(value)}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { label: string; color: string; bg: string }> = {
    available: { label: "Available", color: "#047857", bg: "rgba(5,150,105,0.12)" },
    pilot: { label: "Pilot", color: "#b45309", bg: "rgba(245,158,11,0.15)" },
    research: { label: "Research", color: "#1d4ed8", bg: "rgba(59,130,246,0.12)" },
    discontinued: { label: "Discontinued", color: "#b91c1c", bg: "rgba(239,68,68,0.12)" },
  };
  const s = cfg[status] ?? cfg.research;
  return (
    <span className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider" style={{ color: s.color, background: s.bg }}>
      {s.label}
    </span>
  );
}

function ProvBadge({ entry }: { entry: SpecProvenanceEntry }) {
  const official = entry.tier === "official";
  const color = official ? "#34d399" : "#fbbf24";
  const bg = official ? "rgba(52,211,153,0.14)" : "rgba(251,191,36,0.14)";
  const label = official ? "Official" : "3rd-party";
  const tip = [label + " source", entry.url ?? "", entry.quote ? `"${entry.quote}"` : ""]
    .filter(Boolean)
    .join("\n");
  const badge = (
    <span
      className="rounded px-1 py-0.5 text-[7px] font-bold uppercase tracking-wider cursor-help"
      style={{ color, background: bg }}
      title={tip}
    >
      {official ? "OFF" : "3P"}
    </span>
  );
  if (!entry.url) return badge;
  return (
    <a href={entry.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
      {badge}
    </a>
  );
}

function ConfidenceChip({ robot }: { robot: RobotRow }) {
  const label = robot.confidence_label;
  if (!label) return null;
  if (label === "curated") {
    return (
      <span
        className="rounded-full px-2 py-0.5 text-[8px] font-bold uppercase tracking-wider"
        style={{ color: "#93c5fd", background: "rgba(96,165,250,0.12)" }}
        title="Specs from curated datasheets/seed data (no auto-verified fields yet)"
      >
        Curated
      </span>
    );
  }
  const color = label === "high" ? "#34d399" : label === "medium" ? "#fbbf24" : "#f87171";
  const bg =
    label === "high"
      ? "rgba(52,211,153,0.12)"
      : label === "medium"
        ? "rgba(251,191,36,0.12)"
        : "rgba(248,113,113,0.12)";
  const tip = [
    `Data confidence ${robot.data_confidence}/100 (${label})`,
    `${robot.official_field_count}/${robot.verified_field_count} auto-verified fields from official sources`,
    robot.heif_total_adjusted != null ? `Confidence-adjusted HEIF: ${robot.heif_total_adjusted}` : "",
  ]
    .filter(Boolean)
    .join("\n");
  return (
    <span
      className="rounded-full px-2 py-0.5 text-[8px] font-bold uppercase tracking-wider"
      style={{ color, background: bg }}
      title={tip}
    >
      {robot.data_confidence}% conf
    </span>
  );
}

function RobotNameLink({ name, url }: { name: string; url?: string }) {
  if (!url) {
    return <p className="font-bold text-gray-900 text-base leading-tight">{name}</p>;
  }
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      className="font-bold text-gray-900 text-base leading-tight transition-colors hover:text-emerald-700 underline-offset-2 hover:underline"
    >
      {name}
    </a>
  );
}

function resolveAiStack(robot: RobotRow): AiStack | null {
  if (robot.ai_stack?.primary_model) return robot.ai_stack;
  const nested = robot.specs?.ai_stack;
  if (nested && typeof nested === "object" && !Array.isArray(nested)) {
    const s = nested as AiStack;
    if (s.primary_model) return s;
  }
  return null;
}

function AiStackPanel({ stack }: { stack: AiStack }) {
  const family = stack.model_family
    ? MODEL_FAMILY_LABELS[stack.model_family] ?? stack.model_family
    : null;
  return (
    <div className="sm:col-span-2 lg:col-span-3 rounded-xl border border-emerald-500/20 bg-emerald-600/[0.06] px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-600/80 mb-2">AI stack</p>
      <p className="text-sm font-semibold text-gray-900">{stack.primary_model}</p>
      {family ? <p className="text-[11px] text-gray-500 mt-0.5">{family}</p> : null}
      {stack.stack_layers && stack.stack_layers.length > 0 ? (
        <p className="text-[11px] text-gray-500 mt-2">
          <span className="text-gray-400">Layers: </span>
          {stack.stack_layers.join(" → ")}
        </p>
      ) : null}
      {stack.compute ? (
        <p className="text-[11px] text-gray-500 mt-1">
          <span className="text-gray-400">Compute: </span>
          {stack.compute}
        </p>
      ) : null}
      {stack.third_party && stack.third_party.length > 0 ? (
        <p className="text-[11px] text-gray-500 mt-1">
          <span className="text-gray-400">Partners / platform: </span>
          {stack.third_party.join(", ")}
        </p>
      ) : null}
      {stack.unique_claim ? (
        <p className="text-[11px] text-gray-600 mt-2 leading-relaxed border-t border-gray-100 pt-2">
          {stack.unique_claim}
        </p>
      ) : null}
    </div>
  );
}

function RobotCard({ robot, rank }: { robot: RobotRow; rank: number }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<Partial<RobotRow> | null>(null);
  const heifTotal = robot.heif_total ?? robot.score_total / 25;
  const specs = robot.specs;
  const aiStack = resolveAiStack(robot);
  const recentTracked = isWithinDays(robot.created_at, 60) || isWithinDays(robot.last_scraped_at, 60);
  const policy = policyTone(robot.country);
  const provenance = detail?.spec_provenance ?? robot.spec_provenance ?? {};
  const enriched: RobotRow = detail ? { ...robot, ...detail } : robot;

  useEffect(() => {
    if (!open || detail) return;
    let cancelled = false;
    void fetchWithTimeout(
      `${getApiBase()}/api/humanoid/robots/${robot.model_slug}`,
      publicFetchInit(),
      10_000,
      { publicCache: true },
    )
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d) setDetail(d as Partial<RobotRow>);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [open, detail, robot.model_slug]);

  const cardBg = rank <= 3 ? "rgba(16,185,129,0.07)" : rank % 2 === 0 ? "#0d1a33" : "#0b162f";
  const cardBorder = open ? "rgba(16,185,129,0.45)" : rank <= 3 ? "rgba(16,185,129,0.30)" : "#334155";

  return (
    <div
      className="rounded-xl border overflow-hidden transition-colors shadow-sm"
      style={{
        borderColor: cardBorder,
        background: open ? "rgba(16,185,129,0.10)" : cardBg,
      }}
    >
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full grid gap-4 px-5 py-4 text-left items-center"
        style={{ gridTemplateColumns: "2rem 2.25rem 1fr 4.5rem 4.5rem 3rem" }}
      >
        <span className="text-xl font-black text-gray-900 tabular-nums">#{rank}</span>
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
            <RobotNameLink name={robot.name} url={robot.product_url} />
            <StatusBadge status={robot.status} />
            <span className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider" style={{ color: policy.color, background: policy.bg }}>
              {policy.label}
            </span>
            {recentTracked ? (
              <span className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider" style={{ color: "#0369a1", background: "rgba(56,189,248,0.16)" }}>
                New ≤60d
              </span>
            ) : null}
            {specs?.total_dof != null ? (
              <span
                title={specs.dof_note != null ? String(specs.dof_note) : undefined}
                className="text-[9px] font-bold uppercase tracking-wider text-cyan-300/80 bg-cyan-400/10 border border-cyan-400/25 rounded-full px-2 py-0.5"
              >
                {String(specs.total_dof)} DOF
              </span>
            ) : null}
          </div>
          <p className="text-[11px] text-gray-600 mt-0.5">{robot.vendor}</p>
          {aiStack?.primary_model ? (
            <p className="text-[10px] text-emerald-600/70 mt-1 truncate max-w-md" title={aiStack.primary_model}>
              {aiStack.primary_model}
            </p>
          ) : null}
          <div className="mt-2 grid grid-cols-3 gap-x-3 gap-y-1 max-w-md">
            {HEIF_DIMS.map((d) => (
              <div key={d}>
                <p className="text-[8px] text-gray-500 mb-0.5 uppercase tracking-wider">{HEIF_LABELS[d]}</p>
                <HeifBar value={heifValue(robot, d)} dim={d} />
              </div>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-center justify-center">
          <span className="text-[9px] text-gray-500 uppercase tracking-widest">HEIF</span>
          <span
            className="text-2xl font-black"
            style={{
              color: heifTotal >= 2.8 ? "#34d399" : heifTotal >= 2.0 ? "#fbbf24" : "#f87171",
            }}
          >
            {heifTotal.toFixed(1)}
          </span>
          <span className="text-[9px] text-gray-500">/ 4.0</span>
        </div>
        <div className="flex flex-col items-center justify-center">
          <span className="text-[9px] text-gray-500 uppercase tracking-widest">Index</span>
          <span
            className="text-2xl font-black"
            style={{
              color: robot.score_total >= 65 ? "#34d399" : robot.score_total >= 45 ? "#fbbf24" : "#f87171",
            }}
          >
            {Math.round(robot.score_total)}
          </span>
          <span className="text-[9px] text-gray-500">/ 100</span>
        </div>
        <div className="flex items-center justify-center gap-2">
          {robot.product_url ? (
            <a
              href={robot.product_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
          {open ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-white/7 pt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">HEIF · 0–4</p>
            <div className="space-y-2">
              {HEIF_DIMS.map((d) => (
                <div key={d} className="flex items-center gap-3">
                  <span className="text-[11px] text-gray-500 w-24 shrink-0">{INDEX_LABELS[d]}</span>
                  <div className="flex-1">
                    <HeifBar value={heifValue(robot, d)} dim={d} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">Live index · 0–100</p>
            <div className="space-y-2">
              {INDEX_DIMS.map((d) => (
                <div key={d} className="flex items-center gap-3">
                  <span className="text-[11px] text-gray-500 w-24 shrink-0">{INDEX_LABELS[d]}</span>
                  <div className="flex-1">
                    <ScoreBar value={indexValue(robot, d)} dim={d} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Published specs</p>
              <ConfidenceChip robot={enriched} />
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {([
                ["Top speed", specs.top_speed_mps != null ? `${specs.top_speed_mps} m/s` : null, "top_speed_mps"],
                ["Payload", specs.payload_kg != null ? `${specs.payload_kg} kg` : null, "payload_kg"],
                ["Battery", specs.battery_life_h != null ? `${specs.battery_life_h} h` : null, "battery_life_h"],
                ["Charge time", specs.charge_time_h != null ? `${specs.charge_time_h} h` : null, "charge_time_h"],
                ["Height", specs.height_cm != null ? `${specs.height_cm} cm` : null, "height_cm"],
                ["Weight", specs.weight_kg != null ? `${specs.weight_kg} kg` : null, "weight_kg"],
                ["Fingers", specs.finger_count != null ? String(specs.finger_count) : null, "finger_count"],
                ["DOF", specs.total_dof != null ? `${specs.total_dof}${specs.dof_note != null ? " *" : ""}` : null, "total_dof"],
                ["Peak joint torque", specs.peak_torque_nm != null ? `${specs.peak_torque_nm} N·m` : (specs.peak_torque_note != null ? String(specs.peak_torque_note) : null), "peak_torque_nm"],
                ["Price", specs.price_usd != null ? `$${Number(specs.price_usd).toLocaleString()}` : "undisclosed", "price_usd"],
                ["Stair climbing", specs.can_climb_stairs != null ? (specs.can_climb_stairs ? "Yes" : "No") : null, "can_climb_stairs"],
                ["SDK", specs.has_sdk != null ? (specs.has_sdk ? "Available" : "No") : null, "has_sdk"],
              ] as [string, string | null, string][])
                .filter(([, v]) => v !== null)
                .map(([label, value, key]) => {
                  const prov = provenance[key];
                  return (
                    <div key={label} className="rounded-lg px-2.5 py-1.5 bg-white/[0.03] border border-white/10">
                      <div className="flex items-center justify-between gap-1 mb-0.5">
                        <p className="text-[9px] text-gray-400">{label}</p>
                        {prov ? <ProvBadge entry={prov} /> : null}
                      </div>
                      <p
                        className="text-[11px] font-semibold text-gray-600"
                        title={key === "total_dof" && specs.dof_note != null ? String(specs.dof_note) : undefined}
                      >
                        {String(value)}
                      </p>
                    </div>
                  );
                })}
            </div>
          </div>
          {aiStack ? <AiStackPanel stack={aiStack} /> : null}
        </div>
      )}
    </div>
  );
}

export default function Robots() {
  const cachedRobots = readSurfaceCache<RobotRow[]>(ROBOTS_SURFACE_KEY, ROBOTS_SURFACE_TTL_MS);
  const [robots, setRobots] = useState<RobotRow[]>(cachedRobots?.data ?? []);
  const [loading, setLoading] = useState(!(cachedRobots?.data?.length));
  const [filter, setFilter] = useState<"all" | "available" | "pilot" | "research">("all");
  const [sortDim, setSortDim] = useState<string>("total");
  const api = getPublicReadApiBase();
  const { report: intelligenceReport, loading: reportLoading, error: reportError } =
    useHumanoidIntelligenceReport(12);

  useEffect(() => {
    document.title = "Humanoid Index | Ready For Robots";
  }, []);

  useEffect(() => {
    let cancelled = false;
    const paintedFromCache = Boolean(cachedRobots?.data?.length);
    if (!paintedFromCache) setLoading(true);
    if (paintedFromCache) return;

    void fetchWithTimeout(
      `${api}/api/humanoid/robots`,
      publicFetchInit(),
      15_000,
      { publicCache: true },
    )
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => {
        if (cancelled) return;
        const rows = (d.robots ?? []) as RobotRow[];
        setRobots(rows);
        if (rows.length) writeSurfaceCache(ROBOTS_SURFACE_KEY, rows);
      })
      .catch(() => {
        if (cancelled || paintedFromCache) return;
        setRobots([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
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

  const indexLeader = robots.length
    ? [...robots].sort((a, b) => (b.score_total ?? 0) - (a.score_total ?? 0))[0]
    : null;

  return (
    <div className="robots-page min-h-screen flex flex-col">
      <Header />

      <PageHeroDark
        maxWidthClass="max-w-5xl"
        badge={
          <div className="page-hero-badge">
            {robots.length || 109} humanoids benchmarked · HEIR 2026 · Updated monthly
          </div>
        }
        eyebrow="Humanoid intelligence"
        title={
          <>
            Humanoid Robot{" "}
            <span className="text-emerald-400">Index</span>
          </>
        }
        description="HEIR benchmarking, market signals, and live rankings. HEIR measures humanoids by engineering maturity, not demo choreography — scored across mobility, manipulation, cognition, safety, data pipeline, and production readiness."
        actions={
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[12px]">
            <Link
              href="/robots/report"
              className="inline-flex items-center gap-1 rounded-md bg-emerald-600/90 px-3 py-1.5 font-semibold text-white hover:bg-emerald-500"
            >
              Comparison report <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            {HEIR_REPORTS.map((r) => (
              <a
                key={r.href}
                href={r.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 underline underline-offset-4 decoration-white/20 hover:text-emerald-300"
              >
                HEIR 2026 · {r.title} ↗
              </a>
            ))}
          </div>
        }
        innerClassName="pb-6"
      >
        <RobotsLeaderCards robots={robots} indexValue={indexValue} />
      </PageHeroDark>
      <div className="page-hero-fade" aria-hidden />

      {/* HEIR research — collapsed appendix */}
      <HeirResearchAppendix />

      <HumanoidIndexSummaryIntro
        robotCount={robots.length}
        keyFindings={intelligenceReport?.narrative?.key_findings ?? null}
        loading={reportLoading}
        leaderName={indexLeader?.name}
        leaderScore={indexLeader?.score_total}
      />

      {/* ── Live spec-based index (primary) ── */}
      <section id="live-index" className="mx-auto max-w-5xl px-4 pb-8 pt-2">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
              Live humanoid index
            </p>
            <h2 className="mt-1 text-xl font-bold text-gray-900">Ranked by HEIF · dual 0–4 and 0–100</h2>
            <p className="mt-1 text-[13px] text-gray-600">
              Known vendors use HEIR 2026 research scores; others infer from datasheets. Index = HEIF × 25.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 rounded-lg border border-gray-200 p-0.5">
              {(["all", "available", "pilot", "research"] as const).map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1 rounded-md text-[11px] font-bold capitalize transition-colors ${
                    filter === f
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "text-gray-600 hover:text-emerald-700"
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
              <span>Sort</span>
              <select
                value={sortDim}
                onChange={(e) => setSortDim(e.target.value)}
                className="rounded-md border border-gray-200 bg-transparent px-2 py-1 text-gray-500 text-[11px] outline-none"
              >
                {sortOptions.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>
            <span className="text-[11px] text-gray-500">{filtered.length} robots</span>
          </div>
        </div>

        <div className="space-y-2">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-20 text-gray-400">
              <RefreshCw className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : filtered.length === 0 ? (
            <p className="py-20 text-center text-gray-400">No robots match this filter.</p>
          ) : (
            filtered.map((robot, i) => <RobotCard key={robot.model_slug} robot={robot} rank={i + 1} />)
          )}
        </div>
      </section>

      {/* Optional analysis — below index, collapsed by default */}
      <section id="intelligence-report" className="mx-auto max-w-5xl px-4 pb-10">
        <HumanoidIntelligenceReport
          report={intelligenceReport}
          loading={reportLoading}
          error={reportError}
        />
      </section>

      {/* Footer CTA — inline, no panel */}
      <section className="mx-auto max-w-5xl px-4 pb-16 text-sm text-gray-500">
        <p>
          Looking for robots for your facility?{" "}
          <Link href="/find-robots" className="text-emerald-600/90 hover:text-emerald-700 underline underline-offset-4">
            Submit your use case
          </Link>
          {" · "}
          <Link href="/" className="text-gray-500 hover:text-gray-700 underline underline-offset-4">
            Scan your operation
          </Link>
          {" · "}
          <Link href="/benchmark" className="text-gray-500 hover:text-gray-700 underline underline-offset-4">
            Evaluation criteria
          </Link>
          <ArrowRight className="inline h-3.5 w-3.5 ml-1 opacity-40" />
        </p>
      </section>
      <SiteFooter />
    </div>
  );
}
