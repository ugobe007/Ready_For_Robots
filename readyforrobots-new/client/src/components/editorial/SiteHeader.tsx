import { useLocation } from "wouter";
import { jobsFindHref } from "@/lib/jobsLanding";

type NavLink = { label: string; href: string };

type SiteHeaderProps = {
  signedIn?: boolean;
  initials?: string;
  links?: NavLink[];
  ctaHref?: string;
};

const PUBLIC_LINKS = [
  { label: "Find buyers", href: "/" },
  { label: "How it works", href: "/#how" },
  { label: "Explore", href: "/explore" },
  { label: "Pricing", href: "/pricing" },
  { label: "Sign in", href: "/login" },
];

const SIGNED_IN_LINKS = [
  { label: "Find buyers", href: "/" },
  { label: "My desk", href: "/desk" },
  { label: "Explore", href: "/explore" },
];

export function SiteHeader({
  signedIn = false,
  initials = "RR",
  links: linkOverride,
  ctaHref = jobsFindHref(),
}: SiteHeaderProps) {
  const links = signedIn ? SIGNED_IN_LINKS : linkOverride ?? PUBLIC_LINKS;
  const [location] = useLocation();
  const path = location.split("?")[0] || "/";
  return (
    <header className="rfr-header">
      <div className="rfr-header-inner">
        <a className="rfr-wordmark" href="/" aria-label="Ready For Robots">
          <img src="/branding/rfr-icon-light.svg" alt="" width="22" height="22" />
          <span>READY<span className="rfr-wordmark-for">FOR</span>ROBOTS</span>
        </a>
        <nav className="rfr-nav" aria-label="Site">
          {links.map((link) => (
            <a
              key={link.label}
              href={link.href}
              aria-current={link.href === path ? "page" : undefined}
              className={link.href === path ? "rfr-nav-current" : undefined}
            >
              {link.label}
            </a>
          ))}
          {signedIn ? (
            <span className="rfr-avatar" aria-label="Account">
              {initials}
            </span>
          ) : (
            <a className="rfr-header-cta" href={ctaHref}>
              Start free
            </a>
          )}
        </nav>
      </div>
    </header>
  );
}
