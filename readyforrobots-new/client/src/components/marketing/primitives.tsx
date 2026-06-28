export function LiveDot() {
  return (
    <span className="relative inline-flex h-2 w-2">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
    </span>
  );
}

export function HeatBadge({ heat, onDark = false }: { heat: "HOT" | "WARM" | string; onDark?: boolean }) {
  const tier = heat.toUpperCase();
  if (tier === "HOT") return <span className={onDark ? "badge-hot-on-dark" : "badge-hot"}>HOT</span>;
  return <span className={onDark ? "badge-warm-on-dark" : "badge-warm"}>WARM</span>;
}
