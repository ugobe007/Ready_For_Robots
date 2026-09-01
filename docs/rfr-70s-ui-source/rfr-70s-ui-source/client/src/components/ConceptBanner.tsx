/**
 * Design: neutral concept-gallery chrome.
 * A thin switcher bar pinned to the bottom of every concept page so the user
 * can jump between the three 1970s options. Deliberately understated so it
 * never competes with the concept's own styling.
 */
import { Link, useLocation } from "wouter";

const CONCEPTS = [
  { path: "/mainframe", key: "A", name: "Mainframe ’74" },
  { path: "/help-wanted", key: "B", name: "Help Wanted ’76" },
  { path: "/space-age", key: "C", name: "Space-Age ’72" },
] as const;

export function ConceptBanner() {
  const [location] = useLocation();
  return (
    <div className="fixed bottom-0 inset-x-0 z-50 flex items-center justify-center gap-1 bg-neutral-950/95 border-t border-neutral-800 px-2 py-2 font-sans backdrop-blur-sm">
      <Link href="/" className="text-[11px] uppercase tracking-widest text-neutral-400 hover:text-white px-3 py-1.5 transition-colors">
        ← All options
      </Link>
      <span className="text-neutral-700 select-none">|</span>
      {CONCEPTS.map((c) => (
        <Link
          key={c.path}
          href={c.path}
          className={`text-[11px] uppercase tracking-widest px-3 py-1.5 transition-colors ${
            location === c.path
              ? "bg-amber-400 text-neutral-950 font-semibold"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          {c.key} · {c.name}
        </Link>
      ))}
    </div>
  );
}
