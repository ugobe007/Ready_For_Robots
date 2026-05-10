// ReadyForRobots — AutonomyDial Component
// Design: Clean Workflow / Elevated SaaS
// Prominent segmented toggle: Manual | Assisted | Auto
// Animated sliding pill indicator between modes

import { motion } from "framer-motion";
import { Hand, Cpu, Zap } from "lucide-react";
import type { AutonomyMode } from "../types/readyForRobots";

type AutonomyDialProps = {
  mode: AutonomyMode;
  onChange: (mode: AutonomyMode) => void;
};

const modes: {
  value: AutonomyMode;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  textColor: string;
}[] = [
  {
    value: "manual",
    label: "Manual",
    description: "You control every action",
    icon: Hand,
    color: "neutral",
    bgColor: "bg-neutral-100",
    textColor: "text-neutral-700",
  },
  {
    value: "assisted",
    label: "Assisted",
    description: "System suggests, you approve",
    icon: Cpu,
    color: "blue",
    bgColor: "bg-blue-50",
    textColor: "text-blue-700",
  },
  {
    value: "auto",
    label: "Auto",
    description: "System acts, you review",
    icon: Zap,
    color: "emerald",
    bgColor: "bg-emerald-50",
    textColor: "text-emerald-700",
  },
];

const modeIndex = { manual: 0, assisted: 1, auto: 2 };

export default function AutonomyDial({ mode, onChange }: AutonomyDialProps) {
  const activeMode = modes.find((m) => m.value === mode)!;

  return (
    <div className="flex items-center gap-4 py-3 px-6 border-b border-neutral-100 bg-white">
      {/* Label */}
      <div className="shrink-0">
        <p className="text-xs font-semibold text-neutral-400 uppercase tracking-widest leading-none mb-0.5">
          Autonomy
        </p>
        <p className="text-xs text-neutral-500">{activeMode.description}</p>
      </div>

      {/* Segmented control */}
      <div className="relative flex items-center bg-neutral-100 rounded-lg p-1 gap-0">
        {/* Sliding pill */}
        <motion.div
          className={`absolute top-1 bottom-1 rounded-md shadow-sm ${
            mode === "manual"
              ? "bg-white"
              : mode === "assisted"
              ? "bg-white"
              : "bg-white"
          }`}
          style={{ width: "calc(33.333% - 2px)" }}
          animate={{ x: `calc(${modeIndex[mode]} * 100% + ${modeIndex[mode] * 4}px)` }}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
        />

        {modes.map((m) => {
          const Icon = m.icon;
          const isActive = mode === m.value;
          return (
            <button
              key={m.value}
              onClick={() => onChange(m.value)}
              className={`relative z-10 flex items-center gap-1.5 px-4 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 min-w-[100px] justify-center ${
                isActive
                  ? m.value === "auto"
                    ? "text-emerald-700"
                    : m.value === "assisted"
                    ? "text-blue-700"
                    : "text-neutral-800"
                  : "text-neutral-400 hover:text-neutral-600"
              }`}
            >
              <Icon
                className={`h-3.5 w-3.5 ${
                  isActive
                    ? m.value === "auto"
                      ? "text-emerald-600"
                      : m.value === "assisted"
                      ? "text-blue-600"
                      : "text-neutral-600"
                    : "text-neutral-400"
                }`}
              />
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Status indicator */}
      <div className="flex items-center gap-2 ml-2">
        <div
          className={`h-2 w-2 rounded-full ${
            mode === "auto"
              ? "bg-emerald-500 animate-pulse"
              : mode === "assisted"
              ? "bg-blue-500"
              : "bg-neutral-400"
          }`}
        />
        <span
          className={`text-xs font-medium ${
            mode === "auto"
              ? "text-emerald-700"
              : mode === "assisted"
              ? "text-blue-700"
              : "text-neutral-500"
          }`}
        >
          {mode === "auto"
            ? "System is acting"
            : mode === "assisted"
            ? "Awaiting your approval"
            : "Waiting for your input"}
        </span>
      </div>
    </div>
  );
}
