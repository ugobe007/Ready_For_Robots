import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { toast } from "sonner";

type SalesMessage = {
  id: string;
  direction: "inbound" | "outbound";
  from_email?: string | null;
  to_email?: string | null;
  subject?: string | null;
  body_text?: string | null;
  detected_intent?: string | null;
  created_at?: string | null;
};

type SalesAction = {
  id: string;
  action_type: string;
  status: string;
  risk_level?: string | null;
  requires_approval?: boolean;
  detected_intent?: string | null;
  recommendation?: string | null;
  draft_subject?: string | null;
  draft_body?: string | null;
  payload?: Record<string, unknown>;
  error?: string | null;
  sent_at?: string | null;
  created_at?: string | null;
};

type SalesOpportunity = {
  id: string;
  opportunity_type: string;
  crm_account_id?: string | null;
  robot_company_id?: number | null;
  title: string;
  current_stage: string;
  status: string;
  automation_level: string;
  next_best_action?: { intent?: string; recommendation?: string; stage_after?: string };
  last_inbound_at?: string | null;
  last_outbound_at?: string | null;
  latest_message?: SalesMessage | null;
  messages?: SalesMessage[];
  actions?: SalesAction[];
};

type ApolloProspect = {
  id?: string | null;
  name?: string | null;
  title?: string | null;
  email?: string | null;
  email_status?: string | null;
  linkedin_url?: string | null;
  organization_name?: string | null;
  organization_domain?: string | null;
};

type SalesLearningReport = {
  experience_events: number;
  source_domain_priorities?: { key: string; score: number; positive_events?: number; negative_events?: number }[];
  signal_type_priorities?: { key: string; score: number; positive_events?: number; negative_events?: number }[];
  scraper_guidance?: string[];
};

const AUTOMATION_LEVELS = [
  { value: "manual", label: "Manual" },
  { value: "first_reply_auto", label: "First reply auto" },
  { value: "auto", label: "Automated" },
  { value: "full_auto", label: "Full auto" },
];

function formatDate(value?: string | null) {
  if (!value) return "Not yet";
  return new Date(value).toLocaleString();
}

function statusColor(status: string) {
  if (status === "sent") return "#059669";
  if (status === "failed" || status === "blocked") return "#FF6B6B";
  if (status === "awaiting_approval") return "#FFB000";
  return "rgba(255,255,255,0.6)";
}

function actionLabel(action: SalesAction) {
  const persona = action.payload?.responder_persona === "max" ? "Technical" : "Outreach";
  return `${persona}: ${action.action_type.replace(/_/g, " ")}`;
}

export default function SalesConsole() {
  const { session, loading } = useAuth();
  const [rows, setRows] = useState<SalesOpportunity[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selected, setSelected] = useState<SalesOpportunity | null>(null);
  const [prospects, setProspects] = useState<ApolloProspect[]>([]);
  const [prospectTitles, setProspectTitles] = useState<string[]>([]);
  const [learningReport, setLearningReport] = useState<SalesLearningReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [prospectBusy, setProspectBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [prospectMsg, setProspectMsg] = useState("");
  const [recipientOverride, setRecipientOverride] = useState("");

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const token = session?.access_token;
      if (!token) throw new Error("Not signed in");
      const response = await fetch(
        `${getApiBase()}${path}`,
        liveFetchInit({ ...init, headers: { ...authHeader(token), ...init.headers } }),
      );
      const text = await response.text();
      if (!response.ok) throw new Error(text || response.statusText);
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token],
  );

  const loadRows = useCallback(async () => {
    if (!session?.access_token) return;
    setBusy(true);
    setMsg("");
    try {
      const data = (await authFetch("/api/sales/opportunities")) as SalesOpportunity[];
      const list = Array.isArray(data) ? data : [];
      setRows(list);
      setSelectedId((prev) => (list.some((row) => row.id === prev) ? prev : list[0]?.id ?? ""));
      if (!list.length) setSelected(null);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not load sales console");
    } finally {
      setBusy(false);
    }
  }, [authFetch, session?.access_token]);

  useEffect(() => {
    void loadRows();
  }, [loadRows]);

  useEffect(() => {
    if (!session?.access_token) return;
    (async () => {
      try {
        const data = (await authFetch("/api/sales/learning")) as SalesLearningReport;
        setLearningReport(data);
      } catch {
        setLearningReport(null);
      }
    })();
  }, [authFetch, session?.access_token]);

  useEffect(() => {
    if (!selectedId || !session?.access_token) return;
    (async () => {
      setBusy(true);
      setProspects([]);
      setProspectTitles([]);
      setProspectMsg("");
      try {
        const detail = (await authFetch(`/api/sales/opportunities/${selectedId}`)) as SalesOpportunity;
        setSelected(detail);
        setRecipientOverride(detail.latest_message?.direction === "inbound" ? detail.latest_message.from_email || "" : "");
      } catch (e) {
        setMsg(e instanceof Error ? e.message : "Could not load opportunity");
      } finally {
        setBusy(false);
      }
    })();
  }, [authFetch, selectedId, session?.access_token]);

  const loadProspects = async () => {
    if (!selected) return;
    setProspectBusy(true);
    setProspectMsg("");
    try {
      const result = await authFetch(`/api/sales/opportunities/${selected.id}/prospects`);
      setProspects(Array.isArray(result.prospects) ? result.prospects : []);
      setProspectTitles(Array.isArray(result.recommended_titles) ? result.recommended_titles : []);
      setProspectMsg(
        result.prospects?.length
          ? `Apollo found ${result.prospects.length} likely decision-makers for this opportunity.`
          : "Apollo returned no prospects for this account yet.",
      );
    } catch (e) {
      setProspects([]);
      setProspectMsg(e instanceof Error ? e.message : "Could not search Apollo prospects.");
    } finally {
      setProspectBusy(false);
    }
  };

  const setAutomation = async (level: string) => {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = (await authFetch(`/api/sales/opportunities/${selected.id}/automation`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ automation_level: level }),
      })) as SalesOpportunity;
      setSelected(updated);
      setRows((prev) => prev.map((row) => (row.id === updated.id ? { ...row, automation_level: updated.automation_level } : row)));
      toast.success("Automation updated.");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not update automation.");
    } finally {
      setBusy(false);
    }
  };

  const automateNext = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      const result = await authFetch(`/api/sales/opportunities/${selected.id}/actions/automate-next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: true, recipient: recipientOverride || undefined }),
      });
      setSelected(result.opportunity);
      toast.success(`Action ${result.action.status}.`);
      await loadRows();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not automate next action.");
    } finally {
      setBusy(false);
    }
  };

  const applyProspectContact = async (person: ApolloProspect) => {
    if (!selected?.crm_account_id || !person.email) {
      toast.error("Select an opportunity with a CRM account and a prospect email.");
      return;
    }
    try {
      setBusy(true);
      await authFetch(`/api/crm/accounts/${selected.crm_account_id}/set-contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contact_email: person.email,
          contact_name: person.name,
          contact_title: person.title,
          source: "apollo",
        }),
      });
      toast.success(`Set ${person.email} as outreach contact.`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save contact.");
    } finally {
      setBusy(false);
    }
  };

  const automateAction = async (action: SalesAction) => {
    if (!selected) return;
    setBusy(true);
    try {
      const result = await authFetch(`/api/sales/actions/${action.id}/automate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: true, recipient: recipientOverride || undefined }),
      });
      setSelected(result.opportunity);
      toast.success(`Action ${result.action.status}.`);
      await loadRows();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not automate action.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen bg-slate-50 text-gray-900" />;
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 text-gray-900">
        <Header />
        <main className="max-w-3xl mx-auto px-6 pt-32">
          <h1 className="text-3xl font-bold">Sales Console</h1>
          <p className="mt-4 text-gray-600">Sign in to see buyer replies, opportunity stage movement, and next-best actions.</p>
          <Link href="/login?next=/sales-console" className="inline-flex mt-6 rounded-xl px-4 py-2 font-bold" style={{ background: "#059669", color: "#111827" }}>
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-gray-900">
      <Header />
      <main className="admin-workspace max-w-7xl mx-auto px-6 pt-28 pb-16">
        <AdminNav />
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5">
          <div>
            <p className="text-xs uppercase tracking-[0.25em]" style={{ color: "#059669" }}>SIGNAL sales console</p>
            <h1 className="mt-3 text-4xl md:text-5xl font-black tracking-tight">Sales Console</h1>
            <p className="mt-3 max-w-2xl text-gray-600">
              Review inbound replies, see what SIGNAL already sent, and decide the next action to advance each opportunity.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/crm" className="rounded-xl px-4 py-2 text-sm font-black" style={{ background: "#059669", color: "#111827" }}>
              Draft buyer email
            </Link>
            <Link href="/supply-pipeline" className="rounded-xl border border-amber-400 px-4 py-2 text-sm font-bold text-amber-800">
              Draft robot-company email
            </Link>
            <button
              onClick={() => void loadRows()}
              disabled={busy}
              className="rounded-xl border border-gray-200 px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-100 disabled:opacity-50"
            >
              Refresh
            </button>
          </div>
        </div>

        {msg && <div className="mt-6 rounded-2xl border border-amber-400/30 bg-amber-50 p-4 text-sm text-amber-900">{msg}</div>}

        <section className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Workflow memory</p>
            <p className="mt-3 text-3xl font-black" style={{ color: "#059669" }}>
              {learningReport?.experience_events ?? 0}
            </p>
            <p className="mt-1 text-sm text-gray-500">sales events captured from sends, replies, failures, and escalations</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Best source signal</p>
            <p className="mt-3 text-lg font-bold text-gray-900">
              {learningReport?.source_domain_priorities?.[0]?.key || "Waiting for replies"}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              SIGNAL uses positive reply history to guide scraper priorities.
            </p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Scraper guidance</p>
            <p className="mt-3 text-sm leading-relaxed text-gray-600">
              {learningReport?.scraper_guidance?.[0] || "Guidance appears after SIGNAL observes enough outreach outcomes."}
            </p>
          </div>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-4">
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Open opportunities</p>
            <p className="mt-2 text-3xl font-black text-gray-900">{rows.length}</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Need action</p>
            <p className="mt-2 text-3xl font-black text-amber-800">{rows.filter((row) => row.next_best_action?.recommendation).length}</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Buyer replies</p>
            <p className="mt-2 text-3xl font-black" style={{ color: "#059669" }}>{rows.filter((row) => row.last_inbound_at).length}</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Technical escalations</p>
            <p className="mt-2 text-3xl font-black text-violet-800">{rows.filter((row) => row.current_stage === "technical_escalation").length}</p>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[360px_1fr]">
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500">Opportunities</h2>
              <span className="text-xs text-gray-400">{rows.length} active</span>
            </div>
            <div className="mt-4 space-y-3">
              {rows.map((row) => (
                <button
                  key={row.id}
                  onClick={() => setSelectedId(row.id)}
                  className="w-full rounded-2xl border p-4 text-left transition hover:bg-gray-50"
                  style={{
                    borderColor: selectedId === row.id ? "rgba(3,218,197,0.45)" : "#e5e7eb",
                    background: selectedId === row.id ? "rgba(3,218,197,0.08)" : "#ffffff",
                  }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-bold text-gray-900">{row.title}</p>
                    <span className="rounded-full border border-gray-200 px-2 py-1 text-[10px] uppercase text-gray-500">{row.opportunity_type}</span>
                  </div>
                  <p className="mt-2 text-xs text-gray-500">Stage: {row.current_stage}</p>
                  <p className="mt-1 text-xs text-gray-400">Intent: {row.next_best_action?.intent || row.latest_message?.detected_intent || "unknown"}</p>
                </button>
              ))}
              {!rows.length && !busy && (
                <div className="rounded-2xl border border-gray-200 p-5 text-sm text-gray-500">
                  No sales opportunities yet. They appear here when SIGNAL captures inbound replies.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5">
            {selected ? (
              <>
                <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-gray-400">{selected.opportunity_type} opportunity</p>
                    <h2 className="mt-2 text-3xl font-black">{selected.title}</h2>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full bg-gray-100 px-3 py-1 text-gray-600">Stage: {selected.current_stage}</span>
                      <span className="rounded-full bg-gray-100 px-3 py-1 text-gray-600">Status: {selected.status}</span>
                      <span className="rounded-full bg-gray-100 px-3 py-1 text-gray-600">Last inbound: {formatDate(selected.last_inbound_at)}</span>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-gray-200 bg-slate-50/60 p-4 xl:w-80">
                    <label className="text-xs font-bold uppercase tracking-widest text-gray-400">Automation mode</label>
                    <select
                      value={selected.automation_level}
                      onChange={(event) => void setAutomation(event.target.value)}
                      className="mt-2 w-full rounded-xl border border-gray-200 bg-gray-100 px-3 py-2 text-sm text-gray-900 outline-none"
                    >
                      {AUTOMATION_LEVELS.map((level) => (
                        <option key={level.value} value={level.value} className="bg-slate-50">
                          {level.label}
                        </option>
                      ))}
                    </select>
                    <label className="mt-3 block text-xs font-bold uppercase tracking-widest text-gray-400">Reply recipient</label>
                    <input
                      value={recipientOverride}
                      onChange={(event) => setRecipientOverride(event.target.value)}
                      placeholder="buyer@example.com"
                      className="mt-2 w-full rounded-xl border border-gray-200 bg-gray-100 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400"
                    />
                    <button
                      onClick={() => void automateNext()}
                      disabled={busy}
                      className="mt-3 w-full rounded-xl px-4 py-2 text-sm font-black disabled:opacity-50"
                      style={{ background: "#059669", color: "#111827" }}
                    >
                      Automate next action
                    </button>
                  </div>
                </div>

                <div className="mt-6 rounded-2xl border border-gray-200 bg-slate-50/50 p-5">
                  <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Next best action</p>
                  <p className="mt-2 text-sm text-gray-700">{selected.next_best_action?.recommendation || "SIGNAL will generate the next action from the latest conversation context."}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {selected.crm_account_id && (
                      <Link href="/crm" className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-600">
                        Open CRM draft tools
                      </Link>
                    )}
                    {selected.opportunity_type === "supply" && (
                      <Link href="/supply-pipeline" className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-600">
                        Open Supply Pipeline draft tools
                      </Link>
                    )}
                  </div>
                </div>

                <div className="mt-6 rounded-2xl border border-gray-200 bg-slate-50/50 p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Apollo prospect search</p>
                      <p className="mt-2 text-sm text-gray-600">
                        Find likely decision-makers for this opportunity and use them to route the next outreach step.
                      </p>
                    </div>
                    <button
                      onClick={() => void loadProspects()}
                      disabled={prospectBusy}
                      className="rounded-xl border border-gray-200 px-4 py-2 text-sm font-bold text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                    >
                      {prospectBusy ? "Searching Apollo..." : "Find prospects"}
                    </button>
                  </div>
                  {prospectTitles.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {prospectTitles.map((title) => (
                        <span key={title} className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-[11px] text-gray-500">
                          {title}
                        </span>
                      ))}
                    </div>
                  )}
                  {prospectMsg && <p className="mt-3 text-xs text-amber-800">{prospectMsg}</p>}
                  {prospects.length > 0 && (
                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                      {prospects.slice(0, 6).map((person, idx) => (
                        <div key={person.id || `${person.name}-${idx}`} className="rounded-xl border border-gray-200 bg-white p-3">
                          <p className="font-bold text-gray-900">{person.name || "Unnamed prospect"}</p>
                          <p className="mt-1 text-xs text-gray-500">{person.title || "Title unavailable"}</p>
                          <p className="mt-1 text-xs text-gray-400">{person.organization_name || person.organization_domain || "Organization unavailable"}</p>
                          {person.email && <p className="mt-2 text-xs" style={{ color: "#059669" }}>{person.email}</p>}
                          {person.email && selected.crm_account_id && (
                            <button
                              onClick={() => void applyProspectContact(person)}
                              disabled={busy}
                              className="mt-2 rounded-lg border border-emerald-400/30 px-2 py-1 text-[11px] font-bold text-emerald-800 hover:bg-emerald-50 disabled:opacity-50"
                            >
                              Use as contact
                            </button>
                          )}
                          {person.linkedin_url && (
                            <a href={person.linkedin_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex text-xs text-amber-800 underline">
                              LinkedIn
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="mt-6 grid gap-6 xl:grid-cols-2">
                  <section>
                    <h3 className="text-sm font-bold uppercase tracking-widest text-gray-500">Actions</h3>
                    <div className="mt-3 space-y-3">
                      {(selected.actions || []).map((action) => (
                        <div key={action.id} className="rounded-2xl border border-gray-200 bg-white p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-bold text-gray-900">{actionLabel(action)}</p>
                              <p className="mt-1 text-xs" style={{ color: statusColor(action.status) }}>Status: {action.status}</p>
                              <p className="mt-1 text-[11px] text-gray-400">Intent: {action.detected_intent || "unknown"} · Risk: {action.risk_level || "unknown"}</p>
                            </div>
                            {action.status !== "sent" && (
                              <button
                                onClick={() => void automateAction(action)}
                                disabled={busy}
                                className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-bold text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                              >
                                Automate
                              </button>
                            )}
                          </div>
                          <p className="mt-3 text-sm text-gray-600">{action.recommendation}</p>
                          {action.draft_subject && <p className="mt-3 text-xs font-bold text-gray-500">Subject: {action.draft_subject}</p>}
                          {action.draft_body && (
                            <pre className="mt-2 max-h-56 overflow-y-auto whitespace-pre-wrap rounded-xl border border-gray-300 bg-gray-50 p-3 text-xs leading-relaxed text-gray-800">
                              {action.draft_body}
                            </pre>
                          )}
                          {action.error && <p className="mt-2 text-xs text-red-300">{action.error}</p>}
                        </div>
                      ))}
                      {!(selected.actions || []).length && <p className="text-sm text-gray-500">No actions recorded yet.</p>}
                    </div>
                  </section>

                  <section>
                    <h3 className="text-sm font-bold uppercase tracking-widest text-gray-500">Messages</h3>
                    <div className="mt-3 space-y-3">
                      {(selected.messages || []).map((message) => (
                        <div key={message.id} className="rounded-2xl border border-gray-200 bg-white p-4">
                          <div className="flex items-center justify-between gap-3">
                            <p className="font-bold text-gray-900">{message.direction === "inbound" ? "Inbound" : "Outbound"}</p>
                            <span className="text-xs text-gray-400">{formatDate(message.created_at)}</span>
                          </div>
                          <p className="mt-2 text-xs text-gray-500">{message.subject || "No subject"}</p>
                          <p className="mt-3 line-clamp-5 whitespace-pre-wrap text-sm text-gray-600">{message.body_text || "No body captured."}</p>
                        </div>
                      ))}
                      {!(selected.messages || []).length && <p className="text-sm text-gray-500">No messages recorded yet.</p>}
                    </div>
                  </section>
                </div>
              </>
            ) : (
              <div className="rounded-2xl border border-gray-200 p-8 text-gray-500">
                Select an opportunity to inspect SIGNAL activity.
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
