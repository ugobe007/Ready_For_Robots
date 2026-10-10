import { formatInlineJobLine, type PreviewJob } from "@/lib/robotJobsPreview";

export default function InlineJobLine({ job }: { job: PreviewJob }) {
  return (
    <p className="text-[13px] leading-snug text-slate-200">
      {formatInlineJobLine(job)}
    </p>
  );
}
