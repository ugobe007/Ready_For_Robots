/**
 * Sign up — account creation entry point using Supabase auth (dark workflow theme).
 */
import { useEffect, useMemo, useState } from "react";
import { Github } from "lucide-react";
import { Link, useLocation } from "wouter";
import { SiteFooter, SiteHeader } from "@/components/editorial";
import {
  AUTH_UNAVAILABLE_MSG,
  supabase,
  supabaseOAuthRedirect,
} from "@/lib/supabase";
import { authEmailRejectReason, normalizeAuthEmail } from "@/lib/authEmail";
import {
  readSupplyAttribution,
  trackSupplyConversion,
  trackSignupStart,
} from "@/lib/siteAnalytics";
import {
  clearSupabaseOAuthParams,
  readSupabaseOAuthError,
} from "@/lib/authCallback";
import {
  resolvePostAuthPath,
  storePendingNext,
  postAuthRedirectTarget,
  readPlanParam,
  storeCheckoutIntent,
  navigateAfterAuth,
} from "@/lib/authNext";
import RobotWorkspaceProfileFields from "@/components/pipeline/RobotWorkspaceProfileFields";
import {
  isRobotWorkspaceProfileComplete,
  readRobotWorkspaceProfile,
  writeRobotWorkspaceProfile,
  type RobotWorkspaceProfile,
} from "@/lib/robotWorkspaceProfile";
import {
  resolveSignupWorkflowReturnPath,
  shouldHonorWorkflowResults,
  isJobsProductReturnPath,
  type WorkflowPrefill,
} from "@/lib/signupWorkflowPath";
import { isJobsHandoffSrc, CRM_UNLOCKED_JOBS } from "@/lib/jobsWorkflow";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";

const SIGNUP_NAME_KEY = "rfr_signup_full_name";
const WORKFLOW_CONTEXT_KEY = "rfr_workflow_context";

type InboxLink = { label: string; url: string };

function GoogleGlyph() {
  return (
    <span
      className="inline-flex h-5 w-5 items-center justify-center  bg-white"
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" focusable="false">
        <path
          fill="#EA4335"
          d="M12 10.2v3.9h5.5c-.2 1.2-1.4 3.5-5.5 3.5-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.9 1.5l2.7-2.6C16.9 2.9 14.6 2 12 2 6.8 2 2.6 6.2 2.6 11.4S6.8 20.8 12 20.8c6.9 0 9.1-4.8 9.1-7.3 0-.5-.1-.9-.1-1.3H12Z"
        />
        <path
          fill="#34A853"
          d="M3.7 7.3l3.2 2.3c.9-1.8 2.8-3 5.1-3 1.9 0 3.1.8 3.9 1.5l2.7-2.6C16.9 2.9 14.6 2 12 2 8.1 2 4.8 4.2 3.2 7.3Z"
        />
        <path
          fill="#4285F4"
          d="M12 20.8c2.5 0 4.7-.8 6.3-2.3l-2.9-2.4c-.8.6-1.8 1-3.4 1-4.1 0-5.3-2.8-5.5-3.5l-3.3 2.5c1.6 3.1 4.9 4.7 8.8 4.7Z"
        />
        <path
          fill="#FBBC05"
          d="M3.2 16.1l3.3-2.5c-.1-.4-.2-.9-.2-1.4s.1-1 .2-1.4L3.2 8.3c-.4 1-.6 2-.6 3.1s.2 2.1.6 3.1Z"
        />
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
    "gmail.com": {
      label: "Open Gmail",
      url: "https://mail.google.com/mail/u/0/",
    },
    "googlemail.com": {
      label: "Open Gmail",
      url: "https://mail.google.com/mail/u/0/",
    },
    "outlook.com": {
      label: "Open Outlook",
      url: "https://outlook.live.com/mail/0/",
    },
    "hotmail.com": {
      label: "Open Outlook",
      url: "https://outlook.live.com/mail/0/",
    },
    "live.com": {
      label: "Open Outlook",
      url: "https://outlook.live.com/mail/0/",
    },
    "msn.com": {
      label: "Open Outlook",
      url: "https://outlook.live.com/mail/0/",
    },
    "yahoo.com": { label: "Open Yahoo Mail", url: "https://mail.yahoo.com/" },
    "icloud.com": {
      label: "Open iCloud Mail",
      url: "https://www.icloud.com/mail/",
    },
    "me.com": {
      label: "Open iCloud Mail",
      url: "https://www.icloud.com/mail/",
    },
    "proton.me": {
      label: "Open Proton Mail",
      url: "https://mail.proton.me/u/0/",
    },
    "protonmail.com": {
      label: "Open Proton Mail",
      url: "https://mail.proton.me/u/0/",
    },
  };
  const hit = consumer[domain];
  if (hit) return [hit];
  // Custom work-email domain (the ICP): offer both dominant business hosts.
  return [
    {
      label: "Open Gmail / Workspace",
      url: `https://mail.google.com/a/${domain}`,
    },
    {
      label: "Open Outlook / Microsoft 365",
      url: "https://outlook.office.com/mail/",
    },
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
  if (prefill.intent_focus)
    nextParams.set("intent_focus", prefill.intent_focus);
  if (prefill.company_url) nextParams.set("company_url", prefill.company_url);
  if (prefill.src) nextParams.set("src", prefill.src);
  const serialized = nextParams.toString();
  return serialized ? `${base}?${serialized}` : base;
}

export default function Signup() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle"
  );
  const [errMsg, setErrMsg] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resendNote, setResendNote] = useState("");
  const [oauthPending, setOauthPending] = useState<
    null | "google" | "github" | "azure"
  >(null);
  const [workspaceProfile, setWorkspaceProfile] =
    useState<RobotWorkspaceProfile>(() => {
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
  const pipelineIntent =
    nextRaw.startsWith("/pipeline") || /[?&]lead=\d+/.test(nextRaw);
  const robotJobsIntent =
    isJobsHandoffSrc(params.get("src")) ||
    isJobsProductReturnPath(nextRaw) ||
    nextRaw.startsWith("/crm");
  // Specific buyer the anonymous user was acting on — carried through the signup wall
  // so we restate exactly what they unlock (value-first conversion continuity).
  const jobsHandoff = robotJobsIntent ? readJobsHandoffSnapshot() : null;
  const tasteJobs = (jobsHandoff?.jobs || []).slice(0, CRM_UNLOCKED_JOBS);

  const workflowPrefill = useMemo<WorkflowPrefill>(() => {
    const fromQuery: WorkflowPrefill = {
      wf: (params.get("wf") as WorkflowPrefill["wf"]) || undefined,
      intent_focus: params.get("intent_focus") || undefined,
      company_url: params.get("company_url") || undefined,
      src: params.get("src") || undefined,
    };
    if (fromQuery.wf || fromQuery.intent_focus || fromQuery.company_url)
      return fromQuery;
    return readWorkflowSessionContext();
  }, [params]);

  const matchedUnlockIntent =
    !robotJobsIntent &&
    (params.get("src") === "pipeline_matched_unlock" ||
      (pipelineIntent &&
        Boolean(workflowPrefill.company_url || params.get("company_url"))));

  /** Keep URL-matched unlock on /pipeline?url=… — never fall back to bare /pipeline or Results. */
  const matchedPipelineReturnPath = useMemo(() => {
    const companyUrl = (
      workflowPrefill.company_url ||
      params.get("company_url") ||
      ""
    ).trim();
    if (!matchedUnlockIntent || !companyUrl) return null;
    const p = new URLSearchParams();
    p.set("src", "results_scan");
    p.set("url", companyUrl);
    const leadMatch = nextRaw.match(/[?&]lead=(\d+)/);
    if (leadMatch) p.set("lead", leadMatch[1]);
    return `/pipeline?${p.toString()}`;
  }, [matchedUnlockIntent, workflowPrefill.company_url, params, nextRaw]);

  const workflowReturnPath = useMemo(() => {
    return resolveSignupWorkflowReturnPath({
      nextRaw,
      prefill: workflowPrefill,
      matchedPipelineReturnPath,
    });
  }, [nextRaw, workflowPrefill, matchedPipelineReturnPath]);

  const intendedPostAuthPath = useMemo(() => {
    const base = shouldHonorWorkflowResults(nextRaw, workflowPrefill)
      ? appendWorkflowPrefill(
          postAuthRedirectTarget(workflowReturnPath),
          workflowPrefill
        )
      : postAuthRedirectTarget(workflowReturnPath);
    return base;
  }, [workflowPrefill, workflowReturnPath, nextRaw]);
  const nextPath = () => {
    const resolved = resolvePostAuthPath(workflowReturnPath);
    // Never re-attach a stale company_url onto an explicit pipeline/home return.
    if (
      !shouldHonorWorkflowResults(nextRaw, workflowPrefill) &&
      !resolved.startsWith("/results")
    ) {
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
    if (
      !workflowPrefill.wf &&
      !workflowPrefill.intent_focus &&
      !workflowPrefill.company_url
    )
      return;
    window.sessionStorage.setItem(
      WORKFLOW_CONTEXT_KEY,
      JSON.stringify(workflowPrefill)
    );
  }, [workflowPrefill]);

  useEffect(() => {
    if (!matchedUnlockIntent || !workflowPrefill.company_url) return;
    setWorkspaceProfile(prev => {
      if (prev.company_url === workflowPrefill.company_url && prev.company_name)
        return prev;
      const host = workflowPrefill
        .company_url!.replace(/^https?:\/\//, "")
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
      referrer:
        typeof document !== "undefined" ? document.referrer || null : null,
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
      referrer:
        typeof document !== "undefined" ? document.referrer || null : null,
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
        window.history.replaceState(
          null,
          "",
          clearSupabaseOAuthParams(
            window.location.pathname,
            window.location.search
          )
        );
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

  async function oauth(provider: "google" | "github" | "azure") {
    if (!supabase) {
      setStatus("error");
      setErrMsg(AUTH_UNAVAILABLE_MSG);
      return;
    }
    if (hubspotIntent && !fullName.trim()) {
      setStatus("error");
      setErrMsg(
        "Enter your full name so SIGNAL can authenticate your HubSpot workspace."
      );
      return;
    }
    if (
      matchedUnlockIntent &&
      !isRobotWorkspaceProfileComplete(workspaceProfile)
    ) {
      setStatus("error");
      setErrMsg(
        "Add company name, robot category, and ICP before creating your account."
      );
      return;
    }
    if (matchedUnlockIntent) {
      writeRobotWorkspaceProfile({
        ...workspaceProfile,
        company_url:
          workflowPrefill.company_url || workspaceProfile.company_url,
      });
    }
    persistFullName();
    if (workspaceProfile.company_name.trim() && !matchedUnlockIntent) {
      writeRobotWorkspaceProfile(workspaceProfile);
    }
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
          : error.message
      );
    }
  }

  // Tick down the resend cooldown so users aren't left guessing when they can retry.
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = window.setTimeout(
      () => setResendCooldown(n => Math.max(0, n - 1)),
      1000
    );
    return () => window.clearTimeout(t);
  }, [resendCooldown]);

  async function sendMagicLink(): Promise<boolean> {
    if (!supabase) {
      setStatus("error");
      setErrMsg(AUTH_UNAVAILABLE_MSG);
      return false;
    }
    const reason = authEmailRejectReason(email);
    if (reason) {
      setStatus("error");
      setErrMsg(reason);
      return false;
    }
    const normalized = normalizeAuthEmail(email);
    if (!normalized) return false;
    storePendingNext(intendedPostAuthPath);
    const redirectTo = supabaseOAuthRedirect(intendedPostAuthPath);
    const { error } = await supabase.auth.signInWithOtp({
      email: normalized,
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
    if (!supabase) {
      setStatus("error");
      setErrMsg(AUTH_UNAVAILABLE_MSG);
      return;
    }
    if (!email.trim()) return;
    if (hubspotIntent && !fullName.trim()) {
      setStatus("error");
      setErrMsg(
        "Enter your full name so SIGNAL can authenticate your HubSpot workspace."
      );
      return;
    }
    if (
      matchedUnlockIntent &&
      !isRobotWorkspaceProfileComplete(workspaceProfile)
    ) {
      setStatus("error");
      setErrMsg(
        "Add company name, robot category, and ICP before creating your account."
      );
      return;
    }
    if (matchedUnlockIntent) {
      writeRobotWorkspaceProfile({
        ...workspaceProfile,
        company_url:
          workflowPrefill.company_url || workspaceProfile.company_url,
      });
    }
    persistFullName();
    if (workspaceProfile.company_name.trim() && !matchedUnlockIntent) {
      writeRobotWorkspaceProfile(workspaceProfile);
    }
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
  const savedBuyers = tasteJobs.filter(
    job => !job.is_example && (job.company_name || "").trim()
  );
  const fromFind = savedBuyers.length > 0;
  const buyerCount = savedBuyers.length;
  const gets = [
    {
      n: "01",
      head: "Every buyer for your robot, ranked",
      body: "Company, the workflow, why now, and the source. Budget confirmed first.",
    },
    {
      n: "02",
      head: "Alerts when a new buyer appears",
      body: "A new RFP or robotics hire that fits one of your robots lands in your inbox the day we find it.",
    },
    {
      n: "03",
      head: "A desk to work the list",
      body: "Save buyers, move them from new to contacted to won, and keep notes in one place.",
    },
  ];

  return (
    <div className="rfr-editorial rfr-account">
      <SiteHeader />
      <main>
        <section className="rfr-account-split">
          <div className="rfr-account-copy">
            <div className="rfr-account-kicker">
              {fromFind ? "SAVE THESE BUYERS" : "CREATE ACCOUNT"}
            </div>
            <h1>
              {fromFind
                ? `Keep the ${buyerCount} buyer${buyerCount === 1 ? "" : "s"} we found for your robot.`
                : "Find who is ready to buy your robots."}
            </h1>
            <p className="rfr-account-lede">
              {fromFind
                ? "Create an account to save them to your desk and get an alert when a new buyer fits this robot."
                : "Paste a robot's page and see which companies are budgeting, piloting or hiring for that work. An account keeps them."}
            </p>
            {fromFind ? (
              <div className="rfr-account-saving">
                <div className="rfr-account-saving-head">
                  <span>BUYERS FOR ROBOT · SAVED WHEN YOU SIGN UP</span>
                </div>
                {savedBuyers.map(job => {
                  const label = (job.readiness_label || "").trim();
                  const strong = /budget/i.test(label);
                  return (
                    <div className="rfr-account-buyer" key={job.job_key}>
                      <strong>{job.company_name}</strong>
                      {label ? (
                        <span
                          className={`rfr-account-tag ${strong ? "is-strong" : "is-soft"}`}
                        >
                          {label.toUpperCase()}
                        </span>
                      ) : (
                        <span />
                      )}
                      <em>
                        {[job.workflow || job.title, job.industry]
                          .filter(Boolean)
                          .join(" · ")}
                      </em>
                      <span className="rfr-account-why">
                        {job.why_now || ""}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="rfr-account-gets">
                {gets.map(item => (
                  <div className="rfr-account-get" key={item.n}>
                    <span className="rfr-account-num">{item.n}</span>
                    <b>{item.head}</b>
                    <span>{item.body}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rfr-account-card">
            <div className="rfr-account-tabs">
              <span className="is-on">Create account</span>
              <Link href={loginHref} className="is-off">
                Sign in
              </Link>
            </div>
            {status === "sent" ? (
              <>
                <h2>Check your email</h2>
                <p className="rfr-account-lede">
                  We sent a sign-in link to <b>{email}</b>.
                  {fromFind
                    ? " Open it and you go straight back to your results."
                    : " Open it and we'll take you to the next step."}
                </p>
                {emailInboxLinks(email).map(inbox => (
                  <a
                    key={inbox.url}
                    className="rfr-account-secondary"
                    href={inbox.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {inbox.label}
                  </a>
                ))}
                <button
                  type="button"
                  className="rfr-account-fine"
                  onClick={() => void resendMagicLink()}
                  disabled={resendCooldown > 0}
                >
                  {resendCooldown > 0
                    ? `Resend link in ${resendCooldown}s`
                    : "Resend link"}
                </button>
                {resendNote ? <p className="rfr-account-fine">{resendNote}</p> : null}
                <button
                  type="button"
                  className="rfr-account-secondary"
                  onClick={() => void oauth("google")}
                  disabled={!supabase || oauthPending !== null}
                >
                  <GoogleGlyph />
                  {oauthPending === "google"
                    ? "Redirecting to Google..."
                    : "Continue with Google"}
                </button>
                <button
                  type="button"
                  className="rfr-account-fine"
                  onClick={() => {
                    setStatus("idle");
                    setResendCooldown(0);
                    setResendNote("");
                  }}
                >
                  Use a different email
                </button>
              </>
            ) : (
              <>
                {matchedUnlockIntent && (
                  <RobotWorkspaceProfileFields
                    value={workspaceProfile}
                    onChange={setWorkspaceProfile}
                    submittedHostname={
                      (workflowPrefill.company_url || "")
                        .replace(/^https?:\/\//, "")
                        .replace(/^www\./, "")
                        .split("/")[0] || undefined
                    }
                    tone="light"
                    idPrefix="signup-matched"
                  />
                )}
                {!supabase ? (
                  <p className="rfr-account-error" role="alert">
                    {AUTH_UNAVAILABLE_MSG}
                  </p>
                ) : null}
                {status === "error" && errMsg ? (
                  <p className="rfr-account-error" role="alert">
                    {errMsg}
                  </p>
                ) : null}
                <form onSubmit={e => void magicLink(e)}>
                  <label>
                    <span className="rfr-account-label">YOUR NAME</span>
                    <input
                      type="text"
                      autoComplete="name"
                      placeholder="Alex Rivera"
                      value={fullName}
                      onChange={e => setFullName(e.target.value)}
                      required={hubspotIntent}
                    />
                  </label>
                  {!matchedUnlockIntent && (
                    <label>
                      <span className="rfr-account-label">COMPANY</span>
                      <input
                        type="text"
                        autoComplete="organization"
                        placeholder="Robot maker, dealer or integrator"
                        value={workspaceProfile.company_name}
                        onChange={e =>
                          setWorkspaceProfile(prev => ({
                            ...prev,
                            company_name: e.target.value,
                          }))
                        }
                      />
                    </label>
                  )}
                  <label>
                    <span className="rfr-account-label">WORK EMAIL</span>
                    <input
                      type="email"
                      required
                      autoComplete="email"
                      inputMode="email"
                      spellCheck={false}
                      placeholder="you@company.com"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      disabled={status === "sending"}
                      className={status === "error" ? "is-error" : undefined}
                    />
                  </label>
                  <button
                    type="submit"
                    className="rfr-account-submit"
                    disabled={status === "sending" || !email.trim() || !supabase}
                  >
                    {status === "sending"
                      ? "Sending..."
                      : fromFind
                        ? "Save buyers and create account"
                        : hubspotIntent
                          ? "Sign up and connect HubSpot"
                          : "Create account"}
                  </button>
                </form>
                <p className="rfr-account-fine">
                  {fromFind
                    ? "Free during early access. We use your email for sign-in and buyer alerts only. You go straight back to your results."
                    : "Free during early access. We use your email for sign-in and buyer alerts only."}{" "}
                  Already have an account? <Link href={loginHref}>Sign in</Link>
                </p>
                <button
                  type="button"
                  className="rfr-account-secondary"
                  onClick={() => void oauth("google")}
                  disabled={!supabase || oauthPending !== null}
                >
                  <GoogleGlyph />
                  {oauthPending === "google"
                    ? "Redirecting to Google..."
                    : "Continue with Google"}
                </button>
                <button
                  type="button"
                  className="rfr-account-secondary"
                  onClick={() => void oauth("github")}
                  disabled={!supabase || oauthPending !== null}
                >
                  <Github className="h-4 w-4" aria-hidden="true" />
                  {oauthPending === "github"
                    ? "Redirecting to GitHub..."
                    : "Continue with GitHub"}
                </button>
              </>
            )}
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
