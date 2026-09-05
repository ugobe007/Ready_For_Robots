import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import About from "@/pages/About";
import Dashboard from "@/pages/Dashboard";
import MarketsRoute from "@/pages/MarketsRoute";
import Pipeline from "@/pages/Pipeline";
import NotFound from "@/pages/NotFound";
import RoiCalculator from "@/pages/RoiCalculator";
import SignalsRoute from "@/pages/SignalsRoute";
import {
  AnalyticsPage,
  BriefPage,
  CrmPage,
  LoginPage,
  MarketInsightsPage,
  NewsletterPage,
  PilotCalculatorPage,
  PipelineHealthPage,
  PipelineResultsPage,
  ProfilePage,
  RobotCompaniesPage,
  RobotReadyPage,
  SocialPage,
} from "@/pages/MarketingShellPages";
import AdminHubPage from "@/pages/AdminHubPage";
import PartnersTheRobotGuildPage from "@/pages/admin/PartnersTheRobotGuildPage";
import { Route, Switch, useLocation } from "wouter";
import { useEffect } from "react";
import ErrorBoundary from "./components/ErrorBoundary";
import Home from "./pages/Home";
import MarketingHomePage from "./pages/MarketingHomePage";
import { ThemeProvider } from "./contexts/ThemeContext";

/** Legacy `/search` — same product surface as Dashboard (industry-led browse). */
function SearchRedirectRoute() {
  const [, navigate] = useLocation();
  useEffect(() => {
    const qs = typeof window !== "undefined" ? window.location.search : "";
    navigate(`/dashboard${qs}`, { replace: true });
  }, [navigate]);
  return (
    <div className="container py-16 text-center text-sm text-gray-600" aria-live="polite">
      Redirecting to dashboard…
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/welcome" component={MarketingHomePage} />
      <Route path="/about" component={About} />
      <Route path="/dashboard" component={Dashboard} />
      <Route path="/pipeline" component={Pipeline} />
      <Route path="/search" component={SearchRedirectRoute} />
      <Route path="/signals" component={SignalsRoute} />
      <Route path="/markets" component={MarketsRoute} />
      <Route path="/roi-calculator" component={RoiCalculator} />
      <Route path="/pipeline-results" component={PipelineResultsPage} />
      <Route path="/pipeline-health" component={PipelineHealthPage} />
      <Route path="/crm" component={CrmPage} />
      <Route path="/analytics" component={AnalyticsPage} />
      <Route path="/market-insights" component={MarketInsightsPage} />
      <Route path="/pilot-calculator" component={PilotCalculatorPage} />
      <Route path="/newsletter" component={NewsletterPage} />
      <Route path="/login" component={LoginPage} />
      <Route path="/profile" component={ProfilePage} />
      <Route path="/robot-companies" component={RobotCompaniesPage} />
      <Route path="/robot-ready" component={RobotReadyPage} />
      <Route path="/brief" component={BriefPage} />
      <Route path="/social" component={SocialPage} />
      <Route path="/admin" component={AdminHubPage} />
      <Route path="/admin/partners/the-robot-guild" component={PartnersTheRobotGuildPage} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
