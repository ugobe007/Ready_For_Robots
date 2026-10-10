/**
 * Icon catalog for Jobs pages. Import `SiteIcon` by id — do not copy maps.
 * Visit: /icons
 */
import ExperimentHeader from "@/components/ExperimentHeader";
import PixelIcon from "@/components/PixelIcon";
import SiteIcon from "@/components/SiteIcon";
import { FACE_EMERALD, KARE_FACE, KARE_GRIPPER } from "@/lib/kareIcons";
import {
  SITE_ICON_CATALOG,
  SITE_ICON_FILL,
  SITE_ICON_NAVY,
} from "@/lib/siteIcons";
import { jobsFindHref } from "@/lib/jobsLanding";

export default function Icons() {
  return (
    <div className="jobs-page min-h-screen bg-[#0A0F1E] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto max-w-5xl px-4 pb-16 pt-20 sm:px-6">
        <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-emerald-400">
          ReadyForRobots · Icons
        </p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-[#F4EFE4]">
          Icons for Jobs pages
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          Twenty pixel marks. Import <code>SiteIcon</code> by id on landing,
          FIND, MATCH, About, and CRM — do not copy the bitmaps.
        </p>
        <pre className="mt-4 overflow-x-auto border border-emerald-500/30 bg-[#081126] px-3 py-3 font-mono text-[12px] text-emerald-100">
          {`import SiteIcon, { WorkClassIcon } from "@/components/SiteIcon";
<SiteIcon id="handshake" scale={2} />
<WorkClassIcon classId="healthcare" />`}
        </pre>
        <p className="mt-3 text-sm text-slate-500">
          Matcher stays <code>POST /api/robot-job-match</code>. This page is
          chrome.
        </p>

        <section className="mt-10" aria-label="Jobs icon catalog">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Catalog
          </h2>
          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-5">
            {SITE_ICON_CATALOG.map(entry => (
              <article
                key={entry.id}
                className="border border-emerald-500/40 bg-[#081126] p-3"
              >
                <div
                  className="flex items-center justify-center border border-emerald-400/80 p-3"
                  style={{ background: SITE_ICON_NAVY }}
                >
                  <SiteIcon
                    id={entry.id}
                    scale={3}
                    fill={SITE_ICON_FILL}
                    background="transparent"
                  />
                </div>
                <p className="mt-3 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300">
                  {entry.id}
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-100">
                  {entry.label}
                </p>
                <p className="mt-1 text-[12px] leading-snug text-slate-500">
                  {entry.use}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-12" aria-label="Kare face mark">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Wordmark face (existing)
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Header and landing hero stay <code>KARE_FACE</code>. Do not replace
            that with the sheet face.
          </p>
          <div className="mt-4 flex flex-wrap gap-8">
            <PixelIcon
              map={KARE_FACE}
              scale={6}
              fill={FACE_EMERALD}
              background="transparent"
              label="KARE_FACE"
            />
            <PixelIcon
              map={KARE_GRIPPER}
              scale={6}
              fill={FACE_EMERALD}
              background="transparent"
              label="KARE_GRIPPER"
            />
          </div>
        </section>

        <p className="mt-12 text-sm text-slate-500">
          <a href={jobsFindHref()} className="text-emerald-400 hover:underline">
            Find jobs →
          </a>
          {" · "}
          <a href="/" className="text-emerald-400 hover:underline">
            Landing
          </a>
          {" · "}
          <a href="/icon-review" className="text-emerald-400 hover:underline">
            Kare face review
          </a>
        </p>
      </main>
    </div>
  );
}
