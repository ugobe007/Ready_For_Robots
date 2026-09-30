import { useEffect, useRef, useState } from "react";

/**
 * useFadeUp — returns a ref and a boolean `visible`.
 * Attach `ref` to any element; `visible` becomes true once the element
 * enters the viewport, triggering a CSS fade-up transition.
 *
 * Usage:
 *   const { ref, visible } = useFadeUp();
 *   <div ref={ref} className={visible ? "animate-fade-up" : "opacity-0 translate-y-6"}>
 */
export function useFadeUp(threshold = 0.15) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, visible };
}

/**
 * fadeUpClass — returns the Tailwind classes for a fade-up transition.
 * Pass `visible` from useFadeUp and an optional delay index for staggering.
 *
 * @param visible  - whether the element is in view
 * @param delayMs  - delay in milliseconds (0, 100, 200, …)
 */
export function fadeUpClass(visible: boolean, delayMs = 0): string {
  const base = "transition-all duration-700 ease-out";
  const delay = delayMs ? `delay-[${delayMs}ms]` : "";
  const state = visible
    ? "opacity-100 translate-y-0"
    : "opacity-0 translate-y-6";
  return [base, delay, state].filter(Boolean).join(" ");
}
