import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

type InboxItem = {
  id: string;
  thread_id: string;
  opportunity_type: "crm" | "supply";
  title: string;
  current_stage: string;
  from_email?: string | null;
  subject?: string | null;
  body_text?: string | null;
  detected_intent?: string | null;
  received_at?: string | null;
  next_best_action?: { recommendation?: string; intent?: string };
  latest_action?: { status?: string; draft_subject?: string | null; draft_body?: string | null } | null;
};

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "Unknown";
}

function scheduleHref(item: InboxItem) {
  const params = new URLSearchParams({
    opportunity_id: item.thread_id,
    title: `Meeting with ${item.title}`,
    attendee: item.from_email || "",
    context: item.body_text || item.subject || "",
  });
  return `/calendar?${params.toString()}`;
}

export default function Inbox() {
  const { session, loading } = useAuth();
  const [items, setItems] = useState<InboxItem[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const loadInbox = useCallback(async () => {
    if (!session?.access_token) return;
    setBusy(true);
    setErr("");
    try {
      const response = await fetch(`${getApiBase()}/api/sales/inbox`, liveFetchInit({ headers: authHeader(session.access_token) }));
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      const list = Array.isArray(data) ? data : [];
      setItems(list);
      setSelectedId((current) => (list.some((item) => item.id === current) ? current : list[0]?.id || ""));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not load inbox");
    } finally {
      setBusy(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    void loadInbox();
  }, [loadInbox]);

  if (loading) return <div className="min-h-screen bg-[#0d0520] text-white" />;

  if (!session) {
    return (
      <div className="min-h-screen bg-[#0d0520] text-white">
        <Header />
        <main className="mx-auto max-w-3xl px-6 pt-32">
          <h1 className="text-3xl font-black">Inbox</h1>
          <p className="mt-3 text-white/55">Sign in to review buyer replies.</p>
          <Link href="/login?next=/inbox" className="mt-6 inline-flex rounded-xl bg-amber-400 px-4 py-2 text-sm font-black text-[#160b2c]">
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  const selected = items.find((item) => item.id === selectedId) || null;

  return (
    <div className="min-h-screen bg-[#0d0520] text-white">
      <Header />
      <main className="mx-auto max-w-7xl px-6 pb-16 pt-28">
        <AdminNav />
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-amber-300">Operator inbox</p>
            <h1 className="mt-2 text-4xl font-black">Replies</h1>
            <p className="mt-2 max-w-2xl text-sm text-white/55">
              Buyer and robot-company replies land here before you decide whether SCOUT should respond or you should take over.
            </p>
          </div>
          <button onClick={() => void loadInbox()} disabled={busy} className="rounded-xl border border-white/15 px-4 py-2 text-sm font-bold text-white/70 disabled:opacity-50">
            Refresh
          </button>
        </div>
        {err && <p className="mt-5 rounded-xl border border-red-400/25 bg-red-400/10 p-3 text-sm text-red-100">{err}</p>}
        <section className="mt-8 grid gap-5 lg:grid-cols-[380px_1fr]">
          <aside className="rounded-3xl border border-white/10 bg-white/[0.035] p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold uppercase tracking-widest text-white/35">Inbound replies</p>
              <span className="text-xs text-white/35">{items.length}</span>
            </div>
            <div className="mt-4 space-y-2">
              {items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedId(item.id)}
                  className="w-full rounded-2xl border p-4 text-left transition"
                  style={{
                    borderColor: selectedId === item.id ? "rgba(255,176,0,0.5)" : "rgba(255,255,255,0.08)",
                    background: selectedId === item.id ? "rgba(255,176,0,0.08)" : "rgba(255,255,255,0.025)",
                  }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-bold text-white/85">{item.title}</p>
                    <span className="rounded-full bg-white/8 px-2 py-1 text-[10px] uppercase text-white/45">{item.opportunity_type}</span>
                  </div>
                  <p className="mt-1 truncate text-xs text-white/45">{item.from_email || "Unknown sender"}</p>
                  <p className="mt-2 line-clamp-2 text-xs text-white/35">{item.subject || item.body_text || "No preview"}</p>
                </button>
              ))}
              {!items.length && !busy && <p className="rounded-2xl border border-white/10 p-4 text-sm text-white/40">No inbound replies yet.</p>}
            </div>
          </aside>
          <section className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
            {selected ? (
              <>
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-white/35">{selected.opportunity_type} · {selected.current_stage}</p>
                    <h2 className="mt-2 text-2xl font-black">{selected.title}</h2>
                    <p className="mt-1 text-sm text-white/45">From {selected.from_email || "unknown"} · {formatDate(selected.received_at)}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Link href={`/sales-console`} className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-white/70">
                      Open Sales Console
                    </Link>
                    <Link href={scheduleHref(selected)} className="rounded-lg bg-amber-400 px-3 py-2 text-xs font-black text-[#160b2c]">
                      Schedule meeting
                    </Link>
                  </div>
                </div>
                <div className="mt-5 rounded-2xl border border-white/8 bg-black/15 p-4">
                  <p className="text-xs font-bold uppercase tracking-widest text-white/35">Incoming message</p>
                  <p className="mt-2 text-sm font-bold text-white/75">{selected.subject || "No subject"}</p>
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-white/65">{selected.body_text || "No body captured."}</p>
                </div>
                <div className="mt-5 rounded-2xl border border-emerald-400/15 bg-emerald-400/5 p-4">
                  <p className="text-xs font-bold uppercase tracking-widest text-emerald-100/70">Recommended next step</p>
                  <p className="mt-2 text-sm text-emerald-100/85">{selected.next_best_action?.recommendation || "Review the reply and decide whether to respond or schedule a meeting."}</p>
                  {selected.latest_action?.draft_body && (
                    <pre className="mt-3 max-h-60 overflow-y-auto whitespace-pre-wrap rounded-xl border border-white/8 bg-black/20 p-3 text-xs leading-relaxed text-white/60">
                      {selected.latest_action.draft_body}
                    </pre>
                  )}
                </div>
              </>
            ) : (
              <p className="text-sm text-white/45">Select a reply to review.</p>
            )}
          </section>
        </section>
      </main>
    </div>
  );
}
