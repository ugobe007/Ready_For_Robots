/** HEIR 2026 — static content from Humanoid Engineering Intelligence Report (May 2026). */

export const HEIR_REPORTS = [
  {
    title: "Full report",
    description: "Complete HEIR 2026 analysis — framework, vendor map, and deployment economics.",
    href: "/reports/HEIR_2026_Humanoid_Engineering_Intelligence_Report.pdf",
  },
  {
    title: "Executive summary",
    description: "Condensed overview for buyers, investors, and integrators.",
    href: "/reports/HEIR_2026_Report_Final.pdf",
  },
] as const;

export const HEIR_PULL_QUOTES = [
  "Walking gets attention. Manipulation creates economic value.",
  "The next humanoid moat may be the dataset, not the chassis.",
  "Humanoid intelligence compounds only when the fleet learns from failure.",
] as const;

export const DEMO_VS_DEPLOYMENT = [
  { before: "Choreographed demos", after: "Industrial deployment & integration" },
  { before: "Walking & athletic stunts", after: "Dexterous manipulation & force control" },
  { before: "Laboratory prototypes", after: "Scalable, economical production" },
  { before: "Spectacle", after: "Operational reliability & safety" },
] as const;

export const CAPABILITY_PYRAMID = [
  { level: 7, label: "Reliable industrial labor", note: "The economic goal" },
  { level: 6, label: "Autonomous task execution" },
  { level: 5, label: "Dexterous tool use" },
  { level: 4, label: "Force-controlled manipulation" },
  { level: 3, label: "Dynamic locomotion & recovery" },
  { level: 2, label: "Choreographed / scripted motion" },
  { level: 1, label: "Static posing & demonstrations", note: "The spectacle layer" },
] as const;

export type HeifRow = {
  company: string;
  mobility: number;
  manipulation: number;
  cognition: number;
  safety: number;
  dataPipeline: number;
  production: number;
};

export const HEIF_BENCHMARK: HeifRow[] = [
  { company: "Boston Dynamics", mobility: 4.0, manipulation: 2.5, cognition: 2.0, safety: 2.5, dataPipeline: 2.0, production: 2.0 },
  { company: "EngineAI", mobility: 3.5, manipulation: 1.5, cognition: 1.5, safety: 1.0, dataPipeline: 2.0, production: 2.0 },
  { company: "AgiBot", mobility: 3.0, manipulation: 3.5, cognition: 3.0, safety: 2.0, dataPipeline: 4.0, production: 3.0 },
  { company: "Tesla Optimus", mobility: 3.0, manipulation: 2.5, cognition: 3.0, safety: 2.0, dataPipeline: 3.5, production: 4.0 },
  { company: "Figure AI", mobility: 2.5, manipulation: 3.0, cognition: 3.5, safety: 2.0, dataPipeline: 3.5, production: 2.0 },
  { company: "Unitree", mobility: 3.5, manipulation: 2.0, cognition: 1.5, safety: 1.5, dataPipeline: 2.0, production: 3.5 },
  { company: "Agility Robotics", mobility: 2.5, manipulation: 2.5, cognition: 2.0, safety: 2.5, dataPipeline: 2.0, production: 3.0 },
];

export const READINESS_FUNNEL = [
  { stage: "1", title: "Laboratory demonstration", examples: "Legacy research platforms" },
  { stage: "2", title: "Controlled environment operation", examples: "EngineAI, Figure AI, Tesla Optimus" },
  { stage: "3", title: "Supervised industrial pilot", examples: "AgiBot, Unitree, Boston Dynamics" },
  { stage: "4", title: "Partial autonomous deployment", examples: "Agility Robotics (Digit)" },
  { stage: "5", title: "Scalable production deployment", examples: "Not yet achieved industry-wide" },
] as const;

export const ENGINEERING_SCHOOLS = [
  { school: "Locomotion-first", focus: "Gait, balance, whole-body control", strength: "Dynamic movement", risk: "Weak manipulation evidence" },
  { school: "Manipulation-first", focus: "Hands, force control, bimanual tasks", strength: "Useful physical labor", risk: "Slower mobility progress" },
  { school: "AI-first", focus: "Foundation models, task planning", strength: "Rapid generalization", risk: "Hardware dependency" },
  { school: "Data-first", focus: "Teleoperation, datasets, sim-to-real", strength: "Compounding learning curves", risk: "High infrastructure cost" },
  { school: "Manufacturing-first", focus: "Cost, scale, supply chain", strength: "Affordability & fleet deploy", risk: "Software capability gaps" },
] as const;

export const STRATEGIC_INSIGHTS = [
  { title: "The body commoditizes", body: "Physical chassis and actuator assemblies will commoditize faster than expected. The software stack is the true differentiator." },
  { title: "Datasets are the moat", body: "The company with the most diverse, high-fidelity manipulation trajectories will lead the market long-term." },
  { title: "Scale beats perfection", body: "A lower-cost, reliable Level 4 robot at scale will capture more market share than an expensive Level 6 prototype." },
  { title: "Geography bifurcates", body: "China is rapidly dominating hardware scale and actuator supply chains, while Western companies lead in foundation-model reasoning." },
  { title: "The winner is a hybrid", body: "Winning humanoid companies will resemble automakers combined with cloud AI infrastructure giants." },
  { title: "Ecosystems matter", body: "Service, software, and systems integration may become more valuable than the hardware itself." },
] as const;
