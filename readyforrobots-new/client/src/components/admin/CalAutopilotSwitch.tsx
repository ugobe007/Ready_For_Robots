import { Switch } from "@/components/ui/switch";

type Props = {
  enabled?: boolean;
  disabled?: boolean;
  busy?: boolean;
  everyHours?: number;
  sendLimit?: number;
  onToggle: (enabled: boolean) => void;
  compact?: boolean;
};

export default function CalAutopilotSwitch({
  enabled = false,
  disabled = false,
  busy = false,
  everyHours = 3,
  sendLimit = 25,
  onToggle,
  compact = false,
}: Props) {
  return (
    <div
      className={`flex items-center gap-3 rounded-xl border px-3 py-2 ${
        enabled
          ? "border-emerald-200 bg-emerald-50/80"
          : "border-amber-200 bg-amber-50/60"
      } ${disabled ? "opacity-60" : ""}`}
      title={
        disabled
          ? "Autopilot toggle unavailable — check server logs"
          : enabled
            ? `Cal runs draft/send cycles every ${everyHours}h (up to ${sendLimit} sends)`
            : "Cal will not auto-draft or auto-send until you turn this on"
      }
    >
      <div className="min-w-0">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-700">
          Cal autopilot
        </p>
        {!compact ? (
          <p className="text-[11px] text-gray-600">
            {enabled
              ? `On · up to ${sendLimit} verified sends / ${everyHours}h cycle`
              : "Off · manual draft & send only"}
          </p>
        ) : null}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span
          className={`text-[10px] font-bold ${enabled ? "text-emerald-700" : "text-amber-700"}`}
        >
          {busy ? "…" : enabled ? "ON" : "OFF"}
        </span>
        <Switch
          checked={enabled}
          disabled={disabled || busy}
          onCheckedChange={(checked) => onToggle(checked)}
          aria-label="Cal autopilot"
        />
      </div>
    </div>
  );
}
