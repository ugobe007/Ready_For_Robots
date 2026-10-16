import { useEffect, useMemo, useState } from "react";
import { useSearch } from "wouter";
import { ExampleBadge, SiteFooter, SiteHeader } from "@/components/editorial";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  fetchJobsCrmActivity,
  fetchKeptJobs,
  postJobsCrmActivity,
  type KeptJobRow,
} from "@/lib/jobsCrmAccount";
import { authHeader } from "@/lib/supabase";
import { usePageMeta } from "@/lib/pageMeta";

const COLUMNS = [
  { id: "saved", label: "Saved", hint: "Found and worth a look" },
  { id: "contacted", label: "Contacted", hint: "First outreach sent" },
  { id: "meeting", label: "Meeting", hint: "Call or demo booked" },
  {
    id: "site",
    label: "Site assessment",
    hint: "Walkthrough, layout, workflow fit",
  },
  { id: "pilot", label: "Pilot", hint: "Trial on site" },
  { id: "won", label: "Won", hint: "Signed" },
] as const;

type StageId = (typeof COLUMNS)[number]["id"] | "lost";

type Card = {
  id: string;
  jobKey: string;
  company: string;
  work: string;
  robot: string;
  tier?: string;
  next?: string;
  when?: string;
  stage: StageId;
  sample?: boolean;
};

const SAMPLE_CARDS: Card[] = [
  {
    id: "sample-cafe",
    jobKey: "sample-cafe",
    company: "Cafe chain",
    work: "Drink-making",
    robot: "ADAM",
    tier: "B",
    next: "Read capex plan",
    when: "No date",
    stage: "saved",
    sample: true,
  },
  {
    id: "sample-dc",
    jobKey: "sample-dc",
    company: "Regional distribution center",
    work: "Pallet transport",
    robot: "Pallet Jack",
    tier: "D",
    next: "Find ops lead",
    when: "No date",
    stage: "saved",
    sample: true,
  },
  {
    id: "sample-hotel",
    jobKey: "sample-hotel",
    company: "Hotel group",
    work: "Serving and bussing",
    robot: "Matradee Plus",
    tier: "C",
    next: "Follow up on intro email",
    when: "Due Tue",
    stage: "contacted",
    sample: true,
  },
  {
    id: "sample-3pl",
    jobKey: "sample-3pl",
    company: "Third-party logistics provider",
    work: "Material delivery",
    robot: "Titan",
    tier: "B",
    next: "Demo with site manager",
    when: "Thu 10:00",
    stage: "meeting",
    sample: true,
  },
  {
    id: "sample-resort",
    jobKey: "sample-resort",
    company: "Resort and casino group",
    work: "Drink-making",
    robot: "ADAM",
    tier: "A",
    next: "Answer RFP questions",
    when: "Overdue",
    stage: "site",
    sample: true,
  },
  {
    id: "sample-bar",
    jobKey: "sample-bar",
    company: "Sports bar group",
    work: "Drink-making",
    robot: "Scorpion",
    tier: "C",
    next: "Week 2 check-in",
    when: "Fri",
    stage: "pilot",
    sample: true,
  },
];

const TABS = ["Pipeline", "New signals", "My robots", "Alerts"] as const;
type Tab = (typeof TABS)[number];

function stageFromApplication(status?: string | null): StageId {
  const value = (status || "").toLowerCase();
  if (value === "success") return "won";
  if (value === "failed" || value === "declined") return "lost";
  if (value.startsWith("interview")) return "meeting";
  if (value === "applied") return "contacted";
  return "saved";
}

function isStage(value: string): value is StageId {
  return (
    value === "lost" || COLUMNS.some((column) => column.id === value)
  );
}

function cardFromJob(row: KeptJobRow, stage: StageId): Card {
  const job = row.job || {};
  const tier =
    typeof (job as { tier?: unknown }).tier === "string"
      ? String((job as { tier?: string }).tier)
      : undefined;
  return {
    id: row.id,
    jobKey: row.job_key,
    company: row.employer_name || "Buyer",
    work: row.work_title || "",
    robot: row.robot_name || "",
    tier: tier && /^[A-D]$/.test(tier) ? tier : undefined,
    stage,
  };
}

export default function Desk() {
  const { session } = useAuth();
  const search = useSearch();
  const params = new URLSearchParams(search);
  const openSettings =
    params.get("settings") === "hubspot" || params.get("connected") === "1";
  const [tab, setTab] = useState<Tab>("Pipeline");
  const [settings, setSettings] = useState(openSettings);
  const [showLost, setShowLost] = useState(false);
  const [robotFilter, setRobotFilter] = useState("All robots");
  const [cards, setCards] = useState<Card[]>(SAMPLE_CARDS);
  const [sample, setSample] = useState(true);
  const [robots, setRobots] = useState<
    { name: string; url?: string | null }[]
  >([]);
  const [hubspot, setHubspot] = useState<string>("");
  const [moveError, setMoveError] = useState("");

  usePageMeta({
    title: "My desk — Ready For Robots",
    description: "Saved buyers, from first look through a signed pilot.",
    path: "/desk",
  });

  useEffect(() => {
    setSettings(openSettings);
  }, [openSettings]);

  useEffect(() => {
    const token = session?.access_token;
    if (!token) {
      setCards(SAMPLE_CARDS);
      setSample(true);
      setRobots([]);
      setHubspot("");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [jobs, events] = await Promise.all([
          fetchKeptJobs(token),
          fetchJobsCrmActivity(token),
        ]);
        if (cancelled) return;
        if (!jobs.length) {
          setCards(SAMPLE_CARDS);
          setSample(true);
          return;
        }
        const stageByKey = new Map<string, StageId>();
        for (const event of events) {
          if (event.kind !== "desk_stage" || !event.jobKey) continue;
          if (stageByKey.has(event.jobKey)) continue;
          if (isStage(event.label)) stageByKey.set(event.jobKey, event.label);
        }
        setCards(
          jobs.map((row) =>
            cardFromJob(
              row,
              stageByKey.get(row.job_key) ||
                stageFromApplication(row.application?.status)
            )
          )
        );
        setSample(false);
      } catch {
        if (!cancelled) {
          setCards(SAMPLE_CARDS);
          setSample(true);
        }
      }
      try {
        const res = await fetch(
          `${getApiBase()}/api/crm/robots`,
          liveFetchInit({ headers: authHeader(token) })
        );
        if (!res.ok || cancelled) return;
        const data = (await res.json()) as {
          robots?: {
            robot?: {
              product_name?: string | null;
              company_name?: string | null;
              submitted_url?: string | null;
            } | null;
          }[];
        };
        if (cancelled) return;
        setRobots(
          (data.robots || [])
            .map((group) => ({
              name:
                group.robot?.product_name ||
                group.robot?.company_name ||
                "",
              url: group.robot?.submitted_url,
            }))
            .filter((robot) => robot.name)
        );
      } catch {
        if (!cancelled) setRobots([]);
      }
      try {
        const res = await fetch(
          `${getApiBase()}/api/integrations/hubspot/setup`,
          liveFetchInit({ headers: authHeader(token) })
        );
        if (!res.ok || cancelled) return;
        const data = (await res.json()) as {
          connection?: { connected?: boolean; account_name?: string | null };
        };
        if (cancelled) return;
        setHubspot(
          data.connection?.connected
            ? data.connection.account_name || "Connected"
            : ""
        );
      } catch {
        if (!cancelled) setHubspot("");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  const robotsInBoard = useMemo(() => {
    const names = new Set(cards.map((card) => card.robot).filter(Boolean));
    return ["All robots", ...names];
  }, [cards]);

  const visible = cards.filter((card) => {
    if (robotFilter !== "All robots" && card.robot !== robotFilter) return false;
    if (!showLost && card.stage === "lost") return false;
    if (showLost && card.stage !== "lost") return false;
    return true;
  });

  async function moveCard(id: string, stage: StageId) {
    const card = cards.find((row) => row.id === id);
    if (!card || card.stage === stage) return;
    setCards((current) =>
      current.map((row) => (row.id === id ? { ...row, stage } : row))
    );
    if (card.sample || !session?.access_token) return;
    setMoveError("");
    try {
      await postJobsCrmActivity(session.access_token, {
        kind: "desk_stage",
        label: stage,
        jobKey: card.jobKey,
        company: card.company,
      });
    } catch (err) {
      setMoveError(
        err instanceof Error ? err.message : "Could not save that move."
      );
    }
  }

  async function connectHubspot() {
    const token = session?.access_token;
    if (!token) {
      window.location.href = "/login?next=/desk?settings=hubspot";
      return;
    }
    const res = await fetch(
      `${getApiBase()}/api/integrations/hubspot/connect-url?return_to=/desk`,
      liveFetchInit({ headers: authHeader(token) })
    );
    const data = (await res.json().catch(() => ({}))) as { auth_url?: string };
    if (data.auth_url) window.location.href = data.auth_url;
  }

  const initials = (session?.user?.email || "RR").slice(0, 2).toUpperCase();

  return (
    <div className="rfr-editorial rfr-desk">
      <SiteHeader signedIn initials={initials} />
      <section className="rfr-desk-head">
        <div className="rfr-eyebrow">
          <span>My desk</span>
          {sample ? <ExampleBadge>Sample data</ExampleBadge> : null}
        </div>
        <div className="rfr-desk-title-row">
          <h1>{showLost ? "Lost" : tab}</h1>
          <div className="rfr-desk-tools">
            <label htmlFor="desk-robot">Robot</label>
            <select
              id="desk-robot"
              value={robotFilter}
              onChange={(event) => setRobotFilter(event.target.value)}
            >
              {robotsInBoard.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </select>
            <button type="button" onClick={() => setShowLost((on) => !on)}>
              {showLost ? "Show open stages" : "Lost"}
            </button>
            <button type="button" onClick={() => setSettings((on) => !on)}>
              {hubspot ? "HubSpot connected" : "Sync to HubSpot"}
            </button>
            <a href="/">+ Find buyers</a>
          </div>
        </div>
        <nav className="rfr-desk-tabs" aria-label="Desk sections">
          {TABS.map((name) => (
            <button
              key={name}
              type="button"
              aria-current={tab === name && !showLost ? "page" : undefined}
              onClick={() => {
                setTab(name);
                setShowLost(false);
              }}
            >
              {name}
            </button>
          ))}
        </nav>
      </section>

      {settings ? (
        <section className="rfr-desk-settings">
          <h2>Settings · HubSpot</h2>
          <p>
            {hubspot
              ? `Connected to ${hubspot}. Saved buyers stay on this desk.`
              : "Connect HubSpot to sync saved buyers. The connection uses your existing HubSpot account."}
          </p>
          <button type="button" onClick={() => void connectHubspot()}>
            {session ? "Connect HubSpot" : "Sign in to connect HubSpot"}
          </button>
        </section>
      ) : null}

      {tab === "Pipeline" || showLost ? (
        <section className="rfr-desk-board">
          {showLost ? (
            <LostList cards={visible} onMove={moveCard} />
          ) : (
            <div className="rfr-desk-columns">
              {COLUMNS.map((column) => (
                <div
                  key={column.id}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={(event) => {
                    event.preventDefault();
                    const id = event.dataTransfer.getData("text/plain");
                    if (id) void moveCard(id, column.id);
                  }}
                >
                  <div className="rfr-desk-column-head">
                    <span>{column.label}</span>
                    <span>
                      {visible.filter((card) => card.stage === column.id).length}
                    </span>
                  </div>
                  <p>{column.hint}</p>
                  {visible
                    .filter((card) => card.stage === column.id)
                    .map((card) => (
                      <BuyerCard
                        key={card.id}
                        card={card}
                        onMove={moveCard}
                      />
                    ))}
                </div>
              ))}
            </div>
          )}
          <p className="rfr-desk-note">
            Drag a card to move it. Lost buyers stay under the Lost filter.
          </p>
          {moveError ? (
            <p className="rfr-desk-error" role="alert">
              {moveError}
            </p>
          ) : null}
        </section>
      ) : null}

      {tab === "New signals" && !showLost ? (
        <section className="rfr-desk-panel">
          <p>
            {sample
              ? "Sample only. New signals show up here once a saved buyer has a sourced update."
              : "No new signals on your saved buyers."}
          </p>
        </section>
      ) : null}

      {tab === "My robots" && !showLost ? (
        <section className="rfr-desk-panel">
          {robots.length ? (
            <ul>
              {robots.map((robot) => (
                <li key={robot.name}>
                  {robot.url ? (
                    <a href={robot.url}>{robot.name}</a>
                  ) : (
                    robot.name
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>
              {sample
                ? "Sample board only. Your robots appear here after you save a buyer from a search."
                : "No robots on this desk yet."}
            </p>
          )}
        </section>
      ) : null}

      {tab === "Alerts" && !showLost ? (
        <section className="rfr-desk-panel">
          <p>
            {sample
              ? "Sample only. Alerts turn on when a saved buyer gets a new signal."
              : "No alerts yet."}
          </p>
        </section>
      ) : null}

      <SiteFooter />
    </div>
  );
}

function BuyerCard({
  card,
  onMove,
}: {
  card: Card;
  onMove: (id: string, stage: StageId) => void;
}) {
  return (
    <article
      className={card.tier === "A" ? "rfr-desk-card is-a" : "rfr-desk-card"}
      draggable
      onDragStart={(event) =>
        event.dataTransfer.setData("text/plain", card.id)
      }
    >
      <div>
        <strong>{card.company}</strong>
        {card.tier ? <span className="rfr-desk-tier">{card.tier}</span> : null}
      </div>
      <p>
        {[card.work, card.robot].filter(Boolean).join(" · ")}
      </p>
      {card.next ? (
        <p>
          <span>Next</span> {card.next}
        </p>
      ) : null}
      {card.when ? <p className="rfr-desk-when">{card.when}</p> : null}
      <label className="rfr-desk-move">
        Move
        <select
          value={card.stage}
          onChange={(event) => onMove(card.id, event.target.value as StageId)}
        >
          {COLUMNS.map((column) => (
            <option key={column.id} value={column.id}>
              {column.label}
            </option>
          ))}
          <option value="lost">Lost</option>
        </select>
      </label>
    </article>
  );
}

function LostList({
  cards,
  onMove,
}: {
  cards: Card[];
  onMove: (id: string, stage: StageId) => void;
}) {
  if (!cards.length) {
    return <p className="rfr-desk-note">No lost buyers.</p>;
  }
  return (
    <div className="rfr-desk-lost">
      {cards.map((card) => (
        <BuyerCard key={card.id} card={card} onMove={onMove} />
      ))}
    </div>
  );
}
