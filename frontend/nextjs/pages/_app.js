import '../styles/globals.css';
import Head from 'next/head';
import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

// ── Auth Context ─────────────────────────────────────────────────────────────
export const AuthContext = createContext({ session: null, loading: true });
export const useAuth = () => useContext(AuthContext);

function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </Head>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

