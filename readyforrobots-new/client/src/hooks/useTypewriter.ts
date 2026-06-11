import { useEffect, useRef, useState } from "react";

/** Character-by-character reveal; restarts when `text` changes. */
export function useTypewriter(text: string, speed = 28, startDelay = 200) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  const speedRef = useRef(speed);
  const delayRef = useRef(startDelay);

  useEffect(() => {
    setDisplayed("");
    setDone(false);
    if (!text) return undefined;
    let i = 0;
    let interval: ReturnType<typeof setInterval> | undefined;
    const delay = window.setTimeout(() => {
      interval = window.setInterval(() => {
        i += 1;
        setDisplayed(text.slice(0, i));
        if (i >= text.length) {
          if (interval) window.clearInterval(interval);
          setDone(true);
        }
      }, speedRef.current);
    }, delayRef.current);
    return () => {
      window.clearTimeout(delay);
      if (interval) window.clearInterval(interval);
    };
  }, [text]);

  return { displayed, done };
}

/** Types each segment in order; advances when prior segment completes. */
export function useSequentialTypewriter(
  segments: string[],
  speed = 48,
  gapMs = 600,
  startDelayMs = gapMs,
) {
  const [segmentIdx, setSegmentIdx] = useState(0);
  const active = segments[segmentIdx] ?? "";
  const { displayed, done } = useTypewriter(
    active,
    speed,
    segmentIdx === 0 ? startDelayMs : gapMs,
  );

  useEffect(() => {
    setSegmentIdx(0);
  }, [segments.join("\x00")]);

  useEffect(() => {
    if (!done || segmentIdx >= segments.length - 1) return undefined;
    const t = window.setTimeout(() => setSegmentIdx((i) => i + 1), gapMs);
    return () => window.clearTimeout(t);
  }, [done, segmentIdx, segments.length, gapMs]);

  const allDone = done && segmentIdx >= segments.length - 1;
  const completed = segments.slice(0, segmentIdx);
  const current = displayed;

  return { segments: [...completed, current], segmentIdx, allDone };
}
