import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "wouter";
import { ArrowLeft, ArrowRight, Check, HelpCircle } from "lucide-react";
import { getApiBase } from "@/lib/apiBase";

type ProvenancedField = {
  field_path: string;
  value: unknown;
  truth_state: string;
  confidence: number;
  excerpt?: string | null;
  unit?: string | null;
};

type WorkEnvelopeItem = {
  key: string;
  label: string;
  status: string;
  truth_state: string;
  confidence: number;
  excerpt?: string | null;
};

type AnalysisResponse = {
  schema_version: string;
  analysis_id: string;
  status: string;
  progress: number;
  message?: string;
  warnings?: string[];
  profile_etag?: string | null;
  draft_profile?: {
    manufacturer?: string | null;
    model?: string | null;
    category?: string | null;
    source_url?: string | null;
    work_envelope?: WorkEnvelopeItem[];
    fields?: ProvenancedField[];
    confidence?: number;
  } | null;
  robot_id?: number | null;
};

const TOKEN_KEY = "rfr_v1_analysis_token";

function tokenFor(analysisId: string): string | null {
  try {
    const raw = sessionStorage.getItem(`${TOKEN_KEY}:${analysisId}`);
    return raw || null;
  } catch {
    return null;
  }
}

function formatValue(field: ProvenancedField): string {
  if (field.truth_state === "unknown" || field.value === null || field.value === undefined) {
    return "Unknown";
  }
  if (typeof field.value === "number") {
    return field.unit ? `${field.value} ${field.unit}` : String(field.value);
  }
  return String(field.value);
}

export default function RobotAnalysisReview() {
  const params = useParams<{ analysisId: string }>();
  const analysisId = params.analysisId;
  const [, setLocation] = useLocation();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [payloadOverride, setPayloadOverride] = useState("");

  const fields = useMemo(() => {
    const list = analysis?.draft_profile?.fields || [];
    return Object.fromEntries(list.map((f) => [f.field_path, f]));
  }, [analysis]);

  useEffect(() => {
    if (!analysisId) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const headers: Record<string, string> = {};
        const token = tokenFor(analysisId);
        if (token) headers["X-Analysis-Token"] = token;
        const res = await fetch(`${getApiBase()}/api/v1/robot-analyses/${analysisId}`, { headers });
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(body?.error?.message || `Failed to load analysis (${res.status})`);
        }
        const body = (await res.json()) as AnalysisResponse;
        if (!cancelled) setAnalysis(body);
        if (!cancelled && ["queued", "crawling", "extracting"].includes(body.status)) {
          window.setTimeout(poll, 900);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load analysis");
      }
    };
    void poll();
    return () => {
      cancelled = true;
    };
  }, [analysisId]);

  const confirm = async () => {
    if (!analysisId || !analysis?.profile_etag) return;
    setBusy(true);
    setError(null);
    try {
      const corrections = [];
      if (payloadOverride.trim()) {
        corrections.push({
          field_path: "payload_max_kg",
          value: Number(payloadOverride),
          truth_state: "oem_verified",
          note: "Seller correction",
        });
      }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      const token = tokenFor(analysisId);
      if (token) headers["X-Analysis-Token"] = token;
      const res = await fetch(`${getApiBase()}/api/v1/robot-analyses/${analysisId}/confirm`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          profile_etag: analysis.profile_etag,
          corrections,
        }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(body?.error?.message || `Confirm failed (${res.status})`);
      }
      setLocation(`/robots/${body.robot_id}/review?profile=${body.profile_version_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Confirm failed");
    } finally {
      setBusy(false);
    }
  };

  const envelope = analysis?.draft_profile?.work_envelope || [];

  return (
    <main className="min-h-screen bg-[#081126] text-[#edf4f3]">
      <div className="mx-auto max-w-3xl px-5 py-10">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-300 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Back
        </Link>
        <p className="mt-8 text-[10px] font-semibold uppercase tracking-[0.36em] text-[#7adfc8]">Robot Capability Profile</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-slate-50">
          {analysis?.draft_profile?.model || "Analyzing robot"}
        </h1>
        <p className="mt-2 text-sm text-slate-300">
          {analysis?.draft_profile?.manufacturer || "Manufacturer pending"} · {analysis?.status}
          {typeof analysis?.progress === "number" ? ` · ${analysis.progress}%` : ""}
        </p>
        {analysis?.message && <p className="mt-2 text-sm text-[#8ec8b9]">{analysis.message}</p>}
        {error && <p className="mt-4 rounded-lg border border-red-400/40 bg-red-950/40 px-3 py-2 text-sm text-red-200">{error}</p>}

        {analysis?.draft_profile && (
          <section className="mt-10 space-y-8">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">Work Envelope</h2>
              <ul className="mt-4 space-y-2">
                {envelope.map((item) => (
                  <li key={item.key} className="flex items-start gap-3 text-sm text-slate-200">
                    {item.status === "supported" ? (
                      <Check className="mt-0.5 h-4 w-4 text-emerald-400" />
                    ) : (
                      <HelpCircle className="mt-0.5 h-4 w-4 text-slate-500" />
                    )}
                    <span>
                      <span className="capitalize">{item.label}</span>
                      <span className="ml-2 text-xs uppercase tracking-wide text-slate-500">{item.truth_state}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">Key Specs</h2>
              <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                {["payload_max_kg", "lift_height_max_m", "runtime_hours", "speed_mps", "environment", "category"].map((key) => {
                  const field = fields[key];
                  if (!field) return null;
                  return (
                    <div key={key} className="border-b border-white/10 pb-2">
                      <dt className="text-xs uppercase tracking-wide text-slate-500">{key.replaceAll("_", " ")}</dt>
                      <dd className="mt-1 text-sm text-slate-100">
                        {formatValue(field)}
                        <span className="ml-2 text-xs text-slate-500">{field.truth_state}</span>
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </div>

            <div>
              <label className="text-sm text-slate-300">OEM correction — payload max (kg)</label>
              <input
                value={payloadOverride}
                onChange={(e) => setPayloadOverride(e.target.value)}
                placeholder="Leave blank to keep extracted value"
                className="mt-2 w-full rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm text-white outline-none"
              />
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <button
                type="button"
                disabled={busy || analysis.status !== "needs_review"}
                onClick={() => void confirm()}
                className="inline-flex items-center gap-2 rounded-lg bg-[#00d0a2] px-4 py-2.5 text-sm font-semibold text-[#041019] disabled:opacity-50"
              >
                Confirm profile
                <ArrowRight className="h-4 w-4" />
              </button>
              <p className="text-xs text-slate-400">
                Confidence {Math.round((analysis.draft_profile.confidence || 0) * 100)}%. Unknown stays unknown — never invented as false.
              </p>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
