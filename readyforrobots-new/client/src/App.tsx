import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import Results from "./pages/Results";
import Pipeline from "./pages/Pipeline";
import Signals from "./pages/Signals";
import HowItWorks from "./pages/HowItWorks";
import Intelligence from "./pages/Intelligence";
import Newsletter from "./pages/Newsletter";
import Pricing from "./pages/Pricing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
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
import FindRobots from "./pages/FindRobots";
import Admin from "./pages/Admin";
import Social from "./pages/Social";
import { AuthProvider } from "./contexts/AuthContext";
import { ScoutChat } from "./components/ScoutChat";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/results" component={Results} />
      <Route path="/pipeline" component={Pipeline} />
      <Route path="/signals" component={Signals} />
      <Route path="/intelligence" component={Intelligence} />
      <Route path="/newsletter" component={Newsletter} />
      <Route path="/how-it-works" component={HowItWorks} />
      <Route path="/benchmark" component={Benchmark} />
      <Route path="/robots" component={Robots} />
      <Route path="/find-robots" component={FindRobots} />
      <Route path="/pricing" component={Pricing} />
      <Route path="/social" component={Social} />
      <Route path="/login" component={Login} />
      <Route path="/signup" component={Signup} />
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
      <Route path="/admin/prospects" component={Pipeline} />
      <Route path="/admin" component={Admin} />
      <Route path="/readyforrobots/admin/prospects" component={Pipeline} />
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
      <ThemeProvider defaultTheme="dark">
        <AuthProvider>
          <ScoutChat>
            <TooltipProvider>
              <Toaster />
              <Router />
            </TooltipProvider>
          </ScoutChat>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
