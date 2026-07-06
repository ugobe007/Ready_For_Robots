import { useCallback, useEffect, useState } from "react";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, getDirectApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { cleanAndClampText } from "@/lib/text";
import { toast } from "sonner";

type SupplyCompany = {
  robot_company: {
    id: number;
    company_name: string;
    robot_type?: string | null;
    target_market?: string | null;
    website?: string | null;
    contact_email?: string | null;
    lead_score?: number | null;
    vendor_list_score?: number | null;
  };
  contact_strategy: {
    primary?: { role?: string; contact?: string | null; source?: string; needs_verification?: boolean };
    targets?: Array<{ role?: string; contact?: string | null; source?: string; needs_verification?: boolean }>;
    recommended_to?: string[];
    communication_policy?: {
      role_inboxes?: string[];
      decision_maker_patterns?: string[];
      research_sources?: string[];
      researched_decision_makers?: Array<{
        first_name?: string;
        last_name?: string;
        title?: string | null;
        source_url?: string;
        source?: string;
      }>;
      research_status?: string;
    };
    research_notes?: string[];
  };
  contact_research?: {
    status?: string;
    decision_makers?: Array<{
      first_name?: string;
      last_name?: string;
      title?: string | null;
      source_url?: string;
      source?: string;
    }>;
    sources?: string[];
    linkedin_urls?: string[];
  };
  outreach_history?: Array<{
    id: string;
    status?: string;
    is_test?: boolean;
    to_emails?: string[];
    subject?: string;
    reply_to?: string | null;
    resend_id?: string | null;
    approved_at?: string | null;
    sent_at?: string | null;
    created_at?: string | null;
    delivery_status?: string | null;
    delivered_at?: string | null;
    opened_at?: string | null;
    clicked_at?: string | null;
    problem_at?: string | null;
    problem_reason?: string | null;
    cal_delivery_action?: string | null;
  }>;
  lead_matches: Array<{
    id: number;
    company_name: string;
    industry?: string | null;
    score?: number;
    signal?: string | null;
    why_match?: string | null;
  }>;
  email: { subject: string; body: string };
  cta: { signup: string; meeting: string };
};

type DraftState = {
  to: string;
  subject: string;
  body: string;
  approved: boolean;
  sending: boolean;
  sent: boolean;
  expanded: boolean;
  trackingId?: string;
  replyTo?: string;
  crmAccountId?: string;
  crmOutreachMessageId?: string;
  lastAction?: string;
};

type OutreachHistoryItem = NonNullable<SupplyCompany["outreach_history"]>[number];

const LIVE_SENT_STATUSES = new Set(["sent", "delivered", "opened", "clicked", "delivery_delayed", "bounced", "complained", "suppressed", "resent", "replied"]);

function deliveryLabel(item: OutreachHistoryItem) {
  const status = item.delivery_status || item.status || "tracked";
  if (item.clicked_at) return "Clicked";
  if (item.opened_at) return "Opened";
  if (item.delivered_at) return "Delivered";
  if (["bounced", "complained", "suppressed"].includes(status)) return "Problem";
  if (status === "delivery_delayed") return "Delayed";
  if (status === "resent") return "Resent";
  if (status === "sent") return "Sent";
  if (status === "test_sent") return "Test sent";
  if (status === "draft_approved") return "Approved";
  return status.replace(/_/g, " ");
}

function latestLiveHistory(row: SupplyCompany) {
  return (row.outreach_history || []).find((item) => !item.is_test);
}

function isLiveSent(item?: OutreachHistoryItem) {
  const status = item?.delivery_status || item?.status || "";
  return LIVE_SENT_STATUSES.has(status);
}

function isDraftApproved(item?: OutreachHistoryItem) {
  return (item?.status || "") === "draft_approved";
}

function expectedSupplySubject(row: SupplyCompany) {
  return `Sales channel signals for ${row.robot_company.company_name}`;
}

function initialDraft(row: SupplyCompany): DraftState {
  const recommended = row.contact_strategy.recommended_to || [];
  const contact = recommended.length ? recommended.join(", ") : row.contact_strategy.primary?.contact || row.robot_company.contact_email || "";
  const to = contact.includes("@") ? contact : "";
  const liveHistory = latestLiveHistory(row);
  const sent = isLiveSent(liveHistory);
  const approved = !sent && isDraftApproved(liveHistory);
  return {
    to,
    subject: expectedSupplySubject(row),
    body: row.email.body,
    approved,
    sending: false,
    sent,
    expanded: false,
    trackingId: liveHistory?.id,
    replyTo: liveHistory?.reply_to || undefined,
    lastAction: liveHistory?.delivery_status || liveHistory?.status,
  };
}

export default function SupplyPipeline() {
  const { session } = useAuth();
  const [rows, setRows] = useState<SupplyCompany[]>([]);
  const [drafts, setDrafts] = useState<Record<number, DraftState>>({});
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [sidebarView, setSidebarView] = useState<"needs_action" | "sent" | "all">("needs_action");

  const loadPipeline = useCallback(async () => {
    setLoading(true);
    setErr("");
    // The supply-side agent researches + matches each vendor (~20-30s). Hit Fly
    // directly to skip the Vercel proxy, and abort after 90s so the page never
    // spins forever — show a retryable error instead.
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 90_000);
    try {
      const response = await fetch(
        `${getDirectApiBase()}/api/robot-companies/agent/supply-side?limit=12&research_contacts=false`,
        liveFetchInit({ signal: ctrl.signal }),
      );
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      const companies = Array.isArray(payload.companies) ? payload.companies : [];
      setRows(companies);
      setDrafts(Object.fromEntries(companies.map((row: SupplyCompany) => [row.robot_company.id, initialDraft(row)])));
      setSelectedId(companies[0]?.robot_company?.id ?? null);
    } catch (e) {
      const aborted = e instanceof DOMException && e.name === "AbortError";
      setErr(
        aborted
          ? "The outreach agent took too long to research these companies. Tap Retry to try again."
          : e instanceof Error ? e.message : "Could not load supply pipeline",
      );
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPipeline();
  }, [loadPipeline]);

  const selected = selectedId == null ? null : rows.find((row) => row.robot_company.id === selectedId) ?? null;
  const selectedDraft = selected ? drafts[selected.robot_company.id] : null;
  const approvedCount = Object.values(drafts).filter((draft) => draft.approved && !draft.sent).length;
  const sentCount = Object.values(drafts).filter((draft) => draft.sent).length;
  const needsActionCount = Object.values(drafts).filter((draft) => !draft.sent).length;
  const visibleRows = rows.filter((row) => {
    const draft = drafts[row.robot_company.id];
    if (sidebarView === "sent") return Boolean(draft?.sent);
    if (sidebarView === "needs_action") return !draft?.sent;
    return true;
  });
  const signedInEmail = session?.user?.email || "";

  const patchDraft = (id: number, patch: Partial<DraftState>) => {
    setDrafts((current) => ({
      ...current,
      [id]: { ...current[id], ...patch },
    }));
  };

  const approveDraft = async (row: SupplyCompany) => {
    const id = row.robot_company.id;
    const draft = drafts[id];
    if (!draft) return;
    if (!validateDraftCompanyCopy(row, draft)) return;
    const recipients = parseRecipients(draft.to);
    if (!recipients.length) {
      toast.error("Add a valid recipient email before approving.");
      return;
    }
    if (!draft.subject.trim() || !draft.body.trim()) {
      toast.error("Subject and body are required before approval.");
      return;
    }
    patchDraft(id, { sending: true });
    try {
      const response = await fetch(
        `${getApiBase()}/api/robot-companies/${id}/email/approve`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            to_email: recipients,
            template_type: "supply_pipeline",
            subject: draft.subject,
            body: draft.body,
            payload: {
              operator_checkpoint: "Approved from supply pipeline review console",
              buyer_matches: row.lead_matches.slice(0, 3).map((lead) => lead.company_name),
            },
          }),
        }),
      );
      if (!response.ok) {
        const errorPayload = await response.json().catch(() => null);
        throw new Error(errorPayload?.detail || "Could not send email.");
      }
      const result = await response.json();
      patchDraft(id, {
        approved: true,
        sending: false,
        trackingId: result.supply_outreach_message_id,
        replyTo: result.reply_to,
        lastAction: result.status || "draft_approved",
      });
      toast.success("Draft approved and tracked.");
    } catch (e) {
      patchDraft(id, { sending: false });
      toast.error(e instanceof Error ? e.message : "Could not approve draft.");
    }
  };

  const approveAll = () => {
    void (async () => {
      for (const row of rows) {
        const draft = drafts[row.robot_company.id];
        if (draft && !draft.sent && !draft.approved) {
          await approveDraft(row);
        }
      }
    })();
  };

  const parseRecipients = (value: string) =>
    value
      .split(/[;,]/)
      .map((email) => email.trim())
      .filter((email) => email.includes("@"));

  const validateDraftCompanyCopy = (row: SupplyCompany, draft: DraftState) => {
    const expectedSubject = expectedSupplySubject(row);
    if (draft.subject.trim() !== expectedSubject) {
      toast.error(`Subject mismatch. Expected: ${expectedSubject}`);
      return false;
    }
    if (!draft.body.includes(row.robot_company.company_name)) {
      toast.error(`Draft body mismatch. It must mention ${row.robot_company.company_name}.`);
      return false;
    }
    return true;
  };

  const sendOne = async (row: SupplyCompany, test = false) => {
    const id = row.robot_company.id;
    const draft = drafts[id];
    if (!draft) return;
    if (!validateDraftCompanyCopy(row, draft)) return;
    const recipients = parseRecipients(draft.to);
    if (!test && !recipients.length) {
      toast.error("Add a valid recipient email before sending.");
      return;
    }
    if (test && !signedInEmail) {
      toast.error("Sign in before sending a test email to yourself.");
      return;
    }
    if (!draft.approved && !test) {
      toast.error("Approve the draft before sending.");
      return;
    }
    if (!test && !session?.access_token) {
      toast.error("Sign in before sending live outreach so SIGNAL can copy the message to your CRM.");
      return;
    }
    patchDraft(id, { sending: true });
    try {
      const endpoint = test ? "test-send" : "send";
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.access_token) Object.assign(headers, authHeader(session.access_token));
      const response = await fetch(
        `${getApiBase()}/api/robot-companies/${id}/email/${endpoint}`,
        liveFetchInit({
          method: "POST",
          headers,
          body: JSON.stringify({
            to_email: test ? signedInEmail : recipients,
            template_type: "supply_pipeline",
            subject: draft.subject,
            body: draft.body,
            approved_message_id: draft.trackingId,
          }),
        }),
      );
      if (!response.ok) throw new Error(await response.text());
      const result = await response.json();
      patchDraft(id, {
        sending: false,
        sent: !test || draft.sent,
        trackingId: result.supply_outreach_message_id || draft.trackingId,
        replyTo: result.reply_to || draft.replyTo,
        crmAccountId: result.crm_account_id || draft.crmAccountId,
        crmOutreachMessageId: result.crm_outreach_message_id || draft.crmOutreachMessageId,
        lastAction: result.status || (test ? "test_sent" : "sent"),
      });
      if (!test) {
        setSelectedId(null);
      }
      toast.success(test ? `Test email sent to ${signedInEmail}.` : `Sent outreach to ${row.robot_company.company_name} and copied it to CRM.`);
    } catch (e) {
      patchDraft(id, { sending: false });
      toast.error(e instanceof Error ? e.message : "Could not send email.");
    }
  };

  const bulkSendApproved = async () => {
    const approvedRows = rows.filter((row) => {
      const draft = drafts[row.robot_company.id];
      return draft?.approved && !draft.sent;
    });
    if (!approvedRows.length) {
      toast.info("No approved unsent drafts.");
      return;
    }
    for (const row of approvedRows) {
      // Sequential sends make failures visible and avoid provider rate spikes.
      await sendOne(row);
    }
  };

  const copyDraft = async () => {
    if (!selectedDraft) return;
    await navigator.clipboard.writeText(`To: ${selectedDraft.to}\nSubject: ${selectedDraft.subject}\n\n${selectedDraft.body}`);
    toast.success("Draft copied.");
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="admin-workspace flex-1 px-4 pb-12 pt-24">
        <div className="mx-auto max-w-6xl">
          <AdminNav />
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
            Marketplace supply pipeline
          </p>
          <h1 className="text-2xl font-black text-gray-900">
            Robot company outreach agent
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-gray-500">
            SIGNAL researches robot companies, identifies who to contact, shows three matched buyer leads, and drafts a signup plus meeting email for review.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-2 rounded-2xl border border-gray-200 bg-white p-3">
            <span className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-500">{approvedCount} approved</span>
            <span className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-500">{sentCount} sent</span>
            <a href="/admin" className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-600">
              Open Admin
            </a>
            <a href="/crm" className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-600">
              Open Buyer CRM
            </a>
            <a href="/sales-console" className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-600">
              Open Sales Console
            </a>
            <button
              type="button"
              onClick={approveAll}
              className="rounded-lg border border-violet-300 bg-violet-50 px-3 py-2 text-xs font-bold text-violet-900"
            >
              Bulk approve drafts
            </button>
            <button
              type="button"
              onClick={() => void bulkSendApproved()}
              className="rounded-lg border border-amber-400 bg-amber-400 px-3 py-2 text-xs font-bold text-[#111827]"
            >
              Bulk send approved emails
            </button>
            <p className="text-[11px] text-gray-400">Operator controls: review, edit, approve, then send. Nothing sends without approval.</p>
          </div>
          {err && (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm font-medium text-red-900">
              <span>{err}</span>
              <button
                type="button"
                onClick={() => void loadPipeline()}
                disabled={loading}
                className="rounded-lg border border-red-400 bg-white px-3 py-1.5 text-xs font-bold text-red-900 disabled:opacity-50"
              >
                {loading ? "Loading..." : "Retry"}
              </button>
            </div>
          )}
          {loading && !err && (
            <p className="mt-4 rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-500">
              SIGNAL is researching robot companies and matching buyer leads — this can take up to a minute.
            </p>
          )}

          <div className="mt-6 grid gap-4 lg:grid-cols-[360px_1fr]">
            <aside className="rounded-2xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-4 py-3">
                <p className="text-xs font-bold text-gray-700">{loading ? "Loading..." : `${visibleRows.length} shown · ${rows.length} total`}</p>
                <p className="mt-1 text-[11px] text-gray-400">Unsent prospects are separated from companies SIGNAL already contacted.</p>
                <div className="mt-3 grid grid-cols-3 gap-1 rounded-xl border border-gray-300 bg-gray-100 p-1">
                  {[
                    { key: "needs_action", label: "Unsent", count: needsActionCount },
                    { key: "sent", label: "Sent", count: sentCount },
                    { key: "all", label: "All", count: rows.length },
                  ].map((item) => (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => setSidebarView(item.key as "needs_action" | "sent" | "all")}
                      className={`rounded-lg px-2 py-1.5 text-[10px] font-bold transition ${
                        sidebarView === item.key ? "bg-amber-400 text-[#111827]" : "text-gray-500 hover:text-gray-900"
                      }`}
                    >
                      {item.label} {item.count}
                    </button>
                  ))}
                </div>
              </div>
              <div className="max-h-[680px] overflow-y-auto p-2">
                {visibleRows.length === 0 && (
                  <div className="m-2 rounded-xl border border-dashed border-gray-200 p-4 text-center">
                    <p className="text-xs font-bold text-gray-500">No companies in this view</p>
                    <p className="mt-1 text-[11px] text-gray-400">Switch tabs above to see sent or all companies.</p>
                  </div>
                )}
                {visibleRows.map((row) => {
                  const company = row.robot_company;
                  const active = company.id === selected?.robot_company.id;
                  const draft = drafts[company.id];
                  const liveHistory = latestLiveHistory(row);
                  const sentLabel = liveHistory ? deliveryLabel(liveHistory) : "Sent";
                  return (
                    <button
                      key={company.id}
                      type="button"
                      onClick={() => setSelectedId(company.id)}
                      className={`mb-2 w-full rounded-xl border px-3 py-2.5 text-left ${
                        active
                          ? "border-amber-400 bg-amber-50"
                          : draft?.sent
                          ? "border-emerald-300 bg-emerald-50"
                          : "border-gray-300 bg-white hover:border-gray-400"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-sm font-bold text-gray-800">{company.company_name}</p>
                        <span className="font-mono text-[11px]" style={{ color: "#FFB000" }}>
                          {Math.round(company.vendor_list_score ?? company.lead_score ?? 0)}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-[11px] text-gray-400">
                        {company.robot_type || "robotics"} · {company.target_market || "market TBD"}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {draft?.approved && !draft.sent && (
                          <span className="rounded-full bg-violet-100 px-2 py-0.5 text-[9px] font-bold text-violet-900">Approved</span>
                        )}
                        {draft?.sent && (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[9px] font-bold text-emerald-900">Contacted · {sentLabel}</span>
                        )}
                        {draft?.lastAction && !draft.sent && (
                          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[9px] font-bold text-gray-500">{draft.lastAction}</span>
                        )}
                        {!draft?.to && (
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[9px] font-bold text-amber-900">Needs email</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </aside>

            {selected && selectedDraft && (
              <section className="grid gap-4">
                <div className="rounded-2xl border border-gray-200 bg-white p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <h2 className="text-xl font-black text-gray-900">{selected.robot_company.company_name}</h2>
                      <p className="mt-1 text-sm text-gray-600">
                        {selected.robot_company.robot_type || "Robotics"} for {selected.robot_company.target_market || "target market review"}
                      </p>
                    </div>
                    {selected.robot_company.website && (
                      <a href={selected.robot_company.website} target="_blank" rel="noreferrer" className="text-xs font-bold text-emerald-700 underline">
                        Website
                      </a>
                    )}
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <div className="rounded-xl border border-gray-100 bg-white p-3">
                      <p className="text-[10px] uppercase tracking-widest text-gray-400">Who to contact</p>
                      <p className="mt-1 text-sm font-bold text-gray-800">{selected.contact_strategy.primary?.role || "Partnerships"}</p>
                      <p className="mt-1 break-all text-xs text-gray-500">{selected.contact_strategy.primary?.contact || selected.robot_company.contact_email || "Research contact first"}</p>
                      {selected.contact_strategy.primary?.needs_verification && (
                        <p className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-900">
                          Inferred email. Verify before sending.
                        </p>
                      )}
                    </div>
                    <div className="rounded-xl border border-gray-100 bg-white p-3 md:col-span-2">
                      <p className="text-[10px] uppercase tracking-widest text-gray-400">Research checklist</p>
                      <p className="mt-1 text-xs leading-relaxed text-gray-500">
                        {(selected.contact_strategy.research_notes || []).join(" ")}
                      </p>
                      <p className="mt-2 text-[10px] leading-relaxed text-gray-400">
                        Policy: send to role inboxes first
                        {" "}
                        {(selected.contact_strategy.communication_policy?.role_inboxes || []).join(", ") || "after domain research"}.
                        Named decision makers use first.last, first initial + last, last, and first-name patterns.
                      </p>
                      <p className="mt-2 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                        Research status: {selected.contact_research?.status || selected.contact_strategy.communication_policy?.research_status || "not run"}
                      </p>
                    </div>
                  </div>
                  {!!(selected.contact_research?.decision_makers || []).length && (
                    <div className="mt-3 rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-3">
                      <p className="text-[10px] font-semibold uppercase tracking-widest text-emerald-900">Researched decision makers</p>
                      <div className="mt-2 grid gap-2 md:grid-cols-3">
                        {(selected.contact_research?.decision_makers || []).map((person) => (
                          <div key={`${person.first_name}-${person.last_name}-${person.source_url}`} className="rounded-lg border border-gray-300 bg-gray-50 p-2">
                            <p className="text-xs font-bold text-gray-800">
                              {[person.first_name, person.last_name].filter(Boolean).join(" ")}
                            </p>
                            <p className="mt-1 text-[10px] text-gray-500">{person.title || "Decision maker"}</p>
                            {person.source_url && (
                              <a href={person.source_url} target="_blank" rel="noreferrer" className="mt-1 block truncate text-[10px] text-emerald-200/70 underline">
                                Source
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {(selected.contact_strategy.targets || []).length > 1 && (
                    <div className="mt-3 rounded-xl border border-gray-300 bg-gray-50 p-3">
                      <p className="text-[10px] uppercase tracking-widest text-gray-400">Email candidates</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {(selected.contact_strategy.targets || []).map((target) => (
                          <button
                            key={`${target.role}-${target.contact}`}
                            type="button"
                            onClick={() => target.contact && patchDraft(selected.robot_company.id, { to: target.contact, approved: false })}
                            className="rounded-full border border-gray-300 bg-white px-2 py-1 text-[10px] font-bold text-gray-700 hover:border-amber-400 hover:text-amber-900"
                          >
                            {target.role}: {target.contact || "research"}
                          </button>
                        ))}
                      </div>
                      {!!selected.contact_strategy.recommended_to?.length && (
                        <button
                          type="button"
                          onClick={() => patchDraft(selected.robot_company.id, { to: selected.contact_strategy.recommended_to?.join(", ") || "", approved: false })}
                          className="mt-3 rounded-lg border border-amber-400 bg-amber-50 px-3 py-2 text-[10px] font-bold text-amber-950"
                        >
                          Use policy recipients
                        </button>
                      )}
                    </div>
                  )}
                  <div className="mt-3 rounded-xl border border-gray-300 bg-gray-50 p-3">
                    <button
                      type="button"
                      onClick={() => patchDraft(selected.robot_company.id, { expanded: !selectedDraft.expanded })}
                      className="text-xs font-bold text-amber-800 underline"
                    >
                      {selectedDraft.expanded ? "Hide details" : "Show details"}
                    </button>
                    {selectedDraft.expanded && (
                      <div className="mt-3 grid gap-2 text-xs text-gray-500 md:grid-cols-2">
                        <p><span className="text-gray-600">Website:</span> {selected.robot_company.website || "Unknown"}</p>
                        <p><span className="text-gray-600">Policy recipients:</span> {(selected.contact_strategy.recommended_to || []).join(", ") || "Research needed"}</p>
                        <p><span className="text-gray-600">Research pages:</span> {(selected.contact_research?.sources || []).length || 0}</p>
                        <p><span className="text-gray-600">LinkedIn links:</span> {(selected.contact_research?.linkedin_urls || []).length || 0}</p>
                        <p><span className="text-gray-600">Tracking ID:</span> {selectedDraft.trackingId || "Not tracked yet"}</p>
                        <p><span className="text-gray-600">Reply path:</span> {selectedDraft.replyTo || "Created on approval/send"}</p>
                        <p><span className="text-gray-600">Robot type:</span> {selected.robot_company.robot_type || "Unknown"}</p>
                        <p><span className="text-gray-600">Target market:</span> {selected.robot_company.target_market || "Unknown"}</p>
                        <p><span className="text-gray-600">Lead score:</span> {selected.robot_company.lead_score ?? "Unknown"}</p>
                        <p><span className="text-gray-600">Vendor score:</span> {selected.robot_company.vendor_list_score ?? "Unknown"}</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border border-gray-200 bg-white p-5">
                  <p className="text-[10px] uppercase tracking-widest text-gray-400">3 buyer lead matches for email</p>
                  <div className="mt-3 grid gap-3 md:grid-cols-3">
                    {selected.lead_matches.slice(0, 3).map((lead) => (
                      <div key={lead.id} className="rounded-xl border border-gray-100 bg-white p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="truncate text-sm font-bold text-gray-900/82">{lead.company_name}</p>
                          <span className="font-mono text-[10px] text-emerald-300">{Math.round(lead.score || 0)}</span>
                        </div>
                        <p className="mt-1 text-[11px] text-gray-400">{lead.industry || "industry unknown"}</p>
                        <p className="mt-2 text-[11px] leading-relaxed text-gray-500">{cleanAndClampText(lead.why_match, 150)}</p>
                        <p className="mt-2 text-[10px] leading-relaxed text-gray-400">{cleanAndClampText(lead.signal, 130)}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-gray-200 bg-white p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-[10px] uppercase tracking-widest text-gray-400">Editable outreach draft</p>
                    <span className={`rounded-full border px-2 py-1 text-[10px] font-bold ${
                      selectedDraft.sent
                        ? "border-emerald-400 bg-emerald-50 text-emerald-900"
                        : selectedDraft.approved
                        ? "border-emerald-400 bg-emerald-50 text-emerald-900"
                        : "border-amber-400 bg-amber-50 text-amber-950"
                    }`}>
                      {selectedDraft.sent ? "Sent" : selectedDraft.approved ? "Approved" : "Needs approval"}
                    </span>
                  </div>
                  {!!(selected.outreach_history || []).length && (
                    <div className="mb-4 rounded-xl border border-gray-100 bg-black/10 p-3">
                      <p className="text-[10px] uppercase tracking-widest text-gray-400">Tracked outreach history</p>
                      <div className="mt-2 grid gap-2">
                        {(selected.outreach_history || []).slice(0, 3).map((item) => (
                          <div key={item.id} className="rounded-lg border border-gray-100 bg-white p-2 text-[11px] text-gray-500">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="font-bold text-gray-600">{item.is_test ? "Test" : "Live"} · {deliveryLabel(item)}</span>
                              <span>{item.sent_at || item.approved_at || item.created_at || ""}</span>
                            </div>
                            <p className="mt-1 truncate">{item.subject}</p>
                            <p className="mt-1 truncate">To: {(item.to_emails || []).join(", ")}</p>
                            {(item.resend_id || item.reply_to) && (
                              <p className="mt-1 truncate text-gray-400">
                                Resend: {item.resend_id || "pending"} · Reply: {item.reply_to || "not set"}
                              </p>
                            )}
                            {(item.problem_reason || item.cal_delivery_action) && (
                              <p className="mt-1 rounded border border-amber-300 bg-amber-50 px-2 py-1 text-amber-950">
                                {item.cal_delivery_action || item.problem_reason}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="grid gap-3">
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-widest text-gray-400">Recipients</span>
                      <input
                        value={selectedDraft.to}
                        onChange={(e) => patchDraft(selected.robot_company.id, { to: e.target.value, approved: false })}
                        placeholder="partnerships@robotcompany.com, events@robotcompany.com, marketing@robotcompany.com, sales@robotcompany.com"
                        className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400"
                      />
                      <span className="mt-1 block text-[10px] text-gray-400">
                        Separate multiple recipients with commas. Inferred role inboxes and decision-maker patterns should be verified before live send.
                      </span>
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-widest text-gray-400">Subject</span>
                      <input
                        value={selectedDraft.subject}
                        onChange={(e) => patchDraft(selected.robot_company.id, { subject: e.target.value, approved: false })}
                        className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none"
                      />
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-widest text-gray-400">Body</span>
                      <textarea
                        value={selectedDraft.body}
                        onChange={(e) => patchDraft(selected.robot_company.id, { body: e.target.value, approved: false })}
                        rows={14}
                        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm leading-relaxed text-gray-900 outline-none"
                      />
                    </label>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void approveDraft(selected)}
                      disabled={selectedDraft.sending}
                      className="rounded-lg border border-violet-300 bg-violet-50 px-3 py-2 text-xs font-bold text-violet-900 disabled:opacity-50"
                    >
                      Approve draft
                    </button>
                    <button
                      type="button"
                      onClick={() => void sendOne(selected, true)}
                      disabled={selectedDraft.sending || !signedInEmail}
                      className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-800 disabled:opacity-50"
                    >
                      Send test to me
                    </button>
                    <button
                      type="button"
                      onClick={() => void sendOne(selected)}
                      disabled={selectedDraft.sending || selectedDraft.sent || !selectedDraft.approved || !selectedDraft.to}
                      className="rounded-lg border border-amber-400 bg-amber-400 px-3 py-2 text-xs font-bold text-[#111827] disabled:opacity-50"
                    >
                      {selectedDraft.sent ? "Sent" : selectedDraft.sending ? "Sending..." : "Send live email"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void copyDraft()}
                      className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-500"
                    >
                      Copy
                    </button>
                    <div
                      className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-bold ${
                        selectedDraft.sent
                          ? "border-emerald-500 bg-emerald-50 text-emerald-900"
                          : "border-gray-200 bg-white text-gray-400"
                      }`}
                      title={selectedDraft.sent ? "Outreach sent and copied to CRM sent messages." : "Live send will record this in CRM sent messages."}
                    >
                      <span
                        className={`flex h-4 w-4 items-center justify-center rounded border ${
                          selectedDraft.sent ? "border-emerald-300 bg-emerald-400 text-[#111827]" : "border-gray-200"
                        }`}
                      >
                        {selectedDraft.sent ? "✓" : ""}
                      </span>
                      Sent to CRM
                    </div>
                  </div>
                  {selectedDraft.sent && (
                    <div className="mt-3 rounded-xl border border-emerald-300 bg-emerald-50 p-3 text-xs font-medium text-emerald-950">
                      <p className="font-bold text-emerald-900">Workflow checkpoint complete: email sent and activity copied to CRM sent messages.</p>
                      <p className="mt-1 text-emerald-800">
                        CRM account: {selectedDraft.crmAccountId || "tracked"} · Message: {selectedDraft.crmOutreachMessageId || selectedDraft.trackingId || "tracked"}
                      </p>
                    </div>
                  )}
                  <div className="mt-4 grid gap-2 md:grid-cols-2">
                    <p className="rounded-xl border border-gray-100 bg-white p-3 text-xs text-gray-500">{selected.cta.signup}</p>
                    <p className="rounded-xl border border-gray-100 bg-white p-3 text-xs text-gray-500">{selected.cta.meeting}</p>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
