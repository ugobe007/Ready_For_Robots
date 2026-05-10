import type { AutonomyMode } from "@/types/readyForRobots";

export type AutonomyDialProps = {
  mode: AutonomyMode;
  onChange: (mode: AutonomyMode) => void;
};

const MODES: { value: AutonomyMode; label: string }[] = [
  { value: "manual", label: "Manual" },
  { value: "assisted", label: "Assisted" },
  { value: "auto", label: "Auto" },
];

export default function AutonomyDial({ mode, onChange }: AutonomyDialProps) {
  return (
    <div
      className="flex min-w-0 flex-col gap-2 overflow-hidden border-b border-blue-200 bg-sky-100/80 px-4 py-4 sm:px-8"
      role="group"
      aria-label="Autonomy level"
    >
      <div className="mx-auto flex min-w-0 w-full max-w-[1400px] flex-wrap items-center justify-between gap-4">
        <p className="min-w-0 text-xs font-medium uppercase tracking-wide text-blue-800/80 break-words">
          Autonomy
        </p>
        <div className="inline-flex max-w-full min-w-0 flex-wrap rounded-sm border-2 border-blue-800 bg-white p-0.5 shadow-sm">
          {MODES.map(({ value, label }) => {
            const selected = mode === value;
            return (
              <button
                key={value}
                type="button"
                onClick={() => onChange(value)}
                className={`rounded-sm px-4 py-2 text-sm font-medium transition-colors ${
                  selected
                    ? "bg-blue-800 text-white shadow-inner"
                    : "text-slate-700 hover:bg-sky-100 hover:text-blue-900"
                }`}
                aria-pressed={selected}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>
      <p className="mx-auto w-full min-w-0 max-w-[1400px] break-words text-xs text-slate-600">
        {mode === "manual" && "You approve every action before anything is sent."}
        {mode === "assisted" && "The system drafts; you confirm before send."}
        {mode === "auto" && "The system executes; you review outcomes in the feed."}
      </p>
    </div>
  );
}
