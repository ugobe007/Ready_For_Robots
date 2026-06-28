import { useState } from "react";
import { Link } from "wouter";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { trackRobotSearch } from "@/lib/siteAnalytics";
import { toast } from "sonner";

const TEAL = "#059669";

const inputClass =
  "w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-900 outline-none placeholder:text-gray-400 focus:border-[rgba(3,218,197,0.35)]";
const labelClass = "mb-1.5 block text-[10px] font-bold uppercase tracking-widest text-gray-400";

const ROBOT_TYPES = [
  { value: "humanoid", label: "Humanoid" },
  { value: "amr_warehouse", label: "Warehouse AMR / AGV" },
  { value: "cobot_industrial", label: "Industrial arm / cobot" },
  { value: "service_hospitality", label: "Service / hospitality robot" },
  { value: "cleaning", label: "Cleaning / facilities" },
  { value: "food_processing", label: "Food processing" },
  { value: "healthcare", label: "Healthcare" },
  { value: "agriculture", label: "Agriculture" },
  { value: "other", label: "Other / not sure yet" },
] as const;

const TIMELINES = [
  { value: "immediate_0_3mo", label: "0–3 months (ready to move)" },
  { value: "near_term_3_6mo", label: "3–6 months" },
  { value: "this_year_6_12mo", label: "6–12 months (this year)" },
  { value: "next_year_12_24mo", label: "12–24 months" },
  { value: "exploring", label: "Exploring — no fixed date yet" },
] as const;

const emptyForm = {
  email: "",
  name: "",
  company: "",
  phone: "",
  jobTitle: "",
  useCase: "",
  robotType: "",
  implementationTimeline: "",
  website: "",
};

export default function FindRobots() {
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const api = getApiBase();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.robotType || !form.implementationTimeline) {
      toast.error("Select a robot type and implementation timeline.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`${api}/api/robot-buyer-leads`, liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, source: "find_robots" }),
      }));
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error((data as { detail?: string }).detail || "Could not submit request");
      }
      trackRobotSearch({
        source: "find_robots",
        robotType: form.robotType,
        implementationTimeline: form.implementationTimeline,
        hasEmail: Boolean(form.email),
      });
      setSubmitted(true);
      setForm(emptyForm);
      toast.success("Request received — we'll follow up shortly.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-gray-900">
      <Header />

      <section className="mx-auto max-w-2xl px-4 pt-24 pb-16">
        <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: TEAL }}>
          Buyer intake
        </p>
        <h1
          className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl"
         
        >
          Find the right robots for your operation
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-gray-500">
          Tell us what you are automating, which type of robot you need, and when you plan to deploy.
          Ready For Robots matches your use case to vendors, pilots, and deployment examples from our index.
        </p>

        {submitted ? (
          <div
            className="mt-10 rounded-xl border px-6 py-8 text-center"
            style={{ borderColor: "rgba(3,218,197,0.2)", background: "rgba(3,218,197,0.06)" }}
          >
            <CheckCircle2 className="mx-auto h-10 w-10" style={{ color: TEAL }} />
            <h2 className="mt-4 text-lg font-bold text-gray-900">Thank you — request received</h2>
            <p className="mt-2 text-sm text-gray-500">
              Our team will review your use case and reach out with matched robots and next steps.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm">
              <Link href="/robots" className="text-emerald-600/90 hover:text-emerald-700 underline underline-offset-4">
                Browse humanoid index
              </Link>
              <Link href="/" className="text-gray-500 hover:text-gray-600 underline underline-offset-4">
                Scan your operation
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="mt-10 space-y-5">
            <div className="grid gap-5 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className={labelClass}>Work email *</span>
                <input
                  className={inputClass}
                  type="email"
                  required
                  autoComplete="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="you@company.com"
                />
              </label>
              <label className="block">
                <span className={labelClass}>Your name</span>
                <input
                  className={inputClass}
                  autoComplete="name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Jane Smith"
                />
              </label>
              <label className="block">
                <span className={labelClass}>Job title</span>
                <input
                  className={inputClass}
                  value={form.jobTitle}
                  onChange={(e) => setForm({ ...form, jobTitle: e.target.value })}
                  placeholder="VP Operations"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className={labelClass}>Company *</span>
                <input
                  className={inputClass}
                  required
                  autoComplete="organization"
                  value={form.company}
                  onChange={(e) => setForm({ ...form, company: e.target.value })}
                  placeholder="Acme Logistics"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className={labelClass}>Phone (optional)</span>
                <input
                  className={inputClass}
                  type="tel"
                  autoComplete="tel"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder="+1 555 000 0000"
                />
              </label>
            </div>

            <label className="block">
              <span className={labelClass}>Robot type you are looking for *</span>
              <select
                className={inputClass}
                required
                value={form.robotType}
                onChange={(e) => setForm({ ...form, robotType: e.target.value })}
              >
                <option value="" disabled>
                  Select category
                </option>
                {ROBOT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className={labelClass}>Use case *</span>
              <textarea
                className={`${inputClass} min-h-[120px] leading-relaxed`}
                required
                minLength={10}
                rows={5}
                value={form.useCase}
                onChange={(e) => setForm({ ...form, useCase: e.target.value })}
                placeholder="Describe the task, facility, throughput goals, and any constraints (safety, shifts, integration with WMS/ERP, etc.)"
              />
            </label>

            <label className="block">
              <span className={labelClass}>When do you plan to implement automation? *</span>
              <select
                className={inputClass}
                required
                value={form.implementationTimeline}
                onChange={(e) => setForm({ ...form, implementationTimeline: e.target.value })}
              >
                <option value="" disabled>
                  Select timeline
                </option>
                {TIMELINES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>

            <input
              type="text"
              name="website"
              tabIndex={-1}
              autoComplete="off"
              className="hidden"
              aria-hidden
              value={form.website}
              onChange={(e) => setForm({ ...form, website: e.target.value })}
            />

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-bold text-[#0a0118] transition-opacity disabled:opacity-50"
              style={{ background: TEAL }}
            >
              {submitting ? "Submitting…" : "Submit request"}
              <ArrowRight className="h-4 w-4" />
            </button>

            <p className="text-[11px] text-gray-400">
              By submitting, you agree we may contact you about robotics vendors and deployment options.
              We do not sell your information to third-party lists.
            </p>
          </form>
        )}
      </section>
      <SiteFooter />
    </div>
  );
}
