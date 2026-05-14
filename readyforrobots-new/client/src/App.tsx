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
import SupplyPipeline from "./pages/SupplyPipeline";
import Marketplace from "./pages/Marketplace";
import Admin from "./pages/Admin";
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
      <Route path="/pricing" component={Pricing} />
      <Route path="/login" component={Login} />
      <Route path="/signup" component={Signup} />
      <Route path="/profile" component={Profile} />
      <Route path="/crm" component={Crm} />
      <Route path="/supply-pipeline" component={SupplyPipeline} />
      <Route path="/marketplace" component={Marketplace} />
      <Route path="/admin" component={Admin} />
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
