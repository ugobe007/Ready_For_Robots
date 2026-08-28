/**
 * Employer / OEM watch surface for an allowlisted PoC video URL.
 * Embeds Loom / YouTube / Vimeo. Google Drive is a link-out. Never logs the URL.
 */
import {
  JOBS_POC_VIDEO_WATCH,
  parsePocVideoUrl,
} from "@/lib/pocVideoUrl";
import { JOBS_EYEBROW_CLASS } from "@/lib/jobsWorkflow";

export default function PocVideoWatch({
  url,
  heading = "Video résumé",
}: {
  url?: string | null;
  heading?: string;
}) {
  if (!url) return null;
  let parsed: ReturnType<typeof parsePocVideoUrl> = null;
  try {
    parsed = parsePocVideoUrl(url);
  } catch {
    return null;
  }
  if (!parsed) return null;
  return (
    <div className="mt-4" data-poc-video-watch="1">
      <p className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>{heading}</p>
      {parsed.embedUrl ? (
        <div className="mt-2 aspect-video w-full overflow-hidden border border-slate-600 bg-black">
          <iframe
            title={JOBS_POC_VIDEO_WATCH}
            src={parsed.embedUrl}
            className="h-full w-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            referrerPolicy="no-referrer"
          />
        </div>
      ) : null}
      <a
        href={parsed.url}
        target="_blank"
        rel="noopener noreferrer"
        referrerPolicy="no-referrer"
        className="mt-2 inline-flex text-sm text-emerald-300 underline decoration-emerald-400/50 underline-offset-2"
      >
        {JOBS_POC_VIDEO_WATCH}
      </a>
      {parsed.kind === "drive" ? (
        <p className="mt-1 text-sm text-slate-500">
          Opens Google Drive in a new tab. We do not embed Drive files.
        </p>
      ) : null}
    </div>
  );
}
