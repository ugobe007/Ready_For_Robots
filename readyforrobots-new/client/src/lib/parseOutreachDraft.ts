/** Split a combined outreach draft into subject + body. */
export function parseOutreachDraft(draft: string): { subject?: string; body?: string } {
  const trimmed = draft.trim();
  if (!trimmed) return {};

  const subjectMatch = trimmed.match(/^Subject:\s*(.+?)(?:\r?\n\r?\n|\r?\n)/i);
  if (subjectMatch) {
    return {
      subject: subjectMatch[1].trim(),
      body: trimmed.slice(subjectMatch[0].length).trim(),
    };
  }

  return { body: trimmed };
}
