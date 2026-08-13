/**
 * Sign up — account creation entry point using Supabase auth (dark workflow theme).
 */
import { useEffect, useMemo, useState } from "react";
import { Github } from "lucide-react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { supabase, supabaseOAuthRedirect } from "@/lib/supabase";
import { getPublicReadApiBase } from "@/lib/apiBase";
import { readSupplyAttribution, trackSupplyConversion, trackSignupStart } from "@/lib/siteAnalytics";
import { clearSupabaseOAuthParams, readSupabaseOAuthError } from "@/lib/authCallback";
import { resolvePostAuthPath, storePendingNext, postAuthRedirectTarget, readPlanParam, storeCheckoutIntent, navigateAfterAuth } from "@/lib/authNext";
import RobotWorkspaceProfileFields from "@/components/pipeline/RobotWorkspaceProfileFields";
import {
  isRobotWorkspaceProfileComplete,
  readRobotWorkspaceProfile,
  writeRobotWorkspaceProfile,
  type RobotWorkspaceProfile,
} from "@/lib/robotWorkspaceProfile";

const SIGNUP_NAME_KEY = "rfr_signup_full_name";
const WORKFLOW_CONTEXT_KEY = "rfr_workflow_context";

type WorkflowPrefill = {
  wf?: "robot_company" | "buyer";
  intent_focus?: string;
  company_url?: string;
  src?: string;
};

type InboxLink = { label: string; url: string };

function GoogleGlyph() {
  return (
    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-white" aria-hidden="true">
      <svg viewBox="0 0 24 24" className="h-4 w-4" focusable="false">
        <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.2-1.4 3.5-5.5 3.5-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.9 1.5l2.7-2.6C16.9 2.9 14.6 2 12 2 6.8 2 2.6 6.2 2.6 11.4S6.8 20.8 12 20.8c6.9 0 9.1-4.8 9.1-7.3 0-.5-.1-.9-.1-1.3H12Z"/>
        <path fill="#34A853" d="M3.7 7.3l3.2 2.3c.9-1.8 2.8-3 5.1-3 1.9 0 3.1.8 3.9 1.5l2.7-2.6C16.9 2.9 14.6 2 12 2 8.1 2 4.8 4.2 3.2 7.3Z"/>
        <path fill="#4285F4" d="M12 20.8c2.5 0 4.7-.8 6.3-2.3l-2.9-2.4c-.8.6-1.8 1-3.4 1-4.1 0-5.3-2.8-5.5-3.5l-3.3 2.5c1.6 3.1 4.9 4.7 8.8 4.7Z"/>
        <path fill="#FBBC05" d="M3.2 16.1l3.3-2.5c-.1-.4-.2-.9-.2-1.4s.1-1 .2-1.4L3.2 8.3c-.4 1-.6 2-.6 3.1s.2 2.1.6 3.1Z"/>
      </svg>
    </span>
  );
}

/**
 * Map an email address to its webmail inbox(es) so a user on the "check your
 * email" screen can open their inbox in one tap instead of hunting for it (a
 * common magic-link completion leak).
 *
 * Consumer domains map to a single provider. Our ICP (robot OEMs/integrators)
 * signs up with a *custom work-email domain* whose provider we can't detect
 * client-side without an MX lookup — so we surface the two hosts that cover the
 * overwhelming majority of business mailboxes: Google Workspace and Microsoft
 * 365. The Google link is domain-scoped so it routes straight to a Workspace
 * inbox when one exists. Returns [] only when there is no parseable domain.
 */
function emailInboxLinks(email: string): InboxLink[] {
  const domain = email.split("@")[1]?.toLowerCase().trim();
  if (!domain) return [];
  const consumer: Record<string, InboxLink> = {
    "gmail.com": { label: "Open Gmail", url: "https://mail.google.com/mail/u/0/" },
    "googlemail.com": { label: "Open Gmail", url: "https://mail.google.com/mail/u/0/" },
    "outlook.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "hotmail.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "live.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "msn.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "yahoo.com": { label: "Open Yahoo Mail", url: "https://mail.yahoo.com/" },
    "icloud.com": { label: "Open iCloud Mail", url: "https://www.icloud.com/mail/" },
    "me.com": { label: "Open iCloud Mail", url: "https://www.icloud.com/mail/" },
    "proton.me": { label: "Open Proton Mail", url: "https://mail.proton.me/u/0/" },
    "protonmail.com": { label: "Open Proton Mail", url: "https://mail.proton.me/u/0/" },
  };
  const hit = consumer[domain];
  if (hit) return [hit];
  // Custom work-email domain (the ICP): offer both dominant business hosts.
  return [
    { label: "Open Gmail / Workspace", url: `https://mail.google.com/a/${domain}` },
    { label: "Open Outlook / Microsoft 365", url: "https://outlook.office.com/mail/" },
  ];
}

function readWorkflowSessionContext(): WorkflowPrefill {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.sessionStorage.getItem(WORKFLOW_CONTEXT_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as WorkflowPrefill;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function appendWorkflowPrefill(path: string, prefill: WorkflowPrefill): string {
  const [base, query = ""] = path.split("?", 2);
  const nextParams = new URLSearchParams(query);
  if (prefill.wf) nextParams.set("wf", prefill.wf);
  if (prefill.intent_focus) nextParams.set("intent_focus", prefill.intent_focus);
  if (prefill.company_url) nextParams.set("company_url", prefill.company_url);
  if (prefill.src) nextParams.set("src", prefill.src);
  const serialized = nextParams.toString();
  return serialized ? `${base}?${serialized}` : base;
}

function workflowResultsPath(prefill: WorkflowPrefill): string {
  if (!prefill.company_url) return "/pipeline";
  const params = new URLSearchParams();
  params.set("url", prefill.company_url);
  params.set("limit", "5");
  if (prefill.src) params.set("src", `${prefill.src}_signup_return`);
  return `/results?${params.toString()}`;
}

/** Prefer an explicit ?next= destination over stale workflow URL-scan context. */
function shouldHonorWorkflowResults(nextRaw: string, prefill: WorkflowPrefill): boolean {
  if (!prefill.company_url) return false;
  if (nextRaw.startsWith("/results")) return true;
  // Explicit pipeline / home / pricing returns must not revive a prior URL submit.
  if (nextRaw.startsWith("/pipeline") || nextRaw === "/" || nextRaw.startsWith("/pricing")) {
    return false;
  }
  // Header "Start free workspace" is never a URL-submit continuation.
  if ((prefill.src || "").includes("home_header")) return false;
  return true;
}

export default function Signup() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resendNote, setResendNote] = useState("");
  const [oauthPending, setOauthPending] = useState<null | "google" | "github" | "azure">(null);
  const [liveProof, setLiveProof] = useState<{ hot?: number; companies?: number } | null>(null);
  // A real named HOT buyer from the live pipeline — turns abstract counts into a
  // concrete win the user can picture acting on (value-first proof at the decision point).
  const [liveBuyer, setLiveBuyer] = useState<
    { company: string; industry?: string; tier?: string; blurb?: string; robots: string[] } | null
  >(null);
  const [workspaceProfile, setWorkspaceProfile] = useState<RobotWorkspaceProfile>(() => {
    const existing = readRobotWorkspaceProfile();
    return {
      company_name: existing?.company_name || "",
      category: existing?.category || "",
      icp: existing?.icp || "",
      company_url: existing?.company_url || undefined,
    };
  });

  const search = typeof window !== "undefined" ? window.location.search : "";
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const hubspotIntent = params.get("intent") === "hubspot";
  const nextRaw = params.get("next") || "";
  const pipelineIntent = nextRaw.startsWith("/pipeline") || /[?&]lead=\d+/.test(nextRaw);
  const resultsIntent = nextRaw.startsWith("/results");
  // Specific buyer the anonymous user was acting on — carried through the signup wall
  // so we restate exactly what they unlock (value-first conversion continuity).
  const buyerCo = (params.get("co") || "").trim().slice(0, 80);

  const workflowPrefill = useMemo<WorkflowPrefill>(() => {
    const fromQuery: WorkflowPrefill = {
      wf: (params.get("wf") as WorkflowPrefill["wf"]) || undefined,
      intent_focus: params.get("intent_focus") || undefined,
      company_url: params.get("company_url") || undefined,
      src: params.get("src") || undefined,
    };
    if (fromQuery.wf || fromQuery.intent_focus || fromQuery.company_url) return fromQuery;
    return readWorkflowSessionContext();
  }, [params]);

  const matchedUnlockIntent =
    params.get("src") === "pipeline_matched_unlock" ||
    (pipelineIntent && Boolean(workflowPrefill.company_url || params.get("company_url")));

  const workflowReturnPath = useMemo(() => {
    if (!shouldHonorWorkflowResults(nextRaw, workflowPrefill)) return "/pipeline";
    return workflowResultsPath(workflowPrefill);
  }, [nextRaw, workflowPrefill]);

  const intendedPostAuthPath = useMemo(
    () => {
      const base = shouldHonorWorkflowResults(nextRaw, workflowPrefill)
        ? appendWorkflowPrefill(postAuthRedirectTarget(workflowReturnPath), workflowPrefill)
        : postAuthRedirectTarget(workflowReturnPath);
      return base;
    },
    [workflowPrefill, workflowReturnPath, nextRaw],
  );
  const nextPath = () => {
    const resolved = resolvePostAuthPath(workflowReturnPath);
    // Never re-attach a stale company_url onto an explicit pipeline/home return.
    if (!shouldHonorWorkflowResults(nextRaw, workflowPrefill) && !resolved.startsWith("/results")) {
      return resolved;
    }
    return appendWorkflowPrefill(resolved, workflowPrefill);
  };

  useEffect(() => {
    const plan = readPlanParam(search);
    if (plan) {
      storeCheckoutIntent(plan);
      return;
    }
    const next = params.get("next");
    if (next && next.startsWith("/")) storePendingNext(next);
  }, [params, search]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!workflowPrefill.wf && !workflowPrefill.intent_focus && !workflowPrefill.company_url) return;
    window.sessionStorage.setItem(WORKFLOW_CONTEXT_KEY, JSON.stringify(workflowPrefill));
  }, [workflowPrefill]);

  useEffect(() => {
    if (!matchedUnlockIntent || !workflowPrefill.company_url) return;
    setWorkspaceProfile((prev) => {
      if (prev.company_url === workflowPrefill.company_url && prev.company_name) return prev;
      const host = workflowPrefill.company_url!
        .replace(/^https?:\/\//, "")
        .replace(/^www\./, "")
        .split("/")[0];
      return {
        ...prev,
        company_url: workflowPrefill.company_url,
        company_name: prev.company_name || host || "",
      };
    });
  }, [matchedUnlockIntent, workflowPrefill.company_url]);

  // Funnel #20: record signup intent (denominator). Fires once per page view.
  useEffect(() => {
    trackSignupStart({
      plan: params.get("plan") || null,
      next: params.get("next") || null,
      intent: params.get("intent") || null,
      src: params.get("src") || null,
      referrer: typeof document !== "undefined" ? document.referrer || null : null,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const attribution = readSupplyAttribution(search);
    if (!attribution.utmSource && !attribution.robotCompanyId) return;
    trackSupplyConversion({
      page: "signup",
      utm_source: attribution.utmSource,
      rc: attribution.robotCompanyId,
      msg: attribution.messageToken,
      referrer: typeof document !== "undefined" ? document.referrer || null : null,
    });
  }, [search]);

  const persistFullName = () => {
    if (typeof window === "undefined" || !fullName.trim()) return;
    window.localStorage.setItem(SIGNUP_NAME_KEY, fullName.trim());
  };

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;

    void (async () => {
      const oauthErr = readSupabaseOAuthError();
      if (oauthErr) {
        setStatus("error");
        setErrMsg(oauthErr);
        window.history.replaceState(null, "", clearSupabaseOAuthParams(window.location.pathname, window.location.search));
        return;
      }

      const { data } = await client.auth.getSession();
      if (data?.session) navigateAfterAuth(nextPath());
    })();

    const { data: sub } = client.auth.onAuthStateChange((_event, session) => {
      if (session) {
        const attribution = readSupplyAttribution(search);
        if (attribution.utmSource || attribution.robotCompanyId) {
          trackSupplyConversion({
            page: "signup",
            completed: true,
            utm_source: attribution.utmSource,
            rc: attribution.robotCompanyId,
            msg: attribution.messageToken,
          });
        }
        navigateAfterAuth(nextPath());
      }
    });
    return () => sub.subscription.unsubscribe();
  }, [setLocation]);

  useEffect(() => {
    let cancelled = false;
    void fetch(`${getPublicReadApiBase()}/api/leads/summary?exclude_junk=true`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        const hot = Number(data.hot);
        const companies = Number(data.companies_in_database ?? data.total);
        if (hot > 0 || companies > 0) {
          setLiveProof({
            hot: Number.isFinite(hot) ? hot : undefined,
            companies: Number.isFinite(companies) ? companies : undefined,
          });
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  // Pull one real named HOT buyer from the live pipeline for cold/generic signups.
  // Skipped when the user already carried a specific buyer (buyerCo) or HubSpot intent,
  // so we never show a competing company than the one they came to act on.
  useEffect(() => {
    if (hubspotIntent || buyerCo) return;
    let cancelled = false;
    void fetch(`${getPublicReadApiBase()}/api/leads/pipeline`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        const leads = Array.isArray(data.leads) ? data.leads : [];
        const pick = leads.find(
          (l: any) =>
            String(l?.company_name || "").trim() &&
            String(l?.share_blurb || l?.share_summary || "").trim(),
        );
        if (!pick) return;
        const robots = Array.isArray(pick.robot_types_needed)
          ? pick.robot_types_needed.filter(Boolean)
          : [];
        setLiveBuyer({
          company: String(pick.company_name).trim().slice(0, 60),
          industry: pick.industry ? String(pick.industry) : undefined,
          tier: pick.priority_tier ? String(pick.priority_tier).toUpperCase() : undefined,
          blurb: String(pick.share_blurb || pick.share_summary || "").trim().slice(0, 160),
          robots: robots.slice(0, 2).map((r: any) => String(r)),
        });
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [hubspotIntent, buyerCo]);

  async function oauth(provider: "google" | "github" | "azure") {
    if (!supabase) {
      setStatus("error");
      setErrMsg("Configure VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }
    if (hubspotIntent && !fullName.trim()) {
      setStatus("error");
      setErrMsg("Enter your full name so SIGNAL can authenticate your HubSpot workspace.");
      return;
    }
    if (matchedUnlockIntent && !isRobotWorkspaceProfileComplete(workspaceProfile)) {
      setStatus("error");
      setErrMsg("Add company name, robot category, and ICP before creating your account.");
      return;
    }
    if (matchedUnlockIntent) {
      writeRobotWorkspaceProfile({
        ...workspaceProfile,
        company_url: workflowPrefill.company_url || workspaceProfile.company_url,
      });
    }
    persistFullName();
    setErrMsg("");
    setStatus("idle");
    setOauthPending(provider);
    storePendingNext(intendedPostAuthPath);
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: supabaseOAuthRedirect(intendedPostAuthPath) },
    });
    if (error) {
      setOauthPending(null);
      setStatus("error");
      setErrMsg(
        provider === "azure" && /provider is not enabled/i.test(error.message)
          ? "This OAuth provider is not enabled yet in Supabase Auth. Use Google or GitHub, or enable the provider in Supabase."
          : error.message,
      );
    }
  }

  // Tick down the resend cooldown so users aren't left guessing when they can retry.
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = window.setTimeout(() => setResendCooldown((n) => Math.max(0, n - 1)), 1000);
    return () => window.clearTimeout(t);
  }, [resendCooldown]);

  async function sendMagicLink(): Promise<boolean> {
    if (!email.trim() || !supabase) return false;
    storePendingNext(intendedPostAuthPath);
    const redirectTo = supabaseOAuthRedirect(intendedPostAuthPath);
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: redirectTo },
    });
    if (error) {
      setStatus("error");
      setErrMsg(error.message);
      return false;
    }
    return true;
  }

  async function magicLink(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !supabase) return;
    if (hubspotIntent && !fullName.trim()) {
      setStatus("error");
      setErrMsg("Enter your full name so SIGNAL can authenticate your HubSpot workspace.");
      return;
    }
    if (matchedUnlockIntent && !isRobotWorkspaceProfileComplete(workspaceProfile)) {
      setStatus("error");
      setErrMsg("Add company name, robot category, and ICP before creating your account.");
      return;
    }
    if (matchedUnlockIntent) {
      writeRobotWorkspaceProfile({
        ...workspaceProfile,
        company_url: workflowPrefill.company_url || workspaceProfile.company_url,
      });
    }
    persistFullName();
    setStatus("sending");
    setErrMsg("");
    setResendNote("");
    const ok = await sendMagicLink();
    if (ok) {
      setStatus("sent");
      setResendCooldown(30);
    }
  }

  async function resendMagicLink() {
    if (resendCooldown > 0 || !email.trim()) return;
    setResendNote("Sending…");
    const ok = await sendMagicLink();
    if (ok) {
      setResendNote("Sent again — check your inbox and spam folder.");
      setResendCooldown(30);
    } else {
      setResendNote("");
    }
  }

  const loginHref = `/login${search}`;

  return (
    <div className="min-h-screen flex flex-col bg-[#081126] text-slate-100">
      <Header />
      <main className="flex-1 px-4 pt-24 pb-16">
        <div className="mx-auto grid w-full max-w-5xl items-start gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div>
            <p className="section-eyebrow mb-3">
              {hubspotIntent ? "HubSpot + SIGNAL workspace" : "Robot OEMs & integrators"}
            </p>
            <h1 className="max-w-xl font-display text-4xl font-bold leading-tight text-slate-100 md:text-5xl">
              {hubspotIntent
                ? "Sign up, then SIGNAL links HubSpot automatically."
                : pipelineIntent
                  ? buyerCo
                    ? `Save ${buyerCo}. Copy the draft. Run your pipeline.`
                    : <><span className="text-emerald-300">Save the Lead.</span> Copy the draft. Run your pipeline.</>
                  : resultsIntent
                    ? "Unlock your matched buyers in one workspace."
                    : "Automate your robot sales funnel."}
            </h1>
            <p className="mt-5 max-w-lg text-sm leading-relaxed text-slate-300">
              {hubspotIntent
                ? "Use your work email and full name. After signup, SIGNAL provisions the HubSpot API connection and MCP bridge — no manual app setup."
                : pipelineIntent
                  ? buyerCo
                    ? `Free workspace: land back on ${buyerCo}, save it in one click, copy the outreach draft SIGNAL wrote for them, and sync to HubSpot when you are ready.`
                    : "Free workspace: land on your matched lead, save it in one click, copy the outreach draft, and sync to HubSpot when you are ready."
                  : resultsIntent
                    ? "Sign up to unlock every URL scan match, save leads to CRM, and copy signal-matched outreach drafts."
                    : "For robot OEMs and integrators — live buyer intent, Cal's timely notes, and the first informed conversation with a robot buyer — not another giant contact list."}
            </p>
            {(workflowPrefill.wf || workflowPrefill.intent_focus) && (
              <div className="mt-4 flex flex-wrap items-center gap-2">
                {workflowPrefill.wf && (
                  <span className="rounded-full border border-slate-600 bg-slate-900 px-3 py-1 text-[11px] font-semibold text-slate-200">
                    Workflow: {workflowPrefill.wf === "robot_company" ? "Robot company" : "Potential customer"}
                  </span>
                )}
                {workflowPrefill.intent_focus && (
                  <span className="rounded-full border border-emerald-800 bg-emerald-950/40 px-3 py-1 text-[11px] font-semibold text-emerald-300">
                    Focus: {workflowPrefill.intent_focus}
                  </span>
                )}
              </div>
            )}
            {liveProof && (liveProof.hot || liveProof.companies) && (
              <p className="mt-3 inline-flex rounded-full border border-emerald-800 bg-emerald-950/40 px-3 py-1 text-[11px] font-semibold text-emerald-300">
                Live now ·{" "}
                {liveProof.hot ? `${liveProof.hot.toLocaleString()} hot buyers` : "buyer signals scored"}
                {liveProof.companies ? ` · ${liveProof.companies.toLocaleString()} companies tracked` : ""}
              </p>
            )}
            {!hubspotIntent && !pipelineIntent && !resultsIntent && (
              <ul className="mt-4 space-y-2 text-xs text-slate-300">
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Native pipeline + kanban — or connect HubSpot in one click
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  HOT/WARM buyers with pitch actions and Cal's curiosity-led notes
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Free to start · no credit card
                </li>
              </ul>
            )}
            {(pipelineIntent || resultsIntent) && !hubspotIntent && (
              <ul className="mt-4 space-y-2 text-xs text-slate-300">
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  {buyerCo
                    ? `Pick up right where you left off on ${buyerCo} — draft waiting in pipeline`
                    : "Pick up on the same lead after signup — draft waiting in pipeline"}
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Copy signal-matched outreach drafts in one click
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Live pipeline leads · pitch actions · robot categories
                </li>
              </ul>
            )}
            {liveBuyer && (
              <div className="mt-6 rounded-2xl border border-slate-700 p-4 shadow-sm">
                <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-emerald-700">
                  <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                  </span>
                  Live {liveBuyer.tier || "HOT"} buyer in the pipeline right now
                </div>
                <p className="mt-2 font-display text-base font-bold text-slate-100">
                  {liveBuyer.company}
                  {liveBuyer.industry ? (
                    <span className="ml-2 text-xs font-medium text-slate-400">{liveBuyer.industry}</span>
                  ) : null}
                </p>
                {liveBuyer.blurb && (
                  <p className="mt-1 text-xs leading-relaxed text-slate-300">{liveBuyer.blurb}</p>
                )}
                {liveBuyer.robots.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {liveBuyer.robots.map((r) => (
                      <span
                        key={r}
                        className="rounded-full border border-emerald-500 px-2 py-0.5 text-[10px] font-semibold text-emerald-300"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                )}
                <p className="mt-3 text-[11px] font-medium text-slate-400">
                  Sign up to save these matched leads. Upgrade to unlock full lead coverage, CRM sync, and automated sales process.
                </p>
              </div>
            )}
          </div>

          {status === "sent" ? (
            <div className="rounded-2xl border border-emerald-800 px-6 py-8 text-center">
              <h2 className="text-xl font-bold text-slate-100">Check your email</h2>
              <p className="mt-3 text-sm text-slate-300">
                We sent a one-tap sign-in link to <span className="font-semibold text-emerald-700">{email}</span>.
                Open it and you'll land{" "}
                {pipelineIntent && buyerCo
                  ? `back on ${buyerCo}, ready to save and copy the draft.`
                  : "in your pipeline, ready to save your first lead and copy the outreach draft."}
              </p>
              {(() => {
                const inboxes = emailInboxLinks(email);
                if (inboxes.length === 0) return null;
                return (
                  <div className="mt-6 flex flex-col gap-2">
                    {inboxes.map((inbox, i) => (
                      <a
                        key={inbox.url}
                        href={inbox.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={
                          i === 0
                            ? "inline-block w-full rounded-xl border border-emerald-500 px-4 py-3 text-sm font-bold text-emerald-300 transition-all hover:border-emerald-400"
                            : "inline-block w-full rounded-xl border border-emerald-700 px-4 py-3 text-sm font-semibold text-emerald-300 transition-all hover:border-emerald-500"
                        }
                      >
                        {inbox.label} →
                      </a>
                    ))}
                  </div>
                );
              })()}
              <div className="mt-5 flex flex-col items-center gap-2 text-xs text-slate-300">
                <p>Didn't get it? Check spam, or resend.</p>
                <button
                  type="button"
                  onClick={() => void resendMagicLink()}
                  disabled={resendCooldown > 0}
                    className="font-semibold text-emerald-300 hover:text-emerald-200 disabled:text-slate-500"
                >
                  {resendCooldown > 0 ? `Resend link in ${resendCooldown}s` : "Resend link"}
                </button>
                {resendNote && <p className="text-emerald-700">{resendNote}</p>}
              </div>
              <button
                type="button"
                onClick={() => {
                  setStatus("idle");
                  setResendCooldown(0);
                  setResendNote("");
                }}
                className="mt-6 text-xs text-slate-400 hover:text-slate-200"
              >
                Use a different email
              </button>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-700 p-6 shadow-sm">
              <h2 className="font-display text-xl font-bold text-slate-100">
                {hubspotIntent ? "Sign up for HubSpot sync" : matchedUnlockIntent ? "Company details + free account" : "Start free"}
              </h2>
              <p className="mt-2 text-sm text-slate-300">
                {hubspotIntent
                  ? "Email + full name required. Next step: one-click HubSpot authorize."
                  : matchedUnlockIntent
                    ? "Confirm company name, robot category, and ICP — then create your account to unlock 15 matched sales leads."
                    : params.get("next")
                    ? "Use one-tap OAuth and we create your account instantly, then your matched leads are saved."
                    : "Use one-tap OAuth to create your account instantly, then upgrade to unlock full pipeline coverage and CRM automation."}
              </p>
              {matchedUnlockIntent && (
                <div className="mt-4 rounded-xl border border-amber-500/40 bg-amber-500/5 p-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-amber-300">
                    Required for matched pipeline
                  </p>
                  <div className="mt-3">
                    <RobotWorkspaceProfileFields
                      value={workspaceProfile}
                      onChange={setWorkspaceProfile}
                      submittedHostname={
                        (workflowPrefill.company_url || "")
                          .replace(/^https?:\/\//, "")
                          .replace(/^www\./, "")
                          .split("/")[0] || undefined
                      }
                      tone="dark"
                      idPrefix="signup-matched"
                    />
                  </div>
                </div>
              )}
              {liveProof && (liveProof.hot || liveProof.companies) && (
                <div className="mt-4 flex items-center gap-2 rounded-xl border border-emerald-800 px-3 py-2 text-[11px] font-semibold text-emerald-300">
                  <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                  </span>
                  <span>
                    {liveProof.hot ? `${liveProof.hot.toLocaleString()} HOT buyers live now` : "Live buyer signals scored"}
                    {liveProof.companies ? ` · ${liveProof.companies.toLocaleString()} companies tracked` : ""}
                  </span>
                </div>
              )}
              {hubspotIntent && (
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Full name"
                  className="mt-4 w-full rounded-xl border border-slate-600 bg-transparent px-3 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500"
                />
              )}
              <div className={`${hubspotIntent ? "mt-4" : "mt-6"} flex flex-col gap-2`}>
                <button
                  type="button"
                  onClick={() => void oauth("google")}
                  disabled={!supabase || oauthPending !== null}
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-emerald-500 px-4 py-3 text-sm font-bold text-emerald-300 transition-all hover:border-emerald-400 disabled:opacity-40"
                >
                  <GoogleGlyph />
                  {oauthPending === "google" ? "Redirecting to Google..." : "Continue with Google — one tap"}
                </button>
                <button
                  type="button"
                  onClick={() => void oauth("github")}
                  disabled={!supabase || oauthPending !== null}
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-600 px-4 py-3 text-sm font-bold text-slate-100 transition-all hover:border-slate-400 disabled:opacity-40"
                >
                  <Github className="h-4 w-4" aria-hidden="true" />
                  {oauthPending === "github" ? "Redirecting to GitHub..." : "Continue with GitHub — one tap"}
                </button>
                {!hubspotIntent && (
                  <p className="text-center text-[11px] font-medium text-slate-400">
                    Google OAuth + GitHub are live · account created automatically · no password required
                  </p>
                )}
              </div>
              <div className="mt-4 rounded-xl border border-cyan-700 px-4 py-3 text-xs text-cyan-300">
                Microsoft sign in coming soon.
              </div>
              <div className="my-5 flex items-center gap-3">
                <span className="h-px flex-1 bg-slate-700" />
                <span className="text-[10px] uppercase tracking-widest text-slate-400">
                  {hubspotIntent ? "or" : "or use your work email"}
                </span>
                <span className="h-px flex-1 bg-slate-700" />
              </div>
              <form onSubmit={(e) => void magicLink(e)} className="space-y-3">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@robotcompany.com"
                  disabled={status === "sending"}
                  className="w-full rounded-xl border border-slate-600 bg-transparent px-3 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500"
                />
                {status === "error" && (
                  <p className="rounded-lg border border-red-700 px-3 py-2 text-xs text-red-300">{errMsg}</p>
                )}
                <button
                  type="submit"
                  disabled={status === "sending" || !email.trim()}
                  className={
                    hubspotIntent
                      ? "w-full rounded-xl border border-emerald-500 px-4 py-3 text-sm font-bold text-emerald-300 transition-all hover:border-emerald-400 disabled:opacity-40"
                      : "w-full rounded-xl border border-emerald-500 px-4 py-3 text-sm font-bold text-emerald-300 transition-all hover:border-emerald-400 disabled:opacity-40"
                  }
                >
                  {status === "sending" ? "Sending..." : hubspotIntent ? "Sign up & connect HubSpot" : "Email me a sign-in link"}
                </button>
              </form>
              {!hubspotIntent && (
                <div className="mt-4 text-center text-[11px] text-slate-400">
                  <button type="button" disabled className="font-semibold text-slate-500 underline-offset-2 opacity-60">
                    Microsoft sign in coming soon.
                  </button>
                </div>
              )}
              <p className="mt-5 text-center text-xs text-slate-400">
                Already have an account?{" "}
                <Link href={loginHref} className="font-semibold text-emerald-300 hover:text-emerald-200">
                  Sign in
                </Link>
              </p>
            </div>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
