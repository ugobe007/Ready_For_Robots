import { useState, FormEvent } from "react";
import { X, Sparkles, CheckCircle2, Mail, Lock, Github } from "lucide-react";
import { supabase, supabaseOAuthRedirect, AUTH_UNAVAILABLE_MSG } from "@/lib/supabase";
import { toast } from "sonner";

function GoogleGlyph() {
  return (
    <svg className="w-4 h-4" viewBox="0 0 24 24">
      <path
        fill="#EA4335"
        d="M12 10.2v3.9h5.5c-.2 1.2-1.4 3.5-5.5 3.5-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.9 1.5l2.7-2.6C16.9 2.9 14.6 2 12 2 6.8 2 2.6 6.2 2.6 11.4S6.8 20.8 12 20.8c6.9 0 9.1-4.8 9.1-7.3 0-.5-.1-.9-.1-1.3H12Z"
      />
      <path
        fill="#34A853"
        d="M12 20.8c3.2 0 6-1.1 8-3l-3-2.5c-1.1.8-2.5 1.3-5 1.3-3.1 0-5.8-2.1-6.7-5H2.2v2.6C4.2 18.2 7.8 20.8 12 20.8Z"
      />
      <path
        fill="#4A90E2"
        d="M5.3 11.6c-.2-.7-.3-1.4-.3-2.2s.1-1.5.3-2.2V4.6H2.2C1.4 6.2 1 8 1 9.4s.4 3.2 1.2 4.8l3.1-2.6Z"
      />
      <path
        fill="#FBBC05"
        d="M12 4.8c1.7 0 3.2.6 4.4 1.7l3.3-3.3C17.7 1.4 15.1.4 12 .4 7.8.4 4.2 3 2.2 6.8l3.1 2.6c.9-2.9 3.6-4.6 6.7-4.6Z"
      />
    </svg>
  );
}

type QuickSignupModalProps = {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  source?: string;
};

export default function QuickSignupModal({
  isOpen,
  onClose,
  title = "Unlock Full Engineering Feasibility & Cal Proposals",
  subtitle = "Create your free ReadyForRobots workspace in 10 seconds to save matches, view buyer signals, and generate turnkey commercial quotes.",
  source = "modal_prompt",
}: QuickSignupModalProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<"google" | "github" | null>(null);

  if (!isOpen) return null;

  const handleOAuth = async (provider: "google" | "github") => {
    if (!supabase) {
      toast.error(AUTH_UNAVAILABLE_MSG);
      return;
    }
    setOauthLoading(provider);
    try {
      const redirectTo = supabaseOAuthRedirect(window.location.pathname);
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: { redirectTo },
      });
      if (error) {
        toast.error(`OAuth error: ${error.message}`);
        setOauthLoading(null);
      }
    } catch (e) {
      toast.error("Could not initiate social login.");
      setOauthLoading(null);
    }
  };

  const handleEmailSignup = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      toast.error("Please enter your email and password.");
      return;
    }
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters.");
      return;
    }
    if (!supabase) {
      toast.error(AUTH_UNAVAILABLE_MSG);
      return;
    }

    setIsSubmitting(true);
    try {
      const { error } = await supabase.auth.signUp({
        email: email.trim(),
        password: password,
        options: {
          data: {
            full_name: fullName.trim() || undefined,
            signup_source: source,
          },
        },
      });

      if (error) {
        toast.error(error.message);
        setIsSubmitting(false);
        return;
      }

      toast.success("🎉 Account created successfully! Welcome to ReadyForRobots.");
      setIsSubmitting(false);
      onClose();
      window.location.reload();
    } catch (err) {
      toast.error("Failed to create account. Please try again.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="fixed inset-0" onClick={onClose} />

      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl p-6 sm:p-8 z-10 font-sans text-slate-100 overflow-hidden">
        {/* Decorative blur background */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="space-y-2 text-left relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" /> Free Instant Workspace
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight leading-snug">
            {title}
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            {subtitle}
          </p>
        </div>

        {/* Value Bullets */}
        <div className="mt-5 p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs relative z-10">
          <div className="flex items-center gap-2 text-slate-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span><strong>Verified Enterprise Buyer Signals</strong> ($100M+ revenue)</span>
          </div>
          <div className="flex items-center gap-2 text-slate-200">
            <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span><strong>1-Click Cal AI Commercial Quotes</strong> & RaaS calculations</span>
          </div>
          <div className="flex items-center gap-2 text-slate-200">
            <CheckCircle2 className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span><strong>3D Cell Layout Video Simulations</strong> & HEIR Feasibility</span>
          </div>
        </div>

        {/* 1-Click Social OAuth Buttons */}
        <div className="mt-6 space-y-3 relative z-10">
          <button
            type="button"
            onClick={() => handleOAuth("google")}
            disabled={Boolean(oauthLoading)}
            className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-100 font-semibold text-xs tracking-wide transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer"
          >
            <GoogleGlyph />
            <span>{oauthLoading === "google" ? "Connecting to Google..." : "Continue with Google"}</span>
          </button>

          <button
            type="button"
            onClick={() => handleOAuth("github")}
            disabled={Boolean(oauthLoading)}
            className="w-full py-2.5 px-4 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-200 font-semibold text-xs tracking-wide transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Github className="w-4 h-4 text-slate-300" />
            <span>{oauthLoading === "github" ? "Connecting..." : "Continue with GitHub"}</span>
          </button>
        </div>

        {/* Divider */}
        <div className="relative my-5 text-center text-xs text-slate-500">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-800"></div></div>
          <span className="relative bg-slate-900 px-3 text-[11px] uppercase tracking-wider font-mono text-slate-400">or sign up with email</span>
        </div>

        {/* Form */}
        <form onSubmit={handleEmailSignup} className="space-y-3 relative z-10">
          <div>
            <label className="text-[11px] font-mono text-slate-400 block mb-1">Work Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="email"
                required
                placeholder="you@company.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-sans"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-mono text-slate-400 block mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                required
                minLength={6}
                placeholder="At least 6 characters"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-sans"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 py-3 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-extrabold text-xs tracking-wide uppercase transition-all shadow-lg shadow-emerald-400/20 flex items-center justify-center gap-2 cursor-pointer"
          >
            {isSubmitting ? "Creating Account..." : "Create Free Workspace Account →"}
          </button>
        </form>

        <p className="mt-4 text-[11px] text-slate-400 text-center">
          Already have an account?{" "}
          <a href="/login" className="text-emerald-400 font-bold hover:underline">
            Sign In
          </a>
        </p>
      </div>
    </div>
  );
}
