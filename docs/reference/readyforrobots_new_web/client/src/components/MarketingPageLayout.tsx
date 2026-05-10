import { Link } from "wouter";
import type { ReactNode } from "react";

const EMERALD = "oklch(0.527 0.154 162.5)";

export type MarketingPageLayoutProps = {
  kicker?: string;
  title: string;
  subtitle?: string;
  children?: ReactNode;
};

/**
 * Inner-page hero + prose region — "Precision Craft" (light, emerald accent).
 */
export default function MarketingPageLayout({
  kicker,
  title,
  subtitle,
  children,
}: MarketingPageLayoutProps) {
  return (
    <div>
      <section
        className="relative border-b border-gray-100 overflow-hidden"
        style={{
          background: "linear-gradient(135deg, #ffffff 0%, #f0fdf4 45%, #eff6ff 100%)",
        }}
      >
        <div className="container py-14 md:py-20 max-w-3xl">
          <Link
            href="/"
            className="inline-flex text-sm text-gray-500 hover:text-gray-800 mb-6 transition-colors"
          >
            ← Back to home
          </Link>
          {kicker ? (
            <span
              className="section-label block mb-3 text-xs font-semibold uppercase tracking-widest text-gray-500"
              style={{ letterSpacing: "0.12em" }}
            >
              {kicker}
            </span>
          ) : null}
          <h1
            className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight mb-4"
            style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
          >
            {title}
          </h1>
          {subtitle ? (
            <p className="text-lg text-gray-600 leading-relaxed">{subtitle}</p>
          ) : null}
        </div>
        <div
          className="absolute bottom-0 left-0 right-0 h-1 opacity-90"
          style={{
            background: `linear-gradient(90deg, transparent, ${EMERALD}, oklch(0.488 0.243 264.376), transparent)`,
          }}
        />
      </section>

      <section className="container py-12 md:py-16 max-w-3xl">
        <div className="text-gray-700 leading-relaxed space-y-4 [&_p]:text-base [&_code]:text-sm [&_code]:rounded [&_code]:bg-gray-100 [&_code]:px-1.5 [&_code]:py-0.5">
          {children}
        </div>
      </section>
    </div>
  );
}
