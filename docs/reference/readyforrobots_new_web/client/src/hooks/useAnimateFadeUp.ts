import { useEffect } from "react";

/**
 * Adds `.in-view` to `.animate-fade-up` nodes when they intersect the viewport
 * (see `index.css`). Home wires this globally; routes that mount those sections
 * outside Home must call this hook or content stays at opacity 0 forever.
 */
export function useAnimateFadeUp() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
          }
        });
      },
      { threshold: 0.12 },
    );

    document.querySelectorAll(".animate-fade-up").forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);
}
