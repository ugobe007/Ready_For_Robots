export function decodeBasicHtmlEntities(raw: string): string {
  return raw
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, "\"")
    .replace(/&#39;/g, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">");
}

export function cleanScrapedText(raw: string | null | undefined): string {
  return decodeBasicHtmlEntities(raw || "")
    .replace(/<\s*a\s*href\s*=\s*["'][^"']*["'][^>]*>([\s\S]*?)<\/a>/gi, "$1")
    .replace(/<\s*ahref\s*=\s*["'][^"']*["'][^>]*>([\s\S]*?)<\/a>/gi, "$1")
    .replace(/<a\b[^>]*>([\s\S]*?)<\/a>/gi, "$1")
    .replace(/\bsource_url\s*[:=]?\s*/gi, "")
    .replace(/\bsource_url\s*[:=]?\s*https?:\/\/\S+/gi, "")
    .replace(/href=["'][^"']+["']/gi, "")
    .replace(/href=https?:\/\/[^\s>]+/gi, "")
    .replace(/\bahref=["'][^"']+["']/gi, "")
    .replace(/\bahref=https?:\/\/[^\s>]+/gi, "")
    .replace(/\b(?:target|rel|class|style|title)=["'][^"']*["']/gi, "")
    .replace(/https?:\/\/[^\s"'<>]+/gi, "")
    .replace(/\b(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:\/[^\s"'<>]*)?/gi, "")
    .replace(/\b(?:ca|cc|ved|usg)=[^\s"'<>]+/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/(^|\s)>+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function cleanAndClampText(raw: string | null | undefined, maxLength: number): string {
  const text = cleanScrapedText(raw);
  if (!text || text.length <= maxLength) return text;
  const slice = text.slice(0, maxLength - 1);
  const lastSpace = slice.lastIndexOf(" ");
  const cut = lastSpace > 40 ? slice.slice(0, lastSpace) : slice;
  return `${cut.trimEnd().replace(/[,;:]$/u, "")}…`;
}

/** One or two complete sentences for card previews — never mid-word. */
export function leadPreviewSentences(raw: string | null | undefined, maxSentences = 2, maxChars = 320): string {
  const text = cleanScrapedText(raw);
  if (!text) return "";
  const parts = text.split(/(?<=[.!?])\s+/).filter((p) => p.trim().length > 12);
  if (!parts.length) return cleanAndClampText(text, maxChars);
  let out = "";
  for (const part of parts.slice(0, maxSentences)) {
    const next = out ? `${out} ${part.trim()}` : part.trim();
    if (next.length > maxChars) break;
    out = next;
    if (!out.endsWith(".") && !out.endsWith("!") && !out.endsWith("?")) {
      out += ".";
    }
  }
  return out || cleanAndClampText(text, maxChars);
}
