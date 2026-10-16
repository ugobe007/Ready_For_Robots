/**
 * /social stays unlinked from the public nav and renders only for admins.
 */
import { Redirect } from "wouter";
import { useAdminAccess } from "@/hooks/useIsAdmin";
import Social from "./Social";

export default function SocialRoute() {
  const access = useAdminAccess();
  if (access === "loading") return null;
  if (access === "admin") return <Social />;
  if (access === "signin") return <Redirect to="/login?next=/social" />;
  return <Redirect to="/" />;
}
