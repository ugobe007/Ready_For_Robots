type FunnelMetrics = {
  saved: number;
  sent: number;
  replied: number;
  meetings: number;
};

const STEPS: { key: keyof FunnelMetrics; label: string }[] = [
  { key: "saved", label: "Saved to CRM" },
  { key: "sent", label: "Outreach sent" },
  { key: "replied", label: "Replied" },
  { key: "meetings", label: "Meeting+" },
];

export default function WorkflowFunnelPanel({
  funnel,
}: {
  funnel: FunnelMetrics;
}) {
  const max = Math.max(funnel.saved, 1);

  return (
    <section className="rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-neutral-400">
            Conversion funnel
          </p>
          <h2 className="mt-1 text-base font-semibold text-neutral-950">
            Pipeline → meeting
          </h2>
        </div>
        <p className="text-xs text-neutral-500">
          {funnel.saved} accounts tracked
        </p>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        {STEPS.map((step, index) => {
          const value = funnel[step.key];
          const prevKey = STEPS[index - 1]?.key;
          const prev = prevKey ? funnel[prevKey] : value;
          const pctOfSaved = Math.round((value / max) * 100);
          const stepConv =
            prev > 0 && index > 0 ? Math.round((value / prev) * 100) : null;
          return (
            <div
              key={step.key}
              className="rounded-xl border border-neutral-100 bg-neutral-50 px-3 py-3"
            >
              <p className="text-[10px] font-bold uppercase tracking-wider text-neutral-500">
                {step.label}
              </p>
              <p className="mt-1 text-2xl font-black tabular-nums text-neutral-950">
                {value}
              </p>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-neutral-200">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${pctOfSaved}%` }}
                />
              </div>
              <p className="mt-1 text-[10px] text-neutral-400">
                {pctOfSaved}% of saved
                {stepConv != null ? ` · ${stepConv}% step conv.` : ""}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
