/**
 * Shared site header — same primary nav as dashboard / pipeline.
 * Use on admin and other tools so users can reach Home, Search, Profile, etc.
 */
import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import LoginDropdown from './LoginDropdown';

export default function SiteTopNav({ session }) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <header className="rr-topnav w-full">
      <div className="rr-topnav-inner">
        <Link href="/" className="rr-topnav-brand group min-w-0">
          <div className="rr-brand-logo overflow-hidden">
            <Image src="/logo-r.png" alt="" width={34} height={34} className="!p-0.5 object-contain" priority />
          </div>
          <div className="min-w-0 hidden sm:block">
            <div className="rr-brand-name leading-tight">Automation Projects Ready For Robots</div>
            <div className="rr-brand-sub">with Signal Intelligence</div>
          </div>
        </Link>

        <div className="md:hidden relative ml-auto shrink-0">
          <button
            type="button"
            onClick={() => setShowMenu(!showMenu)}
            className="rr-btn-signin px-3 text-lg leading-none"
            aria-expanded={showMenu}
            aria-label="Open menu"
          >
            ☰
          </button>
          {showMenu && (
            <div className="absolute right-0 top-full mt-2 w-56 border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50">
              <Link href="/" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">🏠 Home</div>
              </Link>
              <Link href="/dashboard" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">📊 Dashboard</div>
              </Link>
              <Link href="/crm/" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">🗂️ CRM</div>
              </Link>
              <Link href="/search" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">🔍 Intelligence Search</div>
              </Link>
              <Link href="/market-insights" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">📈 Market</div>
              </Link>
              <Link href="/roi-calculator" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-yellow-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">💰 ROI Calculator</div>
              </Link>
              <Link href="/pilot-calculator" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">🧪 Pilot Calculator</div>
              </Link>
              <Link href="/robot-ready" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">🤖 Robot Ready</div>
              </Link>
              <Link href="/newsletter" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">📰 Newsletter</div>
              </Link>
              <Link href="/profile" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">♡ Profile</div>
              </Link>
              <Link href="/admin" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">⚙️ Admin Panel</div>
              </Link>
              <Link href="/brief" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">📋 Strategy Brief</div>
              </Link>
              <Link href="/about" onClick={() => setShowMenu(false)}>
                <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900">⚡ Signal Intelligence</div>
              </Link>
            </div>
          )}
        </div>

        <nav className="rr-topnav-links" aria-label="Site">
          <Link href="/">Home</Link>
          <Link href="/dashboard">Pipeline</Link>
          <Link href="/crm/">CRM</Link>
          <Link href="/search">Search</Link>
          <Link href="/market-insights">Market</Link>
          <Link href="/about">Signals</Link>
          <Link href="/newsletter">Newsletter</Link>
          <Link href="/social">Studio</Link>
          <Link href="/roi-calculator">ROI</Link>
          <Link href="/pilot-calculator">Pilot</Link>
          <Link href="/robot-ready">Robot Ready</Link>
          <Link href="/brief">Brief</Link>
          <Link href="/admin">Admin</Link>
          <Link href="/profile">Profile</Link>
        </nav>
        <div className="rr-topnav-right hidden md:flex items-center">
          {session ? (
            <span className="text-sm text-[var(--rr-muted2)] max-w-[10rem] truncate">{session.user.email.split('@')[0]}</span>
          ) : (
            <div title="Browse freely — sign in only to save companies and reports">
              <LoginDropdown
                label="sign in to save"
                className="[&_button]:rounded-md [&_button]:border [&_button]:border-[#1f2d42] [&_button]:px-3 [&_button]:py-1.5 [&_button]:text-sm [&_button]:text-[#94a3b8] [&_button]:hover:border-[#10b981] [&_button]:hover:text-[#10b981]"
              />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
