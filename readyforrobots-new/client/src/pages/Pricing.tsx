/**
 * Pricing — two audiences. Founding seller and Pro check out through Stripe.
 */
import { useEffect, useState } from "react";
import { SiteFooter, SiteHeader } from "@/components/editorial";
import { useAuth } from "@/contexts/AuthContext";
import {
  fetchBillingConfig,
  startCheckout,
  type CheckoutTier,
} from "@/lib/billing";
import { DISCLOSURE } from "@/lib/disclosure";
import { usePageMeta } from "@/lib/pageMeta";


const SELLER_PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "",
    marked: false,
    note: "",
    lines: ["1 robot", "Top 3 opportunities, with reasons"],
    href: "/?visit=jobs",
    cta: "Find buyers",
  },
  {
    name: "Founding seller",
    price: "$49",
    period: "/month",
    marked: true,
    note: "Buyers for your robots, ranked and kept up to date.",
    lines: [
      "Up to 5 robots",
      "Full ranked list",
      "Live RFP alerts",
      "The desk",
    ],
    href: "",
    cta: "Become a founding seller",
    tier: "founding",
    lock: "This price stays while you are subscribed.",
  },
  {
    name: "Pro",
    price: "$199",
    period: "/month",
    marked: false,
    note: "",
    lines: ["More robots and users", "Deployment help"],
    href: "",
    cta: "Choose Pro",
    tier: "seller_pro",
    disclosure: true,
  },
] as const;

function CheckoutButton({
  tier,
  label,
  checkoutTiers,
}: {
  tier: CheckoutTier;
  label: string;
  checkoutTiers: string[] | null;
}) {
  const { session } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!session) {
    return (
      <a className="rfr-pricing-go" href="/signup?next=%2Fpricing">
        {label} →
      </a>
    );
  }
  const open = checkoutTiers?.includes(tier) ?? false;
  return (
    <>
      <button
        type="button"
        className="rfr-pricing-go"
        disabled={!open || busy}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            window.location.href = await startCheckout(
              session.access_token,
              tier
            );
          } catch (err) {
            setError(err instanceof Error ? err.message : "Checkout failed.");
            setBusy(false);
          }
        }}
      >
        {busy ? "Opening checkout…" : `${label} →`}
      </button>
      {checkoutTiers && !open ? (
        <p className="rfr-pricing-pending">Checkout opens after testing.</p>
      ) : null}
      {error ? (
        <p className="rfr-pricing-pending" role="alert">
          {error}
        </p>
      ) : null}
    </>
  );
}

export default function Pricing() {
  const [checkoutTiers, setCheckoutTiers] = useState<string[] | null>(null);
  useEffect(() => {
    let live = true;
    fetchBillingConfig()
      .then(config => live && setCheckoutTiers(config.checkout_tiers ?? []))
      .catch(() => live && setCheckoutTiers([]));
    return () => {
      live = false;
    };
  }, []);
  usePageMeta({
    title: "Pricing — Ready For Robots",
    description:
      "Sellers get buyers for their robots. Employers post a robot job free, and can publish an RFP when they need qualified sellers.",
    path: "/pricing",
  });

  return (
    <div className="rfr-editorial rfr-pricing">
      <SiteHeader />
      <section className="rfr-pricing-hero">
        <div className="rfr-eyebrow">Pricing</div>
        <h1>Sellers and employers.</h1>
        <p>
          Robot sellers see which companies are ready to buy. Robot employers
          post the work. Posting a job does not require a paid plan.
        </p>
      </section>

      <div className="rfr-pricing-audiences">
        <section className="rfr-pricing-audience" aria-labelledby="seller-plans">
          <h2 id="seller-plans">Robot sellers</h2>
          <p>Find companies moving to automate work your robot can do.</p>
          <div className="rfr-pricing-grid">
            {SELLER_PLANS.map(plan => (
              <article
                key={plan.name}
                className={
                  plan.marked
                    ? "rfr-pricing-card is-founding"
                    : "rfr-pricing-card"
                }
              >
                <span className="rfr-pricing-kicker">{plan.name}</span>
                <div className="rfr-pricing-price">
                  <span>{plan.price}</span>
                  {plan.period ? <span>{plan.period}</span> : null}
                </div>
                {"lock" in plan && plan.lock ? (
                  <p className="rfr-pricing-lock">{plan.lock}</p>
                ) : null}
                {plan.note ? (
                  <p className="rfr-pricing-plan-note">{plan.note}</p>
                ) : null}
                <ul>
                  {plan.lines.map(line => (
                    <li key={line}>
                      <span aria-hidden="true">+</span>
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
                {"disclosure" in plan && plan.disclosure ? (
                  <p className="rfr-pricing-disclosure">{DISCLOSURE}</p>
                ) : null}
                {"tier" in plan ? (
                  <CheckoutButton
                    tier={plan.tier}
                    label={plan.cta}
                    checkoutTiers={checkoutTiers}
                  />
                ) : (
                  <a className="rfr-pricing-go" href={plan.href}>
                    {plan.cta} →
                  </a>
                )}
              </article>
            ))}
          </div>
        </section>

        <section
          className="rfr-pricing-audience"
          aria-labelledby="employer-plans"
        >
          <h2 id="employer-plans">Robot employers</h2>
          <p>Posting a robot job is free. It never requires a paid plan.</p>
          <div className="rfr-pricing-grid is-two">
            <article className="rfr-pricing-card">
              <span className="rfr-pricing-kicker">Free</span>
              <div className="rfr-pricing-price">
                <span>$0</span>
              </div>
              <ul>
                <li>
                  <span aria-hidden="true">+</span>
                  <span>Post a robot job</span>
                </li>
              </ul>
              <a className="rfr-pricing-go" href="/?visit=candidates">
                Post a robot job →
              </a>
            </article>
            <article className="rfr-pricing-card">
              <span className="rfr-pricing-kicker">RFP</span>
              <div className="rfr-pricing-price">
                <span>$149</span>
                <span>/month</span>
              </div>
              <ul>
                <li>
                  <span aria-hidden="true">+</span>
                  <span>Publish an RFP</span>
                </li>
                <li>
                  <span aria-hidden="true">+</span>
                  <span>
                    Qualified sellers, with evidence
                    <ul className="rfr-pricing-evidence">
                      <li>Match score</li>
                      <li>Deployments in this workflow</li>
                      <li>Runtime and setting fit</li>
                      <li>Service coverage</li>
                    </ul>
                  </span>
                </li>
              </ul>
              <p className="rfr-pricing-pending">Checkout is not open.</p>
            </article>
          </div>
        </section>
      </div>

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
            <summary>Does posting a job require a paid plan?</summary>
            <p>
              No. Posting a robot job is free. The RFP plan is for publishing
              an RFP and seeing qualified sellers.
            </p>
          </details>
        </div>
        <div>
          <h2>Need a hand?</h2>
          <p>
            Setup, integration planning and installation through vetted local
            partners. Scoped separately from the software.
          </p>
          <p className="rfr-pricing-disclosure">{DISCLOSURE}</p>
          <a className="rfr-pricing-talk" href="/support">
            Talk to us →
          </a>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}
