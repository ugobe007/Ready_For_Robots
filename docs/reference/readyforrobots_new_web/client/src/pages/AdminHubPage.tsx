import SiteShell from "@/components/SiteShell";
import MarketingPageLayout from "@/components/MarketingPageLayout";
import { Link } from "wouter";

/**
 * Lightweight admin hub. Protected APIs still require an admin JWT (see partner workspace).
 */
export default function AdminHubPage() {
  return (
    <SiteShell>
      <MarketingPageLayout
        kicker="Internal"
        title="Admin"
        subtitle="Workspace administration and partner workspaces."
      >
        <div className="prose prose-gray max-w-none">
          <h3 className="text-lg font-bold text-gray-900 mt-0">Partners</h3>
          <ul className="list-disc pl-5 space-y-2 text-gray-800">
            <li>
              <Link href="/admin/partners/the-robot-guild" className="font-semibold text-emerald-800 hover:underline">
                The Robot Guild
              </Link>
              <span className="text-gray-600">
                {" "}
                — Robot-relevant trade shows, dates, and OEM hints scraped for partner GTM (
                <a
                  href="https://www.therobotguild.com/"
                  className="text-emerald-800 hover:underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  therobotguild.com
                </a>
                ).
              </span>
            </li>
          </ul>
          <p className="text-sm text-gray-600">
            Partner pages call <code className="text-xs bg-gray-100 px-1 rounded">/api/admin/…</code>. Paste your
            admin Bearer token once per browser session (stored only in <code className="text-xs">sessionStorage</code>
            ).
          </p>
        </div>
      </MarketingPageLayout>
    </SiteShell>
  );
}
