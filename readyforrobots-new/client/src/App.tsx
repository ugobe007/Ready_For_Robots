import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Redirect, Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import Results from "./pages/Results";
import RobotAnalysisReview from "./pages/RobotAnalysisReview";
import RobotDetailReview from "./pages/RobotDetailReview";
import SalesSamples from "./pages/SalesSamples";
import Pipeline from "./pages/Pipeline";
import Compare from "./pages/Compare";
import Signals from "./pages/Signals";
import Intelligence from "./pages/Intelligence";
import Newsletter from "./pages/Newsletter";
import BillingSuccess from "./pages/BillingSuccess";
import Pricing from "./pages/Pricing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import AuthCallback from "./pages/AuthCallback";
import Profile from "./pages/Profile";
import Crm from "./pages/Crm";
import Inbox from "./pages/Inbox";
import CalendarPage from "./pages/Calendar";
import SalesConsole from "./pages/SalesConsole";
import SalesWorkflow from "./pages/SalesWorkflow";
import SupplyPipeline from "./pages/SupplyPipeline";
import Marketplace from "./pages/Marketplace";
import Integrations from "./pages/Integrations";
import HubSpotConnect from "./pages/HubSpotConnect";
import Benchmark from "./pages/Benchmark";
import Robots from "./pages/Robots";
import HumanoidComparisonReport from "./pages/HumanoidComparisonReport";
import FindRobots from "./pages/FindRobots";
import Admin from "./pages/Admin";
import SpecialProjectsAdmin from "./pages/SpecialProjectsAdmin";
import ProjectPortal from "./pages/ProjectPortal";
import Social from "./pages/Social";
import Jobs from "./pages/Jobs";
import ExperimentRedirect from "./pages/ExperimentRedirect";
import Preview from "./pages/Preview";
import Privacy from "./pages/Privacy";
import VendorDesignBuilder from "./pages/VendorDesignBuilder";
import DesignShare from "./pages/DesignShare";
import IconReview from "./pages/IconReview";
import { AuthProvider } from "./contexts/AuthContext";
import PostAuthRedirect from "./components/PostAuthRedirect";
import { ScoutChat } from "./components/ScoutChat";
import VisitTracker from "./components/VisitTracker";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/robots/analysis/:analysisId" component={RobotAnalysisReview} />
      <Route path="/robots/:robotId/review" component={RobotDetailReview} />
      <Route path="/journey/url" component={Home} />
      <Route path="/journey/identity" component={Home} />
      <Route path="/journey/preview" component={Home} />
      <Route path="/journey/activate" component={Home} />
      <Route path="/results" component={Results} />
      <Route path="/sales/samples" component={SalesSamples} />
      <Route path="/pipeline" component={Pipeline} />
      <Route path="/compare" component={Compare} />
      <Route path="/signals" component={Signals} />
      <Route path="/intelligence" component={Intelligence} />
      <Route path="/newsletter" component={Newsletter} />
      <Route path="/how-it-works">
        <Redirect to="/intelligence" />
      </Route>
      <Route path="/preview" component={Preview} />
      <Route path="/privacy" component={Privacy} />
      <Route path="/vendor/design" component={VendorDesignBuilder} />
      <Route path="/design/:shareId" component={DesignShare} />
      <Route path="/benchmark" component={Benchmark} />
      <Route path="/robots/report" component={HumanoidComparisonReport} />
      <Route path="/robots" component={Robots} />
      <Route path="/find-robots" component={FindRobots} />
      <Route path="/pricing" component={Pricing} />
      <Route path="/billing/success" component={BillingSuccess} />
      <Route path="/social" component={Social} />
      <Route path="/jobs/:slug" component={Jobs} />
      <Route path="/jobs" component={Jobs} />
      <Route path="/experiment" component={ExperimentRedirect} />
      <Route path="/icon-review" component={IconReview} />
      <Route path="/login" component={Login} />
      <Route path="/signup" component={Signup} />
      <Route path="/auth/callback" component={AuthCallback} />
      <Route path="/profile" component={Profile} />
      <Route path="/crm" component={Crm} />
      <Route path="/inbox" component={Inbox} />
      <Route path="/calendar" component={CalendarPage} />
      <Route path="/sales-console" component={SalesConsole} />
      <Route path="/sales-workflow" component={SalesWorkflow} />
      <Route path="/supply-pipeline" component={SupplyPipeline} />
      <Route path="/marketplace" component={Marketplace} />
      <Route path="/integrations" component={Integrations} />
      <Route path="/integrations/hubspot" component={HubSpotConnect} />
      <Route path="/admin/prospects">
        <Redirect to="/pipeline" />
      </Route>
      <Route path="/admin/special-projects" component={SpecialProjectsAdmin} />
      <Route path="/admin/sales-samples">
        <Redirect to="/sales/samples" />
      </Route>
      <Route path="/admin" component={Admin} />
      <Route path="/p/:token" component={ProjectPortal} />
      <Route path="/readyforrobots/admin/prospects">
        <Redirect to="/pipeline" />
      </Route>
      <Route path="/readyforrobots/admin/special-projects" component={SpecialProjectsAdmin} />
      <Route path="/readyforrobots/admin" component={Admin} />
      <Route path="/readyforrobots/crm" component={Crm} />
      <Route path="/readyforrobots/inbox" component={Inbox} />
      <Route path="/readyforrobots/calendar" component={CalendarPage} />
      <Route path="/readyforrobots/sales-console" component={SalesConsole} />
      <Route path="/readyforrobots/sales-workflow" component={SalesWorkflow} />
      <Route path="/readyforrobots/supply-pipeline" component={SupplyPipeline} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <AuthProvider>
          <PostAuthRedirect />
          <ScoutChat>
            <VisitTracker>
            <TooltipProvider>
              <Toaster />
              <Router />
            </TooltipProvider>
            </VisitTracker>
          </ScoutChat>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
