// ReadyForRobots — SecondaryNav Component
// Design: Clean Workflow / Elevated SaaS
// A slim secondary navigation bar below the main header
// Links scroll to in-page anchor sections: About Us, How It Works, Questions

import { BookOpen, Zap, HelpCircle, ArrowRight } from "lucide-react";

const links = [
  { label: "About Us", href: "#about", icon: BookOpen },
  { label: "How It Works", href: "#how-it-works", icon: Zap },
  { label: "Questions", href: "#faq", icon: HelpCircle },
];

export default function SecondaryNav() {
  const handleClick = (href: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    const id = href.replace("#", "");
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="w-full bg-neutral-100 border-b border-neutral-200">
      <div className="max-w-5xl mx-auto px-6 flex items-center justify-between h-9">
        {/* Left: anchor links */}
        <nav className="flex items-center gap-1">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <a
                key={link.label}
                href={link.href}
                onClick={handleClick(link.href)}
                className="flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium text-neutral-500 hover:text-neutral-900 hover:bg-neutral-200 transition-colors"
              >
                <Icon className="h-3 w-3" />
                {link.label}
              </a>
            );
          })}
        </nav>

        {/* Right: quick CTA */}
        <a
          href="#hero-cta"
          onClick={handleClick("#hero-cta")}
          className="hidden sm:flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700 transition-colors"
        >
          Start automating
          <ArrowRight className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}
