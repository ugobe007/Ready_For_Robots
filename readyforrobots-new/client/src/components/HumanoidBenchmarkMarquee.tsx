import { useEffect, useState } from "react";
import { Link } from "wouter";
import { ArrowRight } from "lucide-react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

type MarqueeRobot = {
  name: string;
  vendor: string;
  score: number;
  status: string;
};

const FALLBACK_ROBOTS: MarqueeRobot[] = [
  { name: "Digit", vendor: "Agility Robotics", score: 68, status: "available" },
  { name: "Figure 02", vendor: "Figure AI", score: 66, status: "pilot" },
  { name: "Optimus Gen 2", vendor: "Tesla", score: 64, status: "pilot" },
  { name: "NEO", vendor: "1X Technologies", score: 62, status: "pilot" },
  { name: "G1", vendor: "Unitree", score: 58, status: "available" },
  { name: "Apollo", vendor: "Apptronik", score: 57, status: "pilot" },
  { name: "Atlas", vendor: "Boston Dynamics", score: 55, status: "research" },
  { name: "H1", vendor: "Unitree", score: 52, status: "available" },
];

const STATUS_LABEL: Record<string, string> = {
  available: "Available",
  pilot: "Pilot",
  research: "Research",
  discontinued: "Discontinued",
};

function scoreColor(score: number) {
  if (score >= 65) return "#34d399";
  if (score >= 45) return "#fbbf24";
  return "#f87171";
}

function MarqueeItem({ robot }: { robot: MarqueeRobot }) {
  return (
    <span className="inline-flex shrink-0 items-center gap-2.5 rounded-full border border-white/10 px-3.5 py-1.5" style={{ background: "rgba(255,255,255,0.03)" }}>
      <span className="text-xs font-bold text-white/85">{robot.name}</span>
      <span className="text-[10px] text-white/30">{robot.vendor}</span>
      <span className="font-mono text-[11px] font-bold" style={{ color: scoreColor(robot.score), fontFamily: "'JetBrains Mono', monospace" }}>
        {robot.score}
      </span>
      <span className="text-[9px] font-bold uppercase tracking-wider text-white/22">
        {STATUS_LABEL[robot.status] ?? robot.status}
      </span>
    </span>
  );
}

export default function HumanoidBenchmarkMarquee({ compact = false }: { compact?: boolean }) {
  const [robots, setRobots] = useState<MarqueeRobot[]>(FALLBACK_ROBOTS);
  const [paused, setPaused] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    setReduceMotion(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/humanoid/robots`, liveFetchInit())
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !Array.isArray(data?.robots)) return;
        const mapped = data.robots
          .filter((row: { score_total?: number }) => typeof row.score_total === "number")
          .sort((a: { score_total: number }, b: { score_total: number }) => b.score_total - a.score_total)
          .slice(0, 14)
          .map((row: { name?: string; vendor?: string; score_total?: number; status?: string }) => ({
            name: row.name || "Unknown",
            vendor: row.vendor || "",
            score: Math.round(row.score_total ?? 0),
            status: row.status || "research",
          }));
        if (mapped.length) setRobots(mapped);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const loop = robots.length > 1 ? [...robots, ...robots] : robots;

  return (
    <div
      className={compact ? "border-y border-white/6" : "border-b border-white/8"}
      style={{ background: compact ? "rgba(124,58,237,0.04)" : "rgba(13,5,32,0.65)" }}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className={`mx-auto flex items-center gap-4 overflow-hidden ${compact ? "max-w-6xl px-6 py-3" : "max-w-5xl px-4 py-4 lg:px-6"}`}>
        <div className="flex shrink-0 items-center gap-2">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full animate-pulse" style={{ background: "#a78bfa" }} />
          <p
            className="whitespace-nowrap text-[10px] font-bold uppercase tracking-[0.18em]"
            style={{ color: "#a78bfa", fontFamily: compact ? "'Inter', system-ui, sans-serif" : "'JetBrains Mono', monospace" }}
          >
            {compact ? "Benchmark index" : "Live humanoid scores"}
          </p>
        </div>

        <div className="relative min-w-0 flex-1 overflow-hidden">
          {reduceMotion ? (
            <div className="flex gap-2 overflow-x-auto pb-0.5">
              {robots.slice(0, compact ? 6 : 8).map((robot) => (
                <MarqueeItem key={`${robot.name}-${robot.vendor}`} robot={robot} />
              ))}
            </div>
          ) : (
            <div
              className="flex w-max gap-2.5"
              style={{
                animation: paused ? "none" : "rfr-benchmark-marquee 48s linear infinite",
              }}
            >
              {loop.map((robot, index) => (
                <MarqueeItem key={`${robot.name}-${robot.vendor}-${index}`} robot={robot} />
              ))}
            </div>
          )}
        </div>

        <Link
          href="/robots"
          className="inline-flex shrink-0 items-center gap-1 text-[11px] font-bold transition-colors hover:text-white/80"
          style={{ color: "#c4b5fd" }}
        >
          {compact ? "View all" : "Full index"}
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}
