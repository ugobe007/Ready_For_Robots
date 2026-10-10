import { describe, expect, it } from "vitest";
import { getJobLifecycleState, MAX_APPLICANTS_PER_JOB, JOB_AGING_FRESH_DAYS, JOB_ARCHIVE_DAYS } from "./jobLifecycle";
import type { MatchJob } from "./robotJobMatch";

describe("Job Lifecycle & Applicant Scarcity Rules", () => {
  it("caps applicants at 3 and marks status as PENDING REVIEW when 3 spots are filled", () => {
    const job: MatchJob = {
      job_key: "job-full",
      title: "Automated Welding Robot Operator",
      industry: "Manufacturing",
      path: "/jobs/welding",
      applicants_count: 3,
      posted_at: new Date().toISOString(),
    };

    const state = getJobLifecycleState(job);
    expect(state.applicantsCount).toBe(3);
    expect(state.maxApplicants).toBe(MAX_APPLICANTS_PER_JOB);
    expect(state.isPending).toBe(true);
    expect(state.spotsRemaining).toBe(0);
    expect(state.statusLabel).toBe("PENDING REVIEW");
    expect(state.subLabel).toContain("3/3 Applicant Spots Filled");
  });

  it("calculates fresh status (0-14 days) with open spots", () => {
    const freshDate = new Date(Date.now() - 5 * 86400000).toISOString(); // 5 days old
    const job: MatchJob = {
      job_key: "job-fresh",
      title: "Palletizing Robot Specialist",
      industry: "Logistics",
      path: "/jobs/palletizing",
      applicants_count: 1,
      posted_at: freshDate,
    };

    const state = getJobLifecycleState(job);
    expect(state.applicantsCount).toBe(1);
    expect(state.isPending).toBe(false);
    expect(state.spotsRemaining).toBe(2);
    expect(state.isFresh).toBe(true);
    expect(state.isArchived).toBe(false);
    expect(state.statusLabel).toBe("FRESH MATCH");
    expect(state.subLabel).toContain("2 Spots Open");
  });

  it("marks jobs older than 8 weeks (56 days) as ARCHIVED", () => {
    const oldDate = new Date(Date.now() - 60 * 86400000).toISOString(); // 60 days old
    const job: MatchJob = {
      job_key: "job-archived",
      title: "Autonomous Inspection Robot",
      industry: "Energy",
      path: "/jobs/inspection",
      applicants_count: 0,
      posted_at: oldDate,
    };

    const state = getJobLifecycleState(job);
    expect(state.isArchived).toBe(true);
    expect(state.daysOld).toBeGreaterThanOrEqual(JOB_ARCHIVE_DAYS);
    expect(state.statusLabel).toBe("ARCHIVED");
    expect(state.subLabel).toContain("8+ Weeks Old");
    expect(state.subLabel).toContain("Paid Access Only");
  });

  it("filters and surfaces top 3 active jobs for free users", () => {
    const freshDate = new Date().toISOString();
    const oldDate = new Date(Date.now() - 60 * 86400000).toISOString();

    const jobsList: MatchJob[] = [
      { job_key: "1", title: "Active 1", industry: "Logistics", path: "/1", applicants_count: 1, posted_at: freshDate },
      { job_key: "2", title: "Pending 1", industry: "Logistics", path: "/2", applicants_count: 3, posted_at: freshDate },
      { job_key: "3", title: "Active 2", industry: "Logistics", path: "/3", applicants_count: 0, posted_at: freshDate },
      { job_key: "4", title: "Archived 1", industry: "Logistics", path: "/4", applicants_count: 0, posted_at: oldDate },
      { job_key: "5", title: "Active 3", industry: "Logistics", path: "/5", applicants_count: 2, posted_at: freshDate },
      { job_key: "6", title: "Active 4", industry: "Logistics", path: "/6", applicants_count: 0, posted_at: freshDate },
    ];

    const activeJobs = jobsList.filter(j => !getJobLifecycleState(j).isArchived && !getJobLifecycleState(j).isPending);
    expect(activeJobs.length).toBe(4);
    expect(activeJobs.map(j => j.job_key)).toEqual(["1", "3", "5", "6"]);

    // Free users surface exactly top 3 active jobs
    const freeActiveSample = activeJobs.slice(0, 3);
    expect(freeActiveSample.length).toBe(3);
    expect(freeActiveSample.map(j => j.job_key)).toEqual(["1", "3", "5"]);
  });
});
