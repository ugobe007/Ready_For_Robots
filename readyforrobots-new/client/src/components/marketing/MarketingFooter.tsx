import { Link } from "wouter";

type Props = {
  newsletterEmail: string;
  newsletterStatus: "idle" | "submitting" | "success" | "error";
  onEmailChange: (v: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
};

export default function MarketingFooter({ newsletterEmail, newsletterStatus, onEmailChange, onSubmit }: Props) {
  const links = {
    Product: [
      { label: "Pipeline", href: "/pipeline" },
      { label: "Signals", href: "/signals" },
      { label: "Newsletter", href: "/newsletter" },
      { label: "Robots", href: "/robots" },
      { label: "How It Works", href: "/how-it-works" },
      { label: "Pricing", href: "/pricing" },
    ],
    Intelligence: [
      { label: "Intelligence", href: "/intelligence" },
      { label: "Studio", href: "/social" },
      { label: "Marketplace", href: "/marketplace" },
      { label: "Integrations", href: "/integrations" },
    ],
    Company: [
      { label: "About Us", href: "/#about" },
      { label: "Case Studies", href: "/#case-studies" },
    ],
  };

  return (
    <footer className="bg-slate-950 border-t border-white/5">
      <div className="container py-14">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10 mb-12">
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2.5 mb-4">
              <img src="/logo-r.png" alt="ReadyForRobots" className="h-7 w-7" />
              <div>
                <span className="font-display font-bold text-white text-sm tracking-tight block">ReadyForRobots</span>
                <span className="font-mono-data text-emerald-400 text-[10px] font-semibold tracking-widest uppercase">
                  SIGNAL
                </span>
              </div>
            </Link>
            <p className="text-slate-500 text-sm leading-relaxed mb-5 max-w-xs">
              The only sales intelligence platform built exclusively for robot vendors and integrators.
            </p>
            <form onSubmit={onSubmit} className="flex gap-2 max-w-sm">
              <input
                type="email"
                value={newsletterEmail}
                onChange={(e) => onEmailChange(e.target.value)}
                placeholder="work email"
                className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
              />
              <button
                type="submit"
                disabled={newsletterStatus === "submitting"}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50"
              >
                Subscribe
              </button>
            </form>
            {newsletterStatus === "success" && <p className="text-emerald-400 text-xs mt-2">Subscribed.</p>}
            <p className="text-slate-600 text-xs mt-2">Weekly Robot Intelligence Brief. Free.</p>
          </div>

          {Object.entries(links).map(([group, items]) => (
            <div key={group}>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-4">{group}</p>
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-slate-500 text-sm hover:text-white transition-colors">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-slate-600 text-xs">© 2026 ReadyForRobots · Signal for robotics sales.</p>
          <div className="flex gap-6">
            <Link href="/login" className="text-slate-500 text-xs hover:text-white transition-colors">
              Sign in
            </Link>
            <Link href="/signup" className="text-slate-500 text-xs hover:text-white transition-colors">
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
