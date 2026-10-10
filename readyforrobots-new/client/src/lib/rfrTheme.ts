/** Inline-style color tokens — emerald light theme (replaces legacy violet palette). */
export const RFR = {
  pageBg: "#f8fafc",
  cardBg: "#ffffff",
  cardBorder: "rgba(15,23,42,0.08)",
  primary: "#059669",
  primaryLight: "#10b981",
  primaryMuted: "#d1fae5",
  primaryBg: "rgba(5,150,105,0.08)",
  primaryBorder: "rgba(5,150,105,0.25)",
  primaryBorderStrong: "rgba(5,150,105,0.4)",
  accent: "#d97706",
  accentBg: "rgba(217,119,6,0.08)",
  hot: "#dc2626",
  warm: "#d97706",
  monitor: "#059669",
  text: "#111827",
  textMuted: "#6b7280",
  textSubtle: "#9ca3af",
} as const;

export const LEGACY_VIOLET_TO_EMERALD: Record<string, string> = {
  "#0d0520": RFR.pageBg,
  "#7c3aed": RFR.primary,
  "#a78bfa": RFR.primaryLight,
  "#c4b5fd": "#047857",
  "#818cf8": "#34d399",
  "#03DAC5": RFR.primary,
  "#130d2a": RFR.cardBg,
  "#C084FC": RFR.primaryLight,
};
