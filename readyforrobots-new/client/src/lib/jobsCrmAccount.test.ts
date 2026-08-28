import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  JOBS_APPLY_NEXT_CTA,
  JOBS_APPLY_SEQUENCE,
  JOBS_APPLY_OFFER_CTA,
  JOBS_EMPLOYER_HOLD_CTA,
  JOBS_EMPLOYER_PROPOSE_CTA,
  JOBS_EMPLOYER_DECLINE_CTA,
  JOBS_DECLINE_REASONS,
  JOBS_KEEP_YES_CTA,
  JOBS_MODEL_SELECT_LABEL,
  JOBS_NEXT_STEPS_ANCHOR,
  JOBS_NEXT_STEPS_CTA,
  JOBS_OEM_CONFIRM_HOLD_CTA,
  JOBS_OEM_RELEASE_HOLD_CTA,
  JOBS_PROPOSED_PRICE_LABEL,
  applicationStatusLabel,
  declineReasonLabel,
  suggestedHoldSlots,
  canSubmitNextStepsOffer,
  jobsCrmOfferHref,
  keepJobsSavedLabel,
  keepJobsStatusBar,
  crmDeskForCurrentRobot,
  keptRowMatchesRobot,
} from "./jobsCrmAccount";
import { keepTheseJobsPrompt } from "./jobsWorkflow";
import { jobsCrmOpenHref } from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));

describe("jobs CRM keep / next-steps / apply", () => {
  it("status bar names saved jobs and links to CRM only off the desk", () => {
    expect(keepJobsSavedLabel(0)).toBe("0 jobs saved");
    expect(keepJobsSavedLabel(1)).toBe("1 job saved");
    expect(keepJobsSavedLabel(5)).toBe("5 jobs saved");
    const onDesk = keepJobsStatusBar({
      savedCount: 3,
      onCrmDesk: true,
      signedIn: true,
    });
    expect(onDesk.text).toBe("3 jobs saved");
    expect(onDesk.href).toBe(jobsCrmOfferHref(true));
    expect(onDesk.hrefLabel).toBe(JOBS_APPLY_NEXT_CTA);
    expect(onDesk.href).toContain("next=offer");
    expect(onDesk.href).toContain(JOBS_NEXT_STEPS_ANCHOR);
    const offDesk = keepJobsStatusBar({
      savedCount: 3,
      onCrmDesk: false,
      signedIn: true,
    });
    expect(offDesk.text).toBe("3 jobs saved");
    expect(offDesk.href).toBe(jobsCrmOpenHref(true));
    expect(offDesk.hrefLabel).toBe("Open CRM");
    const wall = keepJobsStatusBar({
      savedCount: 2,
      onCrmDesk: false,
      signedIn: false,
    });
    expect(wall.href).toBe(jobsCrmOpenHref(false));
    expect(wall.href).toMatch(/\/signup\?/);
  });

  it("next-steps apply is gated on proposed price and catalogued model", () => {
    expect(
      canSubmitNextStepsOffer({ monthlyPrice: "", selectedModels: ["Spot"] }),
    ).toBe(false);
    expect(
      canSubmitNextStepsOffer({ monthlyPrice: "tbd", selectedModels: ["Spot"] }),
    ).toBe(false);
    expect(
      canSubmitNextStepsOffer({ monthlyPrice: "4200 / month", selectedModels: [] }),
    ).toBe(false);
    expect(
      canSubmitNextStepsOffer({
        monthlyPrice: "4200 / month",
        selectedModels: ["Spot"],
      }),
    ).toBe(true);
  });

  it("next-steps offer href keeps process 03 on the CRM desk", () => {
    expect(jobsCrmOfferHref(true)).toBe(
      `/pipeline?src=jobs_activate&next=offer#${JOBS_NEXT_STEPS_ANCHOR}`,
    );
    expect(jobsCrmOfferHref(true)).not.toMatch(/href="#"|#$/);
    expect(jobsCrmOfferHref(false)).toMatch(/next=/);
    expect(jobsCrmOfferHref(false)).toMatch(/src=jobs_activate/);
    expect(jobsCrmOfferHref(false)).toMatch(/\/signup\?/);
  });

  it("desk and Job Cards expose keep status, next-steps fields, and apply gate", () => {
    const desk = readFileSync(join(here, "../components/JobsCrmDesk.tsx"), "utf8");
    const next = readFileSync(
      join(here, "../components/JobsCrmNextSteps.tsx"),
      "utf8",
    );
    const status = readFileSync(
      join(here, "../components/JobsKeepStatusBar.tsx"),
      "utf8",
    );
    const inbox = readFileSync(join(here, "../components/JobsCrmInbox.tsx"), "utf8");
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(status).toMatch(/data-jobs-keep-status/);
    expect(status).toMatch(/keepJobsStatusBar/);
    expect(desk).toMatch(/JobsKeepStatusBar/);
    expect(desk).toMatch(/crmSaveJobsBlurb\(product\)/);
    expect(desk).toMatch(/blurb=\{crmSaveJobsBlurb/);
    expect(desk).toMatch(/keepTheseJobsPrompt/);
    expect(desk).toMatch(/CRM_KEEP_YES_CTA/);
    expect(desk).toMatch(/type="submit"/);
    expect(desk).toMatch(/data-jobs-keep-confirm="1"/);
    expect(desk).toMatch(/persistKeptJobs/);
    expect(desk).not.toMatch(/href="#"/);
    expect(desk).not.toMatch(/crmSelectAllLabel/);
    expect(desk).not.toMatch(/Select all/);
    expect(desk).not.toMatch(/Keep these/);
    expect(desk).toMatch(/JOBS_APPLY_SEQUENCE/);
    expect(next).toMatch(/JOBS_APPLY_SEQUENCE/);
    expect(status).toMatch(/blurb \|\| JOBS_APPLY_SEQUENCE/);
    expect(status).toMatch(/blurb\?: string/);
    expect(desk).toMatch(/jobsCrmOfferHref/);
    expect(desk).toMatch(/JOBS_APPLY_NEXT_CTA/);
    expect(desk).toMatch(/JobsCrmNextSteps/);
    expect(desk).toMatch(/JobsCrmInbox/);
    expect(desk).toMatch(/onCrmDesk/);
    expect(next).toMatch(/crmSaveJobsBlurb\(robotName\)/);
    expect(next).not.toMatch(/JOBS_NEXT_STEPS_HINT/);
    expect(next).toMatch(/Robot name/);
    expect(next).toMatch(/JOBS_MODEL_SELECT_LABEL/);
    expect(next).toMatch(/JOBS_PROPOSED_PRICE_LABEL/);
    expect(next).toMatch(/PoC proof if available/);
    expect(next).toMatch(/JOBS_POC_VIDEO_LABEL/);
    expect(next).toMatch(/JOBS_POC_VIDEO_SCRIPT_HEADING/);
    expect(next).toMatch(/pocVideoScriptBeats/);
    expect(next).toMatch(/pocVideoUrl/);
    expect(next).toMatch(/data-poc-video-script="1"/);
    expect(next).toMatch(/canSubmitNextStepsOffer/);
    expect(next).toMatch(/JOBS_APPLY_OFFER_CTA/);
    expect(next).toMatch(/disabled=\{!ready/);
    expect(next).toMatch(/JOBS_DOCS_HEADING/);
    expect(next).toMatch(/uploadRobotDocument/);
    expect(next).toMatch(/documentIds: selectedDocs/);
    expect(next).toMatch(/id="jobs-next-steps"/);
    expect(inbox).toMatch(/JOBS_INBOX_HEADING/);
    expect(inbox).toMatch(/Paste employer reply/);
    expect(workspace).toMatch(/keepTheseJobsPrompt/);
    expect(workspace).toMatch(/JOBS_KEEP_YES_CTA/);
    expect(workspace).toMatch(/JobsKeepStatusBar/);
    expect(workspace).toMatch(/JOBS_NEXT_STEPS_CTA/);
    expect(workspace).toMatch(/jobsCrmOfferHref/);
    expect(keepTheseJobsPrompt(3)).toBe("Keep 3 jobs?");
    expect(keepTheseJobsPrompt(1)).toBe("Keep 1 job?");
    expect(JOBS_KEEP_YES_CTA).toBe("Yes, keep them");
    expect(JOBS_APPLY_NEXT_CTA).toBe("Apply →");
    expect(JOBS_APPLY_SEQUENCE).toMatch(/Apply to the job/);
    expect(JOBS_APPLY_SEQUENCE).toMatch(/schedule interviews/);
    expect(JOBS_APPLY_SEQUENCE).toMatch(/They close/);
    expect(JOBS_APPLY_SEQUENCE).not.toMatch(/\$|rental we invent/i);
    expect(JOBS_NEXT_STEPS_CTA).toMatch(/Next steps/);
    expect(JOBS_MODEL_SELECT_LABEL).toMatch(/Model/);
    expect(JOBS_PROPOSED_PRICE_LABEL).toMatch(/Proposed monthly/);
    expect(JOBS_APPLY_OFFER_CTA).toMatch(/Apply to the job/);
    const appTsx = readFileSync(join(here, "../App.tsx"), "utf8");
    const employer = readFileSync(join(here, "../pages/EmployerDecision.tsx"), "utf8");
    expect(appTsx).toMatch(/\/employer\/:token/);
    expect(employer).toMatch(/JOBS_EMPLOYER_ACCEPT_CTA/);
    expect(employer).toMatch(/JOBS_EMPLOYER_DECLINE_CTA/);
    expect(employer).toMatch(/JOBS_EMPLOYER_INTERVIEW_CTA/);
    expect(employer).toMatch(/JOBS_EMPLOYER_HOLD_CTA/);
    expect(employer).toMatch(/JOBS_EMPLOYER_PROPOSE_CTA/);
    expect(employer).toMatch(/PocVideoWatch/);
    expect(employer).toMatch(/poc_video_url/);
    expect(employer).toMatch(/JOBS_DECLINE_REASONS/);
    expect(employer).toMatch(/\/decline/);
    expect(employer).toMatch(/reason_code/);
    expect(employer).toMatch(/name="decline-reason"/);
    expect(inbox).toMatch(/PocVideoWatch/);
    expect(inbox).toMatch(/poc_video_url/);
    expect(inbox).toMatch(/decline_reason_code/);
    expect(inbox).toMatch(/declineReasonLabel/);
    expect(employer).toMatch(/\/hold/);
    expect(employer).toMatch(/datetime-local/);
    expect(inbox).toMatch(/JOBS_OEM_CONFIRM_HOLD_CTA/);
    expect(inbox).toMatch(/JOBS_OEM_RELEASE_HOLD_CTA/);
    expect(inbox).toMatch(/confirmHoldOnAccount/);
    expect(inbox).toMatch(/releaseHoldOnAccount/);
    expect(appTsx).toMatch(/\/oem-hold\/:token/);
    expect(JOBS_EMPLOYER_HOLD_CTA).toBe("Hold this slot");
    expect(JOBS_EMPLOYER_PROPOSE_CTA).toBe("Propose this time");
    expect(JOBS_EMPLOYER_DECLINE_CTA).toBe("Decline");
    expect(JOBS_OEM_CONFIRM_HOLD_CTA).toBe("Confirm hold");
    expect(JOBS_OEM_RELEASE_HOLD_CTA).toBe("Release hold");
    expect(applicationStatusLabel("interview_held")).toBe("Interview slot held");
    expect(applicationStatusLabel("declined")).toBe("Declined");
    expect(JOBS_DECLINE_REASONS.map(row => row.code)).toEqual([
      "work_mismatch",
      "model_unproven",
      "site_constraints",
      "timing_budget",
      "other",
    ]);
    expect(declineReasonLabel("work_mismatch")).toMatch(/physical work/);
    expect(declineReasonLabel("model_unproven")).toMatch(/task model/);
    const slots = suggestedHoldSlots(new Date("2026-09-01T12:00:00"));
    expect(slots).toHaveLength(3);
    expect(slots[0].start).toMatch(/T10:00$/);
    expect(slots[0].end).toMatch(/T11:00$/);
  });
});

describe("CRM desk binds to the FIND robot, not leftover totes", () => {
  const orchard = {
    id: "kept-orchard",
    job_key: "orchard-rows",
    employer_name: "Sierra Orchard Co-op",
    work_title: "Work orchard rows",
    workplace: "Modesto, CA",
    robot_name: "strawberry robot",
    robot_url: "https://www.agrobot.com/",
    job: {
      job_key: "orchard-rows",
      title: "Work orchard rows",
      industry: "agriculture",
      path: "/jobs/orchard",
      company_name: "Sierra Orchard Co-op",
    },
  };
  const tote = {
    id: "kept-tote",
    job_key: "return-empty-totes",
    employer_name: "Novolex (Pactiv Evergreen)",
    work_title: "Return empty totes",
    workplace: "Warehouse",
    robot_name: "Greenfieldincorporated",
    robot_url: "https://www.greenfieldincorporated.com/",
    job: {
      job_key: "return-empty-totes",
      title: "Return empty totes",
      industry: "logistics",
      path: "/jobs/totes",
      company_name: "Novolex (Pactiv Evergreen)",
    },
  };

  it("does not keep strawberry identity after a Greenfield FIND with no jobs", () => {
    expect(
      keptRowMatchesRobot(orchard, {
        url: "https://www.greenfieldincorporated.com/",
        name: "BOT#25",
      }),
    ).toBe(false);
    expect(
      keptRowMatchesRobot(tote, {
        url: "https://www.greenfieldincorporated.com/",
        name: "BOT#25",
      }),
    ).toBe(true);

    const desk = crmDeskForCurrentRobot({
      snap: {
        url: "https://www.greenfieldincorporated.com/",
        productName: "BOT#25",
        jobs: [],
      },
      accountRows: [orchard, tote],
    });
    expect(desk.product).toBe("BOT#25");
    expect(desk.product).not.toMatch(/strawberry/i);
    expect(desk.jobs).toEqual([]);
    expect(desk.savedCount).toBe(0);
    expect(desk.jobs.map(job => job.title)).not.toContain("Work orchard rows");
    expect(desk.jobs.map(job => job.title)).not.toContain("Return empty totes");
  });

  it("prefers incomplete Greenfield identity over robot-job-match totes from another robot", () => {
    const desk = crmDeskForCurrentRobot({
      snap: {
        url: "https://www.greenfieldincorporated.com/",
        productName: "BOT#25",
        jobs: [],
      },
      accountRows: [orchard],
    });
    expect(desk.product).toBe("BOT#25");
    expect(desk.jobs).toEqual([]);
    expect(desk.savedCount).toBe(0);
    expect(desk.jobs.some(job => /orchard|strawberry/i.test(job.title))).toBe(
      false,
    );
  });

  it("does not treat match-endpoint tote jobs as the Greenfield desk when FIND saved none", () => {
    const desk = crmDeskForCurrentRobot({
      snap: {
        url: "https://www.greenfieldincorporated.com/",
        productName: "BOT#25",
        jobs: [],
      },
      accountRows: [
        {
          ...tote,
          robot_url: "https://harvestcroorobotics.com/",
          robot_name: "strawberry robot",
        },
      ],
    });
    expect(desk.product).toBe("BOT#25");
    expect(desk.jobs).toHaveLength(0);
    expect(desk.savedCount).toBe(0);
  });

  it("uses FIND jobs for this robot and drops leftover strawberry rows", () => {
    const greenfieldJob = {
      job_key: "weed-between-rows",
      title: "Weed between crop rows",
      industry: "agriculture",
      path: "/jobs/weed",
      company_name: "Named Farm Co-op",
    };
    const desk = crmDeskForCurrentRobot({
      snap: {
        url: "https://www.greenfieldincorporated.com/",
        productName: "BOT#25",
        jobs: [greenfieldJob],
      },
      accountRows: [orchard, tote],
    });
    expect(desk.product).toBe("BOT#25");
    expect(desk.jobs.map(job => job.title)).toEqual(["Weed between crop rows"]);
    expect(desk.jobs.some(job => /orchard|strawberry/i.test(job.title))).toBe(
      false,
    );
  });

  it("desk copy and chrome stay on saved jobs for this robot, not the matcher banner", () => {
    const desk = readFileSync(join(here, "../components/JobsCrmDesk.tsx"), "utf8");
    expect(desk).toMatch(/crmDeskForCurrentRobot/);
    expect(desk).toMatch(/crmSaveJobsBlurb\(product\)/);
    expect(desk).not.toMatch(/JobsPstackProtocol/);
    expect(desk).not.toMatch(/robot-job-match/);
    expect(desk).toMatch(/aria-label="Saved jobs"/);
    expect(desk).not.toMatch(/aria-label="Collected jobs"/);
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const findJobs = workspace.slice(
      workspace.indexOf("async function findJobsForActive"),
      workspace.indexOf("async function qualifyActive"),
    );
    expect(findJobs).toMatch(/fetchRobotJobSearch/);
    expect(findJobs).not.toMatch(/fetchRobotJobMatch/);
    const qualify = workspace.slice(
      workspace.indexOf("async function qualifyActive"),
      workspace.indexOf("function revealJobs"),
    );
    expect(qualify).toMatch(/fetchRobotJobSearch/);
    expect(qualify).not.toMatch(/fetchRobotJobMatch/);
    expect(workspace).not.toMatch(/fetchRobotJobMatch/);
    const openJobs = workspace.slice(
      workspace.indexOf("function openJobsFromAnalyses"),
      workspace.indexOf("async function submitFind"),
    );
    expect(openJobs).toMatch(/writeCrmHandoff/);
    const writeHandoff = workspace.slice(
      workspace.indexOf("function writeCrmHandoff"),
      workspace.indexOf("function goToActivate"),
    );
    expect(writeHandoff).not.toMatch(/pool\.length === 0/);
  });
});
