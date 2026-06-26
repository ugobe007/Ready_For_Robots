import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { toast } from "sonner";

type CalendarEvent = {
  id: string;
  title: string;
  description?: string | null;
  start_at: string;
  end_at: string;
  timezone: string;
  location?: string | null;
  meeting_url?: string | null;
  attendees: Array<{ email: string; name?: string }>;
  status: string;
  invite_status: string;
  sales_opportunity_id?: string | null;
};

function localInputValue(date: Date) {
  const copy = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return copy.toISOString().slice(0, 16);
}

function readParam(name: string) {
  return typeof window === "undefined" ? "" : new URLSearchParams(window.location.search).get(name) || "";
}

export default function CalendarPage() {
  const { session, loading } = useAuth();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const defaults = useMemo(() => {
    const start = new Date();
    start.setHours(start.getHours() + 1, 0, 0, 0);
    const end = new Date(start.getTime() + 30 * 60000);
    return { start, end };
  }, []);
  const [form, setForm] = useState({
    title: readParam("title") || "ReadyForRobots meeting",
    description: readParam("context"),
    start_at: localInputValue(defaults.start),
    end_at: localInputValue(defaults.end),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    location: "",
    meeting_url: "",
    attendees: readParam("attendee"),
    sales_opportunity_id: readParam("opportunity_id"),
    send_invites: true,
  });

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      if (!session?.access_token) throw new Error("Not signed in");
      const response = await fetch(`${getApiBase()}${path}`, liveFetchInit({ ...init, headers: { ...authHeader(session.access_token), ...init.headers } }));
      const text = await response.text();
      if (!response.ok) throw new Error(text || response.statusText);
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token],
  );

  const loadEvents = useCallback(async () => {
    if (!session?.access_token) return;
    setBusy(true);
    try {
      const data = await authFetch("/api/calendar/events");
      setEvents(Array.isArray(data) ? data : []);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not load calendar.");
    } finally {
      setBusy(false);
    }
  }, [authFetch, session?.access_token]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const createEvent = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      const attendees = form.attendees
        .split(/[;,]/)
        .map((email) => email.trim())
        .filter(Boolean)
        .map((email) => ({ email, name: email }));
      await authFetch("/api/calendar/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          start_at: new Date(form.start_at).toISOString(),
          end_at: new Date(form.end_at).toISOString(),
          attendees,
          sales_opportunity_id: form.sales_opportunity_id || null,
        }),
      });
      toast.success(form.send_invites ? "Meeting created and invites sent." : "Meeting created.");
      await loadEvents();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not create meeting.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-slate-50 text-gray-900" />;

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 text-gray-900">
        <Header />
        <main className="mx-auto max-w-3xl px-6 pt-32">
          <h1 className="text-3xl font-black">Calendar</h1>
          <p className="mt-3 text-gray-500">Sign in to schedule meetings.</p>
          <Link href="/login?next=/calendar" className="mt-6 inline-flex rounded-xl bg-amber-400 px-4 py-2 text-sm font-black text-[#111827]">
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-gray-900">
      <Header />
      <main className="admin-workspace mx-auto max-w-7xl px-6 pb-16 pt-28">
        <AdminNav />
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-amber-800">Internal calendar</p>
            <h1 className="mt-2 text-4xl font-black">Calendar</h1>
            <p className="mt-2 max-w-2xl text-sm text-gray-500">Schedule meetings and send `.ics` invites. Events are stored internally and ready for future Google Calendar sync.</p>
          </div>
          <button onClick={() => void loadEvents()} disabled={busy} className="rounded-xl border border-gray-200 px-4 py-2 text-sm font-bold text-gray-600 disabled:opacity-50">
            Refresh
          </button>
        </div>
        <section className="mt-8 grid gap-6 lg:grid-cols-[420px_1fr]">
          <form onSubmit={(event) => void createEvent(event)} className="rounded-3xl border border-gray-300 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500">Schedule meeting</h2>
            {[
              ["title", "Title"],
              ["attendees", "Attendees"],
              ["meeting_url", "Meeting URL"],
              ["location", "Location"],
            ].map(([key, label]) => (
              <label key={key} className="mt-4 block">
                <span className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-gray-400">{label}</span>
                <input
                  value={String(form[key as keyof typeof form] || "")}
                  onChange={(e) => setForm((current) => ({ ...current, [key]: e.target.value }))}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none"
                />
              </label>
            ))}
            <div className="mt-4 grid grid-cols-2 gap-3">
              <label>
                <span className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-gray-400">Start</span>
                <input type="datetime-local" value={form.start_at} onChange={(e) => setForm((current) => ({ ...current, start_at: e.target.value }))} className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none" />
              </label>
              <label>
                <span className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-gray-400">End</span>
                <input type="datetime-local" value={form.end_at} onChange={(e) => setForm((current) => ({ ...current, end_at: e.target.value }))} className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none" />
              </label>
            </div>
            <label className="mt-4 block">
              <span className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-gray-400">Context</span>
              <textarea value={form.description} onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))} rows={5} className="w-full rounded-xl border border-gray-200 bg-black/20 px-3 py-2 text-sm text-gray-900 outline-none" />
            </label>
            <label className="mt-4 flex items-center gap-2 text-sm text-gray-600">
              <input type="checkbox" checked={form.send_invites} onChange={(e) => setForm((current) => ({ ...current, send_invites: e.target.checked }))} />
              Send `.ics` invites now
            </label>
            <button disabled={busy} className="mt-5 w-full rounded-xl bg-amber-400 px-4 py-3 text-sm font-black text-[#111827] disabled:opacity-50">
              Create meeting
            </button>
          </form>
          <section className="rounded-3xl border border-gray-200 bg-white/[0.035] p-5">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500">Upcoming events</h2>
            <div className="mt-4 space-y-3">
              {events.map((event) => (
                <div key={event.id} className="rounded-2xl border border-gray-200 bg-white p-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="font-bold text-gray-900">{event.title}</p>
                      <p className="mt-1 text-xs text-gray-500">{new Date(event.start_at).toLocaleString()} to {new Date(event.end_at).toLocaleString()}</p>
                      <p className="mt-2 text-sm text-gray-500">{event.description || "No description"}</p>
                    </div>
                    <span className="rounded-full border border-gray-200 px-3 py-1 text-[10px] uppercase text-gray-500">{event.invite_status}</span>
                  </div>
                  <p className="mt-2 text-xs text-gray-400">Attendees: {(event.attendees || []).map((item) => item.email).join(", ") || "None"}</p>
                  {(event.meeting_url || event.location) && <p className="mt-1 text-xs text-gray-400">Where: {event.meeting_url || event.location}</p>}
                </div>
              ))}
              {!events.length && !busy && <p className="rounded-2xl border border-gray-200 p-4 text-sm text-gray-500">No meetings scheduled yet.</p>}
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}
