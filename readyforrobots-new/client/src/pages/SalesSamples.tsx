import { useMemo, useState } from "react";
import { useEffect } from "react";
import { ArrowRight, Copy, ExternalLink, Shield, AlertTriangle } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { normalizeUrl } from "@/lib/normalizeUrl";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, getFreshAccessToken } from "@/lib/supabase";

type SampleRobotCompany = {
  name: string;
  url: string;
  profile: string;
};

const SAMPLE_ROBOT_COMPANIES: SampleRobotCompany[] = [
  {
    name: "Locus Robotics",
    url: "https://locusrobotics.com",
    profile: "Autonomous mobile robots for warehouses and fulfillment sites.",
  },
  {
    name: "Gecko Robotics",
    url: "https://www.geckorobotics.com",
    profile: "Vision inspection and QA robotics for manufacturing lines.",
  },
  {
    name: "Diligent Robotics",
    url: "https://www.diligentrobots.com",
    profile: "Autonomous transport and workflow robots for hospitals.",
  },
  {
    name: "Miso Robotics",
    url: "https://misorobotics.com",
    profile: "Kitchen automation robotics for food service and QSR operations.",
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
        const res = await fetch(`${getApiBase()}/api/user/me`, liveFetchInit({ headers: authHeader(token) }));
        if (!res.ok) throw new Error(`user/me ${res.status}`);
        const me = await res.json() as { email?: string; is_admin?: boolean };
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

  if ((authLoading && !authWaitExceeded) || meLoading) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <Header />
        <main className="mx-auto max-w-2xl px-6 pt-28 text-center text-slate-500">Checking admin access...</main>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <Shield className="mx-auto mb-4 h-7 w-7 text-amber-500" />
          <h1 className="text-2xl font-bold text-slate-900">Admin sign in required</h1>
          <p className="mt-3 text-sm text-slate-600">This sales sample builder is private to admin accounts.</p>
          <Link href="/login?next=%2Fsales%2Fsamples" className="mt-6 inline-flex rounded-xl border border-amber-500 px-5 py-3 text-sm font-bold text-amber-600">
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <AlertTriangle className="mx-auto mb-4 h-7 w-7 text-red-400" />
          <h1 className="text-2xl font-bold text-slate-900">Admin access required</h1>
          <p className="mt-3 text-sm text-slate-600">
            {signedInEmail || "This account"} is signed in but not in ADMIN_EMAILS.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Link href="/admin" className="inline-flex rounded-xl border border-slate-300 px-5 py-3 text-sm font-bold text-slate-700">
              Open admin
            </Link>
            <Link href="/pipeline" className="inline-flex rounded-xl border border-amber-500 px-5 py-3 text-sm font-bold text-amber-600">
              Back to pipeline
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header />
      <PageHeroDark
        maxWidthClass="max-w-4xl"
        eyebrow="Sales function"
        title="Build a 15-company sample pipeline"
        description="Pick a sample robot company profile or enter your own URL. We generate a shareable results link you can send to prospects immediately."
      />
      <main className="mx-auto max-w-5xl px-4 pb-16 sm:px-6">
        <section className="-mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-900">Sample robot company presets</h2>
            <Link href="/results" className="text-xs font-semibold text-emerald-700 hover:text-emerald-800">
              Open manual scan
            </Link>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {SAMPLE_ROBOT_COMPANIES.map((sample) => {
              const resultsPath = buildResultsPath(sample.url, sample.name);
              const shareUrl = typeof window !== "undefined" ? `${window.location.origin}${resultsPath}` : "";
              return (
                <article key={sample.name} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <h3 className="text-sm font-semibold text-slate-900">{sample.name}</h3>
                  <p className="mt-1 text-xs leading-relaxed text-slate-600">{sample.profile}</p>
                  <p className="mt-3 text-[11px] font-medium text-slate-500">{sample.url}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link
                      href={resultsPath}
                      className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700"
                    >
                      Open 15-company pipeline
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                    <button
                      type="button"
                      onClick={() => {
                        if (!shareUrl) return;
                        void navigator.clipboard.writeText(shareUrl).then(() => {
                          toast.success("Share link copied");
                        });
                      }}
                      className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
                    >
                      <Copy className="h-3.5 w-3.5" />
                      Copy link
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-lg font-semibold text-slate-900">Custom sample pipeline</h2>
          <p className="mt-1 text-sm text-slate-600">
            Enter any robot company and generate a shareable 15-company pipeline URL.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <input
              value={customCompanyName}
              onChange={(e) => setCustomCompanyName(e.target.value)}
              placeholder="Sample company name"
              className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-emerald-500"
            />
            <input
              value={customCompanyUrl}
              onChange={(e) => setCustomCompanyUrl(e.target.value)}
              placeholder="https://robot-company.com"
              className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-emerald-500"
            />
          </div>

          {customResultsPath ? (
            <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-emerald-800">Shareable link</p>
              <p className="mt-2 break-all text-xs text-emerald-900">{customShareUrl}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link href={customResultsPath} className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700">
                  Open pipeline
                  <ExternalLink className="h-3.5 w-3.5" />
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    if (!customShareUrl) return;
                    void navigator.clipboard.writeText(customShareUrl).then(() => {
                      toast.success("Custom share link copied");
                    });
                  }}
                  className="inline-flex items-center gap-2 rounded-lg border border-emerald-300 bg-white px-3 py-2 text-xs font-semibold text-emerald-900 hover:bg-emerald-100"
                >
                  <Copy className="h-3.5 w-3.5" />
                  Copy share link
                </button>
              </div>
            </div>
          ) : (
            <p className="mt-3 text-xs text-slate-500">Add a valid URL to generate a shareable 15-company pipeline link.</p>
          )}
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
