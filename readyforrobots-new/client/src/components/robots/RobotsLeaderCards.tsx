type RobotLeaderRow = {
  name: string;
  vendor?: string;
  score_total?: number;
  heif_total?: number;
  status?: "available" | "pilot" | "research" | "discontinued";
};

type Props = {
  robots: RobotLeaderRow[];
  indexValue: (robot: any, dim: "mobility" | "manipulation" | "cognition" | "safety" | "data_pipeline" | "production") => number;
};

type LeaderCard = {
  label: string;
  name: string;
  detail: string;
  accent: string;
};

function topBy<T>(items: T[], score: (item: T) => number): T | null {
  if (!items.length) return null;
  return [...items].sort((a, b) => score(b) - score(a))[0];
}

export default function RobotsLeaderCards({ robots, indexValue }: Props) {
  if (!robots.length) return null;

  const indexLeader = topBy(robots, (r) => r.score_total ?? 0);
  const mobilityLeader = topBy(robots, (r) => indexValue(r, "mobility"));
  const manipulationLeader = topBy(robots, (r) => indexValue(r, "manipulation"));

  const vendorCounts = robots.reduce<Record<string, number>>((acc, robot) => {
    const vendor = (robot.vendor || "Unknown").trim();
    acc[vendor] = (acc[vendor] ?? 0) + 1;
    return acc;
  }, {});
  const deploymentVendor = Object.entries(vendorCounts).sort((a, b) => b[1] - a[1])[0];
  const deploymentRobots = deploymentVendor
    ? robots.filter((r) => (r.vendor || "").trim() === deploymentVendor[0])
    : [];
  const commercialCount = deploymentRobots.filter((r) => r.status === "available" || r.status === "pilot").length;

  const cards: LeaderCard[] = [
    indexLeader
      ? {
          label: "Index leader",
          name: indexLeader.name,
          detail: `${Math.round(indexLeader.score_total ?? 0)} · HEIF ${(indexLeader.heif_total ?? (indexLeader.score_total ?? 0) / 25).toFixed(1)}/4`,
          accent: "text-emerald-400",
        }
      : null,
    mobilityLeader
      ? {
          label: "Mobility leader",
          name: mobilityLeader.name,
          detail: `${indexValue(mobilityLeader, "mobility")}/100 mobility`,
          accent: "text-sky-400",
        }
      : null,
    manipulationLeader
      ? {
          label: "Manipulation leader",
          name: manipulationLeader.name,
          detail: `${indexValue(manipulationLeader, "manipulation")}/100 manipulation`,
          accent: "text-amber-300",
        }
      : null,
    deploymentVendor
      ? {
          label: "Broadest deployment",
          name: deploymentVendor[0],
          detail: `${deploymentVendor[1]} robot${deploymentVendor[1] === 1 ? "" : "s"} · ${commercialCount || deploymentVendor[1]} commercial evidence`,
          accent: "text-slate-200",
        }
      : null,
  ].filter(Boolean) as LeaderCard[];

  return (
    <div className="mt-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((card, index) => (
        <div
          key={card.label}
          className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 backdrop-blur-sm animate-fade-in-up"
          style={{ animationDelay: `${index * 80}ms` }}
        >
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{card.label}</p>
          <p className={`mt-2 font-display text-sm font-bold leading-tight ${card.accent}`}>{card.name}</p>
          <p className="mt-1 font-mono-data text-[11px] text-slate-400">{card.detail}</p>
        </div>
      ))}
    </div>
  );
}
