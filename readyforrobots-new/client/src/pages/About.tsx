/**
 * /about — website_copy_v1.md §7. No stat tiles.
 */
import { Eyebrow, SiteFooter, SiteHeader } from "@/components/editorial";
import { usePageMeta } from "@/lib/pageMeta";

const BODY =
  "Ready For Robots helps robot makers and sellers find companies that are moving to automate work their robots can do. We classify robots product by product, track public signs that a company is about to automate (RFPs, pilots, budgets, expansion, automation hiring), and show sellers which company, which work, and why now.";

export default function About() {
  usePageMeta({
    title: "About — Ready For Robots",
    description: BODY,
    path: "/about",
  });

  return (
    <div className="rfr-editorial rfr-about">
      <SiteHeader />
      <main className="rfr-about-main">
        <Eyebrow label="About" />
        <h1>
          Robots need jobs.
          <br />
          We find the work.
        </h1>
        <p>{BODY}</p>
      </main>
      <SiteFooter />
    </div>
  );
}
