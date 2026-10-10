import { cleanScrapedText } from "@/lib/text";

const FALLBACK = "Who is buying robots this week";

/**
 * Turn a generated brief title into one sentence.
 * "Medline: to pilot warehouse automation...." is not a headline.
 */
export function readableNewsletterHeadline(text?: string): string {
  let s = cleanScrapedText(text || "");
  s = s.replace(/(?:\s*\.){2,}$/g, "").replace(/\.+$/g, "").trim();
  if (!s) return FALLBACK;

  const split = s.match(/^(.{2,60}?)\s*[:\u2014\u2013]\s+(.+)$/);
  if (split) {
    const left = split[1].trim();
    const right = (split[2].split(/[.!?]/)[0] || split[2]).trim();
    const leftKey = left.slice(0, 4).toLowerCase();
    if (right && /^[a-z]/.test(right)) {
      s = `${left} ${right.charAt(0).toLowerCase()}${right.slice(1)}`;
    } else if (
      right &&
      (left.length < 4 || right.toLowerCase().startsWith(leftKey))
    ) {
      s = right;
    } else if (right) {
      s = `${left}: ${right}`;
    }
  } else {
    s = (s.split(/[.!?]/)[0] || s).trim();
  }

  s = s.replace(/\s+/g, " ").replace(/\.+$/g, "").trim();
  if (!s) return FALLBACK;
  if (s[0] === s[0].toLowerCase()) s = s[0].toUpperCase() + s.slice(1);
  if (s.length > 120) {
    const cut = s.slice(0, 117).replace(/\s+\S*$/, "").trim();
    s = cut || s.slice(0, 117).trim();
  }
  return s;
}
