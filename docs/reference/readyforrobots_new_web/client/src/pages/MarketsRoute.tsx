import MarketsSection from "@/components/MarketsSection";
import SiteShell from "@/components/SiteShell";
import { useAnimateFadeUp } from "@/hooks/useAnimateFadeUp";

export default function MarketsRoute() {
  useAnimateFadeUp();

  return (
    <SiteShell>
      <div className="container py-8 md:py-10 space-y-6">
        <div>
          <h1
            className="text-3xl md:text-4xl font-extrabold text-gray-900 tracking-tight"
            style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
          >
            Markets
          </h1>
          <p className="text-gray-600 mt-1 max-w-2xl text-sm">
            Verticals where automation and robotics land fastest — same coverage story as the home page, on its own
            URL for navigation and deep links.
          </p>
        </div>
        <MarketsSection />
      </div>
    </SiteShell>
  );
}
