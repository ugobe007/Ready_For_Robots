import { PRIMARY_NAV } from "@/lib/siteNav";
import { Link } from "wouter";

export type HeaderProps = {
  activePage: string;
};

export default function Header({ activePage }: HeaderProps) {
  return (
    <header className="border-b border-blue-200 bg-sky-50/95 backdrop-blur-sm">
      <div className="mx-auto flex min-h-[3.5rem] min-w-0 max-w-[1400px] flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-2 sm:flex-nowrap sm:px-8">
        <Link href="/" className="flex min-w-0 max-w-full shrink-0 items-center gap-2 text-blue-900">
          <span
            className="flex h-8 w-8 items-center justify-center border-2 border-blue-800 bg-blue-800 text-xs font-bold text-white"
            aria-hidden
          >
            R
          </span>
          <span className="truncate text-sm font-semibold tracking-tight sm:max-w-[10rem] md:max-w-none">
            Ready For Robots
          </span>
        </Link>

        <nav className="hidden min-w-0 flex-1 flex-wrap items-center justify-center gap-1 md:flex md:justify-center" aria-label="Primary">
          {PRIMARY_NAV.map((item) => {
            const active = activePage === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-sm px-3 py-1.5 text-sm transition-colors ${
                  active
                    ? "border border-blue-800 bg-blue-800 text-white shadow-sm"
                    : "text-slate-600 hover:bg-sky-100 hover:text-blue-900"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex min-w-0 shrink-0 flex-wrap items-center justify-end gap-2 sm:gap-3">
          <Link
            href="/welcome"
            className="hidden text-sm text-blue-800/80 underline-offset-2 hover:text-blue-900 hover:underline sm:inline"
          >
            Marketing site
          </Link>
          <Link
            href="/profile"
            className="rounded-sm border border-blue-200 bg-white px-3 py-1.5 text-sm text-blue-900 hover:border-blue-400 hover:bg-sky-50"
          >
            Profile
          </Link>
        </div>
      </div>
    </header>
  );
}
