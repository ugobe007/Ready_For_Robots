/**
 * FAQ — Frequently Asked Questions
 * Standalone page linked from the hamburger menu
 */
import { useState } from "react";
import { ChevronDown } from "lucide-react";
import Header from "@/components/Header";
import { useScoutChat } from "@/components/ScoutChat";

const faqs = [
  {
    category: "How it works",
    items: [
      {
        q: "How does ReadyForRobots find buying signals?",
        a: "SCOUT monitors 150+ sources continuously — job boards, earnings calls, press releases, OSHA filings, real estate permits, and industry news. It detects patterns that indicate a company is ready to invest in automation.",
      },
      {
        q: "How quickly does SCOUT act on new signals?",
        a: "Signals are detected and scored within minutes. Outreach drafts are ready within the hour. In Auto mode, approved actions are sent within 24 hours of signal detection.",
      },
      {
        q: "What sources does SCOUT monitor?",
        a: "Job postings (warehouse, logistics, manufacturing roles), SEC filings and earnings call transcripts, OSHA incident reports, commercial real estate permits, press releases, LinkedIn company updates, and industry trade publications — over 150 sources in total.",
      },
    ],
  },
  {
    category: "Fit & coverage",
    items: [
      {
        q: "What types of robots does this work for?",
        a: "Any robot category with a B2B sales motion: warehouse AMRs, service robots, industrial arms, cleaning robots, food processing automation, healthcare robots, and more. You tell us your category and SCOUT tunes the signals accordingly.",
      },
      {
        q: "Does it work for partnership deals, not just direct sales?",
        a: "Yes. SCOUT identifies both direct sales opportunities and strategic partnership targets — distributors, system integrators, and channel partners who are actively expanding their automation portfolio.",
      },
      {
        q: "What company sizes does SCOUT target?",
        a: "SCOUT works across company sizes, from mid-market operators (500–5,000 employees) to enterprise. You can configure minimum employee count, revenue range, and geography to match your ideal customer profile.",
      },
    ],
  },
  {
    category: "Getting started",
    items: [
      {
        q: "Do I need to sign up to see results?",
        a: "No. Enter your company URL on the homepage and SCOUT will show you a sample of matched opportunities immediately — no account required. You only sign up when you want to act on them.",
      },
      {
        q: "How is this different from a lead list?",
        a: "A lead list gives you names. ReadyForRobots gives you timing, context, and a reason to reach out. Every opportunity includes the exact signal that triggered it, a fit score, and a drafted outreach message — so you reach the right buyer at the right moment.",
      },
      {
        q: "How long does onboarding take?",
        a: "Most customers are live within 48 hours. You share your robot category, ideal customer profile, and any existing CRM data. SCOUT calibrates to your ICP and begins surfacing opportunities immediately.",
      },
    ],
  },
  {
    category: "Outreach & automation",
    items: [
      {
        q: "Does SCOUT send emails automatically?",
        a: "In Assisted mode, SCOUT drafts every message and you approve before sending. In Auto mode, SCOUT sends on your behalf within configurable guardrails — you set the rules, SCOUT executes. You can switch modes at any time.",
      },
      {
        q: "Can I edit the outreach drafts before they go out?",
        a: "Always. Every draft is editable before sending. SCOUT learns from your edits over time and improves future drafts to match your voice and preferences.",
      },
      {
        q: "Does SCOUT handle follow-ups?",
        a: "Yes. SCOUT tracks reply status, detects intent signals in responses, and schedules follow-ups at the optimal time. It knows when to re-engage and why — and surfaces that context to your team.",
      },
    ],
  },
];

export default function FAQ() {
  const [openItem, setOpenItem] = useState<string | null>(null);
  const { openChat } = useScoutChat();

  const toggle = (key: string) => setOpenItem(openItem === key ? null : key);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      {/* Page header */}
      <section className="pt-28 pb-12 px-6">
        <div className="max-w-3xl mx-auto">
          <p
            className="text-[10px] font-bold uppercase tracking-[0.2em] mb-4"
            style={{ color: "#a78bfa" }}
          >
            FAQ
          </p>
          <h1
            className="font-extrabold text-white mb-4"
            style={{
              fontSize: "clamp(2rem, 4vw, 3rem)",
              fontFamily: "'Sora', system-ui, sans-serif",
              lineHeight: 1.1,
            }}
          >
            Frequently asked questions
          </h1>
          <p className="text-white/50 text-base max-w-xl" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            Can't find what you're looking for?{" "}
            <button
              onClick={openChat}
              className="underline underline-offset-2 transition-colors hover:text-white/80"
              style={{ color: "#FFB000" }}
            >
              Ask SCOUT directly
            </button>
          </p>
        </div>
      </section>

      {/* FAQ categories */}
      <section className="flex-1 px-6 pb-20">
        <div className="max-w-3xl mx-auto flex flex-col gap-12">
          {faqs.map((cat) => (
            <div key={cat.category}>
              <p
                className="text-[10px] font-bold uppercase tracking-[0.18em] mb-4"
                style={{ color: "#03DAC5" }}
              >
                {cat.category}
              </p>
              <div
                className="flex flex-col divide-y"
                style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}
              >
                {cat.items.map((item) => {
                  const key = `${cat.category}-${item.q}`;
                  const isOpen = openItem === key;
                  return (
                    <div key={key} style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                      <button
                        onClick={() => toggle(key)}
                        className="w-full flex items-center justify-between gap-4 py-4 text-left transition-colors hover:text-white"
                        style={{ color: isOpen ? "#fff" : "rgba(255,255,255,0.75)", fontFamily: "'Inter', system-ui, sans-serif" }}
                      >
                        <span className="text-sm font-semibold leading-snug">{item.q}</span>
                        <ChevronDown
                          className="shrink-0 h-4 w-4 transition-transform duration-200"
                          style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0deg)", color: "#a78bfa" }}
                        />
                      </button>
                      {isOpen && (
                        <p
                          className="pb-5 text-sm leading-relaxed"
                          style={{ color: "rgba(255,255,255,0.5)", fontFamily: "'Inter', system-ui, sans-serif" }}
                        >
                          {item.a}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="px-6 pb-16">
        <div
          className="max-w-3xl mx-auto rounded-2xl px-8 py-10 flex flex-col sm:flex-row items-center justify-between gap-6"
          style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.2)" }}
        >
          <div>
            <p className="text-white font-bold text-lg mb-1" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              Ready to see it in action?
            </p>
            <p className="text-white/40 text-sm" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              No signup required. Results in seconds.
            </p>
          </div>
          <button
            onClick={openChat}
            className="shrink-0 inline-flex items-center gap-2 font-bold px-6 py-3 rounded-xl transition-all hover:-translate-y-0.5"
            style={{ color: "#FFB000", border: "1.5px solid rgba(255,176,0,0.55)", background: "transparent", fontFamily: "'Inter', system-ui, sans-serif" }}
          >
            Activate Pipeline
          </button>
        </div>
      </section>
    </div>
  );
}
