import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EMPLOYER_JD_ACCEPT,
  EMPLOYER_MATCH_TIMEOUT_MS,
  readEmployerJdFile,
} from "./employerRobotMatch";

const here = dirname(fileURLToPath(import.meta.url));

describe("employer MATCH catalog budget and JD upload", () => {
  it("client match has a sub-3s timeout and hits Fly catalog only", () => {
    expect(EMPLOYER_MATCH_TIMEOUT_MS).toBe(2_500);
    expect(EMPLOYER_MATCH_TIMEOUT_MS).toBeLessThan(3_000);
    const src = readFileSync(join(here, "./employerRobotMatch.ts"), "utf8");
    expect(src).toMatch(/getPublicReadApiBase/);
    expect(src).toMatch(/fetchWithTimeout/);
    expect(src).toMatch(/EMPLOYER_MATCH_TIMEOUT_MS/);
    expect(src).not.toMatch(/robot-job-search|oem-listing|robot-profile/);
    const py = readFileSync(
      join(here, "../../../../app/services/employer_robot_match.py"),
      "utf8"
    );
    expect(py).toMatch(/catalog_only/);
    expect(py).toMatch(/live_scrape": False/);
    expect(py).not.toMatch(/build_robot_profile|scrape_robot_page/);
  });

  it("reads txt job descriptions and keeps pdf/docx as a filename", async () => {
    expect(EMPLOYER_JD_ACCEPT).toMatch(/pdf/);
    expect(EMPLOYER_JD_ACCEPT).toMatch(/docx/);
    expect(EMPLOYER_JD_ACCEPT).toMatch(/txt/);
    const txt = new File(
      ["Need a night-shift floor scrubber.\n"],
      "floor.txt",
      {
        type: "text/plain",
      }
    );
    const read = await readEmployerJdFile(txt);
    expect(read.filename).toBe("floor.txt");
    expect(read.text).toMatch(/floor scrubber/);
    const pdf = new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], "jd.pdf", {
      type: "application/pdf",
    });
    const pdfRead = await readEmployerJdFile(pdf);
    expect(pdfRead.filename).toBe("jd.pdf");
    expect(pdfRead.text).toBe("");
    const ui = readFileSync(
      join(here, "../components/EmployerMatchWorkspace.tsx"),
      "utf8"
    );
    expect(ui).toMatch(/type="file"/);
    expect(ui).toMatch(/jdFilename/);
    expect(ui).not.toMatch(/hunter\.io|Apollo/i);
  });
});
