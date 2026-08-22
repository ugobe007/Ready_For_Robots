import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import AdminNav from "@/components/AdminNav";
import CrmPathFork from "@/components/pipeline/CrmPathFork";
import CrmAccountWorkspace from "@/components/crm/CrmAccountWorkspace";
import { useAuth } from "@/contexts/AuthContext";
import { useIsAdmin } from "@/hooks/useIsAdmin";
import { openWorkspaceHref } from "@/lib/adminNavLinks";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";
import CrmHero, { type JobsWatchStatus } from "@/components/crm/CrmHero";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";
import {
  CRM_UNLOCKED_JOBS,
  JOBS_ACTIVATE_SRC,
  isJobsHandoffSrc,
  jobsSignupHref,
} from "@/lib/jobsWorkflow";

type Team = { id: string; name: string; role: string };
type Account = {
  id: string;
  name: string;
  company_id: number | null;
  industry?: string | null;
  outreach_stage?: string | null;
  contact_email?: string | null;
  outreach_draft?: string | null;
  outreach_sent_at?: string | null;
  latest_outreach_message_id?: string | null;
  workflow_intelligence?: {
    recommended_action?: string;
    priority_score?: number;
    experience_count?: number;
    sent_count?: number;
    reply_count?: number;
    failed_count?: number;
  } | null;
  prospect_search?: {
    provider?: string;
    organization_name?: string | null;
    organization_domain?: string | null;
    recommended_titles?: string[];
  } | null;
};

type UserSettings = {
  scout_message_style?: string | null;
  scout_preferred_channel?: string | null;
  scout_meeting_preference?: string | null;
  scout_default_cc?: string | null;
  scout_default_bcc?: string | null;
  scout_persona_traits?: string | null;
  scout_collateral_policy?: "none" | "selective" | "all" | null;
  scout_collateral_links?: string | null;
  scout_background_briefing_enabled?: boolean | null;
};

type ScoutSuggestion = { trigger: string; action: string; why: string };

const PERSONA_TRAITS = [
  { id: "insightful", label: "Insightful comments" },
  { id: "industry_refs", label: "Industry references" },
  { id: "robot_examples", label: "Robot examples" },
  { id: "humor", label: "Slight humor, professional" },
  { id: "inquisitive", label: "Inquisitive" },
  { id: "whitepapers", label: "Whitepapers/studies" },
];

const VOICE_FEEDBACK = [
  { label: "Too generic", instruction: "Use one specific signal hook and remove generic claims." },
  { label: "Too long", instruction: "Keep the email under 140 words unless the customer has already replied." },
  { label: "Too salesy", instruction: "Use lower-pressure language and admit uncertainty when the fit is not confirmed." },
  { label: "Better hook needed", instruction: "Lead with the clearest why-now signal before explaining Ready For Robots." },
  { label: "More edge", instruction: "Make the language sharper and more commercially confident without adding hype." },
  { label: "Founder-level", instruction: "Explain the pipeline logic like an operator speaking to a technical founder." },
  { label: "Add off-ramp", instruction: "Include a graceful exit if the signal is not strong enough or the timing is wrong." },
  { label: "Good tone", instruction: "Keep this tone: concise, human, specific, and low-pressure." },
];

export default function Crm() {
  const { session, loading } = useAuth();
  const isAdmin = useIsAdmin();
  const [, setLocation] = useLocation();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState("");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [ccEmails, setCcEmails] = useState("");
  const [bccEmails, setBccEmails] = useState("");
  const [subject, setSubject] = useState("");
  const [draft, setDraft] = useState("");
  const [styleInstruction, setStyleInstruction] = useState("");
  const [selectedTraits, setSelectedTraits] = useState<string[]>([]);
  const [collateralPolicy, setCollateralPolicy] = useState<"none" | "selective" | "all">("selective");
  const [collateralLinks, setCollateralLinks] = useState("");
  const [suggestions, setSuggestions] = useState<ScoutSuggestion[]>([]);
  const [styleApproved, setStyleApproved] = useState(false);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [sending, setSending] = useState(false);
  const [hubspotConnected, setHubspotConnected] = useState(false);
  const [watch, setWatch] = useState<JobsWatchStatus | null>(null);
  const [watchBusy, setWatchBusy] = useState(false);
  const [watchError, setWatchError] = useState<string | null>(null);
  const jobsSrc =
    typeof window !== "undefined"
      ? new URLSearchParams(window.location.search).get("src")
      : null;
  const fromJobs = isJobsHandoffSrc(jobsSrc);
  const crmReturnHref = (() => {
    if (typeof window === "undefined") return "/crm";
    const params = new URLSearchParams(window.location.search);
    if (!isJobsHandoffSrc(params.get("src"))) params.set("src", JOBS_ACTIVATE_SRC);
    const q = params.toString();
    return q ? `/crm?${q}` : "/crm";
  })();

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const t = session?.access_token;
      if (!t) throw new Error("Not signed in");
      const base = getApiBase();
      const r = await fetch(`${base}${path}`, liveFetchInit({ ...init, headers: { ...authHeader(t), ...init.headers } }));
      const text = await r.text();
      if (!r.ok) throw new Error(text || r.statusText);
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token],
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accountParam = params.get("account");
    if (accountParam) setSelectedAccountId(accountParam);
  }, []);

  useEffect(() => {
    if (!session?.access_token) return;
    (async () => {
      setMsg("");
      try {
        const list = (await authFetch("/api/crm/teams")) as Team[];
        setTeams(Array.isArray(list) ? list : []);
        setTeamId((prev) => prev || (list[0]?.id ?? ""));
        const userSettings = (await authFetch("/api/user/settings")) as UserSettings;
        setSettings(userSettings);
        setCcEmails(userSettings.scout_default_cc || "");
        setBccEmails(userSettings.scout_default_bcc || "");
        setStyleInstruction(userSettings.scout_message_style || "");
        setSelectedTraits(
          (userSettings.scout_persona_traits || "")
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean),
        );
        setCollateralPolicy(userSettings.scout_collateral_policy || "selective");
        setCollateralLinks(userSettings.scout_collateral_links || "");
        try {
          const watchStatus = (await authFetch("/api/crm/jobs-watch")) as JobsWatchStatus;
          setWatch(watchStatus);
        } catch {
          setWatch(null);
        }
      } catch (e) {
        setMsg(e instanceof Error ? e.message : "Failed to load teams");
      }
    })();
  }, [session?.access_token, authFetch]);

  useEffect(() => {
    if (!session?.access_token) {
      setHubspotConnected(false);
      return;
    }
    let cancelled = false;
    void fetch(
      `${getApiBase()}/api/integrations`,
      liveFetchInit({ headers: { ...authHeader(session.access_token) } }),
    )
      .then(async (res) => {
        if (cancelled || !res.ok) return;
        const payload = (await res.json()) as {
          integrations?: Array<{ provider: string; connected?: boolean }>;
        };
        const hubspot = (payload.integrations || []).find((row) => row.provider === "hubspot");
        setHubspotConnected(Boolean(hubspot?.connected));
      })
      .catch(() => {
        if (!cancelled) setHubspotConnected(false);
      });
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  useEffect(() => {
    if (!session?.access_token || !teamId || fromJobs) return;
    (async () => {
      setBusy(true);
      setMsg("");
      try {
        const q = `team_id=${encodeURIComponent(teamId)}`;
        const data = (await authFetch(`/api/crm/accounts?${q}`)) as Account[];
        const rows = Array.isArray(data) ? data : [];
        setAccounts(rows);
        setSelectedAccountId((prev) => (rows.some((a) => a.id === prev) ? prev : rows[0]?.id ?? ""));
      } catch (e) {
        setMsg(e instanceof Error ? e.message : "Failed to load accounts");
        setAccounts([]);
        setSelectedAccountId("");
      } finally {
        setBusy(false);
      }
    })();
  }, [session?.access_token, teamId, authFetch, fromJobs]);

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId) ?? null;
  const handoff = readJobsHandoffSnapshot();
  const tasteJobs = (handoff?.jobs || []).slice(0, CRM_UNLOCKED_JOBS);
  const tasteProduct = handoff?.productName || null;

  const optInWatch = useCallback(
    async (optedIn: boolean) => {
      setWatchBusy(true);
      setWatchError(null);
      try {
        const snap = readJobsHandoffSnapshot();
        const payload: Record<string, unknown> = { opted_in: optedIn };
        if (optedIn && snap?.url) {
          payload.robot_url = snap.url;
          payload.product_name = snap.productName || "";
          payload.seed_jobs = (snap.jobs || []).slice(0, CRM_UNLOCKED_JOBS).map(job => ({
            job_key: job.job_key,
            title: job.title,
            company_name: job.company_name,
          }));
        }
        const next = (await authFetch("/api/crm/jobs-watch", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })) as JobsWatchStatus;
        setWatch(next);
      } catch (e) {
        let message = e instanceof Error ? e.message : "Could not update job watch.";
        try {
          const parsed = JSON.parse(message) as { detail?: unknown };
          if (typeof parsed.detail === "string" && parsed.detail.trim()) {
            message = parsed.detail;
          }
        } catch {
          /* raw text */
        }
        setWatchError(message);
      } finally {
        setWatchBusy(false);
      }
    },
    [authFetch],
  );

  useEffect(() => {
    if (!selectedAccount) {
      setContactEmail("");
      setCcEmails(settings?.scout_default_cc || "");
      setBccEmails(settings?.scout_default_bcc || "");
      setSubject("");
      setDraft("");
      setStyleInstruction(settings?.scout_message_style || "");
      setSelectedTraits((settings?.scout_persona_traits || "").split(",").map((x) => x.trim()).filter(Boolean));
      setCollateralPolicy(settings?.scout_collateral_policy || "selective");
      setCollateralLinks(settings?.scout_collateral_links || "");
      setSuggestions([]);
      setStyleApproved(false);
      return;
    }
    setContactEmail(selectedAccount.contact_email || "");
    setCcEmails(settings?.scout_default_cc || "");
    setBccEmails(settings?.scout_default_bcc || "");
    setSubject(`Automation opportunity — ${selectedAccount.name}`);
    setDraft(selectedAccount.outreach_draft || "");
    setStyleInstruction(settings?.scout_message_style || "");
    setSelectedTraits((settings?.scout_persona_traits || "").split(",").map((x) => x.trim()).filter(Boolean));
    setCollateralPolicy(settings?.scout_collateral_policy || "selective");
    setCollateralLinks(settings?.scout_collateral_links || "");
    setSuggestions([]);
    setStyleApproved(
      selectedAccount.outreach_stage === "draft_approved" || selectedAccount.outreach_stage === "intro_sent",
    );
  }, [selectedAccount, settings]);

  const sendBlockers = (): string[] => {
    const blockers: string[] = [];
    if (!contactEmail.trim()) blockers.push("add a recipient email");
    if (!draft.trim()) blockers.push("write or generate a message draft");
    if (!styleApproved) blockers.push('click "Approve draft" to confirm the message');
    return blockers;
  };

  const parseEmails = (value: string) =>
    value
      .replace(/;/g, ",")
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.includes("@"));

  const scoutStyleGuidance = () => {
    const pieces = [
      styleInstruction && `Tone/style: ${styleInstruction}`,
      settings?.scout_preferred_channel && settings.scout_preferred_channel !== "email"
        ? `Preferred next step: suggest a ${settings.scout_preferred_channel}.`
        : "",
      settings?.scout_meeting_preference ? `Scheduling preference: ${settings.scout_meeting_preference}` : "",
    ].filter(Boolean);
    return pieces.length ? `\n\nSIGNAL style memory:\n${pieces.join("\n")}` : "";
  };

  const toggleTrait = (id: string) => {
    setSelectedTraits((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    setStyleApproved(false);
  };

  const applyVoiceFeedback = (instruction: string) => {
    setStyleInstruction((current) => {
      const lines = current.split("\n").map((line) => line.trim()).filter(Boolean);
      if (lines.includes(instruction)) return current;
      return [...lines, instruction].join("\n");
    });
    setStyleApproved(false);
    setMsg("Style feedback saved locally. Click Draft outreach to apply it to the next draft.");
  };

  const draftWithScout = async () => {
    if (!selectedAccount) return;
    setBusy(true);
    setMsg("");
    try {
      const result = await authFetch(`/api/crm/accounts/${selectedAccount.id}/draft-outreach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contact_email: contactEmail || null,
          persona_traits: selectedTraits,
          collateral_policy: collateralPolicy,
          collateral_links: collateralLinks,
          style_instruction: styleInstruction,
        }),
      });
      setSubject(result.subject || subject);
      setDraft(result.outreach_draft || "");
      setSuggestions(Array.isArray(result.suggestions) ? result.suggestions : []);
      setAccounts((prev) => prev.map((a) => (a.id === selectedAccount.id ? { ...a, outreach_stage: "draft_ready", outreach_draft: result.outreach_draft } : a)));
      setStyleApproved(false);
      setMsg(result.checkpoint || "SIGNAL drafted this for review.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not draft outreach");
    } finally {
      setBusy(false);
    }
  };

  const saveDraft = async () => {
    if (!selectedAccount) return;
    setBusy(true);
    setMsg("");
    try {
      const saved = (await authFetch(`/api/crm/accounts/${selectedAccount.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contact_email: contactEmail || null,
          outreach_draft: draft,
          outreach_stage: "draft_approved",
        }),
      })) as Account;
      setAccounts((prev) => prev.map((a) => (a.id === selectedAccount.id ? { ...a, ...saved } : a)));
      setMsg("Checkpoint saved: draft approved and contact captured.");
      setStyleApproved(true);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not save draft");
    } finally {
      setBusy(false);
    }
  };

  const generatePlan = async () => {
    if (!selectedAccount) return;
    setBusy(true);
    setMsg("");
    try {
      const result = (await authFetch(`/api/crm/accounts/${selectedAccount.id}/generate-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ commit_tasks: true }),
      })) as { plan?: { executive_summary?: string }; tasks?: { title: string }[] };
      const taskCount = result.tasks?.length ?? 0;
      setMsg(
        result.plan?.executive_summary
          ? `${result.plan.executive_summary} (${taskCount} task${taskCount === 1 ? "" : "s"} saved.)`
          : `Sales plan generated (${taskCount} tasks).`,
      );
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not generate sales plan");
    } finally {
      setBusy(false);
    }
  };

  const sendWithScout = async () => {
    if (!selectedAccount) return;
    setSending(true);
    setMsg("");
    try {
      const result = await authFetch(`/api/crm/accounts/${selectedAccount.id}/send-outreach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contact_email: contactEmail,
          subject,
          outreach_draft: draft,
          send_identity: "scout",
          cc: parseEmails(ccEmails),
          bcc: parseEmails(bccEmails),
          approved_style: styleInstruction,
        }),
      });
      setAccounts((prev) =>
        prev.map((a) =>
          a.id === selectedAccount.id
            ? { ...a, contact_email: contactEmail, outreach_draft: draft, outreach_stage: "intro_sent" }
            : a,
        ),
      );
      const sentMsg = result?.warning
        ? `Outreach sent. ${result.warning}`
        : `Outreach sent. Replies route to ${result?.reply_to || "your Ready For Robots inbox"} and will notify you.`;
      setMsg(sentMsg);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not send outreach");
    } finally {
      setSending(false);
    }
  };

  if (!supabase) {
    return (
      <div className="pipeline-page-bg min-h-screen px-4 pt-16 text-slate-100">
        <ExperimentHeader />
        <div className="mx-auto max-w-4xl">
          <CrmHero footer="CRM is not connected in this environment." />
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="pipeline-page-bg min-h-screen px-4 pt-16 text-slate-100">
        <ExperimentHeader />
        <div className="mx-auto max-w-4xl">
          <CrmHero
            footer="Loading CRM…"
            tasteJobs={tasteJobs}
            tasteProduct={tasteProduct}
          />
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="pipeline-page-bg min-h-screen px-4 pt-16 text-slate-100">
        <ExperimentHeader />
        <div className="mx-auto max-w-4xl">
          <CrmHero
            tasteJobs={tasteJobs}
            tasteProduct={tasteProduct}
            actions={
              <Link
                href={jobsSignupHref(crmReturnHref, jobsSrc || JOBS_ACTIVATE_SRC)}
                className="inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
              >
                Sign in to CRM →
              </Link>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div className="pipeline-page-bg crm-navy flex min-h-screen flex-col text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 pb-8 pt-16">
        {!fromJobs ? <AdminNav variant="dark" /> : null}
        <CrmHero
          signedIn
          watch={watch}
          watchBusy={watchBusy}
          watchError={watchError}
          onOptIn={optInWatch}
          tasteJobs={tasteJobs}
          tasteProduct={tasteProduct}
          actions={
            fromJobs ? (
              <Link
                href="/integrations"
                className="font-mono text-sm font-semibold uppercase tracking-[0.08em] text-slate-300 hover:text-white"
              >
                Connect HubSpot / GitHub
              </Link>
            ) : (
            <>
              <Link
                href="/pipeline"
                className="inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
              >
                ← Back to pipeline
              </Link>
              {isAdmin && (
                <button
                  type="button"
                  onClick={() => openWorkspaceHref("/admin#cal-outreach", setLocation)}
                  className="font-mono text-sm font-semibold uppercase tracking-[0.08em] text-amber-200 hover:text-amber-100"
                >
                  Cal queue — bulk send
                </button>
              )}
              <Link
                href="/integrations"
                className="font-mono text-sm font-semibold uppercase tracking-[0.08em] text-slate-300 hover:text-white"
              >
                Connect HubSpot / GitHub
              </Link>
            </>
            )
          }
        />
        {!fromJobs ? (
          <>
          {msg && (
          <p className="mb-2 rounded-md border border-amber-400/40 bg-amber-400/10 px-2.5 py-1.5 text-xs font-medium text-amber-200">
            {msg}
          </p>
        )}

        <div className="mb-3">
          <CrmPathFork
            connected={hubspotConnected}
            hasSession
            savedCount={accounts.length}
            variant="compact"
          />
        </div>

        <div className="mb-3 flex flex-wrap gap-1.5">
          {teams.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTeamId(t.id)}
              className={`sb-btn ${teamId === t.id ? "border-emerald-400 bg-emerald-400/15 text-emerald-200" : ""}`}
            >
              {t.name}
            </button>
          ))}
        </div>

        <div className="sb-surface mb-3">
          <div className="flex">
            <div className="sb-surface-rail" />
            <div className="sb-surface-body min-w-0 flex-1 p-0">
          {busy ? (
            <p className="p-4 text-sm text-slate-400">Loading accounts…</p>
          ) : accounts.length === 0 ? (
            <p className="p-4 text-sm text-slate-400">No accounts in this workspace.</p>
          ) : (
            <table className="w-full text-base">
              <thead>
                <tr className="border-b border-slate-600 text-left text-sm font-semibold uppercase tracking-[0.08em] text-slate-300">
                  <th className="px-2 py-1.5">Account</th>
                  <th className="px-2 py-1.5">Company #</th>
                  <th className="px-2 py-1.5">Stage</th>
                  <th className="px-2 py-1.5">Contact</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a) => (
                  <tr
                    key={a.id}
                    onClick={() => setSelectedAccountId(a.id)}
                    className={`cursor-pointer border-b border-slate-700 ${
                      selectedAccountId === a.id ? "bg-emerald-400/10" : "hover:bg-[#081126]"
                    }`}
                  >
                    <td className="px-3 py-2.5 font-display text-lg font-bold text-white">{a.name}</td>
                    <td className="px-3 py-2.5 font-mono text-sm text-slate-300">{a.company_id ?? "—"}</td>
                    <td className="px-3 py-2.5 text-sm text-emerald-300">{a.outreach_stage || "—"}</td>
                    <td className="px-3 py-2.5 text-sm text-slate-300 truncate max-w-[140px]">{a.contact_email || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
            </div>
          </div>
        </div>
        {selectedAccount && (
          <section className="grid gap-2 lg:grid-cols-[1fr_280px]">
            <div className="sb-surface">
              <div className="flex">
                <div className="sb-surface-rail" />
                <div className="sb-surface-body flex-1">
              <div className="mb-2 flex items-start justify-between gap-2 border-b border-slate-700 pb-2">
                <div>
                  <p className="sb-kicker">Job outreach checkpoint</p>
                  <h2 className="mt-0.5 text-xl font-semibold text-white">{selectedAccount.name}</h2>
                </div>
                <span className="inline-flex rounded px-1.5 py-0.5 text-sm font-semibold uppercase tracking-wide text-amber-200" style={{ background: "rgba(251,191,36,0.15)", border: "1px solid rgba(251,191,36,0.3)" }}>
                  {selectedAccount.outreach_stage || "captured"}
                </span>
              </div>
              <label className="mb-2 block">
                <span className="sb-label mb-1 block">Recipient email</span>
                <input
                  value={contactEmail}
                  onChange={(e) => {
                    setContactEmail(e.target.value);
                    setStyleApproved(false);
                  }}
                  placeholder="buyer@example.com"
                  className="sb-input"
                />
              </label>
              <label className="mb-2 block">
                <span className="sb-label mb-1 block">Subject</span>
                <input
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="sb-input"
                />
              </label>
              <label className="block">
                <span className="sb-label mb-1 block">Message draft</span>
                <div className="mb-2 flex flex-wrap gap-1.5">
                  {PERSONA_TRAITS.map((trait) => (
                    <button
                      key={trait.id}
                      type="button"
                      onClick={() => toggleTrait(trait.id)}
                      className={`rounded-full border px-2 py-1 text-sm font-bold ${
                        selectedTraits.includes(trait.id)
                          ? "border-amber-400 bg-amber-400/15 text-amber-200"
                          : "border-slate-600 bg-[#081126] text-slate-400"
                      }`}
                    >
                      {trait.label}
                    </button>
                  ))}
                </div>
                <textarea
                  value={draft}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    setStyleApproved(false);
                  }}
                  rows={8}
                  className="sb-input min-h-[140px] leading-relaxed"
                />
              </label>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                <label className="block">
                  <span className="sb-label mb-1 block">CC</span>
                  <input
                    value={ccEmails}
                    onChange={(e) => setCcEmails(e.target.value)}
                    placeholder="partner@example.com"
                    className="sb-input"
                  />
                </label>
                <label className="block">
                  <span className="sb-label mb-1 block">BCC</span>
                  <input
                    value={bccEmails}
                    onChange={(e) => setBccEmails(e.target.value)}
                    placeholder="archive@example.com"
                    className="sb-input"
                  />
                </label>
              </div>
              <div className="mt-2 grid gap-2 md:grid-cols-[160px_1fr]">
                <label className="block">
                  <span className="sb-label mb-1 block">Collateral</span>
                  <select
                    value={collateralPolicy}
                    onChange={(e) => {
                      setCollateralPolicy(e.target.value as "none" | "selective" | "all");
                      setStyleApproved(false);
                    }}
                    className="sb-input"
                  >
                    <option value="none">No attachments/links</option>
                    <option value="selective">Selective leads only</option>
                    <option value="all">All new leads</option>
                  </select>
                </label>
                <label className="block">
                  <span className="sb-label mb-1 block">Brochures &amp; links</span>
                  <input
                    value={collateralLinks}
                    onChange={(e) => {
                      setCollateralLinks(e.target.value);
                      setStyleApproved(false);
                    }}
                    placeholder="Paste URLs, comma separated"
                    className="sb-input"
                  />
                </label>
              </div>
              <label className="mt-2 block">
                <span className="sb-label mb-1 block">SIGNAL style memory</span>
                <textarea
                  value={styleInstruction}
                  onChange={(e) => {
                    setStyleInstruction(e.target.value);
                    setStyleApproved(false);
                  }}
                  rows={3}
                  placeholder="Tell SIGNAL how to represent you."
                  className="sb-input min-h-[72px] leading-relaxed"
                />
              </label>
              <div className="mt-2 rounded-md border border-slate-600 bg-[#081126] p-2">
                <p className="sb-kicker mb-1.5">Refine from this draft</p>
                <div className="flex flex-wrap gap-1">
                  {VOICE_FEEDBACK.map((item) => (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => applyVoiceFeedback(item.instruction)}
                      className="sb-btn"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
              {scoutStyleGuidance() && (
                <div className="mt-2 rounded-md border border-emerald-500/30 bg-emerald-400/10 p-2 text-[11px] leading-relaxed text-slate-200">
                  {scoutStyleGuidance()}
                </div>
              )}
              <div className="mt-2 flex flex-wrap gap-1.5 border-t border-slate-700 pt-2">
                <button type="button" onClick={() => void generatePlan()} disabled={busy || sending} className="sb-btn">
                  Generate sales plan
                </button>
                <button type="button" onClick={() => void draftWithScout()} disabled={busy || sending} className="sb-btn">
                  Draft outreach
                </button>
                <button
                  type="button"
                  onClick={() => void saveDraft()}
                  disabled={busy || sending || !draft.trim()}
                  className={`sb-btn ${styleApproved ? "border-emerald-400 bg-emerald-400/15 text-emerald-200" : "border-amber-400/50 bg-amber-400/10 text-amber-200"}`}
                >
                  {styleApproved ? "Draft approved ✓" : "Approve draft"}
                </button>
                <button
                  type="button"
                  onClick={() => void sendWithScout()}
                  disabled={sending || sendBlockers().length > 0}
                  className="sb-btn sb-btn-primary"
                  title={sendBlockers().length ? sendBlockers().join("; ") : "Send via Resend"}
                >
                  {sending ? "Sending..." : "Send outreach"}
                </button>
              </div>
              {sendBlockers().length > 0 && (
                <p className="mt-1.5 text-[11px] text-slate-500">
                  Before sending: {sendBlockers().join(" · ")}.
                </p>
              )}
                </div>
              </div>
            </div>
            <aside className="sb-surface">
              <div className="flex h-full">
                <div className="sb-surface-rail bg-emerald-500/80" />
                <div className="sb-surface-body flex-1 space-y-3">
              <CrmAccountWorkspace
                accountId={selectedAccount.id}
                authFetch={authFetch}
                onStageChange={() => {
                  void authFetch(`/api/crm/accounts?team_id=${encodeURIComponent(teamId)}`).then((data) => {
                    setAccounts(Array.isArray(data) ? (data as Account[]) : []);
                  });
                }}
              />
              <div className="rounded-md border border-emerald-500/30 bg-[#081126] p-2">
                <p className="sb-kicker text-emerald-300">SIGNAL workflow intelligence</p>
                <p className="mt-1 text-sm font-semibold text-white">
                  {selectedAccount.workflow_intelligence?.recommended_action || "Waiting for SIGNAL activity on this account."}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-1 text-[11px] text-slate-400">
                  <span>Priority: {selectedAccount.workflow_intelligence?.priority_score ?? "—"}</span>
                  <span>Events: {selectedAccount.workflow_intelligence?.experience_count ?? 0}</span>
                  <span>Sent: {selectedAccount.workflow_intelligence?.sent_count ?? 0}</span>
                  <span>Replies: {selectedAccount.workflow_intelligence?.reply_count ?? 0}</span>
                </div>
              </div>
              <div className="mb-2 rounded-md border border-slate-600 bg-[#081126] p-2">
                <p className="sb-kicker">Apollo prospect search</p>
                <p className="mt-1 text-xs text-slate-400">
                  Search target: {selectedAccount.prospect_search?.organization_domain || selectedAccount.prospect_search?.organization_name || selectedAccount.name}
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {(selectedAccount.prospect_search?.recommended_titles || []).map((title) => (
                    <span key={title} className="sb-btn pointer-events-none">
                      {title}
                    </span>
                  ))}
                </div>
                <Link href="/sales-console" className="sb-btn sb-btn-ghost mt-2">
                  Open Sales Console
                </Link>
              </div>
              <p className="sb-kicker">User checkpoints</p>
              <ol className="mt-1.5 space-y-1.5 text-xs text-slate-400">
                <li><span className="font-semibold text-slate-100">1. Lead captured:</span> account saved to CRM.</li>
                <li><span className="font-semibold text-slate-100">2. Draft review:</span> check recipient, subject, body.</li>
                <li><span className="font-semibold text-slate-100">3. Send approval:</span> outreach sends after you approve.</li>
                <li><span className="font-semibold text-slate-100">4. Reply capture:</span> replies route back into CRM.</li>
                <li><span className="font-semibold text-slate-100">5. Follow-up:</span> SIGNAL tracks workflow from Profile.</li>
              </ol>
              {suggestions.length > 0 && (
                <div className="mt-2 border-t border-slate-600 pt-2">
                  <p className="sb-kicker">SIGNAL background ideas</p>
                  <div className="mt-1.5 space-y-1.5">
                    {suggestions.map((item) => (
                      <div key={item.trigger} className="rounded-md border border-slate-600 bg-[#081126] p-2">
                        <p className="text-[11px] font-semibold text-slate-100">{item.trigger}</p>
                        <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">{item.action}</p>
                        <p className="mt-0.5 text-[10px] leading-relaxed text-slate-500">{item.why}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
                </div>
              </div>
            </aside>
          </section>
        )}
          </>
        ) : null}
      </main>
    </div>
  );
}
