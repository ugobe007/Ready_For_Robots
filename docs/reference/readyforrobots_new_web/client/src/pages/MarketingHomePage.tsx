/**
 * Legacy marketing landing — hero, stats, pipeline sections.
 * Primary product home is `pages/Home.tsx` at `/`.
 */

import { useAnimateFadeUp } from "@/hooks/useAnimateFadeUp";
import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import StatsBar from "@/components/StatsBar";
import MarketsSection from "@/components/MarketsSection";
import PipelineDealsSection from "@/components/PipelineDealsSection";
import SignalsSection from "@/components/SignalsSection";
import HowItWorksSection from "@/components/HowItWorksSection";
import SuccessStoriesSection from "@/components/SuccessStoriesSection";
import CtaSection from "@/components/CtaSection";
import Footer from "@/components/Footer";

export default function MarketingHomePage() {
  useAnimateFadeUp();

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <HeroSection />
      <StatsBar />
      <PipelineDealsSection />
      <MarketsSection />
      <SignalsSection />
      <HowItWorksSection />
      <SuccessStoriesSection />
      <CtaSection />
      <Footer />
    </div>
  );
}
