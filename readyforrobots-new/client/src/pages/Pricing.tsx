/**
 * Pricing — ReadyForRobots
 * Three-tier pricing: Free Preview · Growth · Enterprise
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 */
import { CheckCircle2, ArrowRight, Zap, Shield, Cpu, HelpCircle } from "lucide-react";
import Header from "@/components/Header";
import { Link } from "wouter";
import { toast } from "sonner";
import { useState } from "react";

const tiers = [
  {
    name: "Preview",
    price: "Free",
    period: "",
    tagline: "See your pipeline before you commit",
    color: "#60a5fa",
    icon: HelpCircle,
    cta: "Start for free",
    ctaAction: "signup",
    features: [
      "3 matched prospects per scan",
      "Signal type identification",
      "Company overview and location",
      "Confidence score",
      "1 outreach draft preview",
      "No account required",
    ],
    limitations: [
      "No full pipeline access",
      "No CRM integration",
      "No auto-outreach",
    ],
    highlight: false,
  },
  {
    name: "Growth",
    price: "$490",
    period: "/month",
    tagline: "Your full automated sales pipeline",
    color: "#7c3aed",
    icon: Zap,
    cta: "Start free trial",
    ctaAction: "trial",
    features: [
      "Unlimited matched prospects",
      "All 14 signal types",
      "Full outreach draft library",
      "Pipeline Kanban board",
      "Assisted autonomy mode",
      "CRM sync (HubSpot, Salesforce)",
      "Weekly pipeline report",
      "2026 Automation Imperative report and weekly Intelligence Brief",
      "Email support",
    ],
    limitations: [],
    highlight: true,
    badge: "Most popular",
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    tagline: "For teams with a defined ICP at scale",
    color: "#f472b6",
    icon: Cpu,
    cta: "Talk to sales",
    ctaAction: "sales",
    features: [
      "Everything in Growth",
      "Auto autonomy mode",
      "Custom signal tuning",
      "Dedicated account manager",
      "Multi-user team access",
      "Custom CRM integrations",
      "SLA and uptime guarantee",
      "Quarterly strategy reviews",
    ],
    limitations: [],
    highlight: false,
  },
];

const faqs = [
  {
    q: "Is there a contract or commitment?",
    a: "No. Growth is month-to-month. You can cancel any time. Enterprise contracts are annual with custom terms.",
  },
  {
    q: "What's included in the free trial?",
    a: "Full Growth access for 14 days — no credit card required. You'll see your complete matched pipeline, all signal types, and full outreach drafts.",
  },
  {
    q: "How do you define a 'matched prospect'?",
    a: "A company that has at least one active buying signal in your robot category, scores 60+ on our composite model, and is in your target geography and company size range.",
  },
  {
    q: "Can I use this with my existing CRM?",
    a: "Yes. Growth includes native sync with HubSpot and Salesforce. Enterprise includes custom integrations for any CRM.",
  },
  {
    q: "What if I sell multiple robot categories?",
    a: "Each Growth subscription covers one robot category. Enterprise includes multi-category support. Contact us to discuss your setup.",
  },
];

export default function Pricing() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const handleCta = (action: string, tier: string) => {
    if (action === "signup") toast.success("Creating your free account…");
    else if (action === "trial") toast.success("Starting your 14-day free trial…");
    else toast.success("Connecting you with our sales team…");
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-24 pb-20 px-6">
        <div className="max-w-5xl mx-auto">

          {/* Header */}
          <div className="text-center mb-14">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3" style={{ color: "#a78bfa" }}>
              Pricing
            </p>
            <h1
              className="font-extrabold text-white leading-tight mb-4"
              style={{ fontSize: "clamp(2rem, 4vw, 3rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Simple, transparent pricing
            </h1>
            <p className="text-sm text-white/40 max-w-xl mx-auto">
              Start free. See your pipeline. Upgrade when you're ready to act on it.
            </p>
          </div>

          {/* Tier cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-16">
            {tiers.map((tier) => {
              const Icon = tier.icon;
              return (
                <div
                  key={tier.name}
                  className="rounded-2xl border flex flex-col relative overflow-hidden transition-all hover:-translate-y-1"
                  style={
                    tier.highlight
                      ? {
                          background: "rgba(124,58,237,0.08)",
                          borderColor: "rgba(124,58,237,0.4)",
                          boxShadow: "0 0 40px rgba(124,58,237,0.15)",
                        }
                      : {
                          background: "rgba(255,255,255,0.03)",
                          borderColor: "rgba(255,255,255,0.08)",
                        }
                  }
                >
                  {tier.badge && (
                    <div
                      className="absolute top-0 left-0 right-0 text-center py-1.5 text-[10px] font-bold uppercase tracking-widest"
                      style={{ background: "#7c3aed", color: "#fff" }}
                    >
                      {tier.badge}
                    </div>
                  )}

                  <div className={`p-7 flex flex-col flex-1 ${tier.badge ? "pt-10" : ""}`}>
                    {/* Tier header */}
                    <div className="flex items-center gap-2.5 mb-4">
                      <div
                        className="h-8 w-8 rounded-lg flex items-center justify-center"
                        style={{ background: `${tier.color}18`, border: `1px solid ${tier.color}30` }}
                      >
                        <Icon className="h-4 w-4" style={{ color: tier.color }} />
                      </div>
                      <span className="font-bold text-white text-sm">{tier.name}</span>
                    </div>

                    {/* Price */}
                    <div className="mb-2">
                      <span
                        className="font-extrabold text-white"
                        style={{ fontSize: "2.25rem", fontFamily: "'Sora', system-ui, sans-serif", lineHeight: 1 }}
                      >
                        {tier.price}
                      </span>
                      {tier.period && (
                        <span className="text-sm text-white/35 ml-1">{tier.period}</span>
                      )}
                    </div>
                    <p className="text-xs text-white/35 mb-6">{tier.tagline}</p>

                    {/* CTA */}
                    <button
                      onClick={() => handleCta(tier.ctaAction, tier.name)}
                      className="w-full flex items-center justify-center gap-2 text-sm font-semibold py-3 rounded-xl mb-7 transition-all hover:-translate-y-0.5"
                      style={
                        tier.highlight
                          ? { background: "#7c3aed", color: "#fff", boxShadow: "0 8px 24px rgba(124,58,237,0.35)" }
                          : { background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.7)", border: "1px solid rgba(255,255,255,0.1)" }
                      }
                    >
                      {tier.cta} <ArrowRight className="h-3.5 w-3.5" />
                    </button>

                    {/* Features */}
                    <div className="flex flex-col gap-2.5 flex-1">
                      {tier.features.map((f) => (
                        <div key={f} className="flex items-start gap-2.5">
                          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: tier.color }} />
                          <span className="text-xs text-white/55">{f}</span>
                        </div>
                      ))}
                      {tier.limitations.map((l) => (
                        <div key={l} className="flex items-start gap-2.5 opacity-40">
                          <div className="h-3.5 w-3.5 shrink-0 mt-0.5 flex items-center justify-center">
                            <div className="h-px w-3 bg-white/30" />
                          </div>
                          <span className="text-xs text-white/30">{l}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Comparison note */}
          <div
            className="rounded-2xl border border-white/6 p-6 flex items-start gap-4 mb-16"
            style={{ background: "rgba(255,255,255,0.02)" }}
          >
            <Shield className="h-5 w-5 shrink-0 mt-0.5" style={{ color: "#a78bfa" }} />
            <div>
              <p className="text-sm font-semibold text-white/70 mb-1">No risk. No lock-in.</p>
              <p className="text-xs text-white/35 leading-relaxed">
                The free preview requires no account. The Growth trial requires no credit card. We'd rather you see the pipeline quality before you commit — because once you do, you'll understand why it works.
              </p>
            </div>
          </div>

          {/* FAQ */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3" style={{ color: "#a78bfa" }}>
              Questions
            </p>
            <h2
              className="font-extrabold text-white mb-8"
              style={{ fontSize: "clamp(1.4rem, 2.5vw, 1.8rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Pricing FAQ
            </h2>
            <div className="space-y-2">
              {faqs.map((faq, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-white/6 overflow-hidden"
                  style={{ background: "rgba(255,255,255,0.02)" }}
                >
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full flex items-center justify-between px-5 py-4 text-left"
                  >
                    <span className="text-sm font-semibold text-white/70">{faq.q}</span>
                    <span className="text-white/25 text-lg leading-none shrink-0 ml-4">
                      {openFaq === i ? "−" : "+"}
                    </span>
                  </button>
                  {openFaq === i && (
                    <div className="px-5 pb-4 border-t border-white/6 pt-3">
                      <p className="text-sm text-white/40 leading-relaxed">{faq.a}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
