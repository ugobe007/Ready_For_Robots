import { FormEvent, useState } from "react";
import { SiteFooter, SiteHeader } from "@/components/editorial";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { usePageMeta } from "@/lib/pageMeta";

const FEATURES = [
  "Buyer matches for every robot you sell",
  "Why now for each buyer, with sources",
  "Every workflow at each buyer, including what’s already automated",
  "Save buyers and get alerts on new signals",
  "Your whole product line, matched one product at a time",
];

export default function Pricing() {
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [robotPage, setRobotPage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  usePageMeta({
    title: "Early access pricing — Ready For Robots",
    description:
      "Live buyer signals are rolling out one industry at a time. Use everything free until then.",
    path: "/pricing",
  });

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setDone(false);
    try {
      const res = await fetch(
        `${getApiBase()}/api/waitlist/founding-customer`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email.trim(),
            company: company.trim(),
            robot_page: robotPage.trim() || undefined,
          }),
        })
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        throw new Error(
          typeof detail === "string" ? detail : "Could not submit request"
        );
      }
      setDone(true);
      setEmail("");
      setCompany("");
      setRobotPage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit request");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rfr-editorial rfr-pricing">
      <SiteHeader />
      <section className="rfr-pricing-hero">
        <div className="rfr-eyebrow">Pricing</div>
        <h1>
          Early access.
          <br />
          Free while we build.
        </h1>
        <p>
          Live buyer signals are rolling out one industry at a time. Use
          everything free until then, and lock in founding pricing before
          launch.
        </p>
      </section>

      <section className="rfr-pricing-offer">
        <div className="rfr-pricing-plan">
          <span className="rfr-pricing-kicker">Founding customer</span>
          <div className="rfr-pricing-price">
            <span>$0</span>
            <span>during early access</span>
          </div>
          <ul>
            {FEATURES.map((line) => (
              <li key={line}>
                <span aria-hidden="true">+</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>
        <form onSubmit={submit}>
          <span className="rfr-pricing-form-title">Get early access</span>
          <label htmlFor="work-email">Work email</label>
          <input
            id="work-email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@company.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <label htmlFor="company">Company</label>
          <input
            id="company"
            type="text"
            required
            autoComplete="organization"
            placeholder="Your robot company"
            value={company}
            onChange={(event) => setCompany(event.target.value)}
          />
          <label htmlFor="robot-page">A robot you sell (product page)</label>
          <input
            id="robot-page"
            type="text"
            inputMode="url"
            placeholder="richtechrobotics.com/solutions/adam"
            value={robotPage}
            onChange={(event) => setRobotPage(event.target.value)}
          />
          <button type="submit" disabled={busy}>
            {busy ? "Sending…" : "Get early access →"}
          </button>
          {done ? (
            <p className="rfr-pricing-note" role="status">
              You’re on the list. We’ll email you when live buyers reach your
              industries.
            </p>
          ) : (
            <p className="rfr-pricing-note">
              No card needed. We’ll email you when live buyers reach your
              industries.
            </p>
          )}
          {error ? (
            <p className="rfr-pricing-error" role="alert">
              {error}
            </p>
          ) : null}
        </form>
      </section>

      <section className="rfr-pricing-lower" id="faq">
        <div>
          <h2>Questions</h2>
          <details>
            <summary>Where do buyer signals come from?</summary>
            <p>
              Public procurement notices, company filings and announcements,
              news, and automation hiring at buyer companies. Every signal
              links to its source.
            </p>
          </details>
          <details>
            <summary>Do you sell contact lists?</summary>
            <p>
              No. We show which companies are moving to automate, which work,
              and why now. Contacts come later, opt-in.
            </p>
          </details>
          <details>
            <summary>What does early access cost?</summary>
            <p>Nothing. Founding customers lock in their price before launch.</p>
          </details>
        </div>
        <div>
          <h2>Need a hand?</h2>
          <p>
            Setup, integration planning and installation through vetted local
            partners. Scoped separately from the software.
          </p>
          <a className="rfr-pricing-talk" href="/support">
            Talk to us →
          </a>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}
