import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
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

function initialDraft(row: SupplyCompany): DraftState {
  const recommended = row.contact_strategy.recommended_to || [];
  const contact = recommended.length ? recommended.join(", ") : row.contact_strategy.primary?.contact || row.robot_company.contact_email || "";
  const to = contact.includes("@") ? contact : "";
  return {
    to,
    subject: row.email.subject,
    body: row.email.body,
    approved: false,
    sending: false,
    sent: false,
    expanded: false,
    trackingId: row.outreach_history?.[0]?.id,
    replyTo: row.outreach_history?.[0]?.reply_to || undefined,
    lastAction: row.outreach_history?.[0]?.status,
  };
}

export default function SupplyPipeline() {
  const { session } = useAuth();
  const [rows, setRows] = useState<SupplyCompany[]>([]);
  const [drafts, setDrafts] = useState<Record<number, DraftState>>({});
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const response = await fetch(`${getApiBase()}/api/robot-companies/agent/supply-side?limit=12&research_contacts=false`, liveFetchInit());
        if (!response.ok) throw new Error(await response.text());
        const payload = await response.json();
        const companies = Array.isArray(payload.companies) ? payload.companies : [];
        setRows(companies);
        setDrafts(Object.fromEntries(companies.map((row: SupplyCompany) => [row.robot_company.id, initialDraft(row)])));
        setSelectedId(companies[0]?.robot_company?.id ?? null);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Could not load supply pipeline");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const selected = selectedId == null ? null : rows.find((row) => row.robot_company.id === selectedId) ?? null;
  const selectedDraft = selected ? drafts[selected.robot_company.id] : null;
  const approvedCount = Object.values(drafts).filter((draft) => draft.approved && !draft.sent).length;
  const sentCount = Object.values(drafts).filter((draft) => draft.sent).length;

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

  const sendOne = async (row: SupplyCompany, test = false) => {
    const id = row.robot_company.id;
    const draft = drafts[id];
    if (!draft) return;
    const recipients = parseRecipients(draft.to);
    if (!recipients.length) {
      toast.error("Add a valid recipient email before sending.");
      return;
    }
    if (!draft.approved && !test) {
      toast.error("Approve the draft before sending.");
      return;
    }
    if (!test && !session?.access_token) {
      toast.error("Sign in before sending live outreach so SCOUT can copy the message to your CRM.");
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
            to_email: recipients,
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
      toast.success(test ? "Test email sent." : `Sent outreach to ${row.robot_company.company_name} and copied it to CRM.`);
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
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 px-4 pb-12 pt-24">
        <div className="mx-auto max-w-6xl">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
            Marketplace supply pipeline
          </p>
          <h1 className="text-2xl font-black text-white" style={{ fontFamily: "'Sora', system-ui" }}>
            Robot company outreach agent
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/45">
            Cal researches robot companies, identifies who to contact, shows three matched buyer leads, and drafts a signup plus meeting email for review.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.025] p-3">
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/55">{approvedCount} approved</span>
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/55">{sentCount} sent</span>
            <a href="/sales-console" className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-bold text-white/65">
              Open Sales Console
            </a>
            <button
              type="button"
              onClick={approveAll}
              className="rounded-lg border border-violet-400/35 bg-violet-400/10 px-3 py-2 text-xs font-bold text-violet-100"
            >
              Bulk approve all
            </button>
            <button
              type="button"
              onClick={() => void bulkSendApproved()}
              className="rounded-lg border border-amber-400 bg-amber-400 px-3 py-2 text-xs font-bold text-[#160b2c]"
            >
              Bulk send approved
            </button>
            <p className="text-[11px] text-white/35">Operator controls: review, edit, approve, then send. Nothing sends without approval.</p>
          </div>
          {err && <p className="mt-4 rounded-lg border border-red-500/30 p-3 text-sm text-red-200">{err}</p>}

          <div className="mt-6 grid gap-4 lg:grid-cols-[360px_1fr]">
            <aside className="rounded-2xl border border-white/10 bg-white/[0.025]">
              <div className="border-b border-white/8 px-4 py-3">
                <p className="text-xs font-bold text-white/75">{loading ? "Loading..." : `${rows.length} robot companies`}</p>
                <p className="mt-1 text-[11px] text-white/35">Approve/send queue for marketplace supply.</p>
              </div>
              <div className="max-h-[680px] overflow-y-auto p-2">
                {rows.map((row) => {
                  const company = row.robot_company;
                  const active = company.id === selected?.robot_company.id;
                  const draft = drafts[company.id];
                  return (
                    <button
                      key={company.id}
                      type="button"
                      onClick={() => setSelectedId(company.id)}
                      className="mb-2 w-full rounded-xl border px-3 py-2.5 text-left"
                      style={active ? { borderColor: "rgba(255,176,0,0.45)", background: "rgba(255,176,0,0.08)" } : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-sm font-bold text-white/85">{company.company_name}</p>
                        <span className="font-mono text-[11px]" style={{ color: "#FFB000" }}>
                          {Math.round(company.vendor_list_score ?? company.lead_score ?? 0)}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-[11px] text-white/35">
                        {company.robot_type || "robotics"} · {company.target_market || "market TBD"}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {draft?.approved && !draft.sent && (
                          <span className="rounded-full bg-violet-400/12 px-2 py-0.5 text-[9px] font-bold text-violet-100">Approved</span>
                        )}
                        {draft?.sent && (
                          <span className="rounded-full bg-emerald-400/12 px-2 py-0.5 text-[9px] font-bold text-emerald-100">Sent</span>
                        )}
                        {draft?.lastAction && !draft.sent && (
                          <span className="rounded-full bg-white/8 px-2 py-0.5 text-[9px] font-bold text-white/45">{draft.lastAction}</span>
                        )}
                        {!draft?.to && (
                          <span className="rounded-full bg-amber-400/12 px-2 py-0.5 text-[9px] font-bold text-amber-100">Needs email</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </aside>

            {selected && selectedDraft && (
              <section className="grid gap-4">
                <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <h2 className="text-xl font-black text-white">{selected.robot_company.company_name}</h2>
                      <p className="mt-1 text-sm text-white/42">
                        {selected.robot_company.robot_type || "Robotics"} for {selected.robot_company.target_market || "target market review"}
                      </p>
                    </div>
                    {selected.robot_company.website && (
                      <a href={selected.robot_company.website} target="_blank" rel="noreferrer" className="text-xs font-bold text-amber-300 underline">
                        Website
                      </a>
                    )}
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
                      <p className="text-[10px] uppercase tracking-widest text-white/30">Who to contact</p>
                      <p className="mt-1 text-sm font-bold text-white/80">{selected.contact_strategy.primary?.role || "Partnerships"}</p>
                      <p className="mt-1 break-all text-xs text-white/45">{selected.contact_strategy.primary?.contact || selected.robot_company.contact_email || "Research contact first"}</p>
                      {selected.contact_strategy.primary?.needs_verification && (
                        <p className="mt-2 rounded-lg border border-amber-400/20 bg-amber-400/10 px-2 py-1 text-[10px] font-bold text-amber-100">
                          Inferred email. Verify before sending.
                        </p>
                      )}
                    </div>
                    <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3 md:col-span-2">
                      <p className="text-[10px] uppercase tracking-widest text-white/30">Research checklist</p>
                      <p className="mt-1 text-xs leading-relaxed text-white/45">
                        {(selected.contact_strategy.research_notes || []).join(" ")}
                      </p>
                      <p className="mt-2 text-[10px] leading-relaxed text-white/35">
                        Policy: send to role inboxes first
                        {" "}
                        {(selected.contact_strategy.communication_policy?.role_inboxes || []).join(", ") || "after domain research"}.
                        Named decision makers use first.last, first initial + last, last, and first-name patterns.
                      </p>
                      <p className="mt-2 text-[10px] font-bold uppercase tracking-widest text-white/30">
                        Research status: {selected.contact_research?.status || selected.contact_strategy.communication_policy?.research_status || "not run"}
                      </p>
                    </div>
                  </div>
                  {!!(selected.contact_research?.decision_makers || []).length && (
                    <div className="mt-3 rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-3">
                      <p className="text-[10px] uppercase tracking-widest text-emerald-100/70">Researched decision makers</p>
                      <div className="mt-2 grid gap-2 md:grid-cols-3">
                        {(selected.contact_research?.decision_makers || []).map((person) => (
                          <div key={`${person.first_name}-${person.last_name}-${person.source_url}`} className="rounded-lg border border-white/8 bg-black/10 p-2">
                            <p className="text-xs font-bold text-white/80">
                              {[person.first_name, person.last_name].filter(Boolean).join(" ")}
                            </p>
                            <p className="mt-1 text-[10px] text-white/40">{person.title || "Decision maker"}</p>
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
                    <div className="mt-3 rounded-xl border border-white/8 bg-black/10 p-3">
                      <p className="text-[10px] uppercase tracking-widest text-white/30">Email candidates</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {(selected.contact_strategy.targets || []).map((target) => (
                          <button
                            key={`${target.role}-${target.contact}`}
                            type="button"
                            onClick={() => target.contact && patchDraft(selected.robot_company.id, { to: target.contact, approved: false })}
                            className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-1 text-[10px] font-bold text-white/55 hover:border-amber-400/40 hover:text-amber-100"
                          >
                            {target.role}: {target.contact || "research"}
                          </button>
                        ))}
                      </div>
                      {!!selected.contact_strategy.recommended_to?.length && (
                        <button
                          type="button"
                          onClick={() => patchDraft(selected.robot_company.id, { to: selected.contact_strategy.recommended_to?.join(", ") || "", approved: false })}
                          className="mt-3 rounded-lg border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-[10px] font-bold text-amber-100"
                        >
                          Use policy recipients
                        </button>
                      )}
                    </div>
                  )}
                  <div className="mt-3 rounded-xl border border-white/8 bg-black/10 p-3">
                    <button
                      type="button"
                      onClick={() => patchDraft(selected.robot_company.id, { expanded: !selectedDraft.expanded })}
                      className="text-xs font-bold text-amber-300 underline"
                    >
                      {selectedDraft.expanded ? "Hide details" : "Show details"}
                    </button>
                    {selectedDraft.expanded && (
                      <div className="mt-3 grid gap-2 text-xs text-white/45 md:grid-cols-2">
                        <p><span className="text-white/70">Website:</span> {selected.robot_company.website || "Unknown"}</p>
                        <p><span className="text-white/70">Policy recipients:</span> {(selected.contact_strategy.recommended_to || []).join(", ") || "Research needed"}</p>
                        <p><span className="text-white/70">Research pages:</span> {(selected.contact_research?.sources || []).length || 0}</p>
                        <p><span className="text-white/70">LinkedIn links:</span> {(selected.contact_research?.linkedin_urls || []).length || 0}</p>
                        <p><span className="text-white/70">Tracking ID:</span> {selectedDraft.trackingId || "Not tracked yet"}</p>
                        <p><span className="text-white/70">Reply path:</span> {selectedDraft.replyTo || "Created on approval/send"}</p>
                        <p><span className="text-white/70">Robot type:</span> {selected.robot_company.robot_type || "Unknown"}</p>
                        <p><span className="text-white/70">Target market:</span> {selected.robot_company.target_market || "Unknown"}</p>
                        <p><span className="text-white/70">Lead score:</span> {selected.robot_company.lead_score ?? "Unknown"}</p>
                        <p><span className="text-white/70">Vendor score:</span> {selected.robot_company.vendor_list_score ?? "Unknown"}</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
                  <p className="text-[10px] uppercase tracking-widest text-white/30">3 buyer lead matches for email</p>
                  <div className="mt-3 grid gap-3 md:grid-cols-3">
                    {selected.lead_matches.slice(0, 3).map((lead) => (
                      <div key={lead.id} className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="truncate text-sm font-bold text-white/82">{lead.company_name}</p>
                          <span className="font-mono text-[10px] text-emerald-300">{Math.round(lead.score || 0)}</span>
                        </div>
                        <p className="mt-1 text-[11px] text-white/35">{lead.industry || "industry unknown"}</p>
                        <p className="mt-2 text-[11px] leading-relaxed text-white/48">{cleanAndClampText(lead.why_match, 150)}</p>
                        <p className="mt-2 text-[10px] leading-relaxed text-white/30">{cleanAndClampText(lead.signal, 130)}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-[10px] uppercase tracking-widest text-white/30">Editable outreach draft</p>
                    <span className={`rounded-full border px-2 py-1 text-[10px] font-bold ${
                      selectedDraft.sent
                        ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-100"
                        : selectedDraft.approved
                        ? "border-violet-400/30 bg-violet-400/10 text-violet-100"
                        : "border-amber-400/30 bg-amber-400/10 text-amber-100"
                    }`}>
                      {selectedDraft.sent ? "Sent" : selectedDraft.approved ? "Approved" : "Needs approval"}
                    </span>
                  </div>
                  {!!(selected.outreach_history || []).length && (
                    <div className="mb-4 rounded-xl border border-white/8 bg-black/10 p-3">
                      <p className="text-[10px] uppercase tracking-widest text-white/30">Tracked outreach history</p>
                      <div className="mt-2 grid gap-2">
                        {(selected.outreach_history || []).slice(0, 3).map((item) => (
                          <div key={item.id} className="rounded-lg border border-white/8 bg-white/[0.025] p-2 text-[11px] text-white/45">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="font-bold text-white/65">{item.is_test ? "Test" : "Live"} · {item.status || "tracked"}</span>
                              <span>{item.sent_at || item.approved_at || item.created_at || ""}</span>
                            </div>
                            <p className="mt-1 truncate">{item.subject}</p>
                            <p className="mt-1 truncate">To: {(item.to_emails || []).join(", ")}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="grid gap-3">
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Recipients</span>
                      <input
                        value={selectedDraft.to}
                        onChange={(e) => patchDraft(selected.robot_company.id, { to: e.target.value, approved: false })}
                        placeholder="partnerships@robotcompany.com, events@robotcompany.com, marketing@robotcompany.com, sales@robotcompany.com"
                        className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                      />
                      <span className="mt-1 block text-[10px] text-white/30">
                        Separate multiple recipients with commas. Inferred role inboxes and decision-maker patterns should be verified before live send.
                      </span>
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Subject</span>
                      <input
                        value={selectedDraft.subject}
                        onChange={(e) => patchDraft(selected.robot_company.id, { subject: e.target.value, approved: false })}
                        className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none"
                      />
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Body</span>
                      <textarea
                        value={selectedDraft.body}
                        onChange={(e) => patchDraft(selected.robot_company.id, { body: e.target.value, approved: false })}
                        rows={14}
                        className="w-full rounded-lg border border-white/10 bg-black/15 px-3 py-2 text-sm leading-relaxed text-white outline-none"
                      />
                    </label>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void approveDraft(selected)}
                      disabled={selectedDraft.sending}
                      className="rounded-lg border border-violet-400/35 bg-violet-400/10 px-3 py-2 text-xs font-bold text-violet-100 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      onClick={() => void sendOne(selected, true)}
                      disabled={selectedDraft.sending || !selectedDraft.to}
                      className="rounded-lg border border-white/15 bg-white/[0.05] px-3 py-2 text-xs font-bold text-white/75 disabled:opacity-50"
                    >
                      Send test
                    </button>
                    <button
                      type="button"
                      onClick={() => void sendOne(selected)}
                      disabled={selectedDraft.sending || selectedDraft.sent || !selectedDraft.approved || !selectedDraft.to}
                      className="rounded-lg border border-amber-400 bg-amber-400 px-3 py-2 text-xs font-bold text-[#160b2c] disabled:opacity-50"
                    >
                      {selectedDraft.sent ? "Sent" : selectedDraft.sending ? "Sending..." : "Send approved"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void copyDraft()}
                      className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-bold text-white/55"
                    >
                      Copy
                    </button>
                    <div
                      className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-bold ${
                        selectedDraft.sent
                          ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-100"
                          : "border-white/10 bg-white/[0.025] text-white/35"
                      }`}
                      title={selectedDraft.sent ? "Outreach sent and copied to CRM." : "Send approved outreach to complete this checkpoint."}
                    >
                      <span
                        className={`flex h-4 w-4 items-center justify-center rounded border ${
                          selectedDraft.sent ? "border-emerald-300 bg-emerald-400 text-[#0d0520]" : "border-white/20"
                        }`}
                      >
                        {selectedDraft.sent ? "✓" : ""}
                      </span>
                      Sent checkpoint
                    </div>
                  </div>
                  {selectedDraft.sent && (
                    <div className="mt-3 rounded-xl border border-emerald-400/20 bg-emerald-400/8 p-3 text-xs text-emerald-100">
                      <p className="font-bold">Workflow checkpoint complete: email sent and activity copied to CRM.</p>
                      <p className="mt-1 text-emerald-100/70">
                        CRM account: {selectedDraft.crmAccountId || "tracked"} · Message: {selectedDraft.crmOutreachMessageId || selectedDraft.trackingId || "tracked"}
                      </p>
                    </div>
                  )}
                  <div className="mt-4 grid gap-2 md:grid-cols-2">
                    <p className="rounded-xl border border-white/8 bg-white/[0.025] p-3 text-xs text-white/45">{selected.cta.signup}</p>
                    <p className="rounded-xl border border-white/8 bg-white/[0.025] p-3 text-xs text-white/45">{selected.cta.meeting}</p>
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
