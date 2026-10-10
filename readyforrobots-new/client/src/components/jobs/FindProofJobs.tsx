import { useEffect, useState } from "react";
import InlineJobLine from "@/components/jobs/InlineJobLine";
import { fetchRobotJobsPreview, type PreviewJob } from "@/lib/robotJobsPreview";

export default function FindProofJobs() {
  const [jobs, setJobs] = useState<PreviewJob[] | null>(null);

  useEffect(() => {
    let alive = true;
    void fetchRobotJobsPreview(3)
      .then(rows => {
        if (alive) setJobs(rows);
      })
      .catch(() => {
        if (alive) setJobs([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  if (jobs == null) {
    return (
      <p className="mt-8 text-[13px] leading-snug text-slate-500">
        Loading named-employer jobs…
      </p>
    );
  }

  if (jobs.length === 0) {
    return (
      <p className="mt-8 text-[13px] leading-snug text-slate-500">
        No named-employer jobs in the live table yet.
      </p>
    );
  }

  return (
    <ul className="mt-8 space-y-2" aria-label="Named employer jobs">
      {jobs.map(job => (
        <li key={job.job_key}>
          <InlineJobLine job={job} />
        </li>
      ))}
    </ul>
  );
}
