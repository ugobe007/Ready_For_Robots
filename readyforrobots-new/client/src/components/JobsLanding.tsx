/**
 * `/` home. Search still opens FIND at `/?visit=jobs&url=`.
 * Example case files and the RichTech lineup are design copy, badged Example.
 */
import { useEffect, useState } from "react";
import {
  ExampleBadge,
  Eyebrow,
  SiteFooter,
  SiteHeader,
  TierLetter,
  UrlInput,
} from "@/components/editorial";
import { jobsFindHref } from "@/lib/jobsLanding";
import {
  CASE_ROTATE_MS,
  HOME_CASES,
  HOME_EXPLORE,
  HOME_INDUSTRIES,
  HOME_PRODUCTS,
  HOME_STEPS,
  HOME_TIERS,
  ReasonRow,
} from "@/lib/homeEditorial";

const HOME_NAV = [
  { label: "Find buyers", href: "#find" },
  { label: "How it works", href: "#how" },
  { label: "Explore", href: "#explore" },
  { label: "Pricing", href: "#early" },
  { label: "Sign in", href: "/login" },
];

function openSearch(url: string) {
  const trimmed = url.trim();
  if (!trimmed) return;
  window.location.href = jobsFindHref(trimmed);
}

export default function JobsLanding() {
  const [url, setUrl] = useState("");
  const [caseIndex, setCaseIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [productId, setProductId] = useState(HOME_PRODUCTS[0].id);
  const example = HOME_CASES[caseIndex];
  const product = HOME_PRODUCTS.find((item) => item.id === productId) ?? HOME_PRODUCTS[0];

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setPaused(true);
    }
  }, []);

  useEffect(() => {
    if (paused) return;
    const timer = window.setInterval(() => {
      setCaseIndex((current) => (current + 1) % HOME_CASES.length);
    }, CASE_ROTATE_MS);
    return () => window.clearInterval(timer);
  }, [paused]);

  return (
    <div className="rfr-editorial rfr-home">
      <SiteHeader links={HOME_NAV} ctaHref="#early" />
      <section id="find" className="rfr-home-wrap rfr-home-hero">
        <Eyebrow label="Jobs for robots" aside="The buyer index for robot sellers" />
        <h1>Find the companies ready to hire your robot.</h1>
        <div className="rfr-home-lead">
          <p>
            Paste your robot&apos;s product page. We find the companies moving to automate that work, and show you why now, with sources.
          </p>
          <div className="rfr-home-search">
            <UrlInput
              id="home-url"
              value={url}
              onChange={setUrl}
              onSubmit={openSearch}
              placeholder="richtechrobotics.com/solutions/adam"
            />
            <span className="rfr-home-hint">
              Whole product line? Paste your homepage and pick a product.
            </span>
          </div>
        </div>
        <div>
          <div className="rfr-case-bar">
            <div className="rfr-case-tabs" role="group" aria-label="Example robots">
              <span className="rfr-case-label">EXAMPLE CASE FILES</span>
              {HOME_CASES.map((item, index) => (
                <button
                  key={item.name}
                  type="button"
                  className="rfr-case-tab"
                  aria-pressed={index === caseIndex}
                  onClick={() => {
                    setCaseIndex(index);
                    setPaused(true);
                  }}
                >
                  {item.name}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="rfr-pause"
              aria-pressed={paused}
              aria-label={paused ? "Resume rotating examples" : "Pause rotating examples"}
              onClick={() => setPaused((current) => !current)}
            >
              {paused ? "PLAY" : "PAUSE"}
            </button>
          </div>
          <div className="rfr-case">
            <div className="rfr-case-robot">
              <div className="rfr-case-index">01 · THE ROBOT</div>
              <div>
                <span className="rfr-case-name">{example.name}</span>
                <span className="rfr-case-maker"> · {example.maker}</span>
              </div>
              <dl className="rfr-facts">
                <dt>FORM</dt>
                <dd>{example.form}</dd>
                <dt>MAIN WORK</dt>
                <dd>{example.work}</dd>
                <dt>BUYERS</dt>
                <dd>{example.buyers}</dd>
                <dt>NEVER</dt>
                <dd className="rfr-muted">{example.never}</dd>
              </dl>
            </div>
            <div className="rfr-case-buyer">
              <div className="rfr-buyer-head">
                <span className="rfr-case-index">02 · A BUYER, AND WHY NOW</span>
                <ExampleBadge />
              </div>
              <div className="rfr-buyer-title">
                <strong>{example.buyer}</strong>
                <span className="rfr-muted">{example.buyerMeta}</span>
              </div>
              {example.reasons.map((reason) => (
                <ReasonRow
                  key={reason.title}
                  mark="letter"
                  tier={reason.tier}
                  label={reason.tier}
                  title={reason.title}
                  source={reason.source}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="rfr-home-wrap" aria-labelledby="whynow">
        <div className="rfr-home-section-head">
          <h2 id="whynow">Every buyer comes with evidence.</h2>
          <p>
            Strongest evidence first, and every piece links to its source. Companies that already use robots for that work are skipped.
          </p>
        </div>
        <div className="rfr-tiers">
          {HOME_TIERS.map((tier) => (
            <article key={tier.tier} className="rfr-tier-card">
              <TierLetter tier={tier.tier} />
              <h3>{tier.name}</h3>
              <p>{tier.desc}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="rfr-home-wrap" aria-labelledby="lineup">
        <div className="rfr-home-section-head">
          <div>
            <div className="rfr-home-kicker">BY PRODUCT, NOT BY COMPANY</div>
            <h2 id="lineup">One maker. Eight robots. Eight kinds of buyers.</h2>
          </div>
          <p>
            Example classifications of Richtech Robotics&apos; lineup. Pick one to see where it fits.
          </p>
        </div>
        <div className="rfr-lineup">
          <div className="rfr-lineup-list">
            {HOME_PRODUCTS.map((item, index) => (
              <button
                key={item.id}
                type="button"
                className="rfr-lineup-item"
                aria-pressed={item.id === product.id}
                onClick={() => setProductId(item.id)}
              >
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{item.name}</strong>
                <span>{item.short}</span>
              </button>
            ))}
          </div>
          <div className="rfr-product-detail">
            <div className="rfr-buyer-head">
              <h3>{product.name}</h3>
              <ExampleBadge />
            </div>
            <p>{product.what}</p>
            <dl className="rfr-facts rfr-product-facts">
              <dt>FORM</dt>
              <dd>{product.form}</dd>
              <dt>WORK</dt>
              <dd>{product.work}</dd>
              <dt>MATCHES BUYERS IN</dt>
              <dd>
                <strong>{product.buyers}</strong>
              </dd>
              <dt>NEVER MATCHED TO</dt>
              <dd className="rfr-muted">{product.never}</dd>
            </dl>
            <a className="rfr-find-product" href={jobsFindHref(product.url)}>
              Find buyers for {product.name} →
            </a>
          </div>
        </div>
      </section>

      <section id="how" className="rfr-home-wrap" aria-labelledby="howh">
        <h2 id="howh" className="rfr-home-section-head">
          From your robot to the buyers who need it
        </h2>
        <div className="rfr-steps">
          {HOME_STEPS.map((step) => (
            <article key={step.n} className="rfr-step">
              <span className="rfr-step-num">{step.n}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
        <p className="rfr-job-note">
          A robot job is work a robot can perform at a company that is moving to automate it.
        </p>
      </section>

      <section className="rfr-home-wrap" aria-labelledby="indh">
        <div className="rfr-home-section-head">
          <h2 id="indh">Nine industries, in rollout order</h2>
          <p>Live buyer signals arrive one industry at a time, starting with warehouses and logistics.</p>
        </div>
        <div className="rfr-industries">
          {HOME_INDUSTRIES.map((name, index) => (
            <div key={name} className="rfr-industry">
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{name}</strong>
            </div>
          ))}
        </div>
      </section>

      <section id="explore" className="rfr-home-wrap" aria-labelledby="exph">
        <div className="rfr-home-section-head">
          <h2 id="exph">Go deeper on the robot market</h2>
          <p>Research and tools for robot sellers. Free to use.</p>
        </div>
        <div className="rfr-explore">
          {HOME_EXPLORE.map((item) => (
            <a key={item.kind} className="rfr-explore-card" href={item.href}>
              <em>{item.kind}</em>
              <strong>{item.title}</strong>
              <p>{item.body}</p>
              <span>{item.cta}</span>
            </a>
          ))}
        </div>
      </section>

      <section id="early" className="rfr-home-wrap rfr-early">
        <div className="rfr-early-band">
          <p>
            <em>PRICING</em>
            <strong>Buyers for your robots, ranked and kept up to date.</strong>
          </p>
          <a href="/pricing">See pricing →</a>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}
