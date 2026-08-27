import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  JOBS_APPLY_NEXT_CTA,
  JOBS_APPLY_OFFER_CTA,
  JOBS_EMPLOYER_HOLD_CTA,
  JOBS_EMPLOYER_PROPOSE_CTA,
  JOBS_KEEP_YES_CTA,
  JOBS_MODEL_SELECT_LABEL,
  JOBS_NEXT_STEPS_ANCHOR,
  JOBS_NEXT_STEPS_CTA,
  JOBS_OEM_CONFIRM_HOLD_CTA,
  JOBS_OEM_RELEASE_HOLD_CTA,
  JOBS_PROPOSED_PRICE_LABEL,
  applicationStatusLabel,
  suggestedHoldSlots,
  canSubmitNextStepsOffer,
  jobsCrmOfferHref,
  keepJobsSavedLabel,
  keepJobsStatusBar,
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
    expect(desk).toMatch(/keepTheseJobsPrompt/);
    expect(desk).toMatch(/CRM_KEEP_YES_CTA/);
    expect(desk).toMatch(/jobsCrmOfferHref/);
    expect(desk).toMatch(/JOBS_APPLY_NEXT_CTA/);
    expect(desk).toMatch(/JobsCrmNextSteps/);
    expect(desk).toMatch(/JobsCrmInbox/);
    expect(desk).toMatch(/onCrmDesk/);
    expect(next).toMatch(/Robot name/);
    expect(next).toMatch(/JOBS_MODEL_SELECT_LABEL/);
    expect(next).toMatch(/JOBS_PROPOSED_PRICE_LABEL/);
    expect(next).toMatch(/PoC proof if available/);
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
    expect(keepTheseJobsPrompt(3)).toBe("Keep these 3 jobs?");
    expect(JOBS_KEEP_YES_CTA).toBe("Yes");
    expect(JOBS_APPLY_NEXT_CTA).toBe("Apply →");
    expect(JOBS_NEXT_STEPS_CTA).toMatch(/Next steps/);
    expect(JOBS_MODEL_SELECT_LABEL).toMatch(/Model/);
    expect(JOBS_PROPOSED_PRICE_LABEL).toMatch(/Proposed monthly/);
    expect(JOBS_APPLY_OFFER_CTA).toMatch(/Apply to the job/);
    const appTsx = readFileSync(join(here, "../App.tsx"), "utf8");
    const employer = readFileSync(join(here, "../pages/EmployerDecision.tsx"), "utf8");
    expect(appTsx).toMatch(/\/employer\/:token/);
    expect(employer).toMatch(/JOBS_EMPLOYER_ACCEPT_CTA/);
    expect(employer).toMatch(/JOBS_EMPLOYER_INTERVIEW_CTA/);
    expect(employer).toMatch(/JOBS_EMPLOYER_HOLD_CTA/);
    expect(employer).toMatch(/JOBS_EMPLOYER_PROPOSE_CTA/);
    expect(employer).toMatch(/\/hold/);
    expect(employer).toMatch(/datetime-local/);
    expect(inbox).toMatch(/JOBS_OEM_CONFIRM_HOLD_CTA/);
    expect(inbox).toMatch(/JOBS_OEM_RELEASE_HOLD_CTA/);
    expect(inbox).toMatch(/confirmHoldOnAccount/);
    expect(inbox).toMatch(/releaseHoldOnAccount/);
    expect(appTsx).toMatch(/\/oem-hold\/:token/);
    expect(JOBS_EMPLOYER_HOLD_CTA).toBe("Hold this slot");
    expect(JOBS_EMPLOYER_PROPOSE_CTA).toBe("Propose this time");
    expect(JOBS_OEM_CONFIRM_HOLD_CTA).toBe("Confirm hold");
    expect(JOBS_OEM_RELEASE_HOLD_CTA).toBe("Release hold");
    expect(applicationStatusLabel("interview_held")).toBe("Interview slot held");
    const slots = suggestedHoldSlots(new Date("2026-09-01T12:00:00"));
    expect(slots).toHaveLength(3);
    expect(slots[0].start).toMatch(/T10:00$/);
    expect(slots[0].end).toMatch(/T11:00$/);
  });
});
