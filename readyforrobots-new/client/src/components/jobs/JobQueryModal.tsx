import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Search, Sparkles } from "lucide-react";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSubmitQuery: (selection: {
    jobType: string;
    customQuery: string;
    label: string;
  }) => void;
  currentRobotName?: string;
};

const JOB_DEFINITION_OPTIONS = [
  { id: "hospitality", label: "Hospitality & Guest Services", hint: "Hotel linen transport, room service, bussing" },
  { id: "cleaning", label: "Commercial Cleaning & Sanitation", hint: "Autonomous floor scrubbers, janitorial, terminal care" },
  { id: "logistics", label: "Logistics & 3PL Warehousing", hint: "Material movement, parcel sortation, cross-dock" },
  { id: "factory", label: "Machine Tending & Metal Fabrication", hint: "CNC machine loading, press brake assist, welding cell" },
  { id: "amr", label: "Material Handling & Conveyance", hint: "AMR/AGV tugging, pallet transport, line replenishment" },
  { id: "cobot", label: "Case Palletizing & Packaging", hint: "End-of-line cobots, case packing, carton casing" },
  { id: "quadruped", label: "Inspection & Quality Control", hint: "Jobsite scanning, thermal inspection, facility mapping" },
  { id: "mobile_manipulator", label: "Assembly & Precision Manufacturing", hint: "Kitting, sub-assembly, electronics placement" },
  { id: "healthcare", label: "Healthcare & Hospital Logistics", hint: "Specimen delivery, pharmacy carts, clinical assist" },
  { id: "agriculture", label: "Agriculture & Outdoor Automation", hint: "Autonomous tractors, weeding, crop monitoring" },
  { id: "custom", label: "Other / Custom Job Requirement Entry", hint: "Type custom job specifications or industry below" },
];

export default function JobQueryModal({
  isOpen,
  onClose,
  onSubmitQuery,
  currentRobotName,
}: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [customQuery, setCustomQuery] = useState<string>("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const activeText =
      selectedCategory === "custom"
        ? customQuery.trim()
        : selectedCategory
          ? (JOB_DEFINITION_OPTIONS.find(o => o.id === selectedCategory)?.label || selectedCategory)
          : customQuery.trim();

    if (!activeText) return;

    onSubmitQuery({
      jobType: selectedCategory,
      customQuery: customQuery.trim(),
      label: activeText,
    });
  };

  const selectedHint = JOB_DEFINITION_OPTIONS.find(o => o.id === selectedCategory)?.hint;

  const dialog = (
    <div
      aria-modal="true"
      role="dialog"
      aria-labelledby="job-query-title"
      className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm overflow-y-auto"
      onMouseDown={event => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full max-w-2xl rounded-2xl border border-purple-500/50 bg-[#081126] p-6 shadow-2xl sm:p-8 text-slate-100"
        onMouseDown={event => event.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-slate-700/80 pb-5">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/40 bg-purple-500/10 px-3 py-1 font-mono text-xs font-bold uppercase tracking-wider text-purple-300">
              <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
              <span>Job Opportunity Query</span>
            </div>
            <h2
              id="job-query-title"
              className="mt-3 font-display text-2xl font-bold tracking-tight text-white sm:text-3xl"
            >
              What type of jobs are you looking for?
            </h2>
            <p className="mt-1.5 text-sm text-slate-300">
              {currentRobotName
                ? `Filter or query specific job opportunities tailored to ${currentRobotName}.`
                : "Select a job category or enter custom job requirements to search employer demand."}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="rounded-lg border border-slate-700 p-2 text-slate-400 transition hover:border-slate-500 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-6">
          {/* Dropdown Menu Section */}
          <div>
            <label
              htmlFor="job-category-select"
              className="block font-mono text-xs font-bold uppercase tracking-wider text-slate-300"
            >
              Option 1: Choose from Standard Job Categories (Pull-down Menu)
            </label>
            <div className="mt-2.5">
              <select
                id="job-category-select"
                aria-label="Select Job Category"
                value={selectedCategory}
                onChange={e => {
                  setSelectedCategory(e.target.value);
                  if (e.target.value !== "custom") {
                    setCustomQuery("");
                  }
                }}
                className="w-full rounded-xl border border-slate-600 bg-[#040914] px-4 py-3.5 font-mono text-base text-slate-100 outline-none transition focus:border-purple-500 focus:ring-1 focus:ring-purple-500 sm:text-lg"
              >
                <option value="">-- Select a Job Category (10 Options) --</option>
                {JOB_DEFINITION_OPTIONS.map(opt => (
                  <option key={opt.id} value={opt.id}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            {selectedHint && (
              <p className="mt-2 text-xs font-mono text-emerald-300">
                ✦ Category Scope: {selectedHint}
              </p>
            )}
          </div>

          {/* Custom Input Field Section */}
          <div>
            <label
              htmlFor="custom-job-query"
              className="block font-mono text-xs font-bold uppercase tracking-wider text-slate-300"
            >
              Option 2: Or Type Custom Job Requirements / Industry
            </label>
            <div className="relative mt-2.5">
              <input
                id="custom-job-query"
                type="text"
                value={customQuery}
                onChange={e => {
                  setCustomQuery(e.target.value);
                  if (e.target.value.trim() && selectedCategory !== "custom") {
                    setSelectedCategory("custom");
                  }
                }}
                placeholder="e.g. Laser welding in automotive, food packaging, palletizing 50lb cases"
                className="w-full rounded-xl border border-slate-600 bg-[#040914] px-4 py-3.5 font-mono text-base text-slate-100 placeholder-slate-500 outline-none transition focus:border-purple-500 focus:ring-1 focus:ring-purple-500 sm:text-lg"
              />
              <Search className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500 pointer-events-none" />
            </div>
            <p className="mt-2 text-xs text-slate-400">
              Type any specific payload, environment, or equipment requirement to match against active employer jobs.
            </p>
          </div>

          {/* Modal Actions */}
          <div className="flex flex-wrap items-center justify-end gap-3 border-t border-slate-700/80 pt-5">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-600 px-5 py-3.5 font-mono text-sm font-semibold uppercase tracking-wider text-slate-300 transition hover:border-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedCategory && !customQuery.trim()}
              className="rfr-bevel inline-flex items-center justify-center gap-2.5 rounded-xl border-2 border-purple-500 bg-transparent px-6 py-3.5 text-base font-extrabold uppercase tracking-wider text-purple-300 transition hover:border-purple-400 hover:bg-purple-950/40 hover:text-purple-200 disabled:cursor-not-allowed disabled:opacity-40 sm:text-lg"
            >
              <span>Run Job Query</span>
              <span className="text-emerald-400 font-extrabold text-lg">→</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  if (typeof document === "undefined") return dialog;
  return createPortal(dialog, document.body);
}
