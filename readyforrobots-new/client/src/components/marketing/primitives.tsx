export function LiveDot() {
  return (
    <span className="relative inline-flex h-2 w-2">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
    </span>
  );
}

export function HeatBadge({ heat }: { heat: "HOT" | "WARM" | string }) {
  const tier = heat.toUpperCase();
  if (tier === "HOT") return <span className="badge-hot">HOT</span>;
  return <span className="badge-warm">WARM</span>;
}
