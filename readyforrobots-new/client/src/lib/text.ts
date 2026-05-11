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
    .replace(/\bsource_url\s*[:=]?\s*<a\b[\s\S]*?<\/a>/gi, "")
    .replace(/\bsource_url\s*[:=]?\s*https?:\/\/\S+/gi, "")
    .replace(/<a\b[^>]*href=["']https?:\/\/[^"']+["'][^>]*>[\s\S]*?<\/a>/gi, "")
    .replace(/href=["'][^"']+["']/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function cleanAndClampText(raw: string | null | undefined, maxLength: number): string {
  const text = cleanScrapedText(raw);
  if (!text || text.length <= maxLength) return text;
  return `${text.slice(0, Math.max(0, maxLength - 1)).trimEnd()}…`;
}
