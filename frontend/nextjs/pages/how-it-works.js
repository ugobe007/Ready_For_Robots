import Head from 'next/head';
import Link from 'next/link';
import RrSiteLayout from '../components/RrSiteLayout';

const steps = [
  { title: 'Identify', copy: 'SCOUT watches public buying signals, company context, and automation-fit clues.' },
  { title: 'Develop', copy: 'The six-factor score ranks readiness, use case fit, ROI pressure, deployment size, problem clarity, and customer value.' },
  { title: 'Connect', copy: 'Pipeline actions turn qualified signals into outreach drafts, proposals, and next best actions.' },
];

export default function HowItWorksPage() {
  return (
    <RrSiteLayout active="how-it-works">
      <Head><title>How SCOUT Works | Ready For Robots</title></Head>
      <main className="scout-page px-4 py-12">
        <div className="max-w-5xl mx-auto">
          <p className="scout-kicker">SCOUT workflow</p>
          <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight mb-4">Identify → Develop → Connect</h1>
          <p className="text-slate-300 max-w-2xl mb-10">Ready For Robots converts scattered market signals into a robotics GTM workflow that sales teams can trust.</p>
          <div className="grid md:grid-cols-3 gap-5 mb-10">
            {steps.map((step, index) => (
              <section key={step.title} className="scout-card p-6">
                <div className="scout-score-orb mb-5">{index + 1}</div>
                <h2 className="text-2xl font-bold text-white mb-2">{step.title}</h2>
                <p className="text-sm text-slate-300 leading-relaxed">{step.copy}</p>
              </section>
            ))}
          </div>
          <div className="scout-card p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
            <div>
              <h2 className="text-2xl font-bold text-white">Try the scan flow</h2>
              <p className="text-slate-300 text-sm">Paste a URL and let SCOUT produce the first readiness readout.</p>
            </div>
            <Link href="/results" className="scout-btn-primary">Scan company</Link>
          </div>
        </div>
      </main>
    </RrSiteLayout>
  );
}
