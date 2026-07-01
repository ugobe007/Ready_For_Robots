import { useEffect, useState } from "react";
import { Link } from "wouter";
import { ArrowRight } from "lucide-react";
import RobotAvatar from "@/components/RobotAvatar";
import { getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";
import { LiveDot } from "@/components/marketing/primitives";

type MarqueeRobot = {
  name: string;
  vendor: string;
  modelSlug?: string;
  productUrl?: string;
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

function scoreClass(score: number) {
  if (score >= 65) return "text-emerald-600";
  if (score >= 45) return "text-amber-600";
  return "text-red-500";
}

function MarqueeItem({ robot }: { robot: MarqueeRobot }) {
  return (
    <span className="inline-flex shrink-0 items-center gap-2.5 rounded-full border border-gray-200 bg-white px-3 py-1.5 shadow-sm">
      <RobotAvatar vendor={robot.vendor} modelSlug={robot.modelSlug} size="sm" />
      {robot.productUrl ? (
        <a
          href={robot.productUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-bold text-gray-900 transition-colors hover:text-emerald-700 hover:underline underline-offset-2"
        >
          {robot.name}
        </a>
      ) : (
        <span className="text-xs font-bold text-gray-900">{robot.name}</span>
      )}
      <span className="text-[10px] text-gray-400">{robot.vendor}</span>
      <span className={`font-mono-data text-[11px] font-bold ${scoreClass(robot.score)}`}>{robot.score}</span>
      <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400">
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
    fetch(`${getPublicReadApiBase()}/api/humanoid/robots`, liveFetchInit())
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !Array.isArray(data?.robots)) return;
        const mapped = data.robots
          .filter((row: { score_total?: number }) => typeof row.score_total === "number")
          .sort((a: { score_total: number }, b: { score_total: number }) => b.score_total - a.score_total)
          .slice(0, 14)
          .map((row: { name?: string; vendor?: string; model_slug?: string; product_url?: string; score_total?: number; status?: string }) => ({
            name: row.name || "Unknown",
            vendor: row.vendor || "",
            modelSlug: row.model_slug,
            productUrl: row.product_url,
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
      className={`border-y border-gray-100 bg-emerald-50/50 ${compact ? "" : "bg-slate-50"}`}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className={`container flex items-center gap-4 overflow-hidden ${compact ? "py-3" : "py-4"}`}>
        <div className="flex shrink-0 items-center gap-2">
          <LiveDot />
          <p className="whitespace-nowrap section-eyebrow mb-0 text-[10px]">
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
          className="inline-flex shrink-0 items-center gap-1 text-[11px] font-bold text-emerald-600 hover:text-emerald-700"
        >
          {compact ? "View all" : "Full index"}
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}
