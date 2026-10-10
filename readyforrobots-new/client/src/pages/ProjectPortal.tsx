import { useEffect, useMemo, useState } from "react";
import { useRoute } from "wouter";
import {
  Activity,
  Building2,
  CheckCircle2,
  Loader2,
  Rocket,
} from "lucide-react";
import { getPublicReadApiBase } from "@/lib/apiBase";

type PortalUpdate = {
  id: string;
  title: string;
  body?: string | null;
  category: string;
  created_at?: string | null;
};

type PortalData = {
  name: string;
  company_website?: string | null;
  robot_description?: string | null;
  summary?: string | null;
  status: string;
  metrics: Record<string, unknown>;
  funnel: Array<{ stage: string; count: number }>;
  accounts?: Array<{
    company: string;
    segment?: string | null;
    best_fit_task?: string | null;
    stage: string;
    contacted: boolean;
  }>;
  updated_at?: string | null;
  updates: PortalUpdate[];
};

const CATEGORY_STYLES: Record<string, string> = {
  milestone: "bg-emerald-100 text-emerald-700",
  stat: "bg-blue-100 text-blue-700",
  outreach: "bg-indigo-100 text-indigo-700",
  note: "bg-slate-100 text-slate-600",
};

function humanize(label: string): string {
  return label.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

export default function ProjectPortal() {
  const [, params] = useRoute("/p/:token");
  const token = params?.token || "";
  const api = getPublicReadApiBase();
  const [data, setData] = useState<PortalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let active = true;
    if (!token) {
      setLoading(false);
      setNotFound(true);
      return;
    }
    (async () => {
      try {
        const res = await fetch(`${api}/api/special-projects/portal/${token}`, {
          cache: "no-store",
        });
        if (!active) return;
        if (res.status === 404) {
          setNotFound(true);
          return;
        }
        if (!res.ok) throw new Error(String(res.status));
        setData((await res.json()) as PortalData);
      } catch {
        if (active) setNotFound(true);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [api, token]);

  const maxFunnel = useMemo(
    () => Math.max(1, ...(data?.funnel || []).map(f => f.count)),
    [data]
  );
  const metricEntries = useMemo(
    () => Object.entries(data?.metrics || {}),
    [data]
  );

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-300">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (notFound || !data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-6 text-center text-slate-300">
        <Rocket className="mb-4 h-10 w-10 text-slate-600" />
        <h1 className="text-xl font-semibold text-white">Portal not found</h1>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          This link is invalid or has been rotated. Please check with your Ready
          For Robots contact for an updated link.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-4xl px-5 py-12 sm:px-8">
        {/* Header */}
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-indigo-400">
          <Rocket className="h-3.5 w-3.5" /> Ready For Robots · Cal workspace
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-bold text-white">{data.name}</h1>
          <span className="rounded-full border border-indigo-500/40 bg-indigo-500/10 px-3 py-1 text-xs font-medium capitalize text-indigo-300">
            {data.status}
          </span>
        </div>
        {data.summary && (
          <p className="mt-3 max-w-2xl text-slate-300">{data.summary}</p>
        )}
        {data.robot_description && (
          <p className="mt-1 max-w-2xl text-sm text-slate-400">
            {data.robot_description}
          </p>
        )}
        {data.updated_at && (
          <p className="mt-3 text-xs text-slate-500">
            Last updated {new Date(data.updated_at).toLocaleString()}
          </p>
        )}

        {/* KPI cards */}
        {metricEntries.length > 0 && (
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {metricEntries.map(([key, value]) => (
              <div
                key={key}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-4"
              >
                <div className="text-2xl font-bold text-white">
                  {String(value)}
                </div>
                <div className="mt-1 text-xs uppercase tracking-wide text-slate-400">
                  {humanize(key)}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Funnel */}
        {data.funnel.length > 0 && (
          <div className="mt-8 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
              <Activity className="h-4 w-4 text-indigo-400" /> Pipeline progress
            </h2>
            <div className="space-y-2.5">
              {data.funnel.map(f => (
                <div key={f.stage} className="flex items-center gap-3">
                  <div className="w-28 shrink-0 text-xs capitalize text-slate-400">
                    {f.stage.replace("_", " ")}
                  </div>
                  <div className="h-6 flex-1 overflow-hidden rounded-md bg-slate-800">
                    <div
                      className="flex h-full items-center justify-end rounded-md bg-gradient-to-r from-indigo-600 to-indigo-400 px-2 text-[11px] font-semibold text-white"
                      style={{
                        width: `${Math.max(6, (f.count / maxFunnel) * 100)}%`,
                      }}
                    >
                      {f.count}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Accounts in motion */}
        {data.accounts && data.accounts.length > 0 && (
          <div className="mt-8 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
              <Building2 className="h-4 w-4 text-indigo-400" /> Accounts Cal is
              working ({data.accounts.length})
            </h2>
            <div className="grid gap-2 sm:grid-cols-2">
              {data.accounts.map(a => (
                <div
                  key={a.company}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-white">
                      {a.company}
                    </div>
                    {a.best_fit_task && (
                      <div className="truncate text-[11px] text-slate-500">
                        {a.best_fit_task}
                      </div>
                    )}
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                      a.contacted
                        ? "bg-indigo-500/15 text-indigo-300"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {a.stage.replace("_", " ")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Updates timeline */}
        <div className="mt-8">
          <h2 className="mb-4 text-sm font-semibold text-white">
            Workflow developments
          </h2>
          {data.updates.length === 0 ? (
            <p className="text-sm text-slate-500">
              No updates yet — Cal is getting to work.
            </p>
          ) : (
            <ol className="relative space-y-4 border-l border-slate-800 pl-6">
              {data.updates.map(u => (
                <li key={u.id} className="relative">
                  <span className="absolute -left-[27px] top-1 flex h-4 w-4 items-center justify-center rounded-full border border-slate-700 bg-slate-950">
                    <CheckCircle2 className="h-3 w-3 text-indigo-400" />
                  </span>
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                        CATEGORY_STYLES[u.category] || CATEGORY_STYLES.note
                      }`}
                    >
                      {u.category}
                    </span>
                    <span className="text-sm font-semibold text-white">
                      {u.title}
                    </span>
                  </div>
                  {u.body && (
                    <p className="mt-1 text-sm text-slate-400">{u.body}</p>
                  )}
                  {u.created_at && (
                    <p className="mt-0.5 text-[11px] text-slate-500">
                      {new Date(u.created_at).toLocaleString()}
                    </p>
                  )}
                </li>
              ))}
            </ol>
          )}
        </div>

        <div className="mt-12 border-t border-slate-800 pt-6 text-center text-xs text-slate-500">
          Powered by{" "}
          <span className="font-semibold text-slate-300">Ready For Robots</span>{" "}
          — automated sales pipeline for robot companies.
        </div>
      </div>
    </div>
  );
}
