/**
 * Sign in — Supabase magic link + OAuth (dark workflow theme).
 */
import { useEffect, useState } from "react";
import { Github } from "lucide-react";
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

function MicrosoftGlyph() {
  return (
    <span
      className="inline-flex h-5 w-5 items-center justify-center"
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" focusable="false">
        <rect x="2" y="2" width="9" height="9" fill="#f35325" />
        <rect x="13" y="2" width="9" height="9" fill="#81bc06" />
        <rect x="2" y="13" width="9" height="9" fill="#05a6f0" />
        <rect x="13" y="13" width="9" height="9" fill="#ffba08" />
      </svg>
    </span>
  );
}

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle"
  );
  const [errMsg, setErrMsg] = useState("");
  const [cooldown, setCooldown] = useState(0);

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

  async function oauth(provider: "google" | "github" | "azure") {
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
      setErrMsg(
        provider === "azure" && /provider is not enabled/i.test(error.message)
          ? "Microsoft sign-in is not enabled yet in Supabase Auth (Azure provider). Use Google or a magic link, or enable Azure in the Supabase dashboard."
          : error.message
      );
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

  const loginSearch =
    typeof window !== "undefined" ? window.location.search : "";
  const signupHref = `/signup${loginSearch}`;

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
            <div className="rfr-account-tabs">
              <Link href={signupHref} className="is-off">
                Create account
              </Link>
              <span className="is-on">Sign in</span>
            </div>
            {status === "sent" ? (
              <>
                <h2>Check your email</h2>
                <p className="rfr-account-lede">
                  We sent a sign-in link to <b>{email}</b>.
                </p>
                <button
                  type="button"
                  className="rfr-account-fine"
                  onClick={() => setStatus("idle")}
                >
                  Back to sign-in options
                </button>
              </>
            ) : (
              <>
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
                    className="rfr-account-submit"
                    disabled={status === "sending" || !email.trim() || !supabase}
                  >
                    {status === "sending" ? "Sending…" : "Sign in"}
                  </button>
                </form>
                <p className="rfr-account-fine">
                  New here? <Link href={signupHref}>Create an account</Link>. It takes under a minute.
                </p>
                <button
                  type="button"
                  className="rfr-account-secondary"
                  onClick={() => void oauth("google")}
                  disabled={!supabase}
                >
                  <GoogleGlyph />
                  Continue with Google
                </button>
                <button
                  type="button"
                  className="rfr-account-secondary"
                  onClick={() => void oauth("azure")}
                  disabled={!supabase}
                >
                  <MicrosoftGlyph />
                  Continue with Microsoft 365
                </button>
                <button
                  type="button"
                  className="rfr-account-secondary"
                  onClick={() => void oauth("github")}
                  disabled={!supabase}
                >
                  <Github className="h-4 w-4" aria-hidden="true" />
                  Continue with GitHub
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
