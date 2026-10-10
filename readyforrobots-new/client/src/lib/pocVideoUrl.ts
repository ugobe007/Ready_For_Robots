/**
 * Allowlisted HTTPS video résumé URLs for Jobs CRM apply.
 * Loom / YouTube / Vimeo embed; Google Drive is a link-out. Empty is valid.
 * Error strings must not echo the pasted URL.
 */

export const JOBS_POC_VIDEO_LABEL = "Async video résumé for this Job Card";
export const JOBS_POC_VIDEO_HINT =
  "Paste an unlisted Loom, YouTube, or Vimeo URL. Google Drive opens as a link, not an embed. Empty is fine — this does not block apply. Do not upload a video file here.";
export const JOBS_POC_VIDEO_WATCH = "Watch demo";
export const JOBS_POC_VIDEO_SCRIPT_HEADING =
  "Record this Job Card, not a brand reel";
export const JOBS_POC_VIDEO_BAD_SCHEME =
  "Paste an HTTPS Loom, YouTube, Vimeo, or Google Drive link. Empty is fine — this does not block apply.";
export const JOBS_POC_VIDEO_BAD_HOST =
  "That host is not allowed. Use Loom, YouTube, Vimeo, or Google Drive.";

export type PocVideoKind = "loom" | "youtube" | "vimeo" | "drive";

export type PocVideoParsed = {
  url: string;
  kind: PocVideoKind;
  embedUrl: string | null;
};

export type PocVideoScriptBeat = {
  n: number;
  title: string;
  body: string;
};

const YOUTUBE_ID = /^[A-Za-z0-9_-]{11}$/;
const LOOM_ID = /^[A-Za-z0-9-]{8,64}$/;
const VIMEO_ID = /^(\d{5,12})$/;
const MAX_LEN = 2000;

function bareHost(host: string): string {
  let h = (host || "").toLowerCase().replace(/\.$/, "");
  if (h.startsWith("www.")) h = h.slice(4);
  return h;
}

function hostMatches(host: string, suffixes: string[]): boolean {
  const h = bareHost(host);
  return suffixes.some(suffix => h === suffix || h.endsWith(`.${suffix}`));
}

export function classifyPocVideoHost(host: string): PocVideoKind | null {
  if (hostMatches(host, ["youtu.be", "youtube.com"])) return "youtube";
  if (hostMatches(host, ["loom.com"])) return "loom";
  if (hostMatches(host, ["vimeo.com"])) return "vimeo";
  if (hostMatches(host, ["drive.google.com"])) return "drive";
  return null;
}

function youtubeId(parsed: URL): string {
  const host = bareHost(parsed.hostname);
  const parts = parsed.pathname.split("/").filter(Boolean);
  if (host === "youtu.be" && parts[0]) return parts[0].split("&")[0];
  const v = parsed.searchParams.get("v");
  if (v) return v;
  if (
    (parts[0] === "embed" || parts[0] === "shorts" || parts[0] === "v") &&
    parts[1]
  ) {
    return parts[1];
  }
  return "";
}

function loomId(parsed: URL): string {
  const parts = parsed.pathname.split("/").filter(Boolean);
  if ((parts[0] === "share" || parts[0] === "embed") && parts[1])
    return parts[1];
  return parts[parts.length - 1] || "";
}

function vimeoId(parsed: URL): string {
  const parts = parsed.pathname.split("/").filter(Boolean);
  if (parts[0] === "video" && parts[1]) return parts[1];
  for (let i = parts.length - 1; i >= 0; i -= 1) {
    if (VIMEO_ID.test(parts[i])) return parts[i];
  }
  return "";
}

export function parsePocVideoUrl(
  raw: string | null | undefined
): PocVideoParsed | null {
  const text = (raw || "").trim();
  if (!text) return null;
  if (text.length > MAX_LEN) {
    throw new Error("Video URL is too long.");
  }
  let parsed: URL;
  try {
    parsed = new URL(text);
  } catch {
    throw new Error(JOBS_POC_VIDEO_BAD_SCHEME);
  }
  if (parsed.protocol !== "https:") {
    throw new Error(JOBS_POC_VIDEO_BAD_SCHEME);
  }
  if (parsed.username || parsed.password) {
    throw new Error(JOBS_POC_VIDEO_BAD_SCHEME);
  }
  const kind = classifyPocVideoHost(parsed.hostname);
  if (!kind) {
    throw new Error(JOBS_POC_VIDEO_BAD_HOST);
  }
  parsed.hash = "";
  const url = parsed.toString();
  let embedUrl: string | null = null;
  if (kind === "youtube") {
    const id = youtubeId(parsed);
    if (YOUTUBE_ID.test(id)) {
      embedUrl = `https://www.youtube-nocookie.com/embed/${id}`;
    }
  } else if (kind === "loom") {
    const id = loomId(parsed);
    if (LOOM_ID.test(id)) {
      embedUrl = `https://www.loom.com/embed/${id}`;
    }
  } else if (kind === "vimeo") {
    const id = vimeoId(parsed);
    if (VIMEO_ID.test(id)) {
      embedUrl = `https://player.vimeo.com/video/${id}`;
    }
  }
  return { url, kind, embedUrl };
}

/** Empty is not an issue. Invalid non-empty input returns a host/scheme message (no URL). */
export function pocVideoUrlIssue(
  raw: string | null | undefined
): string | null {
  const text = (raw || "").trim();
  if (!text) return null;
  try {
    parsePocVideoUrl(text);
    return null;
  } catch (err) {
    return err instanceof Error ? err.message : JOBS_POC_VIDEO_BAD_SCHEME;
  }
}

export function pocVideoScriptBeats(opts: {
  robotName: string;
  selectedModels?: string[];
  employer?: string | null;
  jobTitle?: string;
  work?: string;
  requirements?: string[];
}): PocVideoScriptBeat[] {
  const robot = (opts.robotName || "this robot").trim() || "this robot";
  const models = (opts.selectedModels || []).map(m => m.trim()).filter(Boolean);
  const skuLine = models.length
    ? models.join(", ")
    : "the catalogued SKU you will use";
  const employer = (opts.employer || "this employer").trim() || "this employer";
  const jobTitle = (opts.jobTitle || "this job").trim() || "this job";
  const work = (opts.work || "").trim();
  const reqs = (opts.requirements || []).map(r => r.trim()).filter(Boolean);
  const reqLine = reqs.length ? reqs.slice(0, 3).join("; ") : work || jobTitle;
  return [
    {
      n: 1,
      title: "Robot + SKU",
      body: `Show ${robot} and ${skuLine} so they can see which machine this is.`,
    },
    {
      n: 2,
      title: "This employer’s work",
      body: `Show the work ${employer} needs on “${jobTitle}”: ${reqLine}.`,
    },
    {
      n: 3,
      title: "60–90s demo",
      body: "Keep it to 60–90 seconds. Unlisted link. This is a résumé for this Job Card, not a brand reel.",
    },
  ];
}
