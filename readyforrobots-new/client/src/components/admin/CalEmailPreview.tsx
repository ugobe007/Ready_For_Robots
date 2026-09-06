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
    <div className="mt-3 rounded-lg border border-slate-700/60 bg-[#060c1c] p-3 text-slate-100">
      <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">
        Sent email preview {companyName ? `· ${companyName}` : ""}
      </p>
      <div className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-slate-200">
        {text}
      </div>
      <div className="mt-3 border-t border-slate-700/60 pt-3">
        <p className="mb-1.5 text-[10px] font-semibold text-emerald-400">
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
        <p className="mt-1 text-[10px] text-slate-400">
          <a
            href="/preview"
            className="text-emerald-400 underline underline-offset-2 hover:text-emerald-300"
          >
            View full preview
          </a>{" "}
          · appended automatically when sent via Resend
        </p>
      </div>
    </div>
  );
}
