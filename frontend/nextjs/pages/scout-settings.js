import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import RrSiteLayout from '../components/RrSiteLayout';
import { useAuth } from './_app';
import { authHeader } from '../lib/supabase';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

export default function ScoutSettingsPage() {
  const router = useRouter();
  const { session, loading } = useAuth();
  const API = getApiBase();
  const [settings, setSettings] = useState({ target_verticals: '', territory: '', autonomy_level: 'copilot' });
  const [status, setStatus] = useState('');

  useEffect(() => {
    if (loading) return;
    if (!session) {
      router.replace('/login');
      return;
    }
    fetch(`${API}/api/user/settings`, liveFetchInit({ headers: authHeader(session.access_token) }))
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return;
        setSettings((current) => ({
          ...current,
          target_verticals: data.target_verticals || data.targetVerticals || '',
          territory: data.territory || '',
          autonomy_level: data.autonomy_level || data.autonomyLevel || 'copilot',
        }));
      })
      .catch(() => {});
  }, [loading, session?.access_token]);

  async function save(e) {
    e.preventDefault();
    setStatus('Saving…');
    try {
      const response = await fetch(`${API}/api/user/settings`, liveFetchInit({
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authHeader(session.access_token) },
        body: JSON.stringify(settings),
      }));
      if (!response.ok) throw new Error('Save failed');
      setStatus('SCOUT settings saved.');
    } catch {
      setStatus('Could not save settings yet.');
    }
  }

  return (
    <RrSiteLayout active="scout-settings">
      <Head><title>SCOUT Settings | Ready For Robots</title></Head>
      <main className="scout-page px-4 py-12">
        <form onSubmit={save} className="max-w-3xl mx-auto scout-card p-6 space-y-5">
          <div>
            <p className="scout-kicker">Preferences</p>
            <h1 className="text-4xl font-black text-white">SCOUT settings</h1>
            <p className="text-slate-300 text-sm mt-2">Tune the verticals, territory, and autonomy level SCOUT should prioritize.</p>
          </div>
          <label className="block text-sm text-slate-300">
            Target verticals
            <input className="scout-input mt-2 w-full" value={settings.target_verticals} onChange={(e) => setSettings({ ...settings, target_verticals: e.target.value })} placeholder="Logistics, hospitality, healthcare" />
          </label>
          <label className="block text-sm text-slate-300">
            Territory
            <input className="scout-input mt-2 w-full" value={settings.territory} onChange={(e) => setSettings({ ...settings, territory: e.target.value })} placeholder="US Southwest, Nevada, California" />
          </label>
          <label className="block text-sm text-slate-300">
            Autonomy level
            <select className="scout-input mt-2 w-full" value={settings.autonomy_level} onChange={(e) => setSettings({ ...settings, autonomy_level: e.target.value })}>
              <option value="monitor">Monitor only</option>
              <option value="copilot">Copilot recommendations</option>
              <option value="autopilot">Autopilot draft actions</option>
            </select>
          </label>
          <div className="flex items-center gap-4">
            <button className="scout-btn-primary">Save settings</button>
            {status && <span className="text-sm text-amber-300">{status}</span>}
          </div>
        </form>
      </main>
    </RrSiteLayout>
  );
}
