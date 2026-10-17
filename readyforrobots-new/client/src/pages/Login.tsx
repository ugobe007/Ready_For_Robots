/**
 * Sign in — Supabase magic link + OAuth (dark workflow theme).
 */
import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { SiteFooter, SiteHeader } from "@/components/editorial";
import {
  AUTH_UNAVAILABLE_MSG,
  supabase,
  supabaseOAuthRedirect,
} from "@/lib/supabase";
import {
  authEmailRejectReason,
  normalizeAuthEmail,
  otpNoAccountMessage,
} from "@/lib/authEmail";
import { getApiBase } from "@/lib/apiBase";
import {
  readNextParam,
  peekPendingNext,
  postAuthRedirectTarget,
  storePendingNext,
  readPlanParam,
  storeCheckoutIntent,
  resolvePostAuthPath,
  navigateAfterAuth,
} from "@/lib/authNext";
import { markJobsWorkspaceRestoreIfHome } from "@/lib/jobsWorkflow";

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle"
  );
  const [errMsg, setErrMsg] = useState("");
  const [linkFailed, setLinkFailed] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [resendBusy, setResendBusy] = useState(false);

  const redirectTarget = () => postAuthRedirectTarget("/");

  useEffect(() => {
    const plan = readPlanParam();
    if (plan) storeCheckoutIntent(plan);
    const next = readNextParam();
    if (next) storePendingNext(next);
  }, []);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = window.setTimeout(
      () => setCooldown(n => Math.max(0, n - 1)),
      1000
    );
    return () => window.clearTimeout(t);
  }, [cooldown]);

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;

    const params = new URLSearchParams(window.location.search);
    const authError = params.get("auth_error");

    const handleAuthErrorIfNeeded = async () => {
      if (!authError) return;
      const { data } = await client.auth.getSession();
      if (data?.session) {
        const dest = resolvePostAuthPath("/");
        if (readNextParam() || peekPendingNext())
          markJobsWorkspaceRestoreIfHome(dest);
        navigateAfterAuth(dest);
        return;
      }
      setLinkFailed(true);
      setStatus("error");
      setErrMsg(decodeURIComponent(authError.replace(/\+/g, " ")));
      params.delete("auth_error");
      const next = params.toString();
      window.history.replaceState(null, "", next ? `/login?${next}` : "/login");
    };

    void handleAuthErrorIfNeeded();

    async function afterLogin() {
      const { data } = await client.auth.getSession();
      const session = data?.session;
      if (!session) return;
      const hasExplicitReturn = Boolean(readNextParam() || peekPendingNext());
      const dest = resolvePostAuthPath("/");
      if (hasExplicitReturn) markJobsWorkspaceRestoreIfHome(dest);
      try {
        const res = await fetch(`${getApiBase()}/api/user/auth-debug`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) {
          const j = await res.json();
          if (j?.is_admin && !hasExplicitReturn) {
            setLocation("/admin");
            return;
          }
        }
      } catch {
        /* ignore */
      }
      navigateAfterAuth(dest);
    }

    void afterLogin();
    const { data: sub } = client.auth.onAuthStateChange((_e, session) => {
      if (session) void afterLogin();
    });
    return () => sub.subscription.unsubscribe();
  }, [setLocation]);

  async function oauth(provider: "google" | "github") {
    if (!supabase) {
      setStatus("error");
      setErrMsg(AUTH_UNAVAILABLE_MSG);
      return;
    }
    setErrMsg("");
    setStatus("idle");
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: supabaseOAuthRedirect(redirectTarget()) },
    });
    if (error) {
      setStatus("error");
      setErrMsg(error.message);
    }
  }

  async function magicLink(e: React.FormEvent) {
    e.preventDefault();
    if (!supabase) {
      setStatus("error");
      setErrMsg(AUTH_UNAVAILABLE_MSG);
      return;
    }
    const reason = authEmailRejectReason(email);
    if (reason) {
      setStatus("error");
      setErrMsg(reason);
      return;
    }
    if (cooldown > 0) {
      setStatus("error");
      setErrMsg(`Wait ${cooldown}s before requesting another sign-in email.`);
      return;
    }
    const normalized = normalizeAuthEmail(email);
    if (!normalized) return;
    setStatus("sending");
    setErrMsg("");
    const redirectTo = supabaseOAuthRedirect(redirectTarget());
    const { error } = await supabase.auth.signInWithOtp({
      email: normalized,
      options: {
        emailRedirectTo: redirectTo,
        // Do not mint a new Auth user (and bounce a letter) from a login typo.
        shouldCreateUser: false,
      },
    });
    if (error) {
      setStatus("error");
      setErrMsg(otpNoAccountMessage(error.message));
    } else {
      setStatus("sent");
      setCooldown(60);
    }
  }

  async function resendMagicLink() {
    if (!supabase || cooldown > 0 || resendBusy) return;
    const normalized = normalizeAuthEmail(email);
    if (!normalized) return;
    setResendBusy(true);
    const { error } = await supabase.auth.signInWithOtp({
      email: normalized,
      options: {
        emailRedirectTo: supabaseOAuthRedirect(redirectTarget()),
        shouldCreateUser: false,
      },
    });
    setResendBusy(false);
    if (error) {
      setStatus("error");
      setErrMsg(otpNoAccountMessage(error.message));
      return;
    }
    setCooldown(60);
  }

  const loginSearch =
    typeof window !== "undefined" ? window.location.search : "";
  const signupHref = `/signup${loginSearch}`;

  if (status === "sent") {
    return (
      <div className="rfr-editorial rfr-account">
        <SiteHeader />
        <main>
          <section className="rfr-account-callback">
            <div className="rfr-account-kicker">CHECK YOUR INBOX</div>
            <h1>We sent you a sign-in link.</h1>
            <p className="rfr-account-lede">
              It went to <strong>{email}</strong>. Open it on this device to sign in. The link works for one hour.
            </p>
            <div className="rfr-account-actions">
              <button
                type="button"
                className="rfr-account-secondary"
                onClick={() => void resendMagicLink()}
                disabled={cooldown > 0 || resendBusy}
              >
                {cooldown > 0 ? `Resend the link in ${cooldown}s` : "Resend the link"}
              </button>
              <button
                type="button"
                className="rfr-account-textbtn"
                onClick={() => {
                  setStatus("idle");
                  setErrMsg("");
                }}
              >
                Use a different email
              </button>
            </div>
            <p className="rfr-account-fine">
              Nothing after a few minutes? Check spam, or continue with Google or GitHub instead.
            </p>
          </section>
        </main>
        <SiteFooter />
      </div>
    );
  }

  if (linkFailed) {
    return (
      <div className="rfr-editorial rfr-account">
        <SiteHeader />
        <main>
          <section className="rfr-account-callback">
            <div className="rfr-account-kicker">SIGN-IN DIDN'T FINISH</div>
            <h1>That didn't work.</h1>
            <p className="rfr-account-lede">
              The email link expired or was already used, or the Google/GitHub sign-in was cancelled. Try again and we'll take you to the same page.
            </p>
            <button
              type="button"
              className="rfr-account-submit"
              style={{ width: "auto", padding: "0 18px" }}
              onClick={() => {
                setLinkFailed(false);
                setStatus("idle");
                setErrMsg("");
              }}
            >
              Back to sign in
            </button>
          </section>
        </main>
        <SiteFooter />
      </div>
    );
  }

  return (
    <div className="rfr-editorial rfr-account">
      <SiteHeader />
      <main>
        <section className="rfr-account-split">
          <div className="rfr-account-copy">
            <div className="rfr-account-kicker">SIGN IN</div>
            <h1>Sign in to your desk.</h1>
            <p className="rfr-account-lede">
              Your saved buyers, alerts and robots are where you left them.
            </p>
            <div className="rfr-account-gets">
              <div className="rfr-account-get">
                <span className="rfr-account-num">01</span>
                <b>Every buyer for your robot, ranked</b>
                <span>
                  Company, the workflow, why now, and the source. Budget confirmed first.
                </span>
              </div>
              <div className="rfr-account-get">
                <span className="rfr-account-num">02</span>
                <b>Alerts when a new buyer appears</b>
                <span>
                  A new RFP or robotics hire that fits one of your robots lands in your inbox the day we find it.
                </span>
              </div>
              <div className="rfr-account-get">
                <span className="rfr-account-num">03</span>
                <b>A desk to work the list</b>
                <span>
                  Save buyers, move them from new to contacted to won, and keep notes in one place.
                </span>
              </div>
            </div>
          </div>
          <div className="rfr-account-card">
            <h2 className="rfr-account-panel-title">Sign in</h2>
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
            <button
              type="button"
              className="rfr-account-submit"
              onClick={() => void oauth("google")}
              disabled={!supabase}
            >
              Continue with Google
            </button>
            <button
              type="button"
              className="rfr-account-submit"
              onClick={() => void oauth("github")}
              disabled={!supabase}
            >
              Continue with GitHub
            </button>
            <p className="rfr-account-or">OR USE YOUR EMAIL</p>
            <form onSubmit={e => void magicLink(e)}>
              <label>
                <span className="rfr-account-label">WORK EMAIL</span>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  inputMode="email"
                  spellCheck={false}
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  disabled={status === "sending"}
                  className={status === "error" ? "is-error" : undefined}
                />
              </label>
              <button
                type="submit"
                className="rfr-account-secondary"
                disabled={status === "sending" || !email.trim() || !supabase}
              >
                {status === "sending" ? "Sending…" : "Email me a sign-in link"}
              </button>
            </form>
            <p className="rfr-account-fine">Google, GitHub, or a link sent to your email.</p>
            <p className="rfr-account-fine rfr-account-switch">
              New here? <Link href={signupHref}>Create an account</Link>
            </p>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
