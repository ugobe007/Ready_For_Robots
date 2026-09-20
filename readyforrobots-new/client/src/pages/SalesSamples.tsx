import { useMemo, useState, useEffect } from "react";
import {
  ArrowRight,
  Copy,
  ExternalLink,
  Shield,
  AlertTriangle,
  Mail,
  CheckCircle,
  Building2,
} from "lucide-react";
import { Link } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import AdminNav from "@/components/AdminNav";
import { JOBS_HEADER_OFFSET_CLASS } from "@/lib/jobsWorkflow";
import { normalizeUrl } from "@/lib/normalizeUrl";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, getFreshAccessToken } from "@/lib/supabase";

type SampleRobotCompany = {
  name: string;
  url: string;
  profile: string;
  suggestedSubject: string;
  draftBody: string;
};

const SAMPLE_ROBOT_COMPANIES: SampleRobotCompany[] = [
  {
    name: "Locus Robotics",
    url: "https://locusrobotics.com",
    profile: "Autonomous mobile robots (AMRs) for high-volume warehouse & fulfillment sites.",
    suggestedSubject: "Optimizing warehouse picking throughput with Locus AMRs",
    draftBody: `Hi Operations Team,

We noticed your expansion in automated fulfillment centers. SIGNAL has matched Locus Robotics' autonomous mobile robot solution with your facility profile.

Key benefits for your site:
- 2x-3x improvement in order picking speed without facility redesign.
- Rapid integration with existing warehouse management systems (WMS).
- Flexible Robots-as-a-Service (RaaS) financing options available.

Would you be open to a 10-minute briefing on feasibility and ROI estimates for your facilities?

Best regards,
ReadyForRobots Sales Team`,
  },
  {
    name: "Gecko Robotics",
    url: "https://www.geckorobotics.com",
    profile: "Wall-climbing inspection robots and asset integrity software for manufacturing.",
    suggestedSubject: "Automated wall-climbing NDT inspection for industrial assets",
    draftBody: `Hi Maintenance & Engineering Team,

We identified your heavy manufacturing facilities as a prime candidate for automated NDT structural inspections. Gecko Robotics' wall-climbing robots capture 1,000x more data than manual inspections while eliminating hazardous scaffolding.

Key benefits:
- Zero-downtime ultrasonic and visual inspections of tanks, boilers, and piping.
- Predictive corrosion heatmaps to prevent unscheduled outages.
- Immediate deployment by certified robotics technicians.

Can we share a 3-minute video overview and custom ROI assessment for your assets?

Best regards,
ReadyForRobots Sales Team`,
  },
  {
    name: "Diligent Robotics",
    url: "https://www.diligentrobots.com",
    profile: "Moxi autonomous workflow assistant robots for hospital and healthcare logistics.",
    suggestedSubject: "Relieving clinical staff burnout with Moxi autonomous assistant robots",
    draftBody: `Hi Clinical Operations Team,

Nursing teams spend up to 30% of their shifts fetching supplies and medication. Diligent Robotics' Moxi assistant robot automates routine transport so clinical staff can focus on patient care.

Key benefits:
- 24/7 autonomous retrieval of lab samples, pharmacy items, and supplies.
- Seamless integration with hospital elevator and door control systems.
- Proven ROI with over 250,000 hours logged in top health systems.

Would you be open to a brief introductory call with our healthcare robotics team?

Best regards,
ReadyForRobots Sales Team`,
  },
  {
    name: "Miso Robotics",
    url: "https://misorobotics.com",
    profile: "Flippy kitchen automation robotics for QSR and commercial food service.",
    suggestedSubject: "Commercial kitchen automation & frying robotics with Flippy",
    draftBody: `Hi Restaurant Operations Team,

Labor turnover and kitchen safety remain major friction points in high-volume food service. Miso Robotics' Flippy assistant automates fry stations with AI vision and temperature accuracy.

Key benefits:
- 30% increase in kitchen throughput during peak hours.
- Reduced oil waste and consistent food preparation quality.
- Turnkey installation with minimal kitchen reconfiguration.

Would you be interested in reviewing a sample ROI model for your restaurant locations?

Best regards,
ReadyForRobots Sales Team`,
  },
];

function buildResultsPath(url: string, sampleName: string): string {
  const params = new URLSearchParams();
  params.set("url", url);
  params.set("limit", "15");
  params.set("sample", "1");
  if (sampleName.trim()) params.set("sample_name", sampleName.trim());
  return `/results?${params.toString()}`;
}

export default function SalesSamples() {
  const { session, loading: authLoading } = useAuth();
  const [customCompanyName, setCustomCompanyName] = useState("");
  const [customCompanyUrl, setCustomCompanyUrl] = useState("");
  const [meLoading, setMeLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [signedInEmail, setSignedInEmail] = useState("");
  const [authWaitExceeded, setAuthWaitExceeded] = useState(false);

  useEffect(() => {
    if (!authLoading) {
      setAuthWaitExceeded(false);
      return;
    }
    const timer = window.setTimeout(() => setAuthWaitExceeded(true), 1800);
    return () => window.clearTimeout(timer);
  }, [authLoading]);

  useEffect(() => {
    let cancelled = false;
    async function checkAdmin() {
      if (authLoading && !authWaitExceeded) return;
      if (!session?.access_token) {
        if (!cancelled) {
          setIsAdmin(false);
          setMeLoading(false);
        }
        return;
      }
      setMeLoading(true);
      try {
        const token = await getFreshAccessToken(session.access_token);
        const res = await fetch(
          `${getApiBase()}/api/user/me`,
          liveFetchInit({ headers: authHeader(token) })
        );
        if (!res.ok) throw new Error(`user/me ${res.status}`);
        const me = (await res.json()) as { email?: string; is_admin?: boolean };
        if (!cancelled) {
          setSignedInEmail(me.email || "");
          setIsAdmin(Boolean(me.is_admin));
        }
      } catch {
        if (!cancelled) setIsAdmin(false);
      } finally {
        if (!cancelled) setMeLoading(false);
      }
    }
    void checkAdmin();
    return () => {
      cancelled = true;
    };
  }, [authLoading, authWaitExceeded, session?.access_token]);

  const customResultsPath = useMemo(() => {
    const normalized = normalizeUrl(customCompanyUrl);
    if (!normalized) return "";
    return buildResultsPath(normalized, customCompanyName || normalized);
  }, [customCompanyName, customCompanyUrl]);

  const customShareUrl =
    typeof window !== "undefined" && customResultsPath
      ? `${window.location.origin}${customResultsPath}`
      : "";

  const customDraftBody = useMemo(() => {
    if (!customCompanyName) return "";
    return `Hi Team,\n\nWe identified ${customCompanyName} as a key robotics candidate for your commercial operations. SIGNAL has generated a 15-company sample pipeline showing ROI and feasibility metrics.\n\nKey highlights:\n- Verified robot applicability & deployment timeline.\n- ROI breakdown based on labor and throughput.\n\nReview the sample pipeline here: ${customShareUrl || "https://readyforrobots.com/results"}\n\nBest regards,\nReadyForRobots Sales Team`;
  }, [customCompanyName, customShareUrl]);

  if ((authLoading && !authWaitExceeded) || meLoading) {
    return (
      <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
        <ExperimentHeader />
        <main className="mx-auto max-w-2xl px-6 pt-32 text-center text-slate-400">
          Checking admin access...
        </main>
      </div>
    );
  }

  if (!session) {
    return (
      <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
        <ExperimentHeader />
        <main className="mx-auto max-w-xl px-6 pt-32 text-center">
          <Shield className="mx-auto mb-4 h-8 w-8 text-amber-400" />
          <h1 className="text-2xl font-bold text-white">Admin Sign-in Required</h1>
          <p className="mt-3 text-sm text-slate-400">
            This sales draft and proposal generator is private to admin accounts.
          </p>
          <Link
            href="/login?next=%2Fsales%2Fsamples"
            className="mt-6 inline-flex rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-3 text-sm font-bold shadow-lg transition"
          >
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
        <ExperimentHeader />
        <main className="mx-auto max-w-xl px-6 pt-32 text-center">
          <AlertTriangle className="mx-auto mb-4 h-8 w-8 text-rose-400" />
          <h1 className="text-2xl font-bold text-white">Admin Access Required</h1>
          <p className="mt-3 text-sm text-slate-400">
            {signedInEmail || "This account"} is signed in but not registered in ADMIN_EMAILS.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/admin"
              className="inline-flex rounded-xl border border-slate-700 bg-slate-800 px-5 py-3 text-sm font-bold text-slate-200 hover:bg-slate-700"
            >
              Open admin
            </Link>
            <Link
              href="/pipeline"
              className="inline-flex rounded-xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white hover:bg-emerald-500"
            >
              Back to pipeline
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
      <ExperimentHeader />
      <main className="admin-workspace max-w-7xl mx-auto px-4 sm:px-6 pt-8 pb-16">
        <AdminNav variant="dark" />

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5 mb-8">
          <div>
            <p className="text-xs font-extrabold uppercase tracking-[0.25em] text-emerald-400">
              SIGNAL sales tools
            </p>
            <h1 className="mt-2 text-3xl sm:text-4xl font-black tracking-tight text-white">
              Sales Draft & Proposal Generator
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Review, copy, and send high-converting buyer email drafts and shareable sample proposals for top robot OEMs and distributors.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/sales-console"
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition"
            >
              Sales Console
            </Link>
            <Link
              href="/crm"
              className="rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 text-xs font-black shadow-md shadow-emerald-950/50 transition"
            >
              Open CRM Editor
            </Link>
          </div>
        </div>

        {/* Preset Robot Companies */}
        <section className="rounded-3xl border border-slate-700/60 bg-[#0c192e] p-6 shadow-xl backdrop-blur-sm sm:p-8">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Building2 className="h-5 w-5 text-emerald-400" />
                Robot Company Outreach Presets
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Pre-written buyer outreach drafts and sample pipeline benchmarks.
              </p>
            </div>
            <Link
              href="/results"
              className="text-xs font-bold text-emerald-400 hover:text-emerald-300 underline"
            >
              Manual scanner
            </Link>
          </div>

          <div className="mt-6 grid gap-6 md:grid-cols-2">
            {SAMPLE_ROBOT_COMPANIES.map(sample => {
              const resultsPath = buildResultsPath(sample.url, sample.name);
              const shareUrl =
                typeof window !== "undefined"
                  ? `${window.location.origin}${resultsPath}`
                  : "";
              return (
                <article
                  key={sample.name}
                  className="flex flex-col justify-between rounded-2xl border border-slate-700/60 bg-[#081126] p-5 shadow-md"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-base font-extrabold text-white">
                        {sample.name}
                      </h3>
                      <span className="text-[10px] font-mono text-slate-500 truncate max-w-[160px]">
                        {sample.url}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                      {sample.profile}
                    </p>

                    {/* Email Subject */}
                    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/80 p-3">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Suggested Subject
                      </p>
                      <p className="mt-1 text-xs font-bold text-emerald-300">
                        {sample.suggestedSubject}
                      </p>
                    </div>

                    {/* Draft Body */}
                    <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/80 p-3">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Draft Buyer Email
                      </p>
                      <pre className="mt-1 max-h-48 overflow-y-auto whitespace-pre-wrap text-xs text-slate-300 font-sans leading-relaxed">
                        {sample.draftBody}
                      </pre>
                    </div>
                  </div>

                  <div className="mt-5 flex flex-wrap items-center gap-2 pt-3 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => {
                        const fullText = `Subject: ${sample.suggestedSubject}\n\n${sample.draftBody}`;
                        void navigator.clipboard.writeText(fullText).then(() => {
                          toast.success(`Copied draft email for ${sample.name}`);
                        });
                      }}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-950/40 px-3 py-2 text-xs font-bold text-emerald-300 hover:bg-emerald-900/60 transition"
                    >
                      <Copy className="h-3.5 w-3.5" />
                      Copy draft email
                    </button>
                    <Link
                      href="/crm"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition"
                    >
                      <Mail className="h-3.5 w-3.5" />
                      Edit in CRM
                    </Link>
                    <Link
                      href={resultsPath}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-bold text-slate-400 hover:text-slate-200 transition"
                    >
                      Pipeline benchmark
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        {/* Custom Company Builder */}
        <section className="mt-8 rounded-3xl border border-slate-700/60 bg-[#0c192e] p-6 shadow-xl backdrop-blur-sm sm:p-8">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Mail className="h-5 w-5 text-emerald-400" />
            Generate Custom Buyer Draft & Proposal
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Enter any robot manufacturer or distributor to instantly build a draft outreach email and shareable sample proposal.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                Company Name
              </label>
              <input
                value={customCompanyName}
                onChange={e => setCustomCompanyName(e.target.value)}
                placeholder="e.g. Unitree Robotics"
                className="w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-500 focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                Website URL
              </label>
              <input
                value={customCompanyUrl}
                onChange={e => setCustomCompanyUrl(e.target.value)}
                placeholder="https://unitree.com"
                className="w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-500 focus:border-emerald-500"
              />
            </div>
          </div>

          {customDraftBody ? (
            <div className="mt-5 rounded-2xl border border-emerald-500/40 bg-[#081126] p-5">
              <p className="text-xs font-bold uppercase tracking-widest text-emerald-400">
                Generated Buyer Draft & Proposal Link
              </p>
              <pre className="mt-3 max-h-56 overflow-y-auto whitespace-pre-wrap text-xs text-slate-300 font-sans leading-relaxed border border-slate-800 bg-slate-950 p-4 rounded-xl">
                {customDraftBody}
              </pre>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    void navigator.clipboard.writeText(customDraftBody).then(() => {
                      toast.success("Custom buyer draft copied to clipboard!");
                    });
                  }}
                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-500 transition shadow-md shadow-emerald-950/40"
                >
                  <Copy className="h-3.5 w-3.5" />
                  Copy draft email
                </button>
                {customResultsPath && (
                  <Link
                    href={customResultsPath}
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition"
                  >
                    Open sample proposal
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                )}
                {customShareUrl && (
                  <button
                    type="button"
                    onClick={() => {
                      void navigator.clipboard.writeText(customShareUrl).then(() => {
                        toast.success("Shareable proposal link copied");
                      });
                    }}
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-bold text-slate-400 hover:text-slate-200 transition"
                  >
                    Copy share link
                  </button>
                )}
              </div>
            </div>
          ) : (
            <p className="mt-3 text-xs text-slate-500">
              Enter a company name and website URL above to preview the custom buyer draft email.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
