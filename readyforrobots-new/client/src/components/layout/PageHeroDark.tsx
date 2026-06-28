import type { ReactNode } from "react";

type HeroStat = {
  label: string;
  value: ReactNode;
  tone?: "emerald" | "amber" | "white";
};

type PageHeroDarkProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  badge?: ReactNode;
  stats?: HeroStat[];
  actions?: ReactNode;
  children?: ReactNode;
  className?: string;
  innerClassName?: string;
  maxWidthClass?: string;
};

const statToneClass: Record<NonNullable<HeroStat["tone"]>, string> = {
  emerald: "text-emerald-400",
  amber: "text-amber-400",
  white: "text-white",
};

export default function PageHeroDark({
  eyebrow,
  title,
  description,
  badge,
  stats,
  actions,
  children,
  className = "",
  innerClassName = "",
  maxWidthClass = "max-w-6xl",
}: PageHeroDarkProps) {
  return (
    <section className={`page-hero-dark ${className}`}>
      <div className="page-hero-dark-grid pointer-events-none" aria-hidden />
      <div className={`container ${maxWidthClass} page-hero-dark-inner ${innerClassName}`}>
        {badge}
        {eyebrow ? <p className="section-eyebrow-on-dark mb-2">{eyebrow}</p> : null}
        <div className={stats?.length ? "flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between" : undefined}>
          <div className="min-w-0">
            <h1 className="page-hero-title">{title}</h1>
            {description ? <div className="page-hero-description mt-3 max-w-2xl">{description}</div> : null}
            {actions ? <div className="mt-6">{actions}</div> : null}
          </div>
          {stats?.length ? (
            <div className="grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-4">
              {stats.map((stat, index) => (
                <div
                  key={stat.label}
                  className="page-hero-stat-card"
                  style={{ animationDelay: `${index * 80}ms` }}
                >
                  <div className={`font-mono-data text-lg font-black sm:text-xl ${statToneClass[stat.tone ?? "emerald"]}`}>
                    {stat.value}
                  </div>
                  <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500">{stat.label}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
        {children}
      </div>
    </section>
  );
}
