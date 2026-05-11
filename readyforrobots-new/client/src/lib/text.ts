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
  return `${text.slice(0, Math.max(0, maxLength - 1)).trimEnd()}…`;
}
