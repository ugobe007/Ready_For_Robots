/**
 * Shared site header — compact primary nav + dropdowns (Discover, Tools).
 */
import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import LoginDropdown from './LoginDropdown';
import SiteNavPrimaryLinks from './SiteNavPrimaryLinks';

function MobileNavSection({ title, children }) {
  return (
    <div className="border-b border-neutral-800 last:border-0">
      <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
        {title}
      </div>
      <div className="pb-1">{children}</div>
    </div>
  );
}

export default function SiteTopNav({ session }) {
  const [showMenu, setShowMenu] = useState(false);

  const mobileLink = (href, label, colorClass = 'text-neutral-300') => (
    <Link href={href} onClick={() => setShowMenu(false)}>
      <div
        className={`px-4 py-2.5 text-[13px] ${colorClass} hover:bg-neutral-900 cursor-pointer`}
      >
        {label}
      </div>
    </Link>
  );

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
            <div className="absolute right-0 top-full mt-2 w-64 max-h-[min(80vh,520px)] overflow-y-auto border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50">
              <MobileNavSection title="Main">{mobileLink('/', '🏠 Home', 'text-emerald-400')}</MobileNavSection>
              <MobileNavSection title="Pipeline">
                {mobileLink('/dashboard', '📊 Pipeline', 'text-cyan-400')}
                {mobileLink('/crm/', '🗂️ CRM', 'text-emerald-400')}
              </MobileNavSection>
              <MobileNavSection title="Discover">
                {mobileLink('/search', '🔍 Search', 'text-cyan-400')}
                {mobileLink('/market-insights', '📈 Market', 'text-cyan-400')}
                {mobileLink('/about', '⚡ Signals', 'text-emerald-400')}
                {mobileLink('/newsletter', '📰 Newsletter', 'text-neutral-300')}
                {mobileLink('/social', '🎨 Studio', 'text-neutral-300')}
              </MobileNavSection>
              <MobileNavSection title="Tools">
                {mobileLink('/roi-calculator', '💰 ROI', 'text-yellow-400')}
                {mobileLink('/pilot-calculator', '🧪 Pilot', 'text-cyan-400')}
                {mobileLink('/robot-ready', '🤖 Robot Ready', 'text-emerald-400')}
                {mobileLink('/brief', '📋 Brief', 'text-cyan-400')}
                {mobileLink('https://ready-2-robot.fly.dev/admin', '⚙️ Admin', 'text-emerald-400')}
                {mobileLink('/profile', '♡ Profile', 'text-neutral-300')}
              </MobileNavSection>
            </div>
          )}
        </div>

        <SiteNavPrimaryLinks />

        <div className="rr-topnav-right hidden md:flex items-center">
          {session ? (
            <span className="text-xs text-[var(--rr-muted2)] max-w-[10rem] truncate">{session.user.email.split('@')[0]}</span>
          ) : (
            <div title="Browse freely — sign in only to save companies and reports">
              <LoginDropdown
                label="sign in to save"
                className="[&_button]:rounded-md [&_button]:border [&_button]:border-[#1f2d42] [&_button]:px-3 [&_button]:py-1.5 [&_button]:text-xs [&_button]:text-[#cbd5e1] [&_button]:hover:border-[#10b981] [&_button]:hover:text-[#10b981]"
              />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
