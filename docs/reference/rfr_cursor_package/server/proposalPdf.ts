/**
 * Proposal PDF Generator
 * Uses @react-pdf/renderer to produce a branded PDF document.
 * Called from the /api/proposal/pdf Express endpoint.
 */
import React from "react";
import {
  Document,
  Page,
  Text,
  View,
  Image,
  StyleSheet,
  renderToBuffer,
  Font,
} from "@react-pdf/renderer";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Brand colours ──────────────────────────────────────────────────────────────
const BRAND = {
  bg: "#0d0520",
  purple: "#7c3aed",
  teal: "#03DAC5",
  amber: "#FFB000",
  white: "#FFFFFF",
  offWhite: "#E8E0F0",
  muted: "#9B8DB0",
  divider: "#2A1A40",
  sectionBg: "#160A2E",
};

// ── Styles ─────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  page: {
    backgroundColor: BRAND.bg,
    paddingTop: 0,
    paddingBottom: 40,
    paddingHorizontal: 0,
    fontFamily: "Helvetica",
  },

  // ── Header band ──
  headerBand: {
    backgroundColor: BRAND.sectionBg,
    borderBottomWidth: 1,
    borderBottomColor: BRAND.purple,
    paddingHorizontal: 40,
    paddingTop: 32,
    paddingBottom: 24,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  logo: {
    width: 36,
    height: 36,
    borderRadius: 8,
  },
  brandName: {
    fontSize: 14,
    fontFamily: "Helvetica-Bold",
    color: BRAND.white,
    letterSpacing: 0.5,
  },
  headerRight: {
    alignItems: "flex-end",
  },
  headerLabel: {
    fontSize: 8,
    color: BRAND.amber,
    fontFamily: "Helvetica-Bold",
    letterSpacing: 1.5,
    textTransform: "uppercase",
    marginBottom: 2,
  },
  headerDate: {
    fontSize: 8,
    color: BRAND.muted,
  },

  // ── Hero band ──
  heroBand: {
    backgroundColor: BRAND.bg,
    paddingHorizontal: 40,
    paddingTop: 28,
    paddingBottom: 24,
    borderBottomWidth: 1,
    borderBottomColor: BRAND.divider,
  },
  proposalLabel: {
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    color: BRAND.teal,
    letterSpacing: 2,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  companyName: {
    fontSize: 26,
    fontFamily: "Helvetica-Bold",
    color: BRAND.white,
    marginBottom: 6,
  },
  tagRow: {
    flexDirection: "row",
    gap: 8,
    flexWrap: "wrap",
    marginTop: 4,
  },
  tag: {
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    color: BRAND.purple,
    backgroundColor: "#1E0A3C",
    borderWidth: 1,
    borderColor: BRAND.purple,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    letterSpacing: 0.5,
  },
  tagAmber: {
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    color: BRAND.amber,
    backgroundColor: "#1E1200",
    borderWidth: 1,
    borderColor: BRAND.amber,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    letterSpacing: 0.5,
  },

  // ── Signal callout ──
  signalBox: {
    marginHorizontal: 40,
    marginTop: 20,
    marginBottom: 4,
    backgroundColor: "#0A1A1A",
    borderLeftWidth: 3,
    borderLeftColor: BRAND.teal,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 4,
  },
  signalLabel: {
    fontSize: 7,
    fontFamily: "Helvetica-Bold",
    color: BRAND.teal,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    marginBottom: 4,
  },
  signalText: {
    fontSize: 9,
    color: BRAND.offWhite,
    lineHeight: 1.5,
  },

  // ── Body content ──
  body: {
    paddingHorizontal: 40,
    paddingTop: 24,
  },

  // ── Section ──
  section: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    gap: 8,
  },
  sectionAccent: {
    width: 3,
    height: 14,
    backgroundColor: BRAND.amber,
    borderRadius: 2,
  },
  sectionTitle: {
    fontSize: 9,
    fontFamily: "Helvetica-Bold",
    color: BRAND.amber,
    letterSpacing: 1.5,
    textTransform: "uppercase",
  },
  sectionBody: {
    fontSize: 10,
    color: BRAND.offWhite,
    lineHeight: 1.65,
    paddingLeft: 11,
  },

  // ── Bullet list ──
  bulletRow: {
    flexDirection: "row",
    marginBottom: 5,
    paddingLeft: 11,
  },
  bulletDot: {
    fontSize: 10,
    color: BRAND.teal,
    marginRight: 8,
    lineHeight: 1.65,
  },
  bulletText: {
    fontSize: 10,
    color: BRAND.offWhite,
    lineHeight: 1.65,
    flex: 1,
  },

  // ── Divider ──
  divider: {
    borderBottomWidth: 1,
    borderBottomColor: BRAND.divider,
    marginHorizontal: 40,
    marginVertical: 4,
  },

  // ── Score badge ──
  scoreBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 6,
  },
  scoreCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 2,
    borderColor: BRAND.teal,
    backgroundColor: "#0A1A1A",
    alignItems: "center",
    justifyContent: "center",
  },
  scoreNumber: {
    fontSize: 12,
    fontFamily: "Helvetica-Bold",
    color: BRAND.teal,
  },
  scoreLabel: {
    fontSize: 8,
    color: BRAND.muted,
  },

  // ── Footer ──
  footer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    borderTopWidth: 1,
    borderTopColor: BRAND.divider,
    paddingHorizontal: 40,
    paddingVertical: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: BRAND.sectionBg,
  },
  footerLeft: {
    fontSize: 8,
    color: BRAND.muted,
  },
  footerRight: {
    fontSize: 8,
    color: BRAND.muted,
  },
  footerBrand: {
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    color: BRAND.teal,
  },
});

// ── Section parser ─────────────────────────────────────────────────────────────
interface ProposalSection {
  title: string;
  content: string;
  isBullet?: boolean;
}

function parseProposalSections(text: string): ProposalSection[] {
  const sectionPatterns = [
    "EXECUTIVE SUMMARY",
    "THE OPPORTUNITY",
    "PROPOSED SOLUTION",
    "EXPECTED OUTCOMES",
    "NEXT STEPS",
    /^ABOUT .+/,
  ];

  const lines = text.split("\n");
  const sections: ProposalSection[] = [];
  let currentTitle = "";
  let currentLines: string[] = [];

  const isSectionHeader = (line: string): string | null => {
    const trimmed = line.trim().replace(/^#+\s*/, "").replace(/[*_]/g, "");
    for (const pat of sectionPatterns) {
      if (typeof pat === "string") {
        if (trimmed.toUpperCase().startsWith(pat)) return trimmed;
      } else {
        if (pat.test(trimmed.toUpperCase())) return trimmed;
      }
    }
    // Also match numbered headers like "1. EXECUTIVE SUMMARY"
    const numbered = trimmed.match(/^\d+\.\s+(.+)/);
    if (numbered) {
      const inner = numbered[1].toUpperCase();
      for (const pat of sectionPatterns) {
        if (typeof pat === "string") {
          if (inner.startsWith(pat)) return numbered[1];
        } else {
          if (pat.test(inner)) return numbered[1];
        }
      }
    }
    return null;
  };

  for (const line of lines) {
    const header = isSectionHeader(line);
    if (header) {
      if (currentTitle && currentLines.length > 0) {
        sections.push({
          title: currentTitle,
          content: currentLines.join("\n").trim(),
        });
      }
      currentTitle = header.replace(/^\d+\.\s+/, "").trim();
      currentLines = [];
    } else if (currentTitle) {
      currentLines.push(line);
    }
  }
  if (currentTitle && currentLines.length > 0) {
    sections.push({
      title: currentTitle,
      content: currentLines.join("\n").trim(),
    });
  }

  // If no sections were parsed, treat the whole text as a single section
  if (sections.length === 0) {
    sections.push({ title: "PROPOSAL", content: text.trim() });
  }

  return sections;
}

// ── PDF Document component ─────────────────────────────────────────────────────
interface ProposalPdfProps {
  companyName: string;
  senderCompany: string;
  senderName: string;
  senderTitle: string;
  robotCategory?: string;
  signal?: string;
  scoutScore?: number;
  proposalText: string;
  generatedAt: number;
  logoBase64: string;
}

function ProposalDocument({
  companyName,
  senderCompany,
  senderName,
  senderTitle,
  robotCategory,
  signal,
  scoutScore,
  proposalText,
  generatedAt,
  logoBase64,
}: ProposalPdfProps) {
  const sections = parseProposalSections(proposalText);
  const dateStr = new Date(generatedAt).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const scoreColor =
    (scoutScore ?? 0) >= 90
      ? BRAND.teal
      : (scoutScore ?? 0) >= 75
      ? "#a78bfa"
      : BRAND.amber;

  return React.createElement(
    Document,
    {
      title: `Proposal — ${companyName}`,
      author: senderCompany,
      subject: `Automation Proposal for ${companyName}`,
    },
    React.createElement(
      Page,
      { size: "A4", style: styles.page },

      // ── Header band ──
      React.createElement(
        View,
        { style: styles.headerBand },
        React.createElement(
          View,
          { style: styles.headerLeft },
          React.createElement(Image, {
            src: `data:image/png;base64,${logoBase64}`,
            style: styles.logo,
          }),
          React.createElement(Text, { style: styles.brandName }, senderCompany)
        ),
        React.createElement(
          View,
          { style: styles.headerRight },
          React.createElement(Text, { style: styles.headerLabel }, "Sales Proposal"),
          React.createElement(Text, { style: styles.headerDate }, dateStr)
        )
      ),

      // ── Hero band ──
      React.createElement(
        View,
        { style: styles.heroBand },
        React.createElement(Text, { style: styles.proposalLabel }, "Prepared for"),
        React.createElement(Text, { style: styles.companyName }, companyName),
        React.createElement(
          View,
          { style: styles.tagRow },
          robotCategory &&
            React.createElement(Text, { style: styles.tag }, robotCategory),
          scoutScore !== undefined &&
            React.createElement(
              Text,
              {
                style: {
                  ...styles.tagAmber,
                  color: scoreColor,
                  borderColor: scoreColor,
                  backgroundColor: `${scoreColor}15`,
                },
              },
              `SCOUT Score: ${scoutScore}/100`
            ),
          React.createElement(
            Text,
            {
              style: {
                ...styles.tag,
                color: BRAND.teal,
                borderColor: BRAND.teal,
                backgroundColor: "#001A1A",
              },
            },
            "Confidential"
          )
        )
      ),

      // ── Signal callout ──
      signal &&
        React.createElement(
          View,
          { style: styles.signalBox },
          React.createElement(Text, { style: styles.signalLabel }, "Buying Signal Detected"),
          React.createElement(Text, { style: styles.signalText }, signal)
        ),

      // ── Body sections ──
      React.createElement(
        View,
        { style: styles.body },
        ...sections.map((sec, i) => {
          const isBulletSection =
            sec.title.toUpperCase().includes("EXPECTED OUTCOMES") ||
            sec.title.toUpperCase().includes("NEXT STEPS");

          const lines = sec.content
            .split("\n")
            .map((l) => l.trim())
            .filter(Boolean);

          return React.createElement(
            View,
            { key: i, style: styles.section },
            // Section header
            React.createElement(
              View,
              { style: styles.sectionHeader },
              React.createElement(View, { style: styles.sectionAccent }),
              React.createElement(
                Text,
                { style: styles.sectionTitle },
                sec.title.toUpperCase()
              )
            ),
            // Section body
            ...(isBulletSection
              ? lines.map((line, li) => {
                  const clean = line.replace(/^[-•*]\s*/, "").replace(/^\d+\.\s*/, "");
                  return React.createElement(
                    View,
                    { key: li, style: styles.bulletRow },
                    React.createElement(Text, { style: styles.bulletDot }, "▸"),
                    React.createElement(Text, { style: styles.bulletText }, clean)
                  );
                })
              : [
                  React.createElement(
                    Text,
                    { key: "body", style: styles.sectionBody },
                    lines.join(" ")
                  ),
                ]),
            // Divider after each section except last
            i < sections.length - 1 &&
              React.createElement(View, { key: "div", style: { ...styles.divider, marginHorizontal: 0, marginTop: 12 } })
          );
        })
      ),

      // ── Footer ──
      React.createElement(
        View,
        { style: styles.footer, fixed: true },
        React.createElement(
          Text,
          { style: styles.footerLeft },
          `Prepared by ${senderName} · ${senderTitle}`
        ),
        React.createElement(
          Text,
          { style: styles.footerRight },
          React.createElement(Text, { style: styles.footerBrand }, senderCompany),
          ` · Confidential`
        )
      )
    )
  );
}

// ── Public API ─────────────────────────────────────────────────────────────────
export async function generateProposalPdf(props: Omit<ProposalPdfProps, "logoBase64">): Promise<Buffer> {
  // Load logo as base64 — try local file first, then fallback to empty string
  let logoBase64 = "";
  const logoPath = path.resolve(__dirname, "../client/public/rfr-logo.png");
  const fallbackPath = "/home/ubuntu/webdev-static-assets/rfr-logo.png";
  try {
    if (fs.existsSync(logoPath)) {
      logoBase64 = fs.readFileSync(logoPath).toString("base64");
    } else if (fs.existsSync(fallbackPath)) {
      logoBase64 = fs.readFileSync(fallbackPath).toString("base64");
    }
  } catch {
    // Logo unavailable — PDF renders without it
  }

  const doc = React.createElement(ProposalDocument, { ...props, logoBase64 });
  const buffer = await renderToBuffer(doc as any);
  return Buffer.from(buffer);
}
