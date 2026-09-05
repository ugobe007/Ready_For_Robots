/** Max signals to render in UI lists (homepage spotlight, dashboard rows, AI modal). */
export const MAX_SIGNALS_DISPLAY = 10;

/**
 * Sort by weighted_score (API), then strength, so "top" matches backend intent.
 */
export function sortSignalsForDisplay(signals = []) {
  return [...(signals || [])].sort((a, b) => {
    const wa = Number(a.weighted_score ?? 0);
    const wb = Number(b.weighted_score ?? 0);
    if (wb !== wa) return wb - wa;
    const sa = Number(a.strength ?? 0);
    const sb = Number(b.strength ?? 0);
    return sb - sa;
  });
}

export function topSignalsForDisplay(signals = [], limit = MAX_SIGNALS_DISPLAY) {
  return sortSignalsForDisplay(signals).slice(0, limit);
}
