import type { Tier } from "./TierLetter";

const CLASS_BY_TIER: Record<Tier, string> = {
  A: "rfr-tier-chip rfr-tier-chip-a",
  B: "rfr-tier-chip",
  C: "rfr-tier-chip",
  D: "rfr-tier-chip",
  E: "rfr-tier-chip rfr-tier-chip-e",
};

type TierChipProps = {
  tier: Tier;
  label: string;
};

export function TierChip({ tier, label }: TierChipProps) {
  return (
    <span className={CLASS_BY_TIER[tier]}>
      {tier} · {label}
    </span>
  );
}
