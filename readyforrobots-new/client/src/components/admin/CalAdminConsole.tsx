/**
 * Cal sales admin — audit-first operator console.
 * Cal drafts and sends in the background; you review what went out (or approve if manual mode).
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
  Play,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { Link } from "wouter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { readLocalAdminSnapshot, mergeSectionIntoSnapshot, writeLocalAdminSnapshot } from "@/lib/adminSnapshot";
import type { CalActivityData, CalActivityTimelineItem } from "@/components/admin/AdminCalOversightPanel";

type CalProspect = {
  company_id?: number;
  company_name?: string;
  score?: number;
  tier?: string;
  crm_account_id?: string;
  contact_email?: string;
  outreach_stage?: string;
  outreach_sent_at?: string;
  has_draft?: boolean;
  draft_preview?: string;
  draft_full?: string;
};

type CalDraftStatus = {
  summary?: {
    hot?: number;
    warm?: number;
    unsent_drafted?: number;
    sendable?: number;
    needs_approval?: number;
    pending_draft?: number;
    sent?: number;
  };
  prospects?: CalProspect[];
  stale?: boolean;
};

function fmt(n?: number) {
  if (n == null) return "0";
  return new Intl.NumberFormat("en-US").format(n);
}

function isApproved(stage?: string) {
  return (stage || "") === "draft_approved" || stage === "approved";
}

function formatWhen(iso?: string | null) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

const SENT_KINDS = new Set(["intro_sent", "followup_sent", "auto_reply_sent"]);

type Props = {
  accessToken?: string | null;
};

export default function CalAdminConsole({ accessToken }: Props) {
  const [summary, setSummary] = useState<CalDraftStatus["summary"] | null>(() => {
    const cached = readLocalAdminSnapshot()?.sections?.cal?.data as CalDraftStatus | undefined;
    return cached?.summary ?? null;
  });
  const [activity, setActivity] = useState<CalActivityData | null>(null);
  const [draftProspects, setDraftProspects] = useState<CalProspect[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingDrafts, setLoadingDrafts] = useState(false);
  const [warning, setWarning] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [expandedSentId, setExpandedSentId] = useState<string | null>(null);
  const [expandedDraftId, setExpandedDraftId] = useState<string | null>(null);
  const [draftBodies, setDraftBodies] = useState<Record<string, string>>({});
  const [draftEmails, setDraftEmails] = useState<Record<string, string>>({});

  const adminFetch = useCallback(
    async (path: string, init?: RequestInit) => {
      const headers = {
        "Content-Type": "application/json",
        ...authHeader(accessToken ?? undefined),
        ...liveFetchInit().headers,
        ...(init?.headers as Record<string, string> | undefined),
      };
      return fetch(`${getApiBase()}${path}`, { ...liveFetchInit(), ...init, headers });
    },
    [accessToken],
  );

  const loadSummary = useCallback(async () => {
    if (!accessToken) return;
    setLoadingSummary(true);
    try {
      const res = await adminFetch("/api/admin/cal/draft-status?include_prospects=false");
      const data = (await res.json().catch(() => ({}))) as CalDraftStatus & { detail?: string };
      if (!res.ok) throw new Error(data.detail || `Summary failed (${res.status})`);
      setSummary(data.summary ?? null);
      const current = readLocalAdminSnapshot() ?? { sections: {} };
      writeLocalAdminSnapshot(
        mergeSectionIntoSnapshot(current, "cal", new Date().toISOString(), { summary: data.summary }),
      );
    } catch (e) {
      const cached = readLocalAdminSnapshot()?.sections?.cal?.data as CalDraftStatus | undefined;
      if (cached?.summary) {
        setSummary(cached.summary);
        setWarning("Using cached counts — live refresh failed.");
      } else {
        setError(e instanceof Error ? e.message : "Failed to load queue counts");
      }
    } finally {
      setLoadingSummary(false);
    }
  }, [accessToken, adminFetch]);

  const loadActivity = useCallback(async () => {
    if (!accessToken) return;
    setLoadingActivity(true);
    setError("");
    try {
      const res = await adminFetch("/api/admin/cal/activity?limit=50");
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(data.detail || `Activity failed (${res.status})`);
      }
      setActivity((await res.json()) as CalActivityData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load Cal activity");
    } finally {
      setLoadingActivity(false);
    }
  }, [accessToken, adminFetch]);

  const loadDraftProspects = useCallback(async () => {
    if (!accessToken) return;
    setLoadingDrafts(true);
    try {
      const res = await adminFetch(
        "/api/admin/cal/draft-status?include_prospects=true&prospect_limit=40",
      );
      const data = (await res.json().catch(() => ({}))) as CalDraftStatus & { detail?: string };
      if (res.ok) {
        setDraftProspects(
          (data.prospects ?? []).filter((p) => p.has_draft && !p.outreach_sent_at),
        );
      }
    } catch {
      /* optional */
    } finally {
      setLoadingDrafts(false);
    }
  }, [accessToken, adminFetch]);

  const refresh = useCallback(() => {
    void loadSummary();
    void loadActivity();
  }, [loadActivity, loadSummary]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const autopilot = activity?.autopilot;
  const manualMode = autopilot?.manual_approval ?? false;
  const autopilotOn = autopilot?.enabled ?? true;
  const everyHours = autopilot?.every_hours ?? 3;
  const sendLimit = autopilot?.send_limit ?? 25;

  const sentTimeline = useMemo(
    () => (activity?.timeline ?? []).filter((row) => SENT_KINDS.has(row.kind || "")),
    [activity?.timeline],
  );
  const replies = useMemo(
    () => (activity?.timeline ?? []).filter((row) => row.kind === "reply_received"),
    [activity?.timeline],
  );
  const blocked = activity?.needs_you?.filter((n) => n.kind === "edit_draft") ?? [];
  const pendingApprovals = activity?.pending_approvals ?? [];
  const needsApprovalCount = activity?.pending_approval_count ?? summary?.needs_approval ?? 0;

  const operatorState = useMemo(() => {
    if (manualMode && needsApprovalCount > 0) return "waiting_approval";
    if (sentTimeline.length > 0) return "sent_audit";
    return "working";
  }, [manualMode, needsApprovalCount, sentTimeline.length]);

  async function runCycleNow() {
    setBusy("cycle");
    setError("");
    try {
      const res = await adminFetch("/api/admin/cal/autonomy-run", {
        method: "POST",
        body: JSON.stringify({ dry_run: false }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        drafted?: number;
        sent?: number;
        detail?: string;
        reason?: string;
      };
      if (!res.ok) throw new Error(data.detail || data.reason || "Cycle failed");
      setMessage(
        `Cal cycle done — drafted ${data.drafted ?? 0}, sent ${data.sent ?? 0}. Refresh in a few seconds.`,
      );
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Cycle failed");
    } finally {
      setBusy("");
    }
  }

  async function approveOne(crmId: string) {
    setBusy(`approve-${crmId}`);
    setError("");
    try {
      const res = await adminFetch(`/api/admin/cal/approve-one/${crmId}`, { method: "POST" });
      if (!res.ok) {
        throw new Error((await res.json().catch(() => ({})) as { detail?: string }).detail || "Approve failed");
      }
      setMessage("Draft approved.");
      refresh();
      if (draftProspects.length) void loadDraftProspects();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approve failed");
    } finally {
      setBusy("");
    }
  }

  async function approveAll() {
    setBusy("approve-all");
    setError("");
    try {
      const res = await adminFetch("/api/admin/cal/approve-all", { method: "POST" });
      const data = (await res.json().catch(() => ({}))) as { approved?: number; detail?: string };
      if (!res.ok) throw new Error(data.detail || "Approve all failed");
      setMessage(`Approved ${data.approved ?? 0} draft(s).`);
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approve all failed");
    } finally {
      setBusy("");
    }
  }

  async function loadDraftBody(crmId: string) {
    const res = await adminFetch(`/api/admin/cal/draft/${crmId}`);
    if (!res.ok) return;
    const data = (await res.json()) as { draft_full?: string; contact_email?: string };
    if (data.draft_full) {
      setDraftBodies((prev) => (prev[crmId] ? prev : { ...prev, [crmId]: data.draft_full! }));
    }
    if (data.contact_email != null) {
      setDraftEmails((prev) => (prev[crmId] !== undefined ? prev : { ...prev, [crmId]: data.contact_email || "" }));
    }
  }

  function SentRow({ row }: { row: CalActivityTimelineItem }) {
    const open = expandedSentId === row.id;
    const body = row.body_full || row.body_preview;
    return (
      <div className="rounded-xl border border-gray-100 bg-white overflow-hidden">
        <button
          type="button"
          className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-slate-50"
          onClick={() => setExpandedSentId(open ? null : row.id || null)}
        >
          <div className="min-w-[90px] text-[11px] text-gray-400 pt-0.5">{formatWhen(row.at)}</div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900">{row.entity || row.title}</p>
            <p className="text-xs text-gray-600 truncate">{row.title}</p>
            <p className="text-[11px] text-gray-500">{row.to_email || row.detail}</p>
          </div>
          {open ? <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" /> : <ChevronRight className="h-4 w-4 text-gray-400 shrink-0" />}
        </button>
        {open && body ? (
          <div className="border-t border-gray-100 px-4 py-3 bg-slate-50/80">
            <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-gray-800">{body}</pre>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <section id="cal-outreach" className="scroll-mt-24 max-w-4xl mx-auto space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-950">Cal — sales admin</h1>
          <p className="mt-1 text-sm text-gray-600">
            {manualMode
              ? "Cal drafts in the background. You approve; he sends."
              : "Cal drafts and sends on autopilot. Review his audit trail below."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/inbox" className="rounded-lg border border-gray-200 px-3 py-2 text-xs font-semibold text-gray-700">
            Inbox
          </Link>
          <button
            type="button"
            onClick={refresh}
            disabled={loadingActivity || loadingSummary}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-bold text-gray-600 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loadingActivity ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {message && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">{message}</div>
      )}
      {warning && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 flex gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          {warning}
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
      )}

      {/* Operator status */}
      <div
        className={`rounded-2xl border p-5 ${
          operatorState === "waiting_approval"
            ? "border-violet-200 bg-violet-50/60"
            : "border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-white"
        }`}
      >
        <div className="flex flex-wrap items-start gap-3">
          <div className="rounded-xl bg-emerald-600 p-2.5 text-white">
            <Bot className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            {operatorState === "waiting_approval" ? (
              <>
                <p className="text-lg font-bold text-violet-950 flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5" />
                  Cal is waiting for your approval
                </p>
                <p className="mt-1 text-sm text-violet-900/90">
                  {needsApprovalCount} draft{needsApprovalCount === 1 ? "" : "s"} ready to review. Approve below and Cal
                  sends on the next cycle (up to {sendLimit}/run).
                </p>
              </>
            ) : operatorState === "sent_audit" ? (
              <>
                <p className="text-lg font-bold text-emerald-950 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5" />
                  Cal has been sending — review audit trail below
                </p>
                <p className="mt-1 text-sm text-gray-700">
                  Autopilot {autopilotOn ? "ON" : "OFF"} · every {everyHours}h · up to {sendLimit} intros per cycle ·{" "}
                  {fmt(summary?.sent)} sent total in queue
                </p>
              </>
            ) : (
              <>
                <p className="text-lg font-bold text-gray-950">Cal is working in the background</p>
                <p className="mt-1 text-sm text-gray-700">
                  {fmt(summary?.pending_draft)} leads still need drafts. Cal drafts up to {autopilot?.draft_batch ?? 100}{" "}
                  per cycle — nothing for you to click. Check back after the next run (~{everyHours}h).
                </p>
              </>
            )}
          </div>
          <button
            type="button"
            disabled={!!busy}
            onClick={() => void runCycleNow()}
            className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-400 bg-emerald-600 px-3 py-2 text-xs font-bold text-white disabled:opacity-50"
          >
            <Play className="h-3.5 w-3.5" />
            {busy === "cycle" ? "Running…" : "Run cycle now"}
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
          <div className="rounded-lg bg-white/80 border border-gray-100 px-2 py-2">
            <p className="text-[9px] font-bold uppercase text-gray-500">Queue</p>
            <p className="text-sm font-black">{loadingSummary ? "…" : `${fmt(summary?.hot)} hot · ${fmt(summary?.warm)} warm`}</p>
          </div>
          <div className="rounded-lg bg-white/80 border border-gray-100 px-2 py-2">
            <p className="text-[9px] font-bold uppercase text-gray-500">Drafted</p>
            <p className="text-sm font-black">{fmt(summary?.unsent_drafted)}</p>
          </div>
          <div className="rounded-lg bg-white/80 border border-gray-100 px-2 py-2">
            <p className="text-[9px] font-bold uppercase text-gray-500">Sent (audit)</p>
            <p className="text-sm font-black">{fmt(sentTimeline.length)} recent</p>
          </div>
          <div className="rounded-lg bg-white/80 border border-gray-100 px-2 py-2">
            <p className="text-[9px] font-bold uppercase text-gray-500">Replies</p>
            <p className="text-sm font-black">{fmt(replies.length)}</p>
          </div>
        </div>
      </div>

      {/* Approval queue — only when manual mode */}
      {manualMode && needsApprovalCount > 0 && (
        <div id="cal-approvals" className="rounded-2xl border border-violet-200 bg-white p-5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs font-bold uppercase tracking-widest text-violet-800">
              Waiting for approval ({needsApprovalCount})
            </p>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => void approveAll()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-2 text-xs font-bold text-white disabled:opacity-50"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              Approve all
            </button>
          </div>
          <ul className="space-y-2">
            {pendingApprovals.map((p) => (
              <li
                key={p.crm_account_id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-violet-100 bg-violet-50/50 px-3 py-2"
              >
                <div>
                  <p className="text-sm font-semibold text-gray-900">{p.company_name}</p>
                  <p className="text-xs text-gray-600">{p.contact_email || "no email"}</p>
                </div>
                <button
                  type="button"
                  disabled={!!busy}
                  onClick={() => void approveOne(p.crm_account_id!)}
                  className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-bold text-white disabled:opacity-50"
                >
                  Approve
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Audit trail — primary view */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 space-y-3">
        <p className="text-xs font-bold uppercase tracking-widest text-gray-500">Sent emails — audit trail</p>
        {loadingActivity ? (
          <p className="flex items-center justify-center gap-2 py-8 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </p>
        ) : sentTimeline.length === 0 ? (
          <p className="py-8 text-center text-sm text-gray-500">
            No sends in the last 14 days yet. Cal will draft and send on the next autopilot cycle — or click Run cycle
            now.
          </p>
        ) : (
          <div className="space-y-2 max-h-[28rem] overflow-y-auto">
            {sentTimeline.map((row) => (
              <SentRow key={row.id || `${row.at}-${row.title}`} row={row} />
            ))}
          </div>
        )}
      </div>

      {blocked.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-4 space-y-2">
          <p className="text-xs font-bold uppercase tracking-widest text-amber-900">
            Blocked matches ({blocked.length}) — Cal skipped these
          </p>
          <ul className="space-y-1 max-h-32 overflow-y-auto text-sm text-amber-950">
            {blocked.slice(0, 6).map((item, i) => (
              <li key={i} className="text-xs">
                <span className="font-semibold">{item.title}</span>
                {item.detail ? <span className="text-amber-900/80"> — {item.detail}</span> : null}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Manual override — collapsed, no bulk draft */}
      <details
        className="rounded-2xl border border-gray-200 bg-slate-50/50"
        onToggle={(e) => {
          if ((e.target as HTMLDetailsElement).open && draftProspects.length === 0) {
            void loadDraftProspects();
          }
        }}
      >
        <summary className="cursor-pointer px-5 py-4 text-sm font-semibold text-gray-700">
          Manual override — edit or send a specific draft
        </summary>
        <div className="border-t border-gray-200 px-5 py-4 space-y-3">
          <p className="text-xs text-gray-600">
            Cal handles drafting in the background. Only use this to fix copy or force-send one email. Do not bulk-draft
            from here — it blocks the page for minutes.
          </p>
          {loadingDrafts ? (
            <p className="text-sm text-gray-500 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading drafts…
            </p>
          ) : draftProspects.length === 0 ? (
            <p className="text-sm text-gray-500">No unsent drafts loaded.</p>
          ) : (
            draftProspects.slice(0, 15).map((p) => {
              const crmId = p.crm_account_id || "";
              const open = expandedDraftId === crmId;
              return (
                <div key={crmId || p.company_id} className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                  <button
                    type="button"
                    className="w-full px-3 py-2 text-left text-sm font-medium hover:bg-slate-50"
                    onClick={() => {
                      const next = open ? null : crmId;
                      setExpandedDraftId(next);
                      if (next) void loadDraftBody(crmId);
                    }}
                  >
                    {p.company_name} · {p.tier}
                  </button>
                  {open && crmId ? (
                    <div className="border-t px-3 py-3 space-y-2">
                      <textarea
                        rows={8}
                        className="w-full rounded border px-2 py-1 font-mono text-xs"
                        value={draftBodies[crmId] ?? (draftBodyLoading === crmId ? "Loading full draft…" : "")}
                        onChange={(e) => {
                          if (draftBodyLoading === crmId) return;
                          setDraftBodies((prev) => ({ ...prev, [crmId]: e.target.value }));
                        }}
                      />
                      {!isApproved(p.outreach_stage) && manualMode ? (
                        <button
                          type="button"
                          disabled={!!busy}
                          onClick={() => void approveOne(crmId)}
                          className="rounded bg-violet-600 px-3 py-1.5 text-xs font-bold text-white"
                        >
                          Approve
                        </button>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })
          )}
        </div>
      </details>

      <p className="text-[11px] text-gray-400 text-center pb-4">
        Background worker drafts {autopilot?.draft_batch ?? 100}/cycle · sends {sendLimit}/cycle ·{" "}
        <Link href="/supply-pipeline" className="text-emerald-700 underline">
          Supply pipeline
        </Link>
      </p>
    </section>
  );
}
