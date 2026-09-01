import { useEffect } from "react";
import { useLocation } from "wouter";
import { trackSiteVisit } from "@/lib/siteAnalytics";

export default function VisitTracker({
  children,
}: {
  children: React.ReactNode;
}) {
  const [location] = useLocation();

  useEffect(() => {
    trackSiteVisit(location || "/");
  }, [location]);

  return <>{children}</>;
}
