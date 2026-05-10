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
import Pricing from './pages/Pricing';
import FAQ from './pages/FAQ';
import ScoutSettings from './pages/ScoutSettings';
import About from './pages/About';
import CaseStudies from './pages/CaseStudies';
import { ScoutChat } from "./components/ScoutChat";
function Router() {
  // make sure to consider if you need authentication for certain routes
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/results" component={Results} />
      <Route path="/pipeline" component={Pipeline} />
      <Route path="/signals" component={Signals} />
      <Route path="/how-it-works" component={HowItWorks} />
      <Route path="/pricing" component={Pricing} />
      <Route path="/faq" component={FAQ} />
      <Route path="/scout-settings" component={ScoutSettings} />
      <Route path="/about" component={About} />
      <Route path="/case-studies" component={CaseStudies} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <ScoutChat>
            <Toaster />
            <Router />
          </ScoutChat>
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
