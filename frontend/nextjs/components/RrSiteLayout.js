/**
 * Shared shell: homepage navbar + footer (rr-theme) for marketing / tool pages.
 */
import Link from 'next/link';
import Image from 'next/image';
import LoginDropdown from './LoginDropdown';

export default function RrSiteLayout({ children, active, footer = true, subNav = null }) {
  const navCls = (key) => (active === key ? 'rr-nav-active' : undefined);

  return (
    <div className="rr-theme min-h-screen flex flex-col">
      <div className="rr-navbar w-full shrink-0">
        <div className="rr-navbar-inner">
          <div className="rr-nav-brand">
            <Link href="/" className="shrink-0" aria-label="Ready For Robots home">
              <span className="rr-brand-logo block">
                <Image src="/logo-r.png" alt="" width={36} height={36} className="object-contain p-0.5" priority />
              </span>
            </Link>
            <Link href="/" className="rr-brand-name hidden sm:inline">
              Ready For Robots
            </Link>
          </div>
          <nav className="rr-nav-links" aria-label="Main">
            <Link href="/dashboard" className={navCls('dashboard')}>
              Dashboard
            </Link>
            <Link href="/dashboard" className={navCls('pipeline')} title="Lead pipeline and sales workspace">
              Pipeline
            </Link>
            <Link href="/market-insights" className={navCls('market-insights')}>
              Market Insights
            </Link>
            <Link href="/search" className={navCls('search')}>
              Search
            </Link>
            <Link href="/about" className={navCls('about')}>
              Signals
            </Link>
            <Link href="/newsletter" className={navCls('newsletter')}>
              📰 Newsletter
            </Link>
            <Link href="/roi-calculator" className={navCls('roi')}>
              ROI Calculator
            </Link>
            <Link href="/social" className={navCls('social')}>
              Studio
            </Link>
            <Link href="/#leads" className={navCls('leads')}>
              Browse Leads
            </Link>
          </nav>
          <div className="rr-nav-right">
            <div className="hidden md:flex items-center gap-3">
              <LoginDropdown className="[&_button]:rr-btn-signin" />
              <Link href="/login" className="rr-btn-signup">
                Sign Up
              </Link>
            </div>
            <div className="md:hidden relative">
              <button
                type="button"
                onClick={() => {
                  const menu = document.getElementById('rr-mobile-menu');
                  menu?.classList.toggle('hidden');
                }}
                className="text-neutral-400 hover:text-white px-3 py-2 text-xl"
                aria-expanded="false"
                aria-controls="rr-mobile-menu"
              >
                ☰
              </button>
              <div
                id="rr-mobile-menu"
                className="hidden absolute right-0 top-full mt-2 w-56 border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-[300]"
              >
                <Link
                  href="/dashboard"
                  className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  📊 Dashboard
                </Link>
                <Link
                  href="/dashboard"
                  className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  🧭 Pipeline
                </Link>
                <Link
                  href="/market-insights"
                  className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  📈 Market Insights
                </Link>
                <Link
                  href="/search"
                  className="block px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  🔍 Search
                </Link>
                <Link
                  href="/about"
                  className="block px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  ⚡ Signals
                </Link>
                <Link
                  href="/#leads"
                  className="block px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  🔥 Browse Leads
                </Link>
                <Link
                  href="/newsletter"
                  className="block px-4 py-3 text-sm text-cyan-300 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  📰 Newsletter
                </Link>
                <Link
                  href="/roi-calculator"
                  className="block px-4 py-3 text-sm text-yellow-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  💰 ROI Calculator
                </Link>
                <Link
                  href="/social"
                  className="block px-4 py-3 text-sm text-violet-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  ✨ Studio
                </Link>
                <Link
                  href="/#signals"
                  className="block px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  💡 How It Works
                </Link>
                <Link
                  href="/login"
                  className="block px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 border-b border-neutral-800"
                >
                  🔐 Sign in
                </Link>
                <Link href="/login" className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900">
                  ✨ Sign Up
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
      {subNav}
      <div className="flex-1 w-full min-h-0">{children}</div>
      {footer && (
        <footer className="rr-footer shrink-0">
          <div className="flex justify-center mb-3">
            <Image src="/logo-r.png" alt="" width={40} height={40} className="h-10 w-10 opacity-90" />
          </div>
          <p>© 2026 Signal intelligence for robotics sales.</p>
        </footer>
      )}
    </div>
  );
}
