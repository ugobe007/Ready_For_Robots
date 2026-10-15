import type { ComponentType, ReactNode } from "react";
import { Redirect } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref } from "@/lib/authNext";

/** Workspace and internal pages: no public access, sign in and come back. */
export default function RequireSignIn({ children }: { children: ReactNode }) {
  const { session, loading } = useAuth();
  if (loading) return null;
  if (!session) return <Redirect to={loginHref()} />;
  return <>{children}</>;
}

export function signedIn(Page: ComponentType) {
  return function SignedInPage() {
    return (
      <RequireSignIn>
        <Page />
      </RequireSignIn>
    );
  };
}
