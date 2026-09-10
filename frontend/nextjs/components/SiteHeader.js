/**
 * Standardized Harmonized Header for Ready For Robots
 * Unified brand, navigation links, and call-to-action buttons across all pages.
 */
import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import LoginDropdown from './LoginDropdown';

export default function SiteHeader({ active = '', session = null }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (moreRef.current && !moreRef.current.contains(e.target)) {
        setMoreOpen(false);
      }
    }
    if (moreOpen) document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [moreOpen]);

  const navCls = (key) =>
    `px-3 py-2 text-sm font-medium transition-colors ${
      active === key
        ? 'text-emerald-400 font-semibold border-b-2 border-emerald-500'
        : 'text-neutral-300 hover:text-white'
    }`;

  return (
    <header className="w-full bg-[#0b1017] border-b border-neutral-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        {/* Brand & Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <Link href="/" className="flex items-center gap-2.5 group" aria-label="Ready For Robots home">
            <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-emerald-500/40 p-1 flex items-center justify-center group-hover:border-emerald-400 transition-colors">
              <Image src="/logo-r.png" alt="" width={28} height={28} className="object-contain" priority />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-tight text-base sm:text-lg">
                ReadyForRobots
              </span>
              <span className="text-[10px] font-mono font-bold tracking-widest text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-1.5 py-0.5 rounded uppercase">
                SIGNAL
              </span>
            </div>
          </Link>
        </div>

        {/* Primary Desktop Nav Links */}
        <nav className="hidden lg:flex items-center gap-1" aria-label="Primary Navigation">
          <Link href="/dashboard" className={navCls('pipeline')}>
            Pipeline
          </Link>
          <Link href="/about" className={navCls('about')}>
            Signals
          </Link>
          <Link href="/robot-ready" className={navCls('robots')}>
            Robots
          </Link>
          <Link href="/crm/" className={navCls('crm')}>
            CRM
          </Link>
          <Link href="/pricing" className={navCls('pricing')}>
            Pricing
          </Link>
          <Link href="/newsletter" className={navCls('newsletter')}>
            Intelligence
          </Link>
          <Link href="/newsletter#compare" className={navCls('compare')}>
            Compare
          </Link>

          {/* More Dropdown */}
          <div ref={moreRef} className="relative">
            <button
              type="button"
              onClick={() => setMoreOpen(!moreOpen)}
              className="px-3 py-2 text-sm font-medium text-neutral-300 hover:text-white flex items-center gap-1 transition-colors"
              aria-expanded={moreOpen}
            >
              More <span className="text-xs opacity-70">▾</span>
            </button>

            {moreOpen && (
              <div
                className="absolute left-0 top-full mt-2 w-52 border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50 py-2"
                onClick={() => setMoreOpen(false)}
              >
                <Link href="/roi-calculator" className="block px-4 py-2 text-sm text-neutral-300 hover:text-emerald-400 hover:bg-neutral-900">
                  💰 ROI Calculator
                </Link>
                <Link href="/market-insights" className="block px-4 py-2 text-sm text-neutral-300 hover:text-cyan-400 hover:bg-neutral-900">
                  📈 Market Insights
                </Link>
                <Link href="/search" className="block px-4 py-2 text-sm text-neutral-300 hover:text-cyan-400 hover:bg-neutral-900">
                  🔍 Search Leads
                </Link>
                <Link href="/social" className="block px-4 py-2 text-sm text-neutral-300 hover:text-purple-400 hover:bg-neutral-900">
                  🎨 Studio
                </Link>
                <Link href="/brief" className="block px-4 py-2 text-sm text-neutral-300 hover:text-cyan-400 hover:bg-neutral-900">
                  📋 Brief
                </Link>
                <Link href="/pilot-calculator" className="block px-4 py-2 text-sm text-neutral-300 hover:text-amber-400 hover:bg-neutral-900">
                  🧪 Pilot Calculator
                </Link>
              </div>
            )}
          </div>
        </nav>

        {/* Action Buttons (Right) */}
        <div className="hidden sm:flex items-center gap-3 shrink-0">
          <Link
            href="/#leads"
            className="px-3.5 py-1.5 text-xs font-semibold text-emerald-400 border border-emerald-800/60 bg-emerald-950/40 hover:bg-emerald-900/60 hover:border-emerald-500 rounded-lg transition-colors"
          >
            Find leads
          </Link>
          <LoginDropdown label="Sign in" variant="default" />
          <Link
            href="/login"
            className="px-4 py-2 text-xs font-bold text-white bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors shadow-md shadow-purple-500/25"
          >
            ⚡ Start free workspace
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="lg:hidden p-2 text-neutral-400 hover:text-white text-xl"
          aria-label="Toggle navigation menu"
        >
          ☰
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="lg:hidden border-b border-neutral-800 bg-neutral-950 px-4 py-4 space-y-2">
          <Link href="/dashboard" className="block px-3 py-2 text-sm text-emerald-400 hover:bg-neutral-900 rounded">
            📊 Pipeline
          </Link>
          <Link href="/about" className="block px-3 py-2 text-sm text-cyan-400 hover:bg-neutral-900 rounded">
            ⚡ Signals
          </Link>
          <Link href="/robot-ready" className="block px-3 py-2 text-sm text-emerald-400 hover:bg-neutral-900 rounded">
            🤖 Robots
          </Link>
          <Link href="/crm/" className="block px-3 py-2 text-sm text-emerald-400 hover:bg-neutral-900 rounded">
            🗂️ CRM
          </Link>
          <Link href="/pricing" className="block px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-900 rounded">
            🏷️ Pricing
          </Link>
          <Link href="/newsletter" className="block px-3 py-2 text-sm text-cyan-300 hover:bg-neutral-900 rounded">
            📰 Intelligence
          </Link>
          <Link href="/newsletter#compare" className="block px-3 py-2 text-sm text-purple-400 hover:bg-neutral-900 rounded">
            ⚔️ Compare
          </Link>
          <Link href="/roi-calculator" className="block px-3 py-2 text-sm text-amber-400 hover:bg-neutral-900 rounded">
            💰 ROI Calculator
          </Link>
          <div className="pt-2 border-t border-neutral-800 flex flex-col gap-2">
            <Link href="/login" className="block text-center px-4 py-2 text-xs font-bold text-white bg-purple-600 rounded-lg">
              ⚡ Start free workspace
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
