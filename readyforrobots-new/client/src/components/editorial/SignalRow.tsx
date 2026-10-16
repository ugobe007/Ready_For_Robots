import { TierChip } from "./TierChip";
import type { Tier } from "./TierLetter";

type SignalRowProps = {
  tier: Tier;
  label: string;
  title: string;
  source: string;
  mark?: "chip" | "letter";
};

export function SignalRow({
  tier,
  label,
  title,
  source,
  mark = "chip",
}: SignalRowProps) {
  return (
    <div className="rfr-signal-row">
      {mark === "letter" ? (
        <span className="rfr-signal-letter">{tier}</span>
      ) : (
        <TierChip tier={tier} label={label} />
      )}
      <span className="rfr-signal-title">{title}</span>
      <span className="rfr-signal-source">{source}</span>
    </div>
  );
}
