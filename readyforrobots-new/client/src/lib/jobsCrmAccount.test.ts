import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  JOBS_APPLY_OFFER_CTA,
  JOBS_KEEP_JOBS_CTA,
  JOBS_MODEL_SELECT_LABEL,
  JOBS_NEXT_STEPS_CTA,
  JOBS_PROPOSED_PRICE_LABEL,
  canSubmitNextStepsOffer,
  jobsCrmOfferHref,
  keepJobsSavedLabel,
  keepJobsStatusBar,
} from "./jobsCrmAccount";
import { jobsCrmOpenHref } from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));

describe("jobs CRM keep / next-steps / apply", () => {
  it("status bar names saved jobs and links to CRM only off the desk", () => {
    expect(keepJobsSavedLabel(0)).toBe("0 jobs saved");
    expect(keepJobsSavedLabel(1)).toBe("1 job saved");
    expect(keepJobsSavedLabel(5)).toBe("5 jobs saved");
    expect(
      keepJobsStatusBar({ savedCount: 3, onCrmDesk: true, signedIn: true }),
    ).toEqual({ text: "3 jobs saved" });
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
    expect(jobsCrmOfferHref(true)).toBe("/pipeline?src=jobs_activate&next=offer");
    expect(jobsCrmOfferHref(false)).toMatch(/next=/);
    expect(jobsCrmOfferHref(false)).toMatch(/src=jobs_activate/);
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
    expect(desk).toMatch(/JOBS_KEEP_JOBS_CTA/);
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
    expect(inbox).toMatch(/JOBS_INBOX_HEADING/);
    expect(inbox).toMatch(/Paste employer reply/);
    expect(workspace).toMatch(/JOBS_KEEP_JOBS_CTA/);
    expect(workspace).toMatch(/JobsKeepStatusBar/);
    expect(workspace).toMatch(/JOBS_NEXT_STEPS_CTA/);
    expect(JOBS_KEEP_JOBS_CTA).toBe("Keep jobs");
    expect(JOBS_NEXT_STEPS_CTA).toMatch(/Next steps/);
    expect(JOBS_MODEL_SELECT_LABEL).toMatch(/Model/);
    expect(JOBS_PROPOSED_PRICE_LABEL).toMatch(/Proposed monthly/);
    expect(JOBS_APPLY_OFFER_CTA).toMatch(/Apply to the job/);
  });
});
