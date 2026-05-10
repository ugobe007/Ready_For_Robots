import SignalsSection from "@/components/SignalsSection";
import SiteShell from "@/components/SiteShell";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnimateFadeUp } from "@/hooks/useAnimateFadeUp";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { useEffect, useState } from "react";

type Summary = { total?: number; hot?: number; warm?: number; cold?: number };

export default function SignalsRoute() {
  const [summary, setSummary] = useState<Summary | null>(null);
  useAnimateFadeUp();

  useEffect(() => {
    const API = getApiBase();
    (async () => {
      try {
        const r = await fetch(`${API}/api/leads/summary?exclude_junk=true`, liveFetchInit());
        if (r.ok) setSummary(await r.json());
      } catch {
        setSummary(null);
      }
    })();
  }, []);

  return (
    <SiteShell>
      <div className="container py-8 md:py-10 space-y-8">
        <div>
          <h1
            className="text-3xl md:text-4xl font-extrabold text-gray-900 tracking-tight"
            style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
          >
            Signals
          </h1>
          <p className="text-gray-600 mt-1 max-w-2xl text-sm">
            Buying-intent signal types (funding, expansion, labor pain, hires, news, and more) scored into HOT / WARM /
            Emerging tiers — same scoring model as the rest of the product.
          </p>
        </div>

        {summary ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ["Total (capped view)", summary.total],
              ["HOT", summary.hot],
              ["WARM", summary.warm],
              ["Emerging", summary.cold],
            ].map(([label, val]) => (
              <Card key={String(label)} className="border-gray-100 shadow-sm">
                <CardHeader className="py-4">
                  <CardDescription className="text-xs font-semibold uppercase">{label}</CardDescription>
                  <CardTitle className="text-2xl font-mono tabular-nums">{val ?? "—"}</CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>
        ) : null}

        <SignalsSection />
      </div>
    </SiteShell>
  );
}
