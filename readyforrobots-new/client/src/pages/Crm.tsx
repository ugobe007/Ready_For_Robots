import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";

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
  { label: "Good tone", instruction: "Keep this tone: concise, human, specific, and low-pressure." },
];

export default function Crm() {
  const { session, loading } = useAuth();
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
      } catch (e) {
        setMsg(e instanceof Error ? e.message : "Failed to load teams");
      }
    })();
  }, [session?.access_token, authFetch]);

  useEffect(() => {
    if (!session?.access_token || !teamId) return;
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
  }, [session?.access_token, teamId, authFetch]);

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId) ?? null;

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
    setStyleApproved(false);
  }, [selectedAccount, settings]);

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
    return pieces.length ? `\n\nSCOUT style memory:\n${pieces.join("\n")}` : "";
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
    setMsg("Cal voice feedback saved locally. Click Draft with Cal to apply it to the next draft.");
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
      setMsg(result.checkpoint || "SCOUT drafted this for review.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not draft with SCOUT");
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
      setMsg(`Sent by SCOUT. Replies route to ${result?.reply_to || "the SCOUT reply address"} and will notify you.`);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not send outreach");
    } finally {
      setSending(false);
    }
  };

  if (!supabase) {
    return (
      <div className="min-h-screen pt-24 px-4 text-white/50" style={{ background: "#0d0520" }}>
        <Header />
        <p>Supabase not configured.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 text-white/50" style={{ background: "#0d0520" }}>
        <Header />
        Loading…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center" style={{ background: "#0d0520" }}>
        <Header />
        <p className="text-white/60 mb-4">Sign in for CRM workspaces.</p>
        <Link href="/login" className="text-violet-400 underline text-sm">
          Login
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 pt-24 pb-12 px-4 max-w-4xl mx-auto w-full">
        <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-xl font-bold text-white mb-1" style={{ fontFamily: "'Sora', system-ui" }}>
              CRM · Buyer email draft tools
            </h1>
            <p className="text-xs text-white/40">
              Review, edit, approve, and send buyer outreach from Cal. Replies come back to CRM and Sales Console.
            </p>
          </div>
          <Link href="/sales-console" className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-white/65">
            Open Sales Console
          </Link>
        </div>
        {msg && <p className="text-sm text-amber-200/90 mb-4 border border-amber-500/30 rounded p-2">{msg}</p>}

        <div className="flex flex-wrap gap-2 mb-6">
          {teams.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTeamId(t.id)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg border ${
                teamId === t.id ? "border-violet-500 text-violet-200 bg-violet-500/15" : "border-white/10 text-white/50"
              }`}
            >
              {t.name}
            </button>
          ))}
        </div>

        <div className="rounded-xl border border-white/10 overflow-hidden" style={{ background: "rgba(255,255,255,0.02)" }}>
          {busy ? (
            <p className="p-4 text-sm text-white/40">Loading accounts…</p>
          ) : accounts.length === 0 ? (
            <p className="p-4 text-sm text-white/40">No accounts in this workspace.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase text-white/30 border-b border-white/10">
                  <th className="px-3 py-2">Account</th>
                  <th className="px-3 py-2">Company #</th>
                  <th className="px-3 py-2">Stage</th>
                  <th className="px-3 py-2">Contact</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a) => (
                  <tr
                    key={a.id}
                    onClick={() => setSelectedAccountId(a.id)}
                    className={`cursor-pointer border-b border-white/5 text-white/80 ${
                      selectedAccountId === a.id ? "bg-violet-500/10" : "hover:bg-white/[0.03]"
                    }`}
                  >
                    <td className="px-3 py-2" style={{ color: "#FFB000" }}>{a.name}</td>
                    <td className="px-3 py-2 font-mono text-xs" style={{ color: "#FFB000" }}>{a.company_id ?? "—"}</td>
                    <td className="px-3 py-2 text-xs" style={{ color: "#FFB000" }}>{a.outreach_stage || "—"}</td>
                    <td className="px-3 py-2 text-xs truncate max-w-[140px]">{a.contact_email || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        {selectedAccount && (
          <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_320px]">
            <div className="rounded-xl border border-white/10 p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-white/30">Buyer outreach checkpoint</p>
                  <h2 className="mt-1 text-lg font-bold text-white">{selectedAccount.name}</h2>
                </div>
                <span className="rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-1 text-[10px] font-bold text-amber-200">
                  {selectedAccount.outreach_stage || "captured"}
                </span>
              </div>
              <label className="mb-3 block">
                <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Recipient email</span>
                <input
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  placeholder="buyer@example.com"
                  className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                />
              </label>
              <label className="mb-3 block">
                <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Subject</span>
                <input
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Message draft</span>
                <div className="mb-2 flex flex-wrap gap-1.5">
                  {PERSONA_TRAITS.map((trait) => (
                    <button
                      key={trait.id}
                      type="button"
                      onClick={() => toggleTrait(trait.id)}
                      className={`rounded-full border px-2 py-1 text-[10px] font-bold ${
                        selectedTraits.includes(trait.id)
                          ? "border-amber-400 bg-amber-400/15 text-amber-100"
                          : "border-white/10 bg-white/[0.03] text-white/45"
                      }`}
                    >
                      {trait.label}
                    </button>
                  ))}
                </div>
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={10}
                  className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm leading-relaxed text-white outline-none"
                />
              </label>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <label className="block">
                  <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">CC</span>
                  <input
                    value={ccEmails}
                    onChange={(e) => setCcEmails(e.target.value)}
                    placeholder="partner@example.com, colleague@example.com"
                    className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">BCC</span>
                  <input
                    value={bccEmails}
                    onChange={(e) => setBccEmails(e.target.value)}
                    placeholder="archive@example.com"
                    className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                  />
                </label>
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-[180px_1fr]">
                <label className="block">
                  <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Collateral</span>
                  <select
                    value={collateralPolicy}
                    onChange={(e) => {
                      setCollateralPolicy(e.target.value as "none" | "selective" | "all");
                      setStyleApproved(false);
                    }}
                    className="w-full rounded-lg border border-white/10 bg-[#160b2c] px-3 py-2 text-sm text-white outline-none"
                  >
                    <option value="none">No attachments/links</option>
                    <option value="selective">Selective leads only</option>
                    <option value="all">All new leads</option>
                  </select>
                </label>
                <label className="block">
                  <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">Brochures, case studies, whitepapers</span>
                  <input
                    value={collateralLinks}
                    onChange={(e) => {
                      setCollateralLinks(e.target.value);
                      setStyleApproved(false);
                    }}
                    placeholder="Paste URLs, comma separated"
                    className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                  />
                </label>
              </div>
              <label className="mt-3 block">
                <span className="mb-1 block text-[10px] uppercase tracking-widest text-white/30">SCOUT style memory</span>
                <textarea
                  value={styleInstruction}
                  onChange={(e) => {
                    setStyleInstruction(e.target.value);
                    setStyleApproved(false);
                  }}
                  rows={4}
                  placeholder="Tell SCOUT how to represent you. Example: keep emails short, ask for a phone call, copy my operations partner."
                  className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm leading-relaxed text-white outline-none placeholder:text-white/25"
                />
              </label>
              <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.025] p-3">
                <p className="mb-2 text-[10px] uppercase tracking-widest text-white/30">Teach Cal from this draft</p>
                <div className="flex flex-wrap gap-1.5">
                  {VOICE_FEEDBACK.map((item) => (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => applyVoiceFeedback(item.instruction)}
                      className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[10px] font-bold text-white/55 hover:border-amber-300/35 hover:text-amber-100"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
              {scoutStyleGuidance() && (
                <div className="mt-3 rounded-lg border border-violet-500/20 bg-violet-500/10 p-3 text-[11px] leading-relaxed text-violet-100/85">
                  {scoutStyleGuidance()}
                </div>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void draftWithScout()}
                  disabled={busy || sending}
                  className="rounded-lg border border-white/15 bg-white/[0.06] px-3 py-2 text-xs font-bold text-white/80 disabled:opacity-50"
                >
                  Draft with Cal
                </button>
                <button
                  type="button"
                  onClick={() => void saveDraft()}
                  disabled={busy || sending}
                  className="rounded-lg border border-violet-500/35 bg-violet-500/15 px-3 py-2 text-xs font-bold text-violet-100 disabled:opacity-50"
                >
                  Approve Draft
                </button>
                <button
                  type="button"
                  onClick={() => void sendWithScout()}
                  disabled={sending || !contactEmail || !draft || !styleApproved}
                  className="rounded-lg border border-amber-500 bg-amber-500 px-3 py-2 text-xs font-bold text-[#160b2c] disabled:opacity-50"
                >
                  {sending ? "Sending..." : "Send with Cal"}
                </button>
              </div>
              {!styleApproved && (
                <p className="mt-2 text-[11px] text-white/35">
                  Approve the draft first. This confirms the message and teaches Cal the format/style to reuse.
                </p>
              )}
            </div>
            <aside className="rounded-xl border border-white/10 p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
              <div className="mb-5 rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-3">
                <p className="text-[10px] uppercase tracking-widest text-emerald-100/70">SCOUT workflow intelligence</p>
                <p className="mt-2 text-sm font-bold text-white">
                  {selectedAccount.workflow_intelligence?.recommended_action || "Waiting for SCOUT activity on this account."}
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-white/55">
                  <span>Priority: {selectedAccount.workflow_intelligence?.priority_score ?? "—"}</span>
                  <span>Events: {selectedAccount.workflow_intelligence?.experience_count ?? 0}</span>
                  <span>Sent: {selectedAccount.workflow_intelligence?.sent_count ?? 0}</span>
                  <span>Replies: {selectedAccount.workflow_intelligence?.reply_count ?? 0}</span>
                </div>
              </div>
              <div className="mb-5 rounded-lg border border-white/10 bg-white/[0.03] p-3">
                <p className="text-[10px] uppercase tracking-widest text-white/30">Apollo prospect search</p>
                <p className="mt-2 text-xs text-white/55">
                  Search target: {selectedAccount.prospect_search?.organization_domain || selectedAccount.prospect_search?.organization_name || selectedAccount.name}
                </p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {(selectedAccount.prospect_search?.recommended_titles || []).map((title) => (
                    <span key={title} className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] text-white/50">
                      {title}
                    </span>
                  ))}
                </div>
                <Link href="/sales-console" className="mt-3 inline-flex text-[11px] font-bold text-amber-200 underline">
                  Open Sales Console to find prospects
                </Link>
              </div>
              <p className="text-[10px] uppercase tracking-widest text-white/30">User checkpoints</p>
              <ol className="mt-3 space-y-3 text-xs text-white/55">
                <li><span className="font-bold text-white/80">1. Lead captured:</span> user signs in and the account is saved to CRM.</li>
                <li><span className="font-bold text-white/80">2. Draft review:</span> user checks recipient, subject, and body before approval.</li>
                <li><span className="font-bold text-white/80">3. Send approval:</span> SCOUT sends via Resend only after this action unless Auto is enabled.</li>
                <li><span className="font-bold text-white/80">4. Reply capture:</span> buyer replies to a SCOUT token address, then CRM moves to replied.</li>
                <li><span className="font-bold text-white/80">5. User follow-up:</span> SCOUT notifies and forwards the reply based on Profile settings.</li>
              </ol>
              {suggestions.length > 0 && (
                <div className="mt-5 border-t border-white/10 pt-4">
                  <p className="text-[10px] uppercase tracking-widest text-white/30">SCOUT background ideas</p>
                  <div className="mt-3 space-y-3">
                    {suggestions.map((item) => (
                      <div key={item.trigger} className="rounded-lg border border-white/10 bg-white/[0.03] p-2.5">
                        <p className="text-[11px] font-bold text-white/80">{item.trigger}</p>
                        <p className="mt-1 text-[11px] leading-relaxed text-white/55">{item.action}</p>
                        <p className="mt-1 text-[10px] leading-relaxed text-white/35">{item.why}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </aside>
          </section>
        )}
      </main>
    </div>
  );
}
