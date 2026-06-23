/**
 * Pricing — ReadyForRobots
 * Three-tier pricing: Starter · Pro · Premium
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 */
import { CheckCircle2, ArrowRight, Zap, Shield, Cpu, HelpCircle } from "lucide-react";
import Header from "@/components/Header";
import { Link, useLocation } from "wouter";
import { useState } from "react";

const tiers = [
  {
    name: "Starter",
    price: "$19",
    period: "/month",
    tagline: "Signal — start finding robot-ready buyers",
    color: "#03DAC5",
    icon: Zap,
    cta: "Start Starter",
    ctaAction: "signup",
    features: [
      "URL scan and buyer matching",
      "Starter pipeline view",
      "Signal type identification",
      "Lead score and why-now context",
      "Outreach draft previews",
      "Daily newsletter and market signal brief",
    ],
    limitations: [
      "No Signal research feed",
      "Manual Signal workflow",
    ],
    highlight: false,
  },
  {
    name: "Pro",
    price: "$49",
    period: "/month",
    tagline: "Full pipeline + Signal workspace for active sellers",
    color: "#FFB000",
    icon: Cpu,
    cta: "Start Pro",
    ctaAction: "trial",
    features: [
      "Everything in Starter",
      "Expanded lead matching",
      "Research agent updates on WARM and HOT leads",
      "Pipeline Kanban board",
      "Improved outreach drafts by industry",
      "CRM profile enrichment",
      "Weekly pipeline and research summary",
    ],
    limitations: [],
    highlight: true,
    badge: "Most popular",
  },
  {
    name: "Premium",
    price: "$129",
    period: "/month",
    tagline: "For teams ready to act on more accounts",
    color: "#a78bfa",
    icon: Shield,
    cta: "Start Premium",
    ctaAction: "sales",
    features: [
      "Everything in Pro",
      "50 live pipeline leads",
      "Priority Signal research coverage",
      "Team workflow + priority support",
      "Premium signal monitoring",
      "Advanced CRM-ready lead context",
      "Priority support queue",
      "Monthly strategy review prompts",
    ],
    limitations: [],
    highlight: false,
  },
];

const supportServices = [
  {
    title: "Customer support",
    copy: "Help turning signals into workflows, outreach steps, and account review habits.",
  },
  {
    title: "Technical support",
    copy: "Assistance with CRM setup, data handoff, scoring questions, and operational troubleshooting.",
  },
  {
    title: "Robot integration",
    copy: "Introductions to local implementation partners for site review, system integration, and deployment planning.",
  },
  {
    title: "Installation support",
    copy: "Optional help coordinating qualified local vendors for installation, training, and post-install checks.",
  },
];

const faqs = [
  {
    q: "Is there a contract or commitment?",
    a: "No. Starter, Pro, and Premium are month-to-month. You can cancel any time.",
  },
  {
    q: "Which plan should I start with?",
    a: "Starter is best for testing the workflow. Pro is best for active sales teams. Premium is best when you want more research coverage, team workflow, and priority support.",
  },
  {
    q: "How do you define a 'matched prospect'?",
    a: "A company that has at least one active buying signal in your robot category, scores 60+ on our composite model, and is in your target geography and company size range.",
  },
  {
    q: "Can I use this with my existing CRM?",
    a: "Yes — that is the point. Signal is ReadyForRobots' pipeline service on top of your stack. Pro and Premium add HubSpot sync (push qualified leads with score, trigger, and brief). No CRM? Use the native Signal workspace. Salesforce and Pipedrive use the same sync pattern—shipping after HubSpot.",
  },
  {
    q: "What if we use Salesforce or Pipedrive instead of HubSpot?",
    a: "HubSpot sync is live today on Pro and Premium. Salesforce and Pipedrive are next on the roadmap—the same OAuth push model as HubSpot. Until then, run prospecting, qualifying, and outreach in Signal, then export leads and briefs into your CRM. You never have to switch systems of record.",
  },
  {
    q: "Is ReadyForRobots a HubSpot competitor?",
    a: "No. HubSpot is your system of record. Signal is robotics intelligence on top—live signals, scored timing, and outreach—synced into HubSpot when you upgrade. Your team closes in the CRM you already run.",
  },
  {
    q: "How is ReadyForRobots different from an AI revenue OS?",
    a: "Revenue operating systems replace CRM, engagement, and intelligence in one platform—you migrate tools and retrain the team. ReadyForRobots is not a revenue OS. Signal adds a robotics wedge: find robot-ready buyers from live signals, score timing, run outreach, and push context into HubSpot or your CRM. No stack rip-and-replace.",
  },
  {
    q: "Do you help with robot deployment services?",
    a: "Yes. Customer support, technical support, integration, and installation support can be arranged as add-on services through qualified local partners.",
  },
];

export default function Pricing() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [, setLocation] = useLocation();

  const handleCta = (action: string, tier: string) => {
    const plan = tier.toLowerCase();
    if (action === "sales") {
      window.location.href = "mailto:sales@readyforrobots.com?subject=Premium%20workspace%20inquiry";
      return;
    }
    const next = encodeURIComponent("/pipeline");
    const query =
      action === "trial"
        ? `/signup?plan=pro&trial=1&next=${next}`
        : `/signup?plan=${plan}&next=${next}`;
    setLocation(query);
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
              Simple pricing for robot sales teams
            </h1>
            <p className="text-sm text-white/40 max-w-xl mx-auto">
              <span className="font-bold uppercase tracking-[0.1em]" style={{ color: "#c4b5fd" }}>Signal</span>
              {" — robotics prospecting, qualifying, and outreach synced to "}
              <span style={{ color: "#FFB000", fontWeight: 700 }}>HubSpot</span>
              {" or your CRM."}
            </p>
            <p className="mt-3 text-xs text-white/30 max-w-lg mx-auto">
              Paid billing is rolling out — every plan starts with a free workspace. Create an account, browse the pipeline, then upgrade when you are ready.
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

          {/* Services note */}
          <section className="mb-16 rounded-2xl border border-amber-300/15 p-6" style={{ background: "rgba(255,176,0,0.045)" }}>
            <div className="mb-5 flex items-start gap-4">
              <HelpCircle className="h-5 w-5 shrink-0 mt-0.5" style={{ color: "#FFB000" }} />
              <div>
                <p className="text-sm font-semibold mb-1" style={{ color: "#FFB000" }}>Optional support services</p>
                <p className="text-xs text-white/38 leading-relaxed max-w-3xl">
                  Some customers need help beyond software. ReadyForRobots can coordinate additional support for customer success, technical setup, integration planning, and robot installation through vetted local partners. Service pricing is scoped separately based on need.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              {supportServices.map((service) => (
                <div key={service.title} className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(13,5,32,0.5)" }}>
                  <p className="text-xs font-bold mb-2" style={{ color: "#FFB000" }}>{service.title}</p>
                  <p className="text-[11px] leading-relaxed text-white/38">{service.copy}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Comparison note */}
          <div
            className="rounded-2xl border border-white/6 p-6 flex items-start gap-4 mb-16"
            style={{ background: "rgba(255,255,255,0.02)" }}
          >
            <Shield className="h-5 w-5 shrink-0 mt-0.5" style={{ color: "#a78bfa" }} />
            <div>
              <p className="text-sm font-semibold text-white/70 mb-1">No risk. No lock-in.</p>
              <p className="text-xs text-white/35 leading-relaxed">
                Starter, Pro, and Premium are designed to be easy to try and easy to grow into. Additional service work is optional and scoped separately from the software subscription.
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
