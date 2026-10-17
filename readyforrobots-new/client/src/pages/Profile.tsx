import { useEffect, useState } from "react";
import { Link } from "wouter";
import AdminNav from "@/components/AdminNav";
import { SiteFooter, SiteHeader } from "@/components/editorial";
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
      <div className="rfr-editorial rfr-account">
        <SiteHeader />
        <main className="rfr-account-callback">
          <h1>Account</h1>
          <p className="rfr-account-lede">Supabase is not configured in this build.</p>
        </main>
        <SiteFooter />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="rfr-editorial rfr-account">
        <SiteHeader />
        <main className="rfr-account-callback">
          <div className="rfr-account-kicker">YOUR ACCOUNT</div>
          <h1>One moment.</h1>
          <p className="rfr-account-lede">Loading your account.</p>
        </main>
        <SiteFooter />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="rfr-editorial rfr-account">
        <SiteHeader />
        <main className="rfr-account-callback">
          <div className="rfr-account-kicker">YOUR ACCOUNT</div>
          <h1>Sign in to see your account.</h1>
          <Link href="/login?next=/profile" className="rfr-account-submit" style={{ width: "auto", padding: "0 18px" }}>
            Sign in
          </Link>
        </main>
        <SiteFooter />
      </div>
    );
  }

  const accountEmail = me?.email || session.user.email || "";
  const accountName =
    (me?.display_name || "").trim() ||
    accountEmail.split("@")[0] ||
    "Your account";
  const initials = accountName
    .split(/\s+/)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase() || "")
    .join("") || "RR";
  const provider =
    session.user.identities?.[0]?.provider ||
    (session.user.app_metadata?.provider as string | undefined) ||
    "email";
  const signInMethod =
    provider === "google"
      ? "Google"
      : provider === "github"
        ? "GitHub"
        : "Email link";

  return (
    <div className="rfr-editorial rfr-account">
      <SiteHeader signedIn initials={initials} />
      <main>
        <section className="rfr-account-split">
          <div className="rfr-account-copy">
            <div className="rfr-account-kicker">YOUR ACCOUNT</div>
            <h1>{accountName}</h1>
            <AdminNav />
            {err && (
              <p className="rfr-account-error" role="alert">
                {err}
              </p>
            )}
            <div className="rfr-account-rows">
              <div className="rfr-account-row">
                <span>EMAIL</span>
                <b>{accountEmail}</b>
                <span />
              </div>
              <div className="rfr-account-row">
                <span>SIGN-IN</span>
                <b>{signInMethod}</b>
                <span />
              </div>
            </div>
          </div>
          <div className="rfr-account-plan">
            <div className="rfr-account-plan-card">
              <span>PLAN</span>
              <strong>Early access</strong>
              <em>Free while we're in early access.</em>
            </div>
            <Link
              className="rfr-account-secondary"
              href={me?.entitlements?.upgrade_url || "/pricing"}
            >
              Manage plan and billing
            </Link>
            <button
              type="button"
              className="rfr-account-secondary"
              onClick={() => {
                clearPendingNext();
                void supabase?.auth.signOut().then(() => {
                  window.location.href = "/";
                });
              }}
            >
              Sign out
            </button>
          </div>
        </section>
        <section className="rfr-account-stack">
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
        <p className="rfr-account-fine">
          CRM outreach is on <Link href="/crm">/crm</Link>.
        </p>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
