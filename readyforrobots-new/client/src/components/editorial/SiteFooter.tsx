const FOOTER_LINKS = [
  { label: "About", href: "/about" },
  { label: "Newsletter", href: "/newsletter" },
  { label: "Privacy", href: "/privacy" },
  { label: "Terms", href: "/terms" },
  { label: "Support", href: "/support" },
];

export function SiteFooter() {
  return (
    <footer className="rfr-footer">
      <div className="rfr-footer-inner">
        <a className="rfr-wordmark" href="/" aria-label="Ready For Robots">
          READY<span className="rfr-wordmark-for">FOR</span>ROBOTS
        </a>
        <nav aria-label="Footer">
          {FOOTER_LINKS.map((link) => (
            <a key={link.label} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
      </div>
    </footer>
  );
}
