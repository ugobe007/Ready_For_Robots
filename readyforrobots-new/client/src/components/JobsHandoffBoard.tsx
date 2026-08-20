/**
 * Jobs handoff on /results (5) and /pipeline (more than 5).
 * Renders matcher jobs — never SIGNAL buyer companies.
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import { fetchRobotJobSearch } from "@/lib/robotJobSearch";
import { loadJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";
import {
  JOBS_FOR_YOUR_ROBOT_HEADING,
  JOBS_FOR_YOUR_ROBOT_KEEP_CTA,
  buyerLeadsHref,
  jobsSignupHref,
  persistJobsHandoffSrc,
} from "@/lib/jobsWorkflow";
import type { MatchJob } from "@/lib/robotJobMatch";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";

const ctaClass =
  "inline-flex items-center justify-center gap-2 bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300";

function jobKey(job: MatchJob): string {
  return job.job_key || job.title;
}

export default function JobsHandoffBoard({
  robotUrl,
  cap,
  src,
  signedIn,
  variant,
}: {
  robotUrl: string;
  cap: number;
  src?: string | null;
  signedIn: boolean;
  variant: "results" | "pipeline";
}) {
  const jobsSrc = persistJobsHandoffSrc(src);
  const [productName, setProductName] = useState("");
  const [jobs, setJobs] = useState<MatchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const cached = loadJobsHandoffSnapshot(robotUrl);
    if (cached?.jobs.length) {
      setProductName(cached.productName);
      setJobs(cached.jobs);
      setLoading(false);
      setError(null);
      return () => {
        cancelled = true;
      };
    }
    if (!robotUrl.trim()) {
      setLoading(false);
      setError("Paste a robot URL on Jobs first.");
      return () => {
        cancelled = true;
      };
    }
    setLoading(true);
    setError(null);
    void fetchRobotJobSearch({ url: robotUrl })
      .then((res) => {
        if (cancelled) return;
        const list = Array.isArray(res.jobs) ? res.jobs : res.top_jobs || [];
        setProductName(res.robot_name || "");
        setJobs(list);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError("Could not load jobs for this robot.");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [robotUrl]);

  const visible = useMemo(() => jobs.slice(0, cap), [jobs, cap]);
  const pipelineHref = buyerLeadsHref({
    robotUrl,
    signedIn: true,
    src: jobsSrc,
  });
  const signupHref = jobsSignupHref(pipelineHref, jobsSrc);

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-6">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-400">
        {JOBS_FOR_YOUR_ROBOT_HEADING}
      </p>
      <h1 className="mt-1 font-display text-2xl font-bold text-slate-100 sm:text-3xl">
        {productName ? `Jobs for ${productName}` : JOBS_FOR_YOUR_ROBOT_HEADING}
      </h1>
      <p className="mt-1 text-sm text-slate-400">
        {variant === "results"
          ? "Same Jobs terminal. 5 jobs to review. More than 5 jobs live on the pipeline after you sign up."
          : "Same Jobs terminal. More than 5 jobs for this robot live here."}
      </p>

      {loading ? (
        <p className="mt-8 text-sm text-slate-400">Loading jobs for your robot…</p>
      ) : error ? (
        <p className="mt-8 border border-rose-800 bg-rose-950/40 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      ) : visible.length === 0 ? (
        <p className="mt-8 text-sm text-slate-400">No matched jobs for this robot yet.</p>
      ) : (
        <ol className="mt-6 space-y-3">
          {visible.map((job, i) => {
            const key = jobKey(job);
            const open = expanded === key;
            const place = [job.company_name, job.locality].filter(Boolean).join(" · ");
            return (
              <li key={key} className="border border-slate-600 bg-[#081126]">
                <button
                  type="button"
                  onClick={() => setExpanded(open ? null : key)}
                  className="flex w-full items-start gap-3 p-4 text-left"
                >
                  <span className="flex-1">
                    <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                      Job {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="mt-1 block font-display text-base font-bold leading-snug text-slate-100">
                      {job.title}
                    </span>
                    {place ? (
                      <span className="mt-1 block text-[12px] text-slate-400">{place}</span>
                    ) : null}
                  </span>
                </button>
                {open && (job.why?.length || job.still_unknown?.length) ? (
                  <div className="border-t border-slate-700 px-4 py-3 text-[12px] text-slate-300">
                    {job.why?.length ? (
                      <p>
                        <span className="font-semibold text-emerald-300">Why this robot. </span>
                        {job.why.join(" ")}
                      </p>
                    ) : null}
                    {job.still_unknown?.length ? (
                      <p className="mt-2">
                        <span className="font-semibold text-amber-300">Still unknown. </span>
                        {job.still_unknown.join(" ")}
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}

      {!signedIn ? (
        <div className="mt-6 border border-emerald-500/30 bg-emerald-400/5 p-5 text-center">
          <p className="text-sm text-slate-300">
            Sign up to keep these {Math.min(visible.length, cap)} jobs — more than 5
            jobs live on the pipeline.
          </p>
          <Link href={signupHref} className={`${ctaClass} mt-4`}>
            <PixelIcon map={KARE_FACE} scale={2} fill={FACE_EMERALD} background="transparent" />
            {JOBS_FOR_YOUR_ROBOT_KEEP_CTA}
          </Link>
        </div>
      ) : variant === "results" ? (
        <div className="mt-6 text-center">
          <Link href={pipelineHref} className={ctaClass}>
            <PixelIcon map={KARE_FACE} scale={2} fill={FACE_EMERALD} background="transparent" />
            Open the pipeline →
          </Link>
        </div>
      ) : null}
    </main>
  );
}
