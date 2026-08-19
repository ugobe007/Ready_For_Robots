/**
 * Your robots — robot-centric CRM hub.
 * Saved buyer leads grouped by the robot (submission id) that sourced them:
 * "this robot → the buyers/deals I've collected for it".
 */
import { useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { loginHref } from "@/lib/authNext";

type Lead = {
  id: string;
  name: string;
  company_id: number | null;
  industry?: string | null;
  outreach_stage?: string | null;
  outreach_sent_at?: string | null;
  created_at?: string | null;
};

type RobotGroup = {
  robot_submission_id: number;
  robot: {
    id: number;
    company_name?: string | null;
    product_name?: string | null;
    website_domain: string;
    submitted_url: string;
    robot_class?: string | null;
    profile_tier?: string | null;
    capabilities: string[];
    submission_count: number;
    last_seen_at?: string | null;
  } | null;
  lead_count: number;
  stage_counts: Record<string, number>;
  leads: Lead[];
};

export default function MyRobots() {
  const { session } = useAuth();
  const [groups, setGroups] = useState<RobotGroup[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session?.access_token) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${getApiBase()}/api/crm/robots`,
          liveFetchInit({ headers: authHeader(session.access_token) }),
        );
        if (!res.ok) throw new Error(`robots ${res.status}`);
        const data = (await res.json()) as { robots: RobotGroup[] };
        if (!cancelled) setGroups(data.robots || []);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  return (
    <div className="min-h-screen bg-[#081126] text-slate-100">
      <Header />
      <main className="mx-auto max-w-4xl px-4 pt-24 pb-16">
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-400">
          Your robots
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">
          Robots &amp; the buyers you're collecting
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Each robot you research and pursue collects real buyer leads here. Open a
          lead to draft outreach and advance it in your pipeline.
        </p>

        {!session?.access_token ? (
          <div className="mt-10 rounded-2xl border border-slate-700/70 bg-[#0b162f]/85 p-8 text-center">
            <p className="text-sm text-slate-300">
              Sign in to see your robots and the buyers you've collected.
            </p>
            <Link
              href={loginHref("/my-robots")}
              className="mt-4 inline-block rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-semibold text-[#06261f] hover:bg-emerald-300"
            >
              Sign in
            </Link>
          </div>
        ) : error ? (
          <p className="mt-10 text-sm text-red-300">Could not load your robots ({error}).</p>
        ) : groups === null ? (
          <p className="mt-10 text-sm text-slate-400">Loading…</p>
        ) : groups.length === 0 ? (
          <div className="mt-10 rounded-2xl border border-slate-700/70 bg-[#0b162f]/85 p-8 text-center">
            <p className="text-sm text-slate-300">
              No collected leads yet. Research a robot, find buyers hiring for its
              work, and save the ones worth pursuing — they'll show up here grouped
              by robot.
            </p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-semibold text-[#06261f] hover:bg-emerald-300"
            >
              Research a robot →
            </Link>
          </div>
        ) : (
          <div className="mt-8 space-y-5">
            {groups.map(g => (
              <RobotCard key={g.robot_submission_id} group={g} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function RobotCard({ group }: { group: RobotGroup }) {
  const r = group.robot;
  const title = r?.product_name || r?.company_name || r?.website_domain || "Robot";
  const subtitle =
    r?.company_name && r.company_name !== title ? r.company_name : r?.website_domain;
  return (
    <section className="rounded-2xl border border-slate-700/70 bg-[#0b162f]/85 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="min-w-0">
          <h2 className="font-display text-xl font-bold text-slate-100">{title}</h2>
          {subtitle ? (
            <p className="text-xs text-slate-400">{subtitle}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-3 font-mono text-[11px] font-bold uppercase tracking-[0.12em]">
          {r?.profile_tier ? (
            <span className="text-slate-400">Profile {r.profile_tier}</span>
          ) : null}
          <span className="text-emerald-300">{group.lead_count} leads</span>
        </div>
      </div>

      {r?.capabilities?.length ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {r.capabilities.slice(0, 8).map(c => (
            <span
              key={c}
              className="rounded border border-slate-600 px-1.5 py-0.5 font-mono text-[10px] text-slate-300"
            >
              {c}
            </span>
          ))}
        </div>
      ) : null}

      <ul className="mt-4 divide-y divide-slate-700/70 border-t border-slate-700/70">
        {group.leads.map(l => (
          <li key={l.id} className="flex items-center justify-between gap-3 py-2.5">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-100">{l.name}</p>
              {l.industry ? (
                <p className="truncate text-xs text-slate-500">{l.industry}</p>
              ) : null}
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-slate-400">
                {(l.outreach_stage || "new").replace(/_/g, " ")}
              </span>
              {l.company_id ? (
                <Link
                  href={`/pipeline?company=${l.company_id}`}
                  className="font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300 hover:text-emerald-200"
                >
                  Open →
                </Link>
              ) : null}
            </div>
          </li>
        ))}
      </ul>

      {r?.submitted_url ? (
        <div className="mt-4">
          <Link
            href={`/pipeline?url=${encodeURIComponent(r.submitted_url)}&submission=${group.robot_submission_id}&src=my_robots`}
            className="font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-300 hover:text-emerald-300"
          >
            Find more buyers for {title} →
          </Link>
        </div>
      ) : null}
    </section>
  );
}
