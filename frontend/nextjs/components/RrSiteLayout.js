/**
 * Shared shell: homepage navbar + footer (rr-theme) for marketing / tool pages.
 * Integrates standardized harmonized SiteHeader.
 */
import Image from 'next/image';
import SiteHeader from './SiteHeader';

export default function RrSiteLayout({ children, active, footer = true, subNav = null }) {
  return (
    <div className="rr-theme min-h-screen flex flex-col">
      <SiteHeader active={active} />
      {subNav}
      <div className="flex-1 w-full min-h-0">{children}</div>
      {footer && (
        <footer className="rr-footer shrink-0 bg-[#090d14] border-t border-neutral-800 py-8 text-center text-xs text-neutral-500">
          <div className="flex justify-center mb-3">
            <Image src="/logo-r.png" alt="" width={36} height={36} className="h-9 w-9 opacity-80" />
          </div>
          <p>© 2026 Ready For Robots · Signal intelligence &amp; automation sales leads.</p>
        </footer>
      )}
    </div>
  );
}
