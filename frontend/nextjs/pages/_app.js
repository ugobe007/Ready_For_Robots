import '../styles/globals.css';
import Head from 'next/head';
import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';
import { getApiBase } from '../lib/apiBase';

// ── Auth Context ─────────────────────────────────────────────────────────────
export const AuthContext = createContext({ session: null, loading: true });
export const useAuth = () => useContext(AuthContext);

function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If Supabase is not configured, skip auth setup
    if (!supabase) {
      setLoading(false);
      return;
    }

    // Initial session fetch
    supabase.auth.getSession().then(({ data }) => {
      setSession(data?.session ?? null);
      setLoading(false);
    });

    // Listen for auth changes (sign-in, sign-out, token refresh)
    const { data: listener } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
      setLoading(false);
    });

    return () => listener?.subscription?.unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ session, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

function VisitTracker({ children }) {
  const router = useRouter();

  useEffect(() => {
    const track = (path) => {
      fetch(`${getApiBase()}/api/track/visit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: path || '/',
          referrer: typeof document !== 'undefined' ? document.referrer || null : null,
        }),
      }).catch(() => {});
    };

    track(router.pathname);
    router.events?.on('routeChangeComplete', track);
    return () => router.events?.off('routeChangeComplete', track);
  }, [router]);

  return children;
}

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <VisitTracker>
      <Head>
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </Head>
      <Component {...pageProps} />
      </VisitTracker>
    </AuthProvider>
  );
}

