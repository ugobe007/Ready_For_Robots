export type Tier = "A" | "B" | "C" | "D" | "E";

const CLASS_BY_TIER: Record<Tier, string> = {
  A: "rfr-tier-letter rfr-tier-letter-a",
  B: "rfr-tier-letter",
  C: "rfr-tier-letter",
  D: "rfr-tier-letter",
  E: "rfr-tier-letter rfr-tier-letter-e",
};

export function TierLetter({ tier }: { tier: Tier }) {
  return <span className={CLASS_BY_TIER[tier]}>{tier}</span>;
}
