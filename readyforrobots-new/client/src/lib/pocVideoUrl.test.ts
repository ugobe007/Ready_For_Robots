import { describe, expect, it } from "vitest";
import {
  JOBS_POC_VIDEO_BAD_HOST,
  JOBS_POC_VIDEO_BAD_SCHEME,
  JOBS_POC_VIDEO_LABEL,
  JOBS_POC_VIDEO_WATCH,
  parsePocVideoUrl,
  pocVideoScriptBeats,
  pocVideoUrlIssue,
} from "./pocVideoUrl";

describe("pocVideoUrl", () => {
  it("treats empty as skippable", () => {
    expect(pocVideoUrlIssue("")).toBeNull();
    expect(pocVideoUrlIssue("   ")).toBeNull();
    expect(parsePocVideoUrl("")).toBeNull();
  });

  it("allowlists loom youtube vimeo for embed and drive as link-out", () => {
    const loom = parsePocVideoUrl("https://www.loom.com/share/abcd1234efgh5678");
    expect(loom?.kind).toBe("loom");
    expect(loom?.embedUrl).toBe("https://www.loom.com/embed/abcd1234efgh5678");
    const yt = parsePocVideoUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
    expect(yt?.kind).toBe("youtube");
    expect(yt?.embedUrl).toBe("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ");
    const short = parsePocVideoUrl("https://youtu.be/dQw4w9WgXcQ");
    expect(short?.embedUrl).toContain("dQw4w9WgXcQ");
    const vimeo = parsePocVideoUrl("https://vimeo.com/123456789");
    expect(vimeo?.embedUrl).toBe("https://player.vimeo.com/video/123456789");
    const drive = parsePocVideoUrl(
      "https://drive.google.com/file/d/abcDEF123/view",
    );
    expect(drive?.kind).toBe("drive");
    expect(drive?.embedUrl).toBeNull();
  });

  it("rejects http and unknown hosts without echoing the URL", () => {
    const sneaky = "http://www.loom.com/share/abcd1234efgh5678";
    expect(pocVideoUrlIssue(sneaky)).toBe(JOBS_POC_VIDEO_BAD_SCHEME);
    expect(pocVideoUrlIssue(sneaky)).not.toContain(sneaky);
    const junk = "https://evil.example/watch?v=dQw4w9WgXcQ";
    expect(pocVideoUrlIssue(junk)).toBe(JOBS_POC_VIDEO_BAD_HOST);
    expect(pocVideoUrlIssue(junk)).not.toContain("evil.example");
  });

  it("builds three guided beats from live card data", () => {
    const beats = pocVideoScriptBeats({
      robotName: "Spot",
      selectedModels: ["Spot Enterprise"],
      employer: "Fulcrum Technologies",
      jobTitle: "Load parts into CNC",
      work: "machine tending",
      requirements: ["Payload in range", "Indoor industrial cell"],
    });
    expect(beats).toHaveLength(3);
    expect(beats[0].body).toMatch(/Spot/);
    expect(beats[0].body).toMatch(/Spot Enterprise/);
    expect(beats[1].body).toMatch(/Fulcrum Technologies/);
    expect(beats[1].body).toMatch(/Load parts into CNC/);
    expect(beats[1].body).toMatch(/Payload in range/);
    expect(beats[2].body).toMatch(/60–90/);
    expect(beats[2].body).toMatch(/Job Card/);
    expect(JOBS_POC_VIDEO_LABEL).toMatch(/this Job Card/);
    expect(JOBS_POC_VIDEO_WATCH).toBe("Watch demo");
  });
});
