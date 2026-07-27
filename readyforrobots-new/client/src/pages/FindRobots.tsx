import { useState } from "react";
import { Link } from "wouter";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { trackRobotSearch } from "@/lib/siteAnalytics";
import { toast } from "sonner";

const EMERALD = "#10b981";

const inputClass =
  "w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-500 transition-colors focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/15";
const labelClass = "mb-1.5 block text-[10px] font-bold uppercase tracking-widest text-slate-400";

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
    <div className="min-h-screen flex flex-col bg-slate-950 text-white">
      <Header />

      <section className="relative overflow-hidden px-4 pt-24 pb-16 sm:pt-28 sm:pb-20">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-slate-950/90 to-transparent" aria-hidden />
        <div className="pointer-events-none absolute -left-24 top-24 h-72 w-72 rounded-full bg-emerald-500/10 blur-3xl" aria-hidden />
        <div className="pointer-events-none absolute right-0 top-40 h-64 w-64 rounded-full bg-sky-400/10 blur-3xl" aria-hidden />

        <div className="relative mx-auto max-w-3xl rounded-3xl border border-white/10 bg-white/[0.04] px-5 py-6 shadow-2xl shadow-black/30 backdrop-blur sm:px-8 sm:py-8">
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-emerald-300">
            Buyer intake
          </p>
          <h1 className="mt-2 max-w-2xl text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Find the right robots for your operation
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-300">
            Tell us what you are automating, which type of robot you need, and when you plan to deploy.
            Ready For Robots matches your use case to vendors, pilots, and deployment examples from our index.
          </p>

          {submitted ? (
            <div className="mt-10 rounded-2xl border border-emerald-400/20 bg-emerald-400/8 px-6 py-8 text-center">
              <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-300" />
              <h2 className="mt-4 text-lg font-bold text-white">Thank you — request received</h2>
              <p className="mt-2 text-sm text-slate-300">
                Our team will review your use case and reach out with matched robots and next steps.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm">
                <Link href="/robots" className="text-emerald-300 hover:text-emerald-200 underline underline-offset-4">
                  Browse humanoid index
                </Link>
                <Link href="/" className="text-slate-300 hover:text-white underline underline-offset-4">
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
                className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-bold text-slate-950 transition-all disabled:opacity-50"
                style={{ background: EMERALD }}
              >
                {submitting ? "Submitting…" : "Submit request"}
                <ArrowRight className="h-4 w-4" />
              </button>

              <p className="text-[11px] text-slate-400">
                By submitting, you agree we may contact you about robotics vendors and deployment options.
                We do not sell your information to third-party lists.
              </p>
            </form>
          )}
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}
