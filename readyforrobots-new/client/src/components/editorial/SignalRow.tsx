import { TierChip } from "./TierChip";
import type { Tier } from "./TierLetter";

type SignalRowProps = {
  tier: Tier;
  label: string;
  title: string;
  source: string;
};

export function SignalRow({ tier, label, title, source }: SignalRowProps) {
  return (
    <div className="rfr-signal-row">
      <TierChip tier={tier} label={label} />
      <span className="rfr-signal-title">{title}</span>
      <span className="rfr-signal-source">{source}</span>
    </div>
  );
}
