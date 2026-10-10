export function scoutFingerprint(): string {
  const key = "rfr_scout_fingerprint";
  try {
    const existing = localStorage.getItem(key);
    if (existing && existing.length >= 8) return existing;
    const generated = `web_${crypto.randomUUID()}`;
    localStorage.setItem(key, generated);
    return generated;
  } catch {
    return "web_anonymous";
  }
}
