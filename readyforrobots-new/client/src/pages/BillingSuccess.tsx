import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { CheckCircle2, Loader2 } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { useAuth } from "@/contexts/AuthContext";
import { syncCheckoutSession } from "@/lib/billing";
import { supabase } from "@/lib/supabase";

export default function BillingSuccess() {
  const { session, loading } = useAuth();
  const [, setLocation] = useLocation();
  const [status, setStatus] = useState<"working" | "done" | "error">("working");
  const [message, setMessage] = useState("Confirming your subscription…");

  useEffect(() => {
    if (loading) return;
    if (!session?.access_token) {
      setLocation("/login?next=/billing/success");
      return;
    }

    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (!sessionId) {
      setStatus("error");
      setMessage("Missing checkout session. If you were charged, contact support.");
      return;
    }

    void (async () => {
      try {
        await syncCheckoutSession(session.access_token, sessionId);
        if (supabase) {
          await supabase.auth.refreshSession();
        }
        setStatus("done");
        setMessage("You're on Pro — full pipeline and SIGNAL research are unlocked.");
        window.setTimeout(() => setLocation("/pipeline"), 2500);
      } catch (err) {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Could not confirm subscription");
      }
    })();
  }, [loading, session, setLocation]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="max-w-md w-full rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
          {status === "working" ? (
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-emerald-600 mb-4" />
          ) : status === "done" ? (
            <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600 mb-4" />
          ) : null}
          <h1 className="font-display font-extrabold text-gray-900 text-xl mb-2">
            {status === "done" ? "Subscription active" : status === "error" ? "Almost there" : "Processing payment"}
          </h1>
          <p className="text-sm text-gray-600 leading-relaxed mb-6">{message}</p>
          {status === "done" ? (
            <Link href="/pipeline" className="text-sm font-semibold text-emerald-700 hover:underline">
              Go to pipeline →
            </Link>
          ) : status === "error" ? (
            <Link href="/pricing" className="text-sm font-semibold text-emerald-700 hover:underline">
              Back to pricing
            </Link>
          ) : null}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
