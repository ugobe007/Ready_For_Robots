import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { clearPendingNext, peekPendingNext, readNextParam } from "@/lib/authNext";

type AuthCtx = { session: Session | null; loading: boolean };

const AuthContext = createContext<AuthCtx>({ session: null, loading: true });

const NEUTRAL_AFTER_AUTH = new Set(["/", "/login", "/signup", "/auth/callback"]);

function maybeResumeIntentAfterSignIn(session: Session | null): void {
  if (!session || typeof window === "undefined") return;
  const path = window.location.pathname;
  if (!NEUTRAL_AFTER_AUTH.has(path)) return;
  const fromUrl = readNextParam();
  const pending = peekPendingNext();
  if (!fromUrl && !pending) return;
  const dest = fromUrl ?? pending;
  if (!dest || dest === "/" || dest === path) return;
  clearPendingNext();
  window.location.replace(dest);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data?.session ?? null);
      setLoading(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((event, s) => {
      setSession(s);
      setLoading(false);
      if (event === "SIGNED_IN" || event === "INITIAL_SESSION") {
        maybeResumeIntentAfterSignIn(s);
      }
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  return <AuthContext.Provider value={{ session, loading }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthCtx {
  return useContext(AuthContext);
}
