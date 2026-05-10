import { useState } from 'react';
import Head from 'next/head';
import RrSiteLayout from '../components/RrSiteLayout';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

const tiers = [
  { name: 'Scout', price: 'Waitlist', copy: 'For founders validating early robotics demand.', features: ['URL scan results', 'Signal feed', 'SCOUT chat assistant'] },
  { name: 'Pipeline', price: 'Pilot', copy: 'For GTM teams building repeatable robot-ready pipeline.', features: ['CRM-backed pipeline', 'Proposal generation', 'Outreach drafts'] },
  { name: 'Autopilot', price: 'Partner', copy: 'For teams that want SCOUT monitoring and action routing.', features: ['Always-on signal monitoring', 'Autonomous next actions', 'Team reporting'] },
];

export default function PricingPage() {
  const API = getApiBase();
  const [form, setForm] = useState({ email: '', name: '', company: '', useCase: '' });
  const [status, setStatus] = useState('');

  async function submit(e) {
    e.preventDefault();
    setStatus('Joining…');
    try {
      const response = await fetch(`${API}/api/waitlist`, liveFetchInit({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, source: 'pricing' }),
      }));
      if (!response.ok) throw new Error('Waitlist request failed');
      setStatus('You’re on the waitlist. SCOUT will follow up soon.');
      setForm({ email: '', name: '', company: '', useCase: '' });
    } catch {
      setStatus('Could not join the waitlist. Check your email and try again.');
    }
  }

  return (
    <RrSiteLayout active="pricing">
      <Head><title>Pricing | Ready For Robots</title></Head>
      <main className="scout-page px-4 py-12">
        <div className="max-w-6xl mx-auto">
          <p className="scout-kicker">Pricing</p>
          <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight mb-4">Start with SCOUT</h1>
          <p className="text-slate-300 max-w-2xl mb-8">Ready For Robots is opening pilots for teams that sell, deploy, or partner around robotics automation.</p>
          <div className="grid md:grid-cols-3 gap-5 mb-10">
            {tiers.map((tier) => (
              <section key={tier.name} className="scout-card p-6">
                <p className="scout-kicker">{tier.price}</p>
                <h2 className="text-2xl font-bold text-white mb-2">{tier.name}</h2>
                <p className="text-sm text-slate-300 mb-5">{tier.copy}</p>
                <ul className="space-y-2 text-sm text-slate-300">
                  {tier.features.map((feature) => <li key={feature}>✓ {feature}</li>)}
                </ul>
              </section>
            ))}
          </div>
          <form onSubmit={submit} className="scout-card p-6 grid md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <h2 className="text-2xl font-bold text-white">Join the pilot waitlist</h2>
              <p className="text-sm text-slate-400">Tell SCOUT what robotics market you want to pursue.</p>
            </div>
            <input className="scout-input" required type="email" aria-label="Email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input className="scout-input" aria-label="Name" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input className="scout-input" aria-label="Company" placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <input className="scout-input" aria-label="Robotics use case" placeholder="Robotics use case" value={form.useCase} onChange={(e) => setForm({ ...form, useCase: e.target.value })} />
            <button className="scout-btn-primary md:w-fit">Join waitlist</button>
            {status && <p className="text-sm text-amber-300 self-center">{status}</p>}
          </form>
        </div>
      </main>
    </RrSiteLayout>
  );
}
