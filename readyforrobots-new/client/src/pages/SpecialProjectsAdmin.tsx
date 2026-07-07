import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import {
  Bot,
  Copy,
  ExternalLink,
  Plus,
  RefreshCw,
  Rocket,
  Shield,
  Trash2,
} from "lucide-react";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase } from "@/lib/apiBase";
import { authHeader, getFreshAccessToken } from "@/lib/supabase";

const PIPELINE_STAGES = [
  "targeted",
  "contacted",
  "replied",
  "discovery",
  "demo",
  "pilot_signed",
  "validated",
] as const;

const STATUSES = ["discovery", "outreach", "piloting", "active", "paused", "archived"] as const;
const UPDATE_CATEGORIES = ["milestone", "stat", "note", "outreach"] as const;

type ProjectUpdate = {
  id: string;
  title: string;
  body?: string | null;
  category: string;
  created_at?: string | null;
};

type Project = {
  id: string;
  slug: string;
  share_token: string;
  name: string;
  company_website?: string | null;
  contact_email?: string | null;
  robot_description?: string | null;
  summary?: string | null;
  status: string;
  config: Record<string, unknown>;
  metrics: Record<string, unknown>;
  pipeline: Record<string, number>;
  portal_path: string;
  updates?: ProjectUpdate[];
  update_count?: number;
};

type MetricRow = { key: string; value: string };

function metricsToRows(metrics: Record<string, unknown>): MetricRow[] {
  return Object.entries(metrics || {}).map(([key, value]) => ({ key, value: String(value ?? "") }));
}

function rowsToMetrics(rows: MetricRow[]): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const { key, value } of rows) {
    const k = key.trim();
    if (!k) continue;
    const num = Number(value);
    out[k] = value.trim() !== "" && !Number.isNaN(num) ? num : value;
  }
  return out;
}

export default function SpecialProjectsAdmin() {
  const api = getApiBase();
  const { session, loading: authLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [forbidden, setForbidden] = useState(false);

  // Create form
  const [newName, setNewName] = useState("");
  const [newWebsite, setNewWebsite] = useState("");
  const [newContact, setNewContact] = useState("");
  const [newDescription, setNewDescription] = useState("");

  // Editable detail state
  const [editStatus, setEditStatus] = useState<string>("discovery");
  const [editSummary, setEditSummary] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editPipeline, setEditPipeline] = useState<Record<string, string>>({});
  const [metricRows, setMetricRows] = useState<MetricRow[]>([]);

  // Update form
  const [updTitle, setUpdTitle] = useState("");
  const [updBody, setUpdBody] = useState("");
  const [updCategory, setUpdCategory] = useState<string>("milestone");

  const adminFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const token = await getFreshAccessToken(session?.access_token);
      return fetch(`${api}${path}`, {
        cache: "no-store",
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...authHeader(token),
          ...((init.headers as Record<string, string>) || {}),
        },
      });
    },
    [api, session?.access_token],
  );

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await adminFetch("/api/admin/special-projects");
      if (res.status === 401 || res.status === 403) {
        setForbidden(true);
        setProjects([]);
        return;
      }
      if (!res.ok) throw new Error(`Failed to load (${res.status})`);
      const data = (await res.json()) as Project[];
      setProjects(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [adminFetch]);

  const openProject = useCallback(
    async (id: string) => {
      setError("");
      try {
        const res = await adminFetch(`/api/admin/special-projects/${id}`);
        if (!res.ok) throw new Error(`Failed to open (${res.status})`);
        const p = (await res.json()) as Project;
        setSelected(p);
        setEditStatus(p.status);
        setEditSummary(p.summary || "");
        setEditDescription(p.robot_description || "");
        setEditPipeline(
          Object.fromEntries(PIPELINE_STAGES.map((s) => [s, String(p.pipeline?.[s] ?? "")])),
        );
        setMetricRows(metricsToRows(p.metrics));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to open project");
      }
    },
    [adminFetch],
  );

  useEffect(() => {
    if (!authLoading) void loadProjects();
  }, [authLoading, loadProjects]);

  const createProject = useCallback(async () => {
    if (!newName.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = await adminFetch("/api/admin/special-projects", {
        method: "POST",
        body: JSON.stringify({
          name: newName.trim(),
          company_website: newWebsite.trim() || null,
          contact_email: newContact.trim() || null,
          robot_description: newDescription.trim() || null,
        }),
      });
      if (!res.ok) throw new Error(`Create failed (${res.status})`);
      const p = (await res.json()) as Project;
      setNewName("");
      setNewWebsite("");
      setNewContact("");
      setNewDescription("");
      await loadProjects();
      await openProject(p.id);
      setNotice(`Created "${p.name}"`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }, [adminFetch, newName, newWebsite, newContact, newDescription, loadProjects, openProject]);

  const saveDetail = useCallback(async () => {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const pipeline: Record<string, number> = {};
      for (const stage of PIPELINE_STAGES) {
        const raw = editPipeline[stage];
        if (raw != null && String(raw).trim() !== "") pipeline[stage] = Number(raw) || 0;
      }
      const res = await adminFetch(`/api/admin/special-projects/${selected.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: editStatus,
          summary: editSummary,
          robot_description: editDescription,
          pipeline,
          metrics: rowsToMetrics(metricRows),
        }),
      });
      if (!res.ok) throw new Error(`Save failed (${res.status})`);
      const p = (await res.json()) as Project;
      setSelected(p);
      setNotice("Saved");
      await loadProjects();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }, [adminFetch, selected, editStatus, editSummary, editDescription, editPipeline, metricRows, loadProjects]);

  const addUpdate = useCallback(async () => {
    if (!selected || !updTitle.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = await adminFetch(`/api/admin/special-projects/${selected.id}/updates`, {
        method: "POST",
        body: JSON.stringify({ title: updTitle.trim(), body: updBody.trim() || null, category: updCategory }),
      });
      if (!res.ok) throw new Error(`Add update failed (${res.status})`);
      const p = (await res.json()) as Project;
      setSelected(p);
      setUpdTitle("");
      setUpdBody("");
      setNotice("Update posted");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Add update failed");
    } finally {
      setBusy(false);
    }
  }, [adminFetch, selected, updTitle, updBody, updCategory]);

  const deleteUpdate = useCallback(
    async (updateId: string) => {
      if (!selected) return;
      setBusy(true);
      try {
        await adminFetch(`/api/admin/special-projects/${selected.id}/updates/${updateId}`, {
          method: "DELETE",
        });
        await openProject(selected.id);
      } finally {
        setBusy(false);
      }
    },
    [adminFetch, selected, openProject],
  );

  const rotateToken = useCallback(async () => {
    if (!selected) return;
    if (!window.confirm("Rotate the client portal link? The old link will stop working.")) return;
    setBusy(true);
    try {
      const res = await adminFetch(`/api/admin/special-projects/${selected.id}/rotate-token`, {
        method: "POST",
      });
      if (res.ok) {
        await openProject(selected.id);
        setNotice("Portal link rotated");
      }
    } finally {
      setBusy(false);
    }
  }, [adminFetch, selected, openProject]);

  const deleteProject = useCallback(async () => {
    if (!selected) return;
    if (!window.confirm(`Delete "${selected.name}" and all its updates? This cannot be undone.`)) return;
    setBusy(true);
    try {
      await adminFetch(`/api/admin/special-projects/${selected.id}`, { method: "DELETE" });
      setSelected(null);
      await loadProjects();
      setNotice("Project deleted");
    } finally {
      setBusy(false);
    }
  }, [adminFetch, selected, loadProjects]);

  const portalUrl = useMemo(() => {
    if (!selected) return "";
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    return `${origin}/p/${selected.share_token}`;
  }, [selected]);

  const copyPortal = useCallback(() => {
    if (!portalUrl) return;
    void navigator.clipboard?.writeText(portalUrl);
    setNotice("Portal link copied");
  }, [portalUrl]);

  if (forbidden) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="mx-auto max-w-2xl px-6 py-24 text-center">
          <Shield className="mx-auto mb-4 h-10 w-10 text-slate-400" />
          <h1 className="text-xl font-semibold text-slate-900">Admin access required</h1>
          <p className="mt-2 text-slate-600">Special Projects is a private, admin-only workspace.</p>
          <Link href="/admin" className="mt-6 inline-block text-sm font-medium text-indigo-600">
            Back to Command Center
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-indigo-600">
              <Rocket className="h-3.5 w-3.5" /> Special Projects · admin only
            </div>
            <h1 className="mt-1 text-2xl font-bold text-slate-900">Bespoke robot-company engagements</h1>
            <p className="mt-1 text-sm text-slate-600">
              Run a private Cal GTM workflow per company (e.g. NIMO). Share a read-only portal with each client.
            </p>
          </div>
          <button
            onClick={() => void loadProjects()}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>
        )}
        {notice && (
          <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
            {notice}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          {/* Left: list + create */}
          <div className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold text-slate-900">New project</h2>
              <div className="space-y-2">
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Company / project name"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
                <input
                  value={newWebsite}
                  onChange={(e) => setNewWebsite(e.target.value)}
                  placeholder="Website (optional)"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
                <input
                  value={newContact}
                  onChange={(e) => setNewContact(e.target.value)}
                  placeholder="Client contact email (optional)"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
                <textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Robot / product one-liner"
                  rows={2}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
                <button
                  onClick={() => void createProject()}
                  disabled={busy || !newName.trim()}
                  className="inline-flex w-full items-center justify-center gap-1.5 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Plus className="h-4 w-4" /> Create project
                </button>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-4 py-3 text-sm font-semibold text-slate-900">
                Projects {loading ? "…" : `(${projects.length})`}
              </div>
              <ul className="divide-y divide-slate-100">
                {projects.map((p) => (
                  <li key={p.id}>
                    <button
                      onClick={() => void openProject(p.id)}
                      className={`flex w-full items-center justify-between px-4 py-3 text-left hover:bg-slate-50 ${
                        selected?.id === p.id ? "bg-indigo-50" : ""
                      }`}
                    >
                      <span>
                        <span className="block text-sm font-medium text-slate-900">{p.name}</span>
                        <span className="block text-xs text-slate-500">{p.slug}</span>
                      </span>
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                        {p.status}
                      </span>
                    </button>
                  </li>
                ))}
                {!loading && projects.length === 0 && (
                  <li className="px-4 py-6 text-center text-sm text-slate-500">No projects yet.</li>
                )}
              </ul>
            </div>
          </div>

          {/* Right: detail editor */}
          <div>
            {!selected ? (
              <div className="flex h-full min-h-[300px] items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white text-sm text-slate-500">
                Select a project to manage Cal's workflow, KPIs, and the client portal.
              </div>
            ) : (
              <div className="space-y-6">
                <div className="rounded-lg border border-slate-200 bg-white p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="flex items-center gap-2 text-lg font-bold text-slate-900">
                        <Bot className="h-5 w-5 text-indigo-600" /> {selected.name}
                      </h2>
                      {selected.company_website && (
                        <a
                          href={selected.company_website}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-0.5 inline-flex items-center gap-1 text-xs text-indigo-600"
                        >
                          {selected.company_website} <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                    <button
                      onClick={() => void deleteProject()}
                      className="inline-flex items-center gap-1 rounded-md border border-red-200 px-2.5 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Delete
                    </button>
                  </div>

                  {/* Portal link */}
                  <div className="mt-4 rounded-md bg-slate-50 p-3">
                    <div className="text-xs font-semibold text-slate-500">Client portal (read-only, no login)</div>
                    <div className="mt-1 flex items-center gap-2">
                      <code className="flex-1 truncate rounded bg-white px-2 py-1.5 text-xs text-slate-700">
                        {portalUrl}
                      </code>
                      <button onClick={copyPortal} className="rounded-md border border-slate-300 bg-white p-1.5 hover:bg-slate-100" title="Copy link">
                        <Copy className="h-4 w-4 text-slate-600" />
                      </button>
                      <a href={selected.portal_path} target="_blank" rel="noreferrer" className="rounded-md border border-slate-300 bg-white p-1.5 hover:bg-slate-100" title="Open portal">
                        <ExternalLink className="h-4 w-4 text-slate-600" />
                      </a>
                      <button onClick={() => void rotateToken()} className="rounded-md border border-slate-300 bg-white p-1.5 hover:bg-slate-100" title="Rotate link">
                        <RefreshCw className="h-4 w-4 text-slate-600" />
                      </button>
                    </div>
                  </div>

                  {/* Status + summary + description */}
                  <div className="mt-4 grid gap-4 sm:grid-cols-[160px_1fr]">
                    <div>
                      <label className="text-xs font-semibold text-slate-500">Status</label>
                      <select
                        value={editStatus}
                        onChange={(e) => setEditStatus(e.target.value)}
                        className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2 text-sm capitalize"
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-500">Summary (shown to client)</label>
                      <textarea
                        value={editSummary}
                        onChange={(e) => setEditSummary(e.target.value)}
                        rows={2}
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <label className="text-xs font-semibold text-slate-500">Robot / product description</label>
                    <textarea
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      rows={2}
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                {/* Pipeline funnel */}
                <div className="rounded-lg border border-slate-200 bg-white p-5">
                  <h3 className="mb-3 text-sm font-semibold text-slate-900">Pipeline funnel</h3>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
                    {PIPELINE_STAGES.map((stage) => (
                      <div key={stage}>
                        <label className="block text-[11px] font-medium capitalize text-slate-500">
                          {stage.replace("_", " ")}
                        </label>
                        <input
                          type="number"
                          min={0}
                          value={editPipeline[stage] ?? ""}
                          onChange={(e) => setEditPipeline((prev) => ({ ...prev, [stage]: e.target.value }))}
                          className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* KPIs / metrics */}
                <div className="rounded-lg border border-slate-200 bg-white p-5">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-900">KPI cards (shown to client)</h3>
                    <button
                      onClick={() => setMetricRows((r) => [...r, { key: "", value: "" }])}
                      className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600"
                    >
                      <Plus className="h-3.5 w-3.5" /> Add KPI
                    </button>
                  </div>
                  <div className="space-y-2">
                    {metricRows.map((row, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <input
                          value={row.key}
                          onChange={(e) =>
                            setMetricRows((r) => r.map((x, i) => (i === idx ? { ...x, key: e.target.value } : x)))
                          }
                          placeholder="Label (e.g. demos_booked)"
                          className="flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
                        />
                        <input
                          value={row.value}
                          onChange={(e) =>
                            setMetricRows((r) => r.map((x, i) => (i === idx ? { ...x, value: e.target.value } : x)))
                          }
                          placeholder="Value"
                          className="w-32 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
                        />
                        <button
                          onClick={() => setMetricRows((r) => r.filter((_, i) => i !== idx))}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    {metricRows.length === 0 && (
                      <p className="text-xs text-slate-500">No KPIs yet — add cards like “demos_booked”, “pilots_signed”.</p>
                    )}
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => void saveDetail()}
                    disabled={busy}
                    className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Save changes
                  </button>
                </div>

                {/* Updates timeline */}
                <div className="rounded-lg border border-slate-200 bg-white p-5">
                  <h3 className="mb-3 text-sm font-semibold text-slate-900">Workflow updates</h3>
                  <div className="mb-4 grid gap-2 sm:grid-cols-[1fr_160px]">
                    <input
                      value={updTitle}
                      onChange={(e) => setUpdTitle(e.target.value)}
                      placeholder="Update title (e.g. First demo booked)"
                      className="rounded-md border border-slate-300 px-3 py-2 text-sm"
                    />
                    <select
                      value={updCategory}
                      onChange={(e) => setUpdCategory(e.target.value)}
                      className="rounded-md border border-slate-300 px-2 py-2 text-sm capitalize"
                    >
                      {UPDATE_CATEGORIES.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                    <textarea
                      value={updBody}
                      onChange={(e) => setUpdBody(e.target.value)}
                      placeholder="Details (optional)"
                      rows={2}
                      className="rounded-md border border-slate-300 px-3 py-2 text-sm sm:col-span-2"
                    />
                    <button
                      onClick={() => void addUpdate()}
                      disabled={busy || !updTitle.trim()}
                      className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50 sm:col-span-2"
                    >
                      Post update
                    </button>
                  </div>
                  <ul className="space-y-2">
                    {(selected.updates || []).map((u) => (
                      <li key={u.id} className="flex items-start justify-between gap-3 rounded-md border border-slate-100 bg-slate-50 px-3 py-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium capitalize text-slate-600">
                              {u.category}
                            </span>
                            <span className="text-sm font-medium text-slate-900">{u.title}</span>
                          </div>
                          {u.body && <p className="mt-1 text-xs text-slate-600">{u.body}</p>}
                          {u.created_at && (
                            <p className="mt-0.5 text-[11px] text-slate-400">
                              {new Date(u.created_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => void deleteUpdate(u.id)}
                          className="rounded-md p-1 text-slate-400 hover:bg-white hover:text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </li>
                    ))}
                    {(selected.updates || []).length === 0 && (
                      <li className="text-xs text-slate-500">No updates posted yet.</li>
                    )}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
