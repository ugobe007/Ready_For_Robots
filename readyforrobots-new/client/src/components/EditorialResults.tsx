/**
 * Buyers for one robot, the product picker, or an unrecognized page.
 * Data is the robot-job-search payload. Slots the payload does not fill
 * (tier, why-now, form, siblings, committed workflows) stay off the page.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  ExampleBadge,
  SiteFooter,
  SiteHeader,
  UrlInput,
} from "@/components/editorial";
import { buyerSearchView } from "@/lib/buyerSearch";
import { jobsFindHref } from "@/lib/jobsLanding";
import { fetchRobotJobSearch } from "@/lib/robotJobSearch";

const SEARCH_TIMEOUT_MS = 45_000;

const RESULTS_NAV = [
  { label: "Find buyers", href: "/" },
  { label: "How it works", href: "/#how" },
  { label: "Explore", href: "/#explore" },
  { label: "Pricing", href: "/pricing" },
  { label: "Sign in", href: "/login" },
];

type BuyerReason = { title?: string; tier?: string };
type BuyerJob = {
  job_key?: string;
  title?: string;
  industry?: string;
  company_name?: string | null;
  locality?: string | null;
  is_example?: boolean;
  top_tier?: string | null;
  reasons?: BuyerReason[] | null;
};
type BuyerProduct = {
  name?: string;
  display_class?: string | null;
  description?: string | null;
  product_url?: string | null;
  form?: string | null;
};
type BuyerPick = { name: string; url: string };
type BuyerPayload = {
  state?: string;
  robot_name?: string;
  company_name?: string | null;
  capabilities?: { label?: string }[];
  jobs?: BuyerJob[];
  products?: BuyerProduct[];
  needs_product_choice?: boolean;
  zero_reason?: string | null;
  source_url?: string | null;
};

function pickHref(source: string, pick: BuyerPick): string {
  if (pick.url) return jobsFindHref(pick.url);
  if (!source || !pick.name) return jobsFindHref();
  return `${jobsFindHref(source)}&product=${encodeURIComponent(pick.name)}`;
}

function hostLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function mainWork(payload: BuyerPayload): string {
  const label = payload.capabilities?.find((item) => item.label?.trim())?.label?.trim();
  return label || "";
}

function TierMark({ tier }: { tier: string }) {
  return <span className="rfr-result-tier">{tier}</span>;
}

function BuyerRows({ payload }: { payload: BuyerPayload }) {
  const jobs = payload.jobs || [];
  const industries = useMemo(() => {
    const seen = new Set<string>();
    for (const job of jobs) {
      const industry = (job.industry || "").trim();
      if (industry) seen.add(industry);
    }
    return [...seen];
  }, [jobs]);
  const [industry, setIndustry] = useState("all");
  const shown = jobs.filter(
    (job) => industry === "all" || (job.industry || "").trim() === industry
  );
  const anyExample = shown.some((job) => job.is_example);
  const allExample = shown.length > 0 && shown.every((job) => job.is_example);
  const anyTier = shown.some((job) => (job.top_tier || "").trim());
  const anyReasons = shown.some((job) => (job.reasons || []).some((reason) => reason.title?.trim()));
  const work = mainWork(payload);
  const name = payload.robot_name || "This robot";
  const maker = (payload.company_name || "").trim();

  return (
    <>
      <section className="rfr-home-wrap rfr-result-hero">
        <div className="rfr-result-kicker">
          <span>BUYERS FOR</span>
          <a href="/">CHANGE ROBOT ↺</a>
        </div>
        <div className="rfr-result-title">
          <h1>{name}</h1>
          {(maker || work) && (
            <dl className="rfr-result-facts">
              {maker ? (
                <>
                  <dt>MAKER</dt>
                  <dd>{maker}</dd>
                </>
              ) : null}
              {work ? (
                <>
                  <dt>MAIN WORK</dt>
                  <dd>{work}</dd>
                </>
              ) : null}
            </dl>
          )}
        </div>
        {anyExample ? (
          <div className="rfr-result-early">
            <span>EARLY ACCESS</span>
            <p>
              Cards marked <strong>Example</strong> show the kind of work {name} matches.
              Live buyers with sources are rolling out industry by industry, starting with warehouses and logistics.
            </p>
          </div>
        ) : null}
      </section>
      <section className="rfr-home-wrap rfr-result-layout">
        <div>
          {industries.length > 0 ? (
            <div className="rfr-result-filters" role="group" aria-label="Industry">
              <button type="button" aria-pressed={industry === "all"} onClick={() => setIndustry("all")}>
                All matching
              </button>
              {industries.map((item) => (
                <button
                  key={item}
                  type="button"
                  aria-pressed={industry === item}
                  onClick={() => setIndustry(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          ) : null}
          <div className="rfr-result-count">
            <span>
              {shown.length} {allExample ? "EXAMPLE " : ""}
              {shown.length === 1 ? "BUYER" : "BUYERS"}
            </span>
            {anyTier || anyReasons ? <span>TIER · WHY NOW</span> : null}
          </div>
          {shown.length === 0 ? (
            <p className="rfr-result-empty">No buyers in the index for this robot yet.</p>
          ) : (
            shown.map((job, index) => {
              const tier = (job.top_tier || "").trim();
              const reasons = (job.reasons || []).filter((reason) => reason.title?.trim()).slice(0, 3);
              const place = [job.locality, job.industry].filter(Boolean).join(" · ");
              return (
                <article key={job.job_key || `${job.title}-${index}`} className="rfr-result-row">
                  {tier ? <TierMark tier={tier} /> : null}
                  <div>
                    <div className="rfr-result-buyer">
                      <strong>{job.company_name || "Buyer"}</strong>
                      {job.is_example ? <ExampleBadge /> : null}
                    </div>
                    {place ? <span className="rfr-muted">{place}</span> : null}
                    {job.title ? (
                      <span>
                        <strong>{job.title}</strong>
                      </span>
                    ) : null}
                  </div>
                  {reasons.length > 0 ? (
                    <div className="rfr-result-reasons">
                      {reasons.map((reason) => (
                        <div key={reason.title}>
                          {reason.tier ? <span>{reason.tier}</span> : null}
                          <span>{reason.title}</span>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </article>
              );
            })
          )}
          <div className="rfr-result-save">
            <span>Save this robot to get new buyers as signals arrive.</span>
            <a href="/login">Save buyers{payload.robot_name ? ` for ${payload.robot_name}` : ""}</a>
          </div>
        </div>
        {work || industries.length > 0 ? (
          <aside aria-label="About this robot">
            <span>HOW WE MATCHED {(payload.robot_name || "").toUpperCase()}</span>
            {work ? <p>Main work on this page: {work}.</p> : null}
            {industries.length > 0 ? (
              <p>Buyers in this list are in {industries.join(", ")}.</p>
            ) : null}
          </aside>
        ) : null}
      </section>
    </>
  );
}

function Picker({
  payload,
  onSearch,
}: {
  payload: BuyerPayload;
  onSearch: (source: string, picks: BuyerPick[]) => void;
}) {
  const products = (payload.products || []).filter((item) => item.name);
  const showClass = products.some((item) => (item.form || item.display_class || "").trim());
  const showAbout = products.some((item) => (item.description || "").trim());
  const submitted = payload.source_url || "";
  const picks = products.map((product) => ({
    name: product.name || "",
    url: product.product_url || "",
  }));
  const [picked, setPicked] = useState<string[]>(() => (picks[0] ? [picks[0].name] : []));
  const count = picked.length;
  const columns = ["44px", "minmax(0, 1.1fr)"];
  if (showClass) columns.push("minmax(0, 0.7fr)");
  if (showAbout) columns.push("minmax(0, 1.8fr)");
  columns.push("140px");
  const grid = { gridTemplateColumns: columns.join(" ") };

  function toggle(name: string) {
    setPicked((current) =>
      current.includes(name) ? current.filter((item) => item !== name) : [...current, name]
    );
  }

  return (
    <section className="rfr-home-wrap rfr-picker">
      <div className="rfr-result-kicker">
        <span>{submitted ? hostLabel(submitted).toUpperCase() : "PRODUCT PAGES"}</span>
        <a href="/">TRY ANOTHER URL ↺</a>
      </div>
      <h1>
        We found {products.length} {products.length === 1 ? "robot" : "robots"}. Pick the one to sell.
      </h1>
      <p>Each robot does different work for different buyers, so we match them one at a time.</p>
      <div className="rfr-picker-table" role="table">
        <div className="rfr-picker-row rfr-picker-head" role="row" style={grid}>
          <span>PICK</span>
          <span>PRODUCT</span>
          {showClass ? <span>CLASS</span> : null}
          {showAbout ? <span>DESCRIPTION</span> : null}
          <span />
        </div>
        {products.map((product) => {
          const name = product.name || "";
          const id = `pick-${name}`;
          const href = pickHref(submitted, { name, url: product.product_url || "" });
          return (
            <div key={name} className="rfr-picker-row" role="row" style={grid}>
              <input
                id={id}
                type="checkbox"
                aria-label={`Pick ${name}`}
                checked={picked.includes(name)}
                onChange={() => toggle(name)}
              />
              <label htmlFor={id}>{name}</label>
              {showClass ? <span>{product.form || product.display_class || ""}</span> : null}
              {showAbout ? <span>{product.description || ""}</span> : null}
              <a href={href}>FIND BUYERS →</a>
            </div>
          );
        })}
      </div>
      <div className="rfr-picker-actions">
        <span>
          Wrong? Open a product and <a href="mailto:support@readyforrobots.com">tell us</a>.
        </span>
        <button
          type="button"
          disabled={count === 0}
          onClick={() =>
            onSearch(
              submitted,
              picks.filter((item) => picked.includes(item.name))
            )
          }
        >
          Find buyers for {count} {count === 1 ? "robot" : "robots"} →
        </button>
      </div>
    </section>
  );
}

function Unrecognized() {
  return (
    <section className="rfr-home-wrap rfr-unrecognized">
      <h1>We could not tell which robot this page is selling.</h1>
      <p>There are no buyers to show, and we did not substitute another robot.</p>
      <a href="/">Try a product page</a>
    </section>
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="rfr-editorial rfr-home">
      <SiteHeader links={RESULTS_NAV} ctaHref="/pricing" />
      {children}
      <SiteFooter />
    </div>
  );
}

export default function EditorialResults() {
  const initial = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return {
      url: (params.get("url") || "").trim(),
      product: (params.get("product") || "").trim(),
    };
  }, []);
  const initialUrl = initial.url;
  const [url, setUrl] = useState("");
  const [payload, setPayload] = useState<BuyerPayload | null>(null);
  const [stack, setStack] = useState<BuyerPayload[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(Boolean(initialUrl));

  useEffect(() => {
    if (!initialUrl) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetchRobotJobSearch({
      url: initialUrl,
      product: initial.product || undefined,
      lookupGrain: "product",
      signal: controller.signal,
      timeoutMs: SEARCH_TIMEOUT_MS,
    })
      .then((result) => {
        setPayload(result as BuyerPayload);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Could not load buyers.");
        setLoading(false);
      });
    return () => controller.abort();
  }, [initialUrl, initial.product]);

  function openSearch(next: string) {
    const trimmed = next.trim();
    if (!trimmed) return;
    window.location.href = jobsFindHref(trimmed);
  }

  function searchMany(source: string, picks: BuyerPick[]) {
    if (picks.length === 1) {
      window.location.href = pickHref(source, picks[0]);
      return;
    }
    setLoading(true);
    setError("");
    setStack(null);
    Promise.all(
      picks.map((item) =>
        fetchRobotJobSearch({
          url: item.url || source,
          product: item.url ? undefined : item.name,
          lookupGrain: "product",
          timeoutMs: SEARCH_TIMEOUT_MS,
        }).then((result) => result as BuyerPayload)
      )
    )
      .then((found) => setStack(found))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Could not load buyers.");
      })
      .finally(() => setLoading(false));
  }

  let body: ReactNode;
  if (loading) {
    body = <p className="rfr-home-wrap rfr-result-status">Reading the product page.</p>;
  } else if (error) {
    body = (
      <section className="rfr-home-wrap rfr-unrecognized">
        <h1>Could not load buyers.</h1>
        <p>{error}</p>
        <a href="/">Try a product page</a>
      </section>
    );
  } else if (stack) {
    body = stack.map((item, index) => {
      const view = buyerSearchView(item);
      return (
        <div key={item.source_url || index}>
          {view === "picker" ? (
            <Picker payload={item} onSearch={searchMany} />
          ) : view === "unrecognized" ? (
            <Unrecognized />
          ) : (
            <BuyerRows payload={item} />
          )}
        </div>
      );
    });
  } else if (!initialUrl || !payload) {
    body = (
      <section className="rfr-home-wrap rfr-unrecognized">
        <h1>Paste a product page.</h1>
        <UrlInput value={url} onChange={setUrl} onSubmit={openSearch} />
      </section>
    );
  } else if (buyerSearchView(payload) === "picker") {
    body = <Picker payload={payload} onSearch={searchMany} />;
  } else if (buyerSearchView(payload) === "unrecognized") {
    body = <Unrecognized />;
  } else {
    body = <BuyerRows payload={payload} />;
  }

  return <Shell>{body}</Shell>;
}
