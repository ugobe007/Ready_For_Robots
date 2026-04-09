/**
 * Compact primary navigation — used by SiteTopNav and dashboard header.
 * Desktop: Home, Pipeline, CRM, Discover ▾, Tools ▾ (smaller type).
 */
import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

const DISCOVER = [
  { href: '/search', label: 'Search' },
  { href: '/market-insights', label: 'Market' },
  { href: '/about', label: 'Signals' },
  { href: '/newsletter', label: 'Newsletter' },
  { href: '/social', label: 'Studio' },
];

const TOOLS = [
  { href: '/roi-calculator', label: 'ROI' },
  { href: '/pilot-calculator', label: 'Pilot' },
  { href: '/robot-ready', label: 'Robot Ready' },
  { href: '/brief', label: 'Brief' },
  { href: '/pipeline-health', label: 'Pipeline health' },
  { href: '/admin', label: 'Admin' },
  { href: '/profile', label: 'Profile' },
];

function Dropdown({ id, label, items, open, setOpen }) {
  const isOpen = open === id;
  return (
    <div className="relative">
      <button
        type="button"
        className="rr-nav-dd-trigger"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        onClick={(e) => {
          e.stopPropagation();
          setOpen(isOpen ? null : id);
        }}
      >
        {label} <span className="opacity-70">▾</span>
      </button>
      {isOpen && (
        <div
          className="rr-nav-dd-panel"
          role="menu"
          onClick={(e) => e.stopPropagation()}
        >
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              role="menuitem"
              className="rr-nav-dd-item"
              onClick={() => setOpen(null)}
            >
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SiteNavPrimaryLinks({
  extraAfterHome = null,
  prepend = null,
  className = '',
  ariaLabel = 'Site',
}) {
  const [open, setOpen] = useState(null);
  const wrapRef = useRef(null);

  useEffect(() => {
    function close() {
      setOpen(null);
    }
    function onDocMouseDown(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) close();
    }
    document.addEventListener('mousedown', onDocMouseDown);
    return () => document.removeEventListener('mousedown', onDocMouseDown);
  }, []);

  return (
    <nav
      ref={wrapRef}
      className={`rr-topnav-links rr-topnav-links--compact ${className}`.trim()}
      aria-label={ariaLabel}
      onKeyDown={(e) => {
        if (e.key === 'Escape') setOpen(null);
      }}
    >
      {prepend}
      <Link href="/" className="rr-nav-link-priority">
        Home
      </Link>
      {extraAfterHome}
      <Link href="/dashboard" className="rr-nav-link-priority">
        Pipeline
      </Link>
      <Link href="/crm/" className="rr-nav-link-priority">
        CRM
      </Link>
      <Dropdown id="discover" label="Discover" items={DISCOVER} open={open} setOpen={setOpen} />
      <Dropdown id="tools" label="Tools" items={TOOLS} open={open} setOpen={setOpen} />
    </nav>
  );
}
