/**
 * Jobs CRM must not dump SIGNAL overlay internals (fit scores, labor/facility
 * flags, rfr_inference_v1 dumps, robot-type slugs). Keep named people, job
 * titles, videos, and real vendor names only.
 */

const SIGNAL_RATIONALE_NOISE = [
  /hot-type signals/i,
  /\d+\s+signals\b/i,
  /work family:\s*unknown/i,
  /high-fit industry/i,
  /^\[rfr_inference_v1\]/i,
];

export function isRealVendorName(value: string): boolean {
  const t = value.trim();
  if (t.length < 3 || t.length > 48) return false;
  if (t.includes("_")) return false;
  if (/^[a-z0-9]+$/.test(t)) return false;
  if (/^(amr|agv|cobot|arm|humanoid|uav|drone|mobile.?manipulator)$/i.test(t)) return false;
  return /[A-Z]/.test(t) || /\s/.test(t);
}

export function humanizeOverlayRationale(raw: string | null | undefined): string {
  if (!raw) return "";
  const stripped = raw.replace(/^\[rfr_inference_v1\]\s*/i, "").trim();
  const parts = stripped
    .split(/;\s*/)
    .map((p) => p.trim())
    .filter(Boolean)
    .filter((p) => !SIGNAL_RATIONALE_NOISE.some((re) => re.test(p)));
  const seen = new Set<string>();
  const unique: string[] = [];
  for (const p of parts) {
    const key = p.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(p);
  }
  return unique.slice(0, 1).join("");
}

function vendorLabel(item: string | { vendor?: string | null } | null | undefined): string {
  if (!item) return "";
  if (typeof item === "string") return item.trim();
  return (item.vendor || "").trim();
}

export type HermesJobEvidence = {
  rationale: string;
  decisionMakers: { name: string; title: string }[];
  jobTitles: string[];
  videos: { url: string; title: string }[];
  vendors: { vendor: string; model: string; why: string }[];
};

export function extractHermesJobEvidence(qualify: {
  rationale?: string | null;
  vendor_shortlist?: Array<string | { vendor?: string | null; model?: string | null; why?: string | null }> | null;
  decision_makers?: { name?: string | null; title?: string | null }[] | null;
  job_posts?: { title?: string | null; url?: string | null }[] | null;
} | null | undefined): Pick<HermesJobEvidence, "rationale" | "vendors" | "decisionMakers" | "jobTitles"> {
  if (!qualify) {
    return { rationale: "", vendors: [], decisionMakers: [], jobTitles: [] };
  }
  const decisionMakers = (qualify.decision_makers || [])
    .map((p) => ({ name: (p.name || "").trim(), title: (p.title || "").trim() }))
    .filter((p) => p.name || p.title)
    .slice(0, 3);
  const jobTitles = (qualify.job_posts || [])
    .map((j) => (j.title || "").trim())
    .filter(Boolean)
    .slice(0, 3);
  const vendors = (qualify.vendor_shortlist || [])
    .map((item) => {
      if (typeof item === "string") {
        return { vendor: item.trim(), model: "", why: "" };
      }
      return {
        vendor: (item.vendor || "").trim(),
        model: (item.model || "").trim(),
        why: (item.why || "").trim(),
      };
    })
    .filter((v) => isRealVendorName(v.vendor))
    .slice(0, 4);
  return {
    rationale: humanizeOverlayRationale(qualify.rationale),
    vendors,
    decisionMakers,
    jobTitles,
  };
}

export function pipelineHermesCard(deal: {
  hermesQualify?: {
    rationale?: string | null;
    vendor_shortlist?: Array<{ vendor?: string | null; model?: string | null; why?: string | null }>;
    decision_makers?: { name?: string | null; title?: string | null }[] | null;
  } | null;
  hermesJobTitles?: string[] | null;
  hermesDecisionMakers?: Array<{ name?: string | null; title?: string | null }> | null;
  hermesVideoEvidence?: Array<{ source_url?: string | null; title?: string | null }> | null;
}): HermesJobEvidence | null {
  const fromQualify = extractHermesJobEvidence(deal.hermesQualify);
  const jobTitles = fromQualify.jobTitles.length
    ? fromQualify.jobTitles
    : (deal.hermesJobTitles || []).map((t) => t.trim()).filter(Boolean).slice(0, 3);
  const decisionMakers = fromQualify.decisionMakers.length
    ? fromQualify.decisionMakers
    : (deal.hermesDecisionMakers || [])
        .map((p) => ({ name: (p.name || "").trim(), title: (p.title || "").trim() }))
        .filter((p) => p.name || p.title)
        .slice(0, 4);
  const videos = (deal.hermesVideoEvidence || [])
    .map((v) => ({ url: (v.source_url || "").trim(), title: (v.title || "").trim() }))
    .filter((v) => v.url)
    .slice(0, 4);
  if (
    fromQualify.vendors.length === 0 &&
    jobTitles.length === 0 &&
    decisionMakers.length === 0 &&
    videos.length === 0
  ) {
    return null;
  }
  return {
    rationale: fromQualify.rationale,
    vendors: fromQualify.vendors,
    decisionMakers,
    jobTitles,
    videos,
  };
}
