/**
 * Pricing — ReadyForRobots (Precision Intelligence light theme)
 */
import { CheckCircle2, ArrowRight, Zap, Shield, Cpu, HelpCircle, ChevronDown } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { useLocation, Link } from "wouter";
import { useState } from "react";

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "",
    tagline: "Start browsing the live pipeline — no card required",
    accent: "emerald" as const,
    icon: Zap,
    cta: "Start free workspace",
    ctaAction: "signup",
    features: [
      "URL scan and buyer matching",
      "10 live pipeline leads (HOT / WARM / monitor mix)",
      "Lead score and why-now context",
      "Save up to 5 leads to your workspace",
      "Outreach draft previews",
      "Daily newsletter and market signal brief",
    ],
    limitations: ["No SIGNAL research feed", "HubSpot connect only — auto-sync on Pro"],
    highlight: false,
  },
  {
    name: "Pro",
    price: "$49",
    period: "/month",
    tagline: "Full pipeline + cited research for active sellers",
    accent: "amber" as const,
    icon: Cpu,
    cta: "Upgrade to Pro",
    ctaAction: "trial",
    features: [
      "Everything in Free",
      "Unlimited saved leads",
      "SIGNAL research updates on WARM and HOT leads",
      "HubSpot auto-sync (push score, trigger, brief)",
      "Pipeline Kanban board",
      "Improved outreach drafts by industry",
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
    accent: "slate" as const,
    icon: Shield,
    cta: "Talk to sales",
    ctaAction: "sales",
    features: [
      "Everything in Pro",
      "Priority SIGNAL research coverage",
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
    a: "No. Pro and Premium are month-to-month when billing is enabled. The Free workspace stays free — no card required to browse and save up to 5 leads.",
  },
  {
    q: "Which plan should I start with?",
    a: "Start on Free — scan URLs, browse 10 live pipeline leads, and save your first 5 accounts. Upgrade to Pro when you need cited SIGNAL research and HubSpot auto-sync.",
  },
  {
    q: "How do you define a 'matched prospect'?",
    a: "A company that has at least one active buying signal in your robot category, scores 60+ on our composite model, and is in your target geography and company size range.",
  },
  {
    q: "Can I use this with my existing CRM?",
    a: "Yes. Signal sits on top of your stack. Free workspace can connect HubSpot manually; Pro and Premium add automatic sync (push qualified leads with score, trigger, and brief). No CRM? Use the native Signal workspace.",
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
    q: "How is ReadyForRobots different from Reevo or other revenue operating systems?",
    a: "Reevo and similar platforms ($80M+ funded) sell one AI-native stack that replaces CRM, engagement, and intelligence—you migrate tools and retrain the team. ReadyForRobots is not a revenue OS. We wedge in for robot sales: live buyer signals, HOT/WARM timing, pipeline_action (what to do next), robot_types_needed (what SKU to pitch), outreach drafts, and HubSpot sync. Keep HubSpot or use our native pipeline—no rip-and-replace. See /compare.",
  },
  {
    q: "How is this different from Explee, Apollo, or other company search tools?",
    a: "Those tools help you find accounts and export contacts—we help robot sales teams run the full funnel. ReadyForRobots surfaces buyers showing live robot intent (capex, labor, deployment signals), ranks HOT/WARM timing, tells you which robot categories to pitch, and advances deals in our pipeline or HubSpot. You are not buying another stale list; you are automating a sales pipeline built for robotics. See our full comparison at /compare.",
  },
  {
    q: "Do you help with robot deployment services?",
    a: "Yes. Customer support, technical support, integration, and installation support can be arranged as add-on services through qualified local partners.",
  },
];

const accentStyles = {
  emerald: { icon: "text-emerald-600", bg: "bg-emerald-50 border-emerald-100", check: "text-emerald-600" },
  amber: { icon: "text-amber-600", bg: "bg-amber-50 border-amber-100", check: "text-amber-600" },
  slate: { icon: "text-slate-600", bg: "bg-slate-50 border-slate-200", check: "text-slate-600" },
};

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
        ? `/signup?plan=pro&next=${next}`
        : `/signup?plan=${plan}&next=${next}`;
    setLocation(query);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <PageHeroDark
        maxWidthClass="max-w-5xl"
        eyebrow="Pricing"
        title="Simple pricing for robot sales teams"
        description={
          <>
            <span className="font-bold uppercase tracking-widest text-emerald-400">Signal</span>
            {" — robotics prospecting, qualifying, and outreach synced to "}
            <span className="font-bold text-amber-400">HubSpot</span>
            {" or your CRM. Paid billing is rolling out — every plan starts with a free workspace."}
          </>
        }
        innerClassName="pb-8 text-center [&_.page-hero-title]:mx-auto [&_.page-hero-description]:mx-auto"
      />
      <div className="page-hero-fade" aria-hidden />

      <main className="flex-1 pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs text-gray-500 max-w-lg mx-auto">
              Create an account, browse the pipeline, then upgrade when you are ready.{" "}
              <Link href="/compare" className="text-emerald-700 font-semibold hover:underline">
                Compare vs data tools
              </Link>
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-16">
            {tiers.map((tier) => {
              const Icon = tier.icon;
              const accent = accentStyles[tier.accent];
              return (
                <div
                  key={tier.name}
                  className={`rounded-2xl border flex flex-col relative overflow-hidden transition-all hover:-translate-y-1 bg-white ${
                    tier.highlight ? "border-emerald-300 shadow-lg shadow-emerald-100/50 ring-1 ring-emerald-200" : "border-gray-200 shadow-sm"
                  }`}
                >
                  {tier.badge && (
                    <div className="absolute top-0 left-0 right-0 text-center py-1.5 text-[10px] font-bold uppercase tracking-widest bg-emerald-600 text-white">
                      {tier.badge}
                    </div>
                  )}

                  <div className={`p-7 flex flex-col flex-1 ${tier.badge ? "pt-10" : ""}`}>
                    <div className="flex items-center gap-2.5 mb-4">
                      <div className={`h-8 w-8 rounded-lg flex items-center justify-center border ${accent.bg}`}>
                        <Icon className={`h-4 w-4 ${accent.icon}`} />
                      </div>
                      <span className="font-bold text-gray-900 text-sm">{tier.name}</span>
                    </div>

                    <div className="mb-2">
                      <span className="font-display font-extrabold text-gray-900 text-4xl leading-none">{tier.price}</span>
                      {tier.period && <span className="text-sm text-gray-500 ml-1">{tier.period}</span>}
                    </div>
                    <p className="text-xs text-gray-500 mb-6">{tier.tagline}</p>

                    <button
                      onClick={() => handleCta(tier.ctaAction, tier.name)}
                      className={`w-full flex items-center justify-center gap-2 text-sm font-semibold py-3 rounded-xl mb-7 transition-all hover:-translate-y-0.5 ${
                        tier.highlight
                          ? "bg-emerald-600 text-white hover:bg-emerald-700 shadow-md shadow-emerald-200"
                          : "bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100"
                      }`}
                    >
                      {tier.cta} <ArrowRight className="h-3.5 w-3.5" />
                    </button>

                    <div className="flex flex-col gap-2.5 flex-1">
                      {tier.features.map((f) => (
                        <div key={f} className="flex items-start gap-2.5">
                          <CheckCircle2 className={`h-3.5 w-3.5 shrink-0 mt-0.5 ${accent.check}`} />
                          <span className="text-xs text-gray-600">{f}</span>
                        </div>
                      ))}
                      {tier.limitations.map((l) => (
                        <div key={l} className="flex items-start gap-2.5 opacity-50">
                          <div className="h-3.5 w-3.5 shrink-0 mt-0.5 flex items-center justify-center">
                            <div className="h-px w-3 bg-gray-300" />
                          </div>
                          <span className="text-xs text-gray-400">{l}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <section className="mb-16 rounded-2xl border border-amber-200 bg-amber-50/50 p-6">
            <div className="mb-5 flex items-start gap-4">
              <HelpCircle className="h-5 w-5 shrink-0 mt-0.5 text-amber-600" />
              <div>
                <p className="text-sm font-semibold mb-1 text-amber-800">Optional support services</p>
                <p className="text-xs text-gray-600 leading-relaxed max-w-3xl">
                  Some customers need help beyond software. ReadyForRobots can coordinate additional support for customer success, technical setup, integration planning, and robot installation through vetted local partners. Service pricing is scoped separately based on need.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              {supportServices.map((service) => (
                <div key={service.title} className="rounded-xl border border-gray-200 bg-white p-4">
                  <p className="text-xs font-bold mb-2 text-amber-700">{service.title}</p>
                  <p className="text-[11px] leading-relaxed text-gray-600">{service.copy}</p>
                </div>
              ))}
            </div>
          </section>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 flex items-start gap-4 mb-16 shadow-sm">
            <Shield className="h-5 w-5 shrink-0 mt-0.5 text-emerald-600" />
            <div>
              <p className="text-sm font-semibold text-gray-900 mb-1">No risk. No lock-in.</p>
              <p className="text-xs text-gray-600 leading-relaxed">
                Starter, Pro, and Premium are designed to be easy to try and easy to grow into. Additional service work is optional and scoped separately from the software subscription.
              </p>
            </div>
          </div>

          <div id="faq">
            <p className="section-eyebrow mb-3">Questions</p>
            <h2 className="font-display font-extrabold text-gray-900 mb-8 text-[clamp(1.4rem,2.5vw,1.8rem)]">
              Pricing FAQ
            </h2>
            <div className="space-y-2">
              {faqs.map((faq, i) => (
                <div key={i} className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full flex items-center justify-between px-5 py-4 text-left"
                  >
                    <span className="text-sm font-semibold text-gray-800">{faq.q}</span>
                    <ChevronDown className={`h-4 w-4 text-gray-400 shrink-0 ml-4 transition-transform ${openFaq === i ? "rotate-180" : ""}`} />
                  </button>
                  {openFaq === i && (
                    <div className="px-5 pb-4 border-t border-gray-100 pt-3">
                      <p className="text-sm text-gray-600 leading-relaxed">{faq.a}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
