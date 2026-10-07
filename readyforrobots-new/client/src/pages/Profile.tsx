import { useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import SiteFooter from "@/components/layout/SiteFooter";
import AutonomyDial from "@/components/AutonomyDial";
import HubSpotConnectPanel, {
  type HubSpotIntegrationStatus,
} from "@/components/HubSpotConnectPanel";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";
import { clearPendingNext } from "@/lib/authNext";
import type { AutonomyMode } from "@/types/readyForRobots";

const PERSONA_TRAITS = [
  { id: "insightful", label: "Insightful comments" },
  { id: "industry_refs", label: "Industry references" },
  { id: "robot_examples", label: "Robot examples" },
  { id: "humor", label: "Slight humor, professional" },
  { id: "inquisitive", label: "Inquisitive" },
  { id: "whitepapers", label: "Whitepapers/studies" },
];

export default function Profile() {
  const { session, loading } = useAuth();
  const [me, setMe] = useState<{
    email?: string;
    display_name?: string | null;
    entitlements?: {
      display_name?: string;
      plan?: string;
      saved_count?: number;
      saved_limit?: number | null;
      pipeline_limit?: number;
      features?: { research_updates?: boolean; unlimited_saves?: boolean };
      upgrade_url?: string;
    };
  } | null>(null);
  const [settings, setSettings] = useState({
    scout_automation_level: "assisted" as AutonomyMode,
    reply_forwarding_enabled: true,
    reply_forward_email: "",
    scout_message_style: "",
    scout_preferred_channel: "email",
    scout_meeting_preference: "",
    scout_default_cc: "",
    scout_default_bcc: "",
    scout_persona_traits: "",
    scout_collateral_policy: "selective",
    scout_collateral_links: "",
    scout_background_briefing_enabled: true,
  });
  const [counts, setCounts] = useState({ saved: 0, reports: 0, lists: 0 });
  const [hubspotStatus, setHubspotStatus] =
    useState<HubSpotIntegrationStatus | null>(null);
  const [hubspotLoading, setHubspotLoading] = useState(false);
  const [err, setErr] = useState("");
  const [savingSettings, setSavingSettings] = useState(false);

  useEffect(() => {
    if (loading || !session?.access_token) return;
    const t = session.access_token;
    const base = getApiBase();
    (async () => {
      setErr("");
      try {
        setHubspotLoading(true);
        const [rMe, rSettings, rSaved, rReports, rLists, rIntegrations] =
          await Promise.all([
            fetch(
              `${base}/api/user/me`,
              liveFetchInit({ headers: { ...authHeader(t) } })
            ),
            fetch(
              `${base}/api/user/settings`,
              liveFetchInit({ headers: { ...authHeader(t) } })
            ),
            fetch(
              `${base}/api/user/saved`,
              liveFetchInit({ headers: { ...authHeader(t) } })
            ),
            fetch(
              `${base}/api/user/reports`,
              liveFetchInit({ headers: { ...authHeader(t) } })
            ),
            fetch(
              `${base}/api/user/lists`,
              liveFetchInit({ headers: { ...authHeader(t) } })
            ),
            fetch(
              `${base}/api/integrations`,
              liveFetchInit({ headers: { ...authHeader(t) } })
            ),
          ]);
        if (!rMe.ok) throw new Error(await rMe.text());
        setMe(await rMe.json());
        if (rSettings.ok) {
          const next = await rSettings.json();
          setSettings({
            scout_automation_level: next.scout_automation_level || "assisted",
            reply_forwarding_enabled: next.reply_forwarding_enabled ?? true,
            reply_forward_email: next.reply_forward_email || "",
            scout_message_style: next.scout_message_style || "",
            scout_preferred_channel: next.scout_preferred_channel || "email",
            scout_meeting_preference: next.scout_meeting_preference || "",
            scout_default_cc: next.scout_default_cc || "",
            scout_default_bcc: next.scout_default_bcc || "",
            scout_persona_traits: next.scout_persona_traits || "",
            scout_collateral_policy:
              next.scout_collateral_policy || "selective",
            scout_collateral_links: next.scout_collateral_links || "",
            scout_background_briefing_enabled:
              next.scout_background_briefing_enabled ?? true,
          });
        }
        const saved = rSaved.ok
          ? ((await rSaved.json()) as unknown[]).length
          : undefined;
        const reports = rReports.ok
          ? ((await rReports.json()) as unknown[]).length
          : undefined;
        const lists = rLists.ok
          ? ((await rLists.json()) as unknown[]).length
          : undefined;
        setCounts(c => ({
          saved: saved ?? c.saved,
          reports: reports ?? c.reports,
          lists: lists ?? c.lists,
        }));
        if (rIntegrations.ok) {
          const payload = (await rIntegrations.json()) as {
            integrations?: Array<{
              provider: string;
              connected?: boolean;
              entitled?: boolean;
              entitlement_message?: string | null;
              account_login?: string | null;
              account_name?: string | null;
            }>;
          };
          const hubspot = (payload.integrations || []).find(
            row => row.provider === "hubspot"
          );
          setHubspotStatus(
            hubspot
              ? {
                  connected: hubspot.connected,
                  entitled: hubspot.entitled,
                  entitlement_message: hubspot.entitlement_message,
                  account_login: hubspot.account_login,
                  account_name: hubspot.account_name,
                }
              : null
          );
        }
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Failed to load profile");
      } finally {
        setHubspotLoading(false);
      }
    })();
  }, [session, loading]);

  const saveSettings = async (patch: Partial<typeof settings>) => {
    if (!session?.access_token) return;
    const next = { ...settings, ...patch };
    setSettings(next);
    setSavingSettings(true);
    setErr("");
    try {
      const response = await fetch(
        `${getApiBase()}/api/user/settings`,
        liveFetchInit({
          method: "PUT",
          headers: {
            ...authHeader(session.access_token),
            "Content-Type": "application/json",
          },
          body: JSON.stringify(next),
        })
      );
      if (!response.ok) throw new Error(await response.text());
      const saved = await response.json();
      setSettings({
        scout_automation_level: saved.scout_automation_level || "assisted",
        reply_forwarding_enabled: saved.reply_forwarding_enabled ?? true,
        reply_forward_email: saved.reply_forward_email || "",
        scout_message_style: saved.scout_message_style || "",
        scout_preferred_channel: saved.scout_preferred_channel || "email",
        scout_meeting_preference: saved.scout_meeting_preference || "",
        scout_default_cc: saved.scout_default_cc || "",
        scout_default_bcc: saved.scout_default_bcc || "",
        scout_persona_traits: saved.scout_persona_traits || "",
        scout_collateral_policy: saved.scout_collateral_policy || "selective",
        scout_collateral_links: saved.scout_collateral_links || "",
        scout_background_briefing_enabled:
          saved.scout_background_briefing_enabled ?? true,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to save SIGNAL settings");
    } finally {
      setSavingSettings(false);
    }
  };

  const traitList = settings.scout_persona_traits
    .split(",")
    .map(x => x.trim())
    .filter(Boolean);
  const toggleTrait = (id: string) => {
    const next = traitList.includes(id)
      ? traitList.filter(x => x !== id)
      : [...traitList, id];
    void saveSettings({ scout_persona_traits: next.join(", ") });
  };

  if (!supabase) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center text-gray-500 bg-slate-50">
        <Header />
        <p>Supabase is not configured in this build.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 text-center text-gray-500 bg-slate-50">
        <Header />
        Loading…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center bg-slate-50">
        <Header />
        <p className="text-gray-600 mb-4">Sign in to view your workspace.</p>
        <Link href="/login" className="text-emerald-700 underline text-sm">
          Go to login
        </Link>
      </div>
    );
  }

  return (
    <div className="admin-workspace min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="flex-1 pt-28 pb-12 px-4 max-w-lg mx-auto w-full">
        <AdminNav />
        <h1 className="text-xl font-bold text-gray-900 mb-1">Your workspace</h1>
        <p className="text-xs text-gray-500 mb-6">
          Same data as before — powered by SIGNAL + FastAPI.
        </p>
        {err && (
          <p className="text-sm text-red-700 mb-4 border border-red-200 bg-red-50 rounded p-2">
            {err}
          </p>
        )}
        <div className="rounded-xl border border-gray-200 p-4 space-y-2 mb-6">
          <p className="text-[10px] uppercase tracking-widest text-gray-400">
            Signed in as
          </p>
          <p className="text-sm text-gray-900 font-medium">
            {me?.display_name || me?.email || session.user.email}
          </p>
          <p className="text-xs text-gray-500">{session.user.email}</p>
        </div>
        {me?.entitlements && (
          <div
            className="rounded-xl border border-emerald-400/20 p-4 mb-6 space-y-3"
            style={{ background: "rgba(5,150,105,0.06)" }}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-emerald-700/70">
                  Workspace plan
                </p>
                <p className="text-sm font-semibold text-gray-900 mt-0.5">
                  {me.entitlements.display_name || "Free workspace"}
                </p>
              </div>
              {me.entitlements.plan !== "paid" && (
                <Link
                  href={me.entitlements.upgrade_url || "/pricing"}
                  className="shrink-0 rounded-lg px-3 py-1.5 text-[10px] font-bold text-gray-900"
                  style={{ background: "#059669" }}
                >
                  Upgrade
                </Link>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="rounded-lg border border-gray-100 px-2.5 py-2">
                <p className="text-gray-400 uppercase text-[9px] tracking-wider">
                  Saved leads
                </p>
                <p className="font-mono font-bold text-emerald-700 mt-0.5">
                  {me.entitlements.saved_count ?? counts.saved}
                  {me.entitlements.saved_limit != null
                    ? ` / ${me.entitlements.saved_limit}`
                    : ""}
                </p>
              </div>
              <div className="rounded-lg border border-gray-100 px-2.5 py-2">
                <p className="text-gray-400 uppercase text-[9px] tracking-wider">
                  Pipeline
                </p>
                <p className="font-mono font-bold text-emerald-700 mt-0.5">
                  {me.entitlements.pipeline_limit ?? 10} leads
                </p>
              </div>
            </div>
            {!me.entitlements.features?.research_updates && (
              <p className="text-[10px] leading-relaxed text-gray-500">
                SIGNAL research feed unlocks on Pro.{" "}
                <Link
                  href="/pricing?reason=research"
                  className="text-emerald-600 hover:text-emerald-700"
                >
                  See pricing
                </Link>
              </p>
            )}
          </div>
        )}
        <div className="grid grid-cols-3 gap-2 mb-8">
          {[
            { n: counts.saved, l: "Saved" },
            { n: counts.reports, l: "Reports" },
            { n: counts.lists, l: "Lists" },
          ].map(x => (
            <div
              key={x.l}
              className="rounded-lg border border-gray-200 p-3 text-center"
            >
              <p className="text-lg font-mono font-bold text-emerald-600">
                {x.n}
              </p>
              <p className="text-[10px] text-gray-400 uppercase">{x.l}</p>
            </div>
          ))}
        </div>
        <div className="rounded-xl border border-gray-200 mb-6 overflow-hidden">
          <AutonomyDial
            mode={settings.scout_automation_level}
            onChange={mode =>
              void saveSettings({ scout_automation_level: mode })
            }
          />
          <div className="space-y-3 p-4">
            <label className="flex items-center justify-between gap-3 text-xs text-gray-500">
              Forward buyer replies to me
              <input
                type="checkbox"
                checked={settings.reply_forwarding_enabled}
                onChange={e =>
                  void saveSettings({
                    reply_forwarding_enabled: e.target.checked,
                  })
                }
              />
            </label>
            <input
              value={settings.reply_forward_email}
              onChange={e =>
                setSettings(s => ({
                  ...s,
                  reply_forward_email: e.target.value,
                }))
              }
              onBlur={() =>
                void saveSettings({
                  reply_forward_email: settings.reply_forward_email,
                })
              }
              placeholder={session.user.email || "Reply forwarding email"}
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-900 outline-none placeholder:text-gray-400"
            />
            <p className="text-[11px] text-gray-400">
              {savingSettings
                ? "Saving communication settings..."
                : "Outreach sends from the ReadyForRobots domain. Replies route back into your SIGNAL workflow and can be forwarded here."}
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-gray-200 mb-6 p-4 space-y-3">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-400">
              Outreach preferences
            </p>
            <p className="mt-1 text-xs leading-relaxed text-gray-500">
              Tell SIGNAL how you want to sound in outreach — tone, preferred
              next step, and who should be copied.
            </p>
          </div>
          <label className="block">
            <span className="mb-1 block text-[10px] uppercase tracking-widest text-gray-400">
              Communication style
            </span>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {PERSONA_TRAITS.map(trait => (
                <button
                  key={trait.id}
                  type="button"
                  onClick={() => toggleTrait(trait.id)}
                  className={`rounded-full border px-2 py-1 text-[10px] font-bold ${
                    traitList.includes(trait.id)
                      ? "border-amber-400 bg-amber-400/15 text-amber-100"
                      : "border-gray-200 bg-white text-gray-500"
                  }`}
                >
                  {trait.label}
                </button>
              ))}
            </div>
            <textarea
              value={settings.scout_message_style}
              onChange={e =>
                setSettings(s => ({
                  ...s,
                  scout_message_style: e.target.value,
                }))
              }
              onBlur={() =>
                void saveSettings({
                  scout_message_style: settings.scout_message_style,
                })
              }
              rows={4}
              placeholder="Example: concise, practical, warm, ask for a phone call quickly, avoid long email threads."
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-relaxed text-gray-900 outline-none placeholder:text-gray-400"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-[10px] uppercase tracking-widest text-gray-400">
              Preferred next step
            </span>
            <select
              value={settings.scout_preferred_channel}
              onChange={e =>
                void saveSettings({ scout_preferred_channel: e.target.value })
              }
              className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-900 outline-none"
            >
              <option value="email">Email conversation</option>
              <option value="phone">Phone call</option>
              <option value="meeting">Scheduled meeting</option>
            </select>
          </label>
          <input
            value={settings.scout_meeting_preference}
            onChange={e =>
              setSettings(s => ({
                ...s,
                scout_meeting_preference: e.target.value,
              }))
            }
            onBlur={() =>
              void saveSettings({
                scout_meeting_preference: settings.scout_meeting_preference,
              })
            }
            placeholder="Meeting/call preference, e.g. ask for a 15 minute intro call Tue-Thu afternoons"
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-900 outline-none placeholder:text-gray-400"
          />
          <input
            value={settings.scout_default_cc}
            onChange={e =>
              setSettings(s => ({ ...s, scout_default_cc: e.target.value }))
            }
            onBlur={() =>
              void saveSettings({ scout_default_cc: settings.scout_default_cc })
            }
            placeholder="Default CC emails, comma separated"
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-900 outline-none placeholder:text-gray-400"
          />
          <input
            value={settings.scout_default_bcc}
            onChange={e =>
              setSettings(s => ({ ...s, scout_default_bcc: e.target.value }))
            }
            onBlur={() =>
              void saveSettings({
                scout_default_bcc: settings.scout_default_bcc,
              })
            }
            placeholder="Default BCC emails, comma separated"
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-900 outline-none placeholder:text-gray-400"
          />
          <label className="block">
            <span className="mb-1 block text-[10px] uppercase tracking-widest text-gray-400">
              Collateral policy
            </span>
            <select
              value={settings.scout_collateral_policy}
              onChange={e =>
                void saveSettings({ scout_collateral_policy: e.target.value })
              }
              className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-900 outline-none"
            >
              <option value="none">Do not include collateral by default</option>
              <option value="selective">
                Suggest collateral for select leads
              </option>
              <option value="all">Include collateral for all new leads</option>
            </select>
          </label>
          <textarea
            value={settings.scout_collateral_links}
            onChange={e =>
              setSettings(s => ({
                ...s,
                scout_collateral_links: e.target.value,
              }))
            }
            onBlur={() =>
              void saveSettings({
                scout_collateral_links: settings.scout_collateral_links,
              })
            }
            rows={3}
            placeholder="Marketing brochures, case studies, or third-party whitepaper URLs, one per line or comma separated"
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-relaxed text-gray-900 outline-none placeholder:text-gray-400"
          />
          <label className="flex items-center justify-between gap-3 text-xs text-gray-500">
            Let SIGNAL brief me with next-best-action ideas from replies, no
            response, new research, and customer tone
            <input
              type="checkbox"
              checked={settings.scout_background_briefing_enabled}
              onChange={e =>
                void saveSettings({
                  scout_background_briefing_enabled: e.target.checked,
                })
              }
            />
          </label>
        </div>
        <div className="mb-4">
          <HubSpotConnectPanel
            status={hubspotStatus}
            loading={hubspotLoading}
          />
          <p className="mt-2 text-center text-[11px] text-gray-500">
            <Link href="/integrations" className="text-emerald-700 underline">
              All integrations
            </Link>
          </p>
        </div>
        <p className="text-xs text-gray-400 mb-4">
          CRM outreach is on{" "}
          <Link href="/crm" className="text-emerald-700 underline">
            /crm
          </Link>
          .
        </p>
        <button
          type="button"
          onClick={() => {
            clearPendingNext();
            void supabase?.auth.signOut().then(() => {
              window.location.href = "/";
            });
          }}
          className="text-xs text-red-400/90 border border-red-500/30 rounded px-3 py-2 hover:bg-red-500/10"
        >
          Sign out
        </button>
      </main>
      <SiteFooter />
    </div>
  );
}
