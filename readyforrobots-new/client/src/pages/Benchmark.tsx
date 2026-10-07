import { useState } from "react";
import { Link } from "wouter";
import {
  ArrowRight,
  ShieldCheck,
  Zap,
  Eye,
  Cpu,
  Lock,
  Battery,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Calculator,
  TrendingUp,
  DollarSign,
  Clock,
  Bot,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import ExperimentHeader from "@/components/ExperimentHeader";
import PageHeroDark from "@/components/layout/PageHeroDark";
import SiteFooter from "@/components/layout/SiteFooter";
import WorkflowDriveBanner from "@/components/WorkflowDriveBanner";

// ── Criteria Data ────────────────────────────────────────────────────────────

const CRITERIA = [
  {
    number: "01",
    icon: Cpu,
    color: "#93c5fd",
    bg: "rgba(96,165,250,0.08)",
    border: "rgba(96,165,250,0.2)",
    label: "Technology & Basic Abilities",
    summary: "Sensors, manipulation, walking speed, and gripping force.",
    description:
      "Examines the installed hardware and software stack and tests foundational physical capabilities. This determines the robot's technological potential before evaluating complex tasks.",
    tests: [
      "Sensor stack audit (vision, audio, text & speech recognition, human detection)",
      "Manipulation assessment — gripper type, finger count, degrees of freedom",
      "Walking speed measurement via 3D Vicon tracker",
      "Gripping force and maximum payload tests",
    ],
    g1Results: [
      { label: "Walking (slow)", value: "0.49 m/s (1.1 mph)" },
      { label: "Walking (fast)", value: "0.84 m/s (1.9 mph)" },
      {
        label: "Dexterity",
        value: "Below human level — requires additional software",
      },
      {
        label: "Arm endurance",
        value: "1–2 min before actuator overheat at full extension",
      },
    ],
    standard: null,
    verdict:
      "Current humanoids require significant software work before autonomous task execution is viable.",
  },
  {
    number: "02",
    icon: Zap,
    color: "#10b981",
    bg: "rgba(5,150,105,0.08)",
    border: "rgba(167,139,250,0.2)",
    label: "Complex Abilities",
    summary:
      "Whole-body movement, navigation, obstacle courses, and precision control.",
    description:
      "Tests combined use of technologies across realistic task domains. Intentionally designed to exceed current capabilities — establishing a forward-compatible benchmark across generations.",
    tests: [
      "Whole-body movements: running, jumping, climbing, ramp navigation",
      "Manipulative tasks: opening doors, object retrieval",
      "Obstacle course navigation",
      "Precision and force control under varying loads",
    ],
    g1Results: [
      {
        label: "Stair climbing",
        value: "Not supported per manufacturer specs",
      },
      {
        label: "Ramp stability (20% incline)",
        value: "Good — no balance loss recorded",
      },
      {
        label: "Floor recovery",
        value: "Requires high-friction surface — fails on tile/hardwood",
      },
      {
        label: "Obstacle course",
        value: "Not feasible with onboard abilities",
      },
    ],
    standard: null,
    verdict:
      "Most complex benchmarks are forward-looking. Only future hardware generations will fully pass — by design.",
  },
  {
    number: "03",
    icon: Eye,
    color: "#34d399",
    bg: "rgba(52,211,153,0.08)",
    border: "rgba(52,211,153,0.2)",
    label: "Cleanliness",
    summary:
      "Particle emissions, outgassing, and hygienic design for sensitive environments.",
    description:
      "Evaluates whether the robot can operate in semiconductor, pharmaceutical, food, or biotech production without causing contamination. Fraunhofer IPA has qualified 3,000+ automation components under ISO 14644.",
    tests: [
      "Particle emission testing per ISO 14644-14",
      "Outgassing measurement per ISO 14644-15",
      "Cleanability and hygienic design assessment",
    ],
    g1Results: [
      {
        label: "Particle emissions",
        value: "Compliant with ISO Class 5 cleanrooms",
      },
      {
        label: "Outgassing",
        value: "Promising — no critical contamination detected",
      },
      {
        label: "Hygienic design",
        value:
          "Not suitable for high-hygiene environments — joints have inaccessible gaps",
      },
    ],
    standard: "ISO 14644-14 / ISO 14644-15",
    verdict:
      "Suitable for semiconductor cleanrooms but not food or pharma environments without hardware modifications.",
  },
  {
    number: "04",
    icon: ShieldCheck,
    color: "#fbbf24",
    bg: "rgba(251,191,36,0.08)",
    border: "rgba(251,191,36,0.2)",
    label: "Functional Safety",
    summary:
      "Collision forces, stability, emergency stop, and human co-working risk.",
    description:
      "Humanoids are designed to operate alongside humans. This section measures actual collision forces, stability across surfaces, and compliance with human-robot collaboration safety standards. The ISO standard for humanoids (ISO 25785-1) is not expected until 2028.",
    tests: [
      "Collision force measurement — arm movements and full-body contact",
      "Slope stability testing (ramp walking, stops, direction changes)",
      "Multi-surface stability (steps, cable ducts, approach angles)",
      "Emergency stop accessibility audit",
    ],
    g1Results: [
      {
        label: "Collision force (full-body)",
        value: "> 500 N — exceeds ISO TS 15066 pain thresholds",
        warn: true,
      },
      {
        label: "Surface stability",
        value: "Strong — difficult to destabilize even on challenging surfaces",
      },
      {
        label: "Emergency stop",
        value: "No physical E-stop — must remove battery to cut power",
        warn: true,
      },
      {
        label: "Joint pinch points",
        value: "Improvement needed at joint edges",
      },
    ],
    standard:
      "ISO 10218 / ISO TS 15066 (cobots) — ISO 25785-1 for humanoids expected 2028",
    verdict:
      "Not safe for unguarded human co-working at current collision forces. Requires case-by-case risk assessment.",
  },
  {
    number: "05",
    icon: Lock,
    color: "#f87171",
    bg: "rgba(248,113,113,0.08)",
    border: "rgba(248,113,113,0.2)",
    label: "Cybersecurity",
    summary:
      "Vulnerability analysis, secure lifecycle, network interfaces, and penetration resistance.",
    description:
      "As network-connected devices that receive regular updates, humanoids present an expanding attack surface. This module covers four areas: vulnerability management, software lifecycle, network security, and operational resilience.",
    tests: [
      "Known vulnerability analysis (CVE database review)",
      "Software update handling and end-of-life policy review",
      "Network interface security (WiFi, Bluetooth, cloud connections)",
      "Load testing and penetration resistance",
    ],
    g1Results: [
      {
        label: "Bluetooth vulnerability",
        value: "Remote code execution found — patched in later firmware",
        warn: true,
      },
      {
        label: "Data transmission",
        value:
          "Continuous sensor data sent to manufacturer — no disable option documented",
        warn: true,
      },
      {
        label: "Update transparency",
        value: "No published EOL or patch schedule",
      },
      { label: "Load stability", value: "Performed well under stress testing" },
    ],
    standard: null,
    verdict:
      "Significant data governance and vulnerability disclosure gaps. Require contractual commitments from vendors before deployment.",
  },
  {
    number: "06",
    icon: Battery,
    color: "#6ee7b7",
    bg: "rgba(52,211,153,0.05)",
    border: "rgba(110,231,183,0.2)",
    label: "Energy Efficiency",
    summary:
      "Power consumption by mode, battery runtime, and charging behavior.",
    description:
      "Battery life determines operational window and shift planning. This benchmark measures real power draw across defined scenarios (standing, walking flat, walking uphill, carrying load) to produce a standardized energy metric.",
    tests: [
      "Power consumption in standing, walking flat, walking uphill, and loaded scenarios",
      "Power-on / power-off cycle measurement",
      "Battery charge time and degradation curve",
    ],
    g1Results: [
      { label: "Standing power", value: "~154 W avg" },
      { label: "Walking (flat)", value: "~272 W avg" },
      { label: "Walking (10% incline)", value: "~283 W avg" },
      { label: "Typical scenario avg", value: "~239 W" },
      { label: "Battery life (standing)", value: "2 h 49 min" },
      { label: "Battery life (typical)", value: "1 h 49 min" },
    ],
    standard: null,
    verdict:
      "Under 2-hour battery life in active operation. Multi-shift deployments require battery swaps or charging infrastructure.",
  },
];

const BUYERS_CHECKLIST = [
  "Request independent benchmark results — not just vendor marketing demos",
  "Test collision forces against ISO TS 15066 before any human co-working application",
  "Ask for a written cybersecurity disclosure: known CVEs, EOL policy, data transmission practices",
  "Define your floor surface conditions — recovery and stability vary significantly",
  "Confirm cleanroom or hygiene requirements before procurement",
  "Model charging cycles into shift planning — assume ~1.5–2 hour active windows per charge",
  "Get contractual software update commitments — current humanoids are early-stage products",
];

// ── Interactive ROI Calculator Component ─────────────────────────────────────

function InteractiveRoiCalculator() {
  const [fleetSize, setFleetSize] = useState(10);
  const [laborRate, setLaborRate] = useState(32);
  const [shifts, setShifts] = useState(2);
  const [model, setModel] = useState<"raas" | "capex">("raas");
  const [raasFee, setRaasFee] = useState(6500);
  const [capexCost, setCapexCost] = useState(95000);

  // Calculations
  const hoursPerShiftPerDay = 8;
  const operatingDaysPerYear = 300;
  const annualHoursPerRobot = shifts * hoursPerShiftPerDay * operatingDaysPerYear; // e.g. 2 * 8 * 300 = 4,800 hrs

  // Annual Human Labor Cost Replaced (1 robot replaces ~1 FTE per shift)
  const annualHumanLaborCost = fleetSize * annualHoursPerRobot * laborRate;
  const hourlyHumanCost = laborRate;

  // RaaS Model Costs
  const annualRaasCost = fleetSize * raasFee * 12;
  const raasHourlyCost = (raasFee * 12) / annualHoursPerRobot;
  const annualSavingsRaas = annualHumanLaborCost - annualRaasCost;
  const raasOpExSavingsPct = Math.round((annualSavingsRaas / annualHumanLaborCost) * 100);

  // CapEx Model Costs (Maintenance & Software Support = ~$8k/yr per robot)
  const totalCapExInitial = fleetSize * capexCost;
  const annualCapExMaintenance = fleetSize * 8000;
  const annualSavingsCapEx = annualHumanLaborCost - annualCapExMaintenance;
  const capexPaybackMonths = Math.max(0.5, (totalCapExInitial / Math.max(1, annualSavingsCapEx)) * 12);
  const capexFiveYearNetSavings = annualSavingsCapEx * 5 - totalCapExInitial;
  const capexFiveYearRoiPct = Math.round((capexFiveYearNetSavings / Math.max(1, totalCapExInitial)) * 100);

  // Active metrics depending on selected model
  const activeAnnualSavings = model === "raas" ? annualSavingsRaas : annualSavingsCapEx;
  const activePaybackLabel = model === "raas" ? "Day 1 (Instant Cashflow)" : `${capexPaybackMonths.toFixed(1)} Months`;
  const activeHourlyCost = model === "raas" ? raasHourlyCost : (capexCost / (annualHoursPerRobot * 3)) + (8000 / annualHoursPerRobot);
  const activeSavingsPct = model === "raas" ? raasOpExSavingsPct : Math.round((activeAnnualSavings / annualHumanLaborCost) * 100);

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-700/80 bg-[#0d1b38] shadow-2xl p-6 sm:p-8 mb-12">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/80 pb-6 mb-6">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-mono font-bold text-purple-300">
            <Calculator className="h-3.5 w-3.5 text-purple-400" />
            Interactive Enterprise Financial Model
          </span>
          <h2 className="text-2xl font-extrabold text-white font-display mt-2">
            Humanoid & Automation ROI & RaaS Payback Calculator
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl">
            Simulate OpEx savings, hourly cost replacement, and payback timelines for RaaS subscriptions vs CapEx purchases across 300 operating days.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-[#081126] p-1 border border-slate-700/80">
          <button
            type="button"
            onClick={() => setModel("raas")}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              model === "raas"
                ? "bg-purple-600 text-white shadow-md shadow-purple-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            RaaS (Subscription)
          </button>
          <button
            type="button"
            onClick={() => setModel("capex")}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              model === "capex"
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            CapEx (Outright Purchase)
          </button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-12">
        {/* Controls Column */}
        <div className="lg:col-span-6 space-y-6">
          {/* Fleet Size */}
          <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center gap-1.5">
                <Bot className="h-4 w-4 text-purple-400" /> Fleet Size (Humanoids / AMRs)
              </label>
              <span className="font-mono text-base font-extrabold text-purple-300 bg-purple-500/20 px-2.5 py-0.5 rounded-lg border border-purple-500/30">
                {fleetSize} Robots
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="50"
              value={fleetSize}
              onChange={(e) => setFleetSize(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
              <span>1 Robot (Pilot)</span>
              <span>25 Robots (Facility)</span>
              <span>50 Robots (Enterprise)</span>
            </div>
          </div>

          {/* Hourly Labor Rate */}
          <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center gap-1.5">
                <DollarSign className="h-4 w-4 text-emerald-400" /> Hourly Labor Cost Replaced
              </label>
              <span className="font-mono text-base font-extrabold text-emerald-300 bg-emerald-500/20 px-2.5 py-0.5 rounded-lg border border-emerald-500/30">
                ${laborRate}/hr
              </span>
            </div>
            <input
              type="range"
              min="18"
              max="65"
              step="1"
              value={laborRate}
              onChange={(e) => setLaborRate(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
              <span>$18/hr (Basic Warehouse)</span>
              <span>$35/hr (Manufacturing)</span>
              <span>$65/hr (Specialized)</span>
            </div>
          </div>

          {/* Shifts */}
          <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-amber-400" /> Operational Shifts / Day
              </label>
              <span className="font-mono text-base font-extrabold text-amber-300 bg-amber-500/20 px-2.5 py-0.5 rounded-lg border border-amber-500/30">
                {shifts} Shift{shifts > 1 ? "s" : ""} ({shifts * 8} hrs/day)
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 mt-2">
              {[1, 2, 3].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setShifts(s)}
                  className={`py-2 text-xs font-mono font-bold rounded-lg border transition-all ${
                    shifts === s
                      ? "border-amber-400 bg-amber-500/20 text-amber-300"
                      : "border-slate-800 bg-slate-900 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  {s} Shift{s > 1 ? "s" : ""} ({s * 8}h)
                </button>
              ))}
            </div>
          </div>

          {/* Model Specific Cost Input */}
          {model === "raas" ? (
            <div className="rounded-xl border border-purple-500/30 bg-purple-950/20 p-4">
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-mono font-bold uppercase text-purple-300">
                  RaaS Monthly Subscription / Robot
                </label>
                <span className="font-mono text-sm font-extrabold text-purple-200">
                  ${raasFee.toLocaleString()}/mo
                </span>
              </div>
              <input
                type="range"
                min="4500"
                max="12000"
                step="500"
                value={raasFee}
                onChange={(e) => setRaasFee(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"
              />
              <p className="text-[11px] text-slate-400 mt-2">
                Includes hardware lease, software updates, maintenance, and 24/7 cloud support.
              </p>
            </div>
          ) : (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4">
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-mono font-bold uppercase text-emerald-300">
                  CapEx Purchase Price / Robot
                </label>
                <span className="font-mono text-sm font-extrabold text-emerald-200">
                  ${capexCost.toLocaleString()}
                </span>
              </div>
              <input
                type="range"
                min="45000"
                max="180000"
                step="5000"
                value={capexCost}
                onChange={(e) => setCapexCost(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
              />
              <p className="text-[11px] text-slate-400 mt-2">
                Outright hardware purchase + ~$8k/year per robot maintenance & software license.
              </p>
            </div>
          )}
        </div>

        {/* Results KPI Panel */}
        <div className="lg:col-span-6 flex flex-col justify-between space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Net Annual Savings */}
            <div className="rounded-xl border border-emerald-500/40 bg-gradient-to-br from-[#08152c] to-[#0a2336] p-5 shadow-lg">
              <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
                <TrendingUp className="h-3.5 w-3.5" /> Net Annual Savings
              </p>
              <p className="mt-2 text-3xl font-black font-mono text-emerald-300">
                ${Math.max(0, activeAnnualSavings).toLocaleString()}
              </p>
              <p className="mt-1 text-[11px] text-emerald-400/80 font-medium">
                {activeSavingsPct}% Reduction in Annual Labor Cost
              </p>
            </div>

            {/* Payback Window */}
            <div className="rounded-xl border border-purple-500/40 bg-gradient-to-br from-[#0f1430] to-[#1c123d] p-5 shadow-lg">
              <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-purple-300 flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5 text-purple-400" /> Payback Window
              </p>
              <p className="mt-2 text-2xl font-black font-mono text-purple-200">
                {activePaybackLabel}
              </p>
              <p className="mt-1 text-[11px] text-purple-300/80 font-medium">
                {model === "raas" ? "Zero upfront capital requirement" : "Full payback of initial hardware expenditure"}
              </p>
            </div>

            {/* Effective Hourly Cost per Robot */}
            <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4.5">
              <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                Robot Hourly Cost
              </p>
              <p className="mt-1 text-2xl font-black font-mono text-cyan-300">
                ${activeHourlyCost.toFixed(2)}/hr
              </p>
              <p className="mt-1 text-[11px] text-slate-400">
                vs <span className="line-through text-slate-500">${hourlyHumanCost}.00/hr</span> human rate
              </p>
            </div>

            {/* 5-Year Cumulative Impact */}
            <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4.5">
              <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                {model === "raas" ? "5-Year Cumulative Savings" : "5-Year ROI %"}
              </p>
              <p className="mt-1 text-2xl font-black font-mono text-amber-300">
                {model === "raas"
                  ? `$${(annualSavingsRaas * 5).toLocaleString()}`
                  : `${capexFiveYearRoiPct}% ROI`}
              </p>
              <p className="mt-1 text-[11px] text-slate-400">
                Across {fleetSize} deployed units over 5 years
              </p>
            </div>
          </div>

          {/* Comparative Summary Table */}
          <div className="rounded-xl border border-slate-700/60 bg-[#081126] p-4 text-xs">
            <h4 className="font-mono font-bold uppercase tracking-wider text-slate-300 mb-3 text-[11px]">
              Annual Operational Breakdown ({fleetSize} Robots · {shifts} Shifts)
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between border-b border-slate-800 pb-1.5 text-slate-400">
                <span>Human Labor Base Cost:</span>
                <span className="font-mono text-slate-200 font-bold">${annualHumanLaborCost.toLocaleString()}/yr</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5 text-slate-400">
                <span>{model === "raas" ? "RaaS Subscription Cost:" : "CapEx Maintenance & License:"}</span>
                <span className="font-mono text-purple-300 font-bold">
                  -${(model === "raas" ? annualRaasCost : annualCapExMaintenance).toLocaleString()}/yr
                </span>
              </div>
              <div className="flex justify-between pt-1 font-bold text-emerald-300 text-sm">
                <span>Net Operating Advantage:</span>
                <span className="font-mono">+${Math.max(0, activeAnnualSavings).toLocaleString()}/yr</span>
              </div>
            </div>
          </div>

          <div className="pt-2">
            <Link
              href="/pipeline"
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-purple-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-purple-500/30 hover:bg-purple-500 transition-all cursor-pointer"
            >
              Match This ROI Model to 25 Verified Buyer Leads <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Page Component ──────────────────────────────────────────────────────

export default function Benchmark() {
  const [expanded, setExpanded] = useState<number | null>(0);

  const toggle = (i: number) => setExpanded(expanded === i ? null : i);

  return (
    <div className="min-h-screen flex flex-col bg-[#081126] text-slate-100 font-sans">
      <ExperimentHeader />

      <PageHeroDark
        maxWidthClass="max-w-6xl"
        eyebrow={
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            Robotics Financial Model & Fraunhofer Benchmark
          </span>
        }
        title={
          <span>
            Enterprise Robotics <span className="text-emerald-400">ROI Calculator</span> & Benchmark
          </span>
        }
        description={
          <p className="max-w-2xl text-sm leading-relaxed text-slate-300 sm:text-base">
            Model RaaS subscription payback, calculate hourly labor replacement costs, and review independent Fraunhofer IPA testing benchmarks for humanoid deployments.
          </p>
        }
        stats={[
          {
            label: "Avg RaaS Payback",
            value: "Day 1",
            tone: "emerald",
          },
          {
            label: "OpEx Reduction",
            value: "34%–48%",
            tone: "amber",
          },
          {
            label: "Evaluated Criteria",
            value: "6 Pillars",
            tone: "white",
          },
          {
            label: "Reference Model",
            value: "Unitree G1",
            tone: "white",
          },
        ]}
      />

      <div className="page-dark-shell-fade" />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-20 pt-8 lg:px-6">
        {/* Interactive ROI Calculator */}
        <InteractiveRoiCalculator />

        {/* ── Fraunhofer Benchmark Section Header ── */}
        <div className="mb-8 text-center sm:text-left">
          <span className="text-[11px] font-mono uppercase font-bold text-emerald-400 tracking-wider">
            Fraunhofer IPA Evaluation Standards
          </span>
          <h2 className="text-2xl font-bold text-white font-display mt-1">
            How to Benchmark a Humanoid Robot Before Deployment
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-300">
            Most vendors show curated marketing demos. Independent benchmarks show reality. Fraunhofer IPA — Europe&apos;s leading applied research institute — established a six-criteria test framework for humanoid robotics.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-slate-400">
            <span>Source: Fraunhofer IPA, May 2026</span>
            <span className="text-slate-600">·</span>
            <a
              href="https://www.therobotreport.com/fraunhofer-ipa-offers-new-test-benchmark-for-humanoid-robots/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-emerald-400 hover:underline"
            >
              Original article <ExternalLink className="h-3 w-3" />
            </a>
            <span className="text-slate-600">·</span>
            <span>Reference Unit: Unitree G1</span>
          </div>
        </div>

        {/* ── Six criteria accordion ── */}
        <section className="mb-12 space-y-4">
          {CRITERIA.map((c, i) => {
            const Icon = c.icon;
            const open = expanded === i;
            return (
              <div
                key={i}
                className={`rounded-2xl border overflow-hidden transition-all bg-[#0d1b38] shadow-xl ${
                  open ? "border-emerald-500/50" : "border-slate-700/80"
                }`}
              >
                {/* Header row */}
                <button
                  type="button"
                  onClick={() => toggle(i)}
                  className="w-full flex items-center gap-4 px-6 py-5 text-left hover:bg-slate-800/30 transition-colors"
                >
                  <span
                    className="shrink-0 flex items-center justify-center rounded-xl w-10 h-10 font-mono text-[11px] font-bold"
                    style={{
                      background: c.bg,
                      color: c.color,
                      border: `1px solid ${c.border}`,
                    }}
                  >
                    {c.number}
                  </span>
                  <Icon className="h-5 w-5 shrink-0" style={{ color: c.color }} />
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-white text-[15px] font-display">
                      {c.label}
                    </p>
                    <p className="text-[12px] text-slate-300 mt-0.5">
                      {c.summary}
                    </p>
                  </div>
                  {open ? (
                    <ChevronUp className="h-4 w-4 text-slate-400 shrink-0" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
                  )}
                </button>

                {/* Expanded detail */}
                {open && (
                  <div className="px-6 pb-6 space-y-5 border-t border-slate-700/60 pt-5">
                    <p className="text-sm text-slate-300 leading-relaxed">
                      {c.description}
                    </p>

                    {c.standard && (
                      <p className="text-[11px] font-mono text-slate-400">
                        Standard:{" "}
                        <span className="text-emerald-300">{c.standard}</span>
                      </p>
                    )}

                    {/* Tests */}
                    <div>
                      <p className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 mb-2">
                        What is tested
                      </p>
                      <ul className="space-y-1.5">
                        {c.tests.map((t, j) => (
                          <li
                            key={j}
                            className="flex items-start gap-2 text-[12px] text-slate-300"
                          >
                            <span
                              className="mt-1.5 h-1.5 w-1.5 rounded-full shrink-0"
                              style={{ background: c.color }}
                            />
                            {t}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* G1 results */}
                    <div>
                      <p className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 mb-2">
                        Unitree G1 results (reference)
                      </p>
                      <div className="grid gap-2 sm:grid-cols-2">
                        {c.g1Results.map((r, j) => (
                          <div
                            key={j}
                            className="rounded-xl px-3 py-2.5"
                            style={{
                              background: r.warn
                                ? "rgba(248,113,113,0.12)"
                                : "#081126",
                              border: r.warn
                                ? "1px solid rgba(248,113,113,0.3)"
                                : "1px solid rgba(51,65,85,0.6)",
                            }}
                          >
                            <p className="text-[10px] font-mono text-slate-400 mb-0.5">
                              {r.label}
                            </p>
                            <p
                              className="text-[12px] font-semibold"
                              style={{
                                color: r.warn
                                  ? "#f87171"
                                  : "#e2e8f0",
                              }}
                            >
                              {r.value}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Verdict */}
                    <div
                      className="rounded-xl px-4 py-3"
                      style={{
                        background: `${c.color}0d`,
                        border: `1px solid ${c.border}`,
                      }}
                    >
                      <p
                        className="text-[10px] font-mono font-bold uppercase tracking-widest mb-1"
                        style={{ color: c.color }}
                      >
                        Buyer takeaway
                      </p>
                      <p className="text-[12px] text-slate-200">{c.verdict}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </section>

        {/* ── Buyer checklist ── */}
        <section className="mb-12">
          <div className="rounded-2xl border border-emerald-500/40 bg-gradient-to-br from-[#08152c] to-[#0a2336] p-8 shadow-2xl">
            <div className="mb-2 text-[10px] font-mono font-bold uppercase tracking-widest text-emerald-400">
              Procurement Audit Checklist
            </div>
            <h2 className="font-display text-2xl font-extrabold text-white mb-6">
              7 Critical Questions Every Robotics Buyer Must Ask
            </h2>
            <ul className="space-y-3.5">
              {BUYERS_CHECKLIST.map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="shrink-0 flex items-center justify-center rounded-full w-5 h-5 text-[10px] font-mono font-bold mt-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    {i + 1}
                  </span>
                  <p className="text-sm text-slate-200 leading-relaxed">{item}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Bottom CTA Block */}
        <section className="mb-8 text-center">
          <div className="rounded-2xl border border-slate-700/80 bg-[#0d1b38] px-8 py-10 shadow-2xl">
            <h2 className="font-display text-2xl font-extrabold text-white mb-3">
              Ready to find the right robot for your operation?
            </h2>
            <p className="text-sm text-slate-300 mb-7 max-w-xl mx-auto">
              Ready For Robots matches enterprise buyer requirements to vetted robot vendors — backed by signal data and live intent, not pitch decks.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/pipeline"
                className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-purple-500/30 hover:bg-purple-500 transition-all cursor-pointer"
              >
                Build 25 Lead Pipeline <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/newsletter"
                className="inline-flex items-center gap-2 rounded-xl border border-emerald-400 text-emerald-400 px-6 py-3 text-sm font-bold hover:bg-emerald-500/10 transition-all"
              >
                View Robot Intelligence Brief
              </Link>
            </div>
          </div>

          <WorkflowDriveBanner
            title="Turn RaaS ROI Analysis into 25 Live Deals"
            subtitle="Match your deployment cost benchmark to 25 verified enterprise buyers currently searching for automation."
            buttonText="Generate 25 Lead Pipeline"
          />
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
