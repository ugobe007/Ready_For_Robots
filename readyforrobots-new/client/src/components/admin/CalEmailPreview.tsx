/**
 * Shows how the Cal email will look when sent — body text + pipeline GIF trailer.
 */
type Props = {
  bodyText: string;
  companyName?: string;
};

export default function CalEmailPreview({ bodyText, companyName }: Props) {
  const text = (bodyText || "").trim();
  if (!text) return null;

  return (
    <div className="mt-3 rounded-xl border border-emerald-500/40 bg-[#040914] p-4 text-white shadow-xl">
      <p className="mb-2 text-[10px] font-extrabold uppercase tracking-widest text-emerald-400">
        Sent email preview {companyName ? `· ${companyName}` : ""}
      </p>
      <div className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-white bg-slate-900/90 p-3 rounded-lg border border-slate-800 select-all">
        {text}
      </div>
      <div className="mt-3 border-t border-slate-800 pt-3">
        <p className="mb-1.5 text-[10px] font-bold text-emerald-400">
          Cal · pipeline preview · 6-sec loop
        </p>
        <img
          src="/marketing/cal-pipeline-demo.gif"
          alt="Cal pipeline preview animation"
          className="max-w-[280px] rounded-md border border-slate-700/60"
          width={280}
          height={95}
          loading="lazy"
        />
        <p className="mt-1 text-[10px] text-slate-300 font-medium">
          <a
            href="/preview"
            className="text-emerald-400 underline underline-offset-2 hover:text-emerald-300 font-bold"
          >
            View full preview
          </a>{" "}
          · appended automatically when sent via Resend
        </p>
      </div>
    </div>
  );
}
