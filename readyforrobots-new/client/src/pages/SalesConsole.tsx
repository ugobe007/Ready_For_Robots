import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import AdminNav from "@/components/AdminNav";
import { JOBS_HEADER_OFFSET_CLASS } from "@/lib/jobsWorkflow";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { toast } from "sonner";
import { FileText, ShieldCheck, CheckCircle2, ExternalLink, Clock, Zap, Mail } from "lucide-react";
import CalProposalQuoteDrawer from "@/components/admin/CalProposalQuoteDrawer";
import CalAutopilotSwitch from "@/components/admin/CalAutopilotSwitch";
import ResendEmailModal from "@/components/ResendEmailModal";

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
  next_best_action?: {
    intent?: string;
    recommendation?: string;
    stage_after?: string;
  };
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
  source_domain_priorities?: {
    key: string;
    score: number;
    positive_events?: number;
    negative_events?: number;
  }[];
  signal_type_priorities?: {
    key: string;
    score: number;
    positive_events?: number;
    negative_events?: number;
  }[];
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
  if (status === "sent") return "#10B981";
  if (status === "failed" || status === "blocked") return "#F87171";
  if (status === "awaiting_approval") return "#FBBF24";
  return "#94A3B8";
}

function actionLabel(action: SalesAction) {
  const persona =
    action.payload?.responder_persona === "max" ? "Technical" : "Outreach";
  return `${persona}: ${action.action_type.replace(/_/g, " ")}`;
}

export default function SalesConsole() {
  const { session, loading } = useAuth();
  const [rows, setRows] = useState<SalesOpportunity[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selected, setSelected] = useState<SalesOpportunity | null>(null);
  const [prospects, setProspects] = useState<ApolloProspect[]>([]);
  const [prospectTitles, setProspectTitles] = useState<string[]>([]);
  const [learningReport, setLearningReport] =
    useState<SalesLearningReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [prospectBusy, setProspectBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [prospectMsg, setProspectMsg] = useState("");
  const [recipientOverride, setRecipientOverride] = useState("");
  const [isProposalDrawerOpen, setIsProposalDrawerOpen] = useState(false);
  const [autopilotEnabled, setAutopilotEnabled] = useState(true);
  const [stageFilter, setStageFilter] = useState("all");
  const [resendModal, setResendModal] = useState<{
    isOpen: boolean;
    to: string;
    subject: string;
    body: string;
    companyName: string;
    crmAccountId?: string;
  } | null>(null);

  const filteredRows = useMemo(() => {
    return rows.filter(r => {
      if (stageFilter === "all") return true;
      if (stageFilter === "contact_qualification") return r.current_stage === "contact_qualification" || !r.latest_message?.to_email;
      if (stageFilter === "ready_for_draft") return r.current_stage === "ready_for_draft";
      if (stageFilter === "intro_sent") return r.current_stage === "intro_sent" || r.last_inbound_at != null;
      if (stageFilter === "placement") return r.current_stage === "placement";
      return true;
    });
  }, [rows, stageFilter]);

  const [confirmEmail, setConfirmEmail] = useState("");
  const [confirmName, setConfirmName] = useState("");
  const [confirmTitle, setConfirmTitle] = useState("");
  const [confirmingContact, setConfirmingContact] = useState(false);

  const runAutomaticOutreachCycle = async () => {
    setBusy(true);
    toast.info("Executing Phelan automatic outreach cycle...");
    try {
      const res = await authFetch("/api/admin/cal/autonomy-run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dry_run: false }),
      });
      toast.success(
        `Phelan automatic outreach complete! Drafted: ${res?.drafted ?? 0}, Refreshed: ${res?.refreshed ?? 0}, Sent: ${res?.sent ?? 0}.`
      );
      await loadRows();
    } catch (e) {
      toast.error(
        e instanceof Error ? e.message : "Could not execute automatic outreach cycle."
      );
    } finally {
      setBusy(false);
    }
  };

  const handleToggleAutopilot = async (nextEnabled: boolean) => {
    setBusy(true);
    try {
      const res = await authFetch("/api/admin/cal/autonomy-toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: nextEnabled }),
      });
      setAutopilotEnabled(Boolean(res?.enabled));
      toast.success(`Phelan autopilot turned ${res?.enabled ? "ON" : "OFF"}.`);
    } catch (e) {
      toast.error(
        e instanceof Error ? e.message : "Could not toggle Phelan autopilot."
      );
    } finally {
      setBusy(false);
    }
  };

  const seedOpportunitiesFromPipeline = async () => {
    setBusy(true);
    try {
      const res = await authFetch("/api/sales/opportunities/seed", {
        method: "POST",
      });
      toast.success(`Imported ${res?.created_count ?? 0} pipeline accounts into queue!`);
      await loadRows();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not seed opportunities.");
    } finally {
      setBusy(false);
    }
  };

  const saveConfirmedContact = async () => {
    if (!selected || !confirmEmail) {
      toast.error("Please enter a valid OEM/Vendor email address.");
      return;
    }
    setConfirmingContact(true);
    try {
      const updated = (await authFetch(
        `/api/sales/opportunities/${selected.id}/confirm-contact`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contact_email: confirmEmail,
            contact_name: confirmName || undefined,
            contact_title: confirmTitle || undefined,
          }),
        }
      )) as SalesOpportunity;
      setSelected(updated);
      setRecipientOverride(confirmEmail);
      toast.success(`Confirmed OEM/Vendor email: ${confirmEmail}`);
      await loadRows();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not confirm contact email.");
    } finally {
      setConfirmingContact(false);
    }
  };

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const token = session?.access_token;
      if (!token) throw new Error("Not signed in");
      const response = await fetch(
        `${getApiBase()}${path}`,
        liveFetchInit({
          ...init,
          headers: { ...authHeader(token), ...init.headers },
        })
      );
      const text = await response.text();
      if (!response.ok) throw new Error(text || response.statusText);
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token]
  );

  const loadRows = useCallback(async () => {
    if (!session?.access_token) return;
    setBusy(true);
    setMsg("");
    try {
      const data = (await authFetch(
        "/api/sales/opportunities"
      )) as SalesOpportunity[];
      const list = Array.isArray(data) ? data : [];
      setRows(list);
      setSelectedId(prev =>
        list.some(row => row.id === prev) ? prev : (list[0]?.id ?? "")
      );
      if (!list.length) setSelected(null);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not load sales console");
    } finally {
      setBusy(false);
    }
  }, [authFetch, session?.access_token]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oppId = params.get("opportunity_id");
    if (oppId) setSelectedId(oppId);
  }, []);

  useEffect(() => {
    void loadRows();
  }, [loadRows]);

  useEffect(() => {
    if (!session?.access_token) return;
    (async () => {
      try {
        const data = (await authFetch(
          "/api/sales/learning"
        )) as SalesLearningReport;
        setLearningReport(data);
      } catch {
        setLearningReport(null);
      }
      try {
        const status = await authFetch("/api/admin/cal/autonomy-status");
        if (status && typeof status.enabled === "boolean") {
          setAutopilotEnabled(status.enabled);
        }
      } catch {
        /* fallback to default */
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
        const detail = (await authFetch(
          `/api/sales/opportunities/${selectedId}`
        )) as SalesOpportunity;
        setSelected(detail);
        const latestFrom = detail.latest_message?.direction === "inbound" ? detail.latest_message.from_email : "";
        setRecipientOverride(latestFrom || "");
        setConfirmEmail(latestFrom || "");
        setConfirmName("");
        setConfirmTitle("");
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
      const result = await authFetch(
        `/api/sales/opportunities/${selected.id}/prospects`
      );
      setProspects(Array.isArray(result.prospects) ? result.prospects : []);
      setProspectTitles(
        Array.isArray(result.recommended_titles)
          ? result.recommended_titles
          : []
      );
      setProspectMsg(
        result.prospects?.length
          ? `Hunter.io found ${result.prospects.length} verified decision-makers for this opportunity.`
          : "Hunter.io returned no prospects for this account yet."
      );
    } catch (e) {
      setProspects([]);
      setProspectMsg(
        e instanceof Error ? e.message : "Could not search Hunter.io prospects."
      );
    } finally {
      setProspectBusy(false);
    }
  };

  const setAutomation = async (level: string) => {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = (await authFetch(
        `/api/sales/opportunities/${selected.id}/automation`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ automation_level: level }),
        }
      )) as SalesOpportunity;
      setSelected(updated);
      setRows(prev =>
        prev.map(row =>
          row.id === updated.id
            ? { ...row, automation_level: updated.automation_level }
            : row
        )
      );
      toast.success("Automation updated.");
    } catch (e) {
      toast.error(
        e instanceof Error ? e.message : "Could not update automation."
      );
    } finally {
      setBusy(false);
    }
  };

  const automateNext = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      const result = await authFetch(
        `/api/sales/opportunities/${selected.id}/actions/automate-next`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            force: true,
            recipient: recipientOverride || undefined,
          }),
        }
      );
      setSelected(result.opportunity);
      toast.success(`Action ${result.action.status}.`);
      await loadRows();
    } catch (e) {
      toast.error(
        e instanceof Error ? e.message : "Could not automate next action."
      );
    } finally {
      setBusy(false);
    }
  };

  const applyProspectContact = async (person: ApolloProspect) => {
    if (!selected?.crm_account_id || !person.email) {
      toast.error(
        "Select an opportunity with a CRM account and a prospect email."
      );
      return;
    }
    try {
      setBusy(true);
      await authFetch(
        `/api/crm/accounts/${selected.crm_account_id}/set-contact`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contact_email: person.email,
            contact_name: person.name,
            contact_title: person.title,
            source: "apollo",
          }),
        }
      );
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
      const result = await authFetch(
        `/api/sales/actions/${action.id}/automate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            force: true,
            recipient: recipientOverride || undefined,
          }),
        }
      );
      setSelected(result.opportunity);
      toast.success(`Action ${result.action.status}.`);
      await loadRows();
    } catch (e) {
      toast.error(
        e instanceof Error ? e.message : "Could not automate action."
      );
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`} />;
  }

  if (!session) {
    return (
      <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
        <ExperimentHeader />
        <main className="max-w-3xl mx-auto px-6 pt-32">
          <h1 className="text-3xl font-bold text-white">Sales Console</h1>
          <p className="mt-4 text-slate-400">
            Sign in to see buyer replies, opportunity stage movement, and
            next-best actions.
          </p>
          <Link
            href="/login?next=/sales-console"
            className="inline-flex mt-6 rounded-xl px-4 py-2 font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition"
          >
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
      <ExperimentHeader />
      <main className="admin-workspace max-w-7xl mx-auto px-6 pt-8 pb-16">
        <AdminNav variant="dark" />
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5">
          <div>
            <p className="text-xs font-extrabold uppercase tracking-[0.25em] text-emerald-400">
              SIGNAL sales console
            </p>
            <h1 className="mt-3 text-4xl md:text-5xl font-black tracking-tight text-white">
              Sales Console
            </h1>
            <p className="mt-3 max-w-2xl text-slate-400">
              Review inbound replies, see what SIGNAL already sent, and decide
              the next action to advance each opportunity.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <CalAutopilotSwitch
              enabled={autopilotEnabled}
              onToggle={handleToggleAutopilot}
              busy={busy}
              compact
            />
            <button
              onClick={runAutomaticOutreachCycle}
              disabled={busy}
              className="rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-4 py-2 text-xs font-black uppercase tracking-wide shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5 text-slate-950 fill-slate-950" />
              Run Auto-Outreach Cycle
            </button>
            <button
              onClick={() => setIsProposalDrawerOpen(true)}
              className="rounded-xl border border-cyan-500/50 bg-cyan-950/40 px-4 py-2 text-xs font-bold text-cyan-300 hover:bg-cyan-900/60 transition flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              Phelan Proposals
            </button>
            <button
              onClick={() =>
                setResendModal({
                  isOpen: true,
                  to: confirmEmail || recipientOverride || selected?.latest_message?.from_email || "",
                  subject: `Robotic Labor Placement — ${selected?.title || "ReadyForRobots"}`,
                  body: "",
                  companyName: selected?.title || "",
                  crmAccountId: selected?.crm_account_id || undefined,
                })
              }
              className="rounded-xl border border-emerald-500/50 bg-emerald-950/40 px-4 py-2 text-xs font-extrabold text-emerald-300 hover:bg-emerald-900/60 transition flex items-center gap-1.5"
            >
              <Mail className="w-3.5 h-3.5 text-emerald-400" />
              Send Email via Resend
            </button>
            <button
              onClick={() => void loadRows()}
              disabled={busy}
              className="rounded-xl border border-slate-700/80 bg-slate-800/80 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-50 transition"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Visual Stick Diagram — Sales & Placement Workflow */}
        <div className="mt-6 rounded-2xl border border-slate-700/60 bg-[#0c192e] p-5 shadow-xl">
          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
            <span className="text-xs font-extrabold uppercase tracking-wider text-emerald-400">
              Outreach & Placement Workflow Map
            </span>
            <span className="text-xs text-slate-400">
              Click a stage to filter active opportunities
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            {[
              { key: "all", step: "1", title: "DISCOVER", count: rows.length, color: "border-cyan-500/40 bg-cyan-950/40 text-cyan-300" },
              { key: "contact_qualification", step: "2", title: "CONFIRM EMAIL", count: rows.filter(r => r.current_stage === "contact_qualification" || !r.latest_message?.to_email).length, color: "border-amber-500/40 bg-amber-950/40 text-amber-300" },
              { key: "ready_for_draft", step: "3", title: "PHELAN AUTO-DRAFT", count: rows.filter(r => r.current_stage === "ready_for_draft").length, color: "border-purple-500/40 bg-purple-950/40 text-purple-300" },
              { key: "intro_sent", step: "4", title: "OUTREACH & REPLIES", count: rows.filter(r => r.current_stage === "intro_sent" || r.last_inbound_at).length, color: "border-emerald-500/40 bg-emerald-950/40 text-emerald-300" },
              { key: "placement", step: "5", title: "PLACEMENT", count: rows.filter(r => r.current_stage === "placement").length, color: "border-indigo-500/40 bg-indigo-950/40 text-indigo-300" },
            ].map((st, idx) => (
              <button
                key={st.key}
                onClick={() => setStageFilter(st.key)}
                className={`relative rounded-xl border p-3 text-left transition flex flex-col justify-between ${st.color} ${stageFilter === st.key ? "ring-2 ring-emerald-400" : "opacity-85 hover:opacity-100"}`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono uppercase font-bold">
                  <span>Step {st.step}</span>
                  <span className="rounded-full bg-slate-900/80 px-2 py-0.5 border border-slate-700">{st.count}</span>
                </div>
                <p className="mt-2 text-xs font-black tracking-tight leading-snug">{st.title}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Phelan Robot Proposals OEM Approval Banner */}
        <div className="mt-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 border border-cyan-500/30 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                  Phelan AI Robot Proposal & Quote Strategy
                </span>
                <span className="text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                  2 Awaiting OEM Approval
                </span>
              </div>
              <p className="text-sm font-semibold text-white mt-1">
                Pre-Send OEM Gate: Phelan prepares quotes & matches robots to job openings for OEM sign-off before buyer dispatch.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/proposal/oem-review?id=PROP-8842-APEX"
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-all"
            >
              Open OEM Review Gate <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
            </Link>
            <button
              onClick={() => setIsProposalDrawerOpen(true)}
              className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-extrabold tracking-wide uppercase transition-all shadow-md shadow-cyan-500/20"
            >
              Manage Proposal Quotes
            </button>
          </div>
        </div>

        {msg && (
          <div className="mt-6 rounded-2xl border border-amber-500/30 bg-amber-950/30 p-4 text-sm text-amber-200">
            {msg}
          </div>
        )}

        <section className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Workflow memory
            </p>
            <p className="mt-3 text-3xl font-black text-emerald-400">
              {learningReport?.experience_events ?? 0}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              sales events captured from sends, replies, failures, and
              escalations
            </p>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Best source signal
            </p>
            <p className="mt-3 text-lg font-bold text-white">
              {learningReport?.source_domain_priorities?.[0]?.key ||
                "Waiting for replies"}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              SIGNAL uses positive reply history to guide scraper priorities.
            </p>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Scraper guidance
            </p>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              {learningReport?.scraper_guidance?.[0] ||
                "Guidance appears after SIGNAL observes enough outreach outcomes."}
            </p>
          </div>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-4">
          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Open opportunities
            </p>
            <p className="mt-2 text-3xl font-black text-white">
              {rows.length}
            </p>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Need action
            </p>
            <p className="mt-2 text-3xl font-black text-amber-400">
              {rows.filter(row => row.next_best_action?.recommendation).length}
            </p>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Buyer replies
            </p>
            <p className="mt-2 text-3xl font-black text-emerald-400">
              {rows.filter(row => row.last_inbound_at).length}
            </p>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
              Technical escalations
            </p>
            <p className="mt-2 text-3xl font-black text-purple-400">
              {
                rows.filter(row => row.current_stage === "technical_escalation")
                  .length
              }
            </p>
          </div>
        </section>

        {/* Opportunities List + Detail Panel */}
        <section className="mt-8 grid gap-6 lg:grid-cols-[360px_1fr]">
              <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold uppercase tracking-widest text-slate-400">
                    Opportunities
                  </h2>
                  <span className="text-xs text-slate-500">
                    {filteredRows.length} active
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  {filteredRows.map(row => (
                    <button
                      key={row.id}
                      onClick={() => setSelectedId(row.id)}
                      className="w-full rounded-2xl border p-4 text-left transition"
                      style={{
                        borderColor:
                          selectedId === row.id
                            ? "rgba(52, 211, 153, 0.6)"
                            : "rgba(51, 65, 85, 0.6)",
                        background:
                          selectedId === row.id
                            ? "rgba(6, 78, 59, 0.35)"
                            : "rgba(15, 23, 42, 0.6)",
                      }}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-bold text-white">{row.title}</p>
                        <span className="rounded-full border border-slate-700 bg-slate-800/80 px-2 py-1 text-[10px] uppercase text-slate-300">
                          {row.opportunity_type}
                        </span>
                      </div>
                      <p className="mt-2 text-xs text-slate-400">
                        Stage: {row.current_stage}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Intent:{" "}
                        {row.next_best_action?.intent ||
                          row.latest_message?.detected_intent ||
                          "unknown"}
                      </p>
                    </button>
                  ))}
                  {!filteredRows.length && !busy && (
                    <div className="rounded-2xl border border-dashed border-emerald-500/40 bg-emerald-950/20 p-5 text-center shadow-inner">
                      <p className="text-sm font-bold text-white">No opportunities in queue</p>
                      <p className="mt-1 text-xs text-slate-400">
                        Populate your console with open leads from your pipeline.
                      </p>
                      <button
                        onClick={seedOpportunitiesFromPipeline}
                        disabled={busy}
                        className="mt-3 inline-flex items-center gap-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1.5 text-xs font-black uppercase tracking-wider transition"
                      >
                        <Zap className="w-3.5 h-3.5 fill-slate-950" />
                        Populate Queue from Pipeline
                      </button>
                    </div>
                  )}
                </div>
              </div>

          <div className="rounded-3xl border border-slate-700/60 bg-[#0c192e] shadow-xl p-5">
            {selected ? (
              <React.Fragment>
                <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                      {selected.opportunity_type} opportunity
                    </p>
                    <h2 className="mt-2 text-3xl font-black text-white">
                      {selected.title}
                    </h2>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full border border-slate-700 bg-slate-800/90 px-3 py-1 text-slate-300">
                        Stage: {selected.current_stage}
                      </span>
                      <span className="rounded-full border border-slate-700 bg-slate-800/90 px-3 py-1 text-slate-300">
                        Status: {selected.status}
                      </span>
                      <span className="rounded-full border border-slate-700 bg-slate-800/90 px-3 py-1 text-slate-300">
                        Last inbound: {formatDate(selected.last_inbound_at)}
                      </span>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-700/60 bg-[#081126] p-4 xl:w-80">
                    <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                      Automation mode
                    </label>
                    <select
                      value={selected.automation_level}
                      onChange={event => void setAutomation(event.target.value)}
                      className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
                    >
                      {AUTOMATION_LEVELS.map(level => (
                        <option
                          key={level.value}
                          value={level.value}
                          className="bg-[#0c192e] text-white"
                        >
                          {level.label}
                        </option>
                      ))}
                    </select>
                    <label className="mt-3 block text-xs font-bold uppercase tracking-widest text-slate-400">
                      Reply recipient
                    </label>
                    <input
                      value={recipientOverride}
                      onChange={event =>
                        setRecipientOverride(event.target.value)
                      }
                      placeholder="buyer@example.com"
                      className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-500 focus:border-emerald-500"
                    />
                    <button
                      onClick={() => void automateNext()}
                      disabled={busy}
                      className="mt-3 w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 text-sm font-black disabled:opacity-50 transition shadow-md shadow-emerald-950/40"
                    >
                      Automate next action
                    </button>
                  </div>
                </div>

                {/* OEM & Vendor Contact Email Confirmation Panel */}
                <div className="mt-6 rounded-2xl border border-amber-500/40 bg-amber-950/20 p-5 shadow-lg">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
                      <span className="text-xs font-mono font-extrabold uppercase tracking-wider text-amber-400">
                        OEM / Vendor Email Confirmation
                      </span>
                    </div>
                    <span className="text-[10px] font-mono bg-slate-900/90 px-2 py-1 rounded border border-slate-700 text-slate-300">
                      {confirmEmail ? "Email Set" : "Action Required: Missing Email"}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-slate-300">
                    Confirm decision-maker contact email for <strong>{selected.title}</strong> before Phelan dispatches quotes.
                  </p>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400">OEM / Vendor Email *</label>
                      <input
                        value={confirmEmail}
                        onChange={e => setConfirmEmail(e.target.value)}
                        placeholder="decision.maker@oem.com"
                        className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2 text-xs text-white outline-none focus:border-amber-400"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400">Contact Name</label>
                      <input
                        value={confirmName}
                        onChange={e => setConfirmName(e.target.value)}
                        placeholder="e.g. Jane Doe"
                        className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2 text-xs text-white outline-none focus:border-amber-400"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400">Title / Role</label>
                      <input
                        value={confirmTitle}
                        onChange={e => setConfirmTitle(e.target.value)}
                        placeholder="e.g. VP of Automation"
                        className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2 text-xs text-white outline-none focus:border-amber-400"
                      />
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <button
                      onClick={saveConfirmedContact}
                      disabled={confirmingContact || !confirmEmail}
                      className="rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 px-4 py-2 text-xs font-black uppercase tracking-wider shadow-md disabled:opacity-50 transition"
                    >
                      {confirmingContact ? "Saving..." : "Save & Confirm Contact Email"}
                    </button>
                    <button
                      onClick={() => void loadProspects()}
                      disabled={prospectBusy}
                      className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition"
                    >
                      Search Hunter.io Contacts
                    </button>
                  </div>
                </div>

                <div className="mt-6 rounded-2xl border border-slate-700/60 bg-[#081126] p-5">
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                    Next best action
                  </p>
                  <p className="mt-2 text-sm text-slate-200">
                    {selected.next_best_action?.recommendation ||
                      "SIGNAL will generate the next action from the latest conversation context."}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      onClick={() =>
                        setResendModal({
                          isOpen: true,
                          to: confirmEmail || recipientOverride || selected.latest_message?.from_email || "",
                          subject: `Robotic Labor Placement — ${selected.title}`,
                          body: "",
                          companyName: selected.title,
                          crmAccountId: selected.crm_account_id || undefined,
                        })
                      }
                      className="rounded-lg bg-emerald-600 border border-emerald-500 px-3 py-2 text-xs font-extrabold text-white hover:bg-emerald-500 transition shadow-md flex items-center gap-1.5"
                    >
                      <Mail className="w-3.5 h-3.5 text-white" />
                      Send Email via Resend
                    </button>
                    {selected.crm_account_id && (
                      <Link
                        href="/crm"
                        className="rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition"
                      >
                        Open CRM draft tools
                      </Link>
                    )}
                    {selected.opportunity_type === "supply" && (
                      <Link
                        href="/supply-pipeline"
                        className="rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition"
                      >
                        Open Supply Pipeline draft tools
                      </Link>
                    )}
                  </div>
                </div>

                <div className="mt-6 rounded-2xl border border-slate-700/60 bg-[#081126] p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                        Hunter.io prospect search
                      </p>
                      <p className="mt-2 text-sm text-slate-400">
                        Find verified decision-makers for this opportunity and use
                        them to route the next outreach step.
                      </p>
                    </div>
                    <button
                      onClick={() => void loadProspects()}
                      disabled={prospectBusy}
                      className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-bold text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-50 transition"
                    >
                      {prospectBusy ? "Searching Hunter.io..." : "Find prospects"}
                    </button>
                  </div>
                  {prospectTitles.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {prospectTitles.map(title => (
                        <span
                          key={title}
                          className="rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1 text-[11px] text-slate-400"
                        >
                          {title}
                        </span>
                      ))}
                    </div>
                  )}
                  {prospectMsg && (
                    <p className="mt-3 text-xs text-amber-300">{prospectMsg}</p>
                  )}
                  {prospects.length > 0 && (
                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                      {prospects.slice(0, 6).map((person, idx) => (
                        <div
                          key={person.id || `${person.name}-${idx}`}
                          className="rounded-xl border border-slate-700/60 bg-[#0c192e] p-3"
                        >
                          <p className="font-bold text-white">
                            {person.name || "Unnamed prospect"}
                          </p>
                          <p className="mt-1 text-xs text-slate-400">
                            {person.title || "Title unavailable"}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            {person.organization_name ||
                              person.organization_domain ||
                              "Organization unavailable"}
                          </p>
                          {person.email && (
                            <p
                              className="mt-2 text-xs font-semibold text-emerald-400"
                            >
                              {person.email}
                            </p>
                          )}
                          {person.email && selected.crm_account_id && (
                            <button
                              onClick={() => void applyProspectContact(person)}
                              disabled={busy}
                              className="mt-2 rounded-lg border border-emerald-500/40 bg-emerald-950/40 px-2 py-1 text-[11px] font-bold text-emerald-300 hover:bg-emerald-900/60 disabled:opacity-50 transition"
                            >
                              Use as contact
                            </button>
                          )}
                          {person.linkedin_url && (
                            <a
                              href={person.linkedin_url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-2 inline-flex text-xs text-amber-400 hover:text-amber-300 underline"
                            >
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
                    <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">
                      Actions
                    </h3>
                    <div className="mt-3 space-y-3">
                      {(selected.actions || []).map(action => (
                        <div
                          key={action.id}
                          className="rounded-2xl border border-slate-700/60 bg-[#081126] p-4"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-bold text-white">
                                {actionLabel(action)}
                              </p>
                              <p
                                className="mt-1 text-xs font-semibold"
                                style={{ color: statusColor(action.status) }}
                              >
                                Status: {action.status}
                              </p>
                              <p className="mt-1 text-[11px] text-slate-400">
                                Intent: {action.detected_intent || "unknown"} ·
                                Risk: {action.risk_level || "unknown"}
                              </p>
                            </div>
                            {action.status !== "sent" && (
                              <button
                                onClick={() => void automateAction(action)}
                                disabled={busy}
                                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-50 transition"
                              >
                                Automate
                              </button>
                            )}
                          </div>
                          <p className="mt-3 text-sm text-slate-300">
                            {action.recommendation}
                          </p>
                          {action.draft_subject && (
                            <p className="mt-3 text-xs font-bold text-slate-400">
                              Subject: {action.draft_subject}
                            </p>
                          )}
                          {action.draft_body && (
                            <pre className="mt-2 max-h-56 overflow-y-auto whitespace-pre-wrap rounded-xl border border-slate-700/60 bg-slate-950 p-3 text-xs leading-relaxed text-slate-300 font-mono">
                              {action.draft_body}
                            </pre>
                          )}
                          {action.error && (
                            <p className="mt-2 text-xs text-red-400">
                              {action.error}
                            </p>
                          )}
                        </div>
                      ))}
                      {!(selected.actions || []).length && (
                        <p className="text-sm text-slate-500">
                          No actions recorded yet.
                        </p>
                      )}
                    </div>
                  </section>

                  <section>
                    <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">
                      Messages
                    </h3>
                    <div className="mt-3 space-y-3">
                      {(selected.messages || []).map(message => (
                        <div
                          key={message.id}
                          className="rounded-2xl border border-slate-700/60 bg-[#081126] p-4"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="font-bold text-white">
                              {message.direction === "inbound"
                                ? "Inbound"
                                : "Outbound"}
                            </p>
                            <span className="text-xs text-slate-500">
                              {formatDate(message.created_at)}
                            </span>
                          </div>
                          <p className="mt-2 text-xs font-semibold text-slate-400">
                            {message.subject || "No subject"}
                          </p>
                          <p className="mt-3 line-clamp-5 whitespace-pre-wrap text-sm text-slate-300">
                            {message.body_text || "No body captured."}
                          </p>
                        </div>
                      ))}
                      {!(selected.messages || []).length && (
                        <p className="text-sm text-slate-500">
                          No messages recorded yet.
                        </p>
                      )}
                    </div>
                  </section>
                </div>
              </React.Fragment>
            ) : (
              <div className="rounded-2xl border border-slate-700/60 bg-slate-900/50 p-8 text-slate-400">
                Select an opportunity to inspect SIGNAL activity.
              </div>
            )}
          </div>
        </section>

        <CalProposalQuoteDrawer
          isOpen={isProposalDrawerOpen}
          onClose={() => setIsProposalDrawerOpen(false)}
        />

        {resendModal && (
          <ResendEmailModal
            isOpen={resendModal.isOpen}
            onClose={() => setResendModal(null)}
            defaultTo={resendModal.to}
            defaultSubject={resendModal.subject}
            defaultBody={resendModal.body}
            companyName={resendModal.companyName}
            crmAccountId={resendModal.crmAccountId}
            onSent={() => void loadRows()}
          />
        )}
      </main>
    </div>
  );
}
