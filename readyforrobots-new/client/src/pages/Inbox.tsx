import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import { Mail } from "lucide-react";
import ExperimentHeader from "@/components/ExperimentHeader";
import AdminNav from "@/components/AdminNav";
import { JOBS_HEADER_OFFSET_CLASS } from "@/lib/jobsWorkflow";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import ResendEmailModal from "@/components/ResendEmailModal";

type InboxItem = {
  id: string;
  thread_id: string | null;
  opportunity_type: "crm" | "supply";
  title: string;
  current_stage: string;
  from_email?: string | null;
  subject?: string | null;
  body_text?: string | null;
  detected_intent?: string | null;
  received_at?: string | null;
  folder?: "main" | "test";
  next_best_action?: { recommendation?: string; intent?: string };
  latest_action?: {
    id?: string;
    status?: string;
    draft_subject?: string | null;
    draft_body?: string | null;
  } | null;
};

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "Unknown";
}

function scheduleHref(item: InboxItem) {
  if (!item.thread_id) {
    return "#";
  }
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
  const [selectedId, setSelectedId] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [replyModalOpen, setReplyModalOpen] = useState(false);
  const [folderTab, setFolderTab] = useState<"all" | "main" | "test">("all");
  const [allItems, setAllItems] = useState<InboxItem[]>([]);

  const loadInbox = useCallback(async () => {
    if (!session?.access_token) return;
    setBusy(true);
    setErr("");
    try {
      const response = await fetch(
        `${getApiBase()}/api/sales/inbox?folder=all`,
        liveFetchInit({ headers: authHeader(session.access_token) })
      );
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      const list = Array.isArray(data) ? data : [];
      setAllItems(list);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not load inbox");
    } finally {
      setBusy(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    void loadInbox();
  }, [loadInbox]);

  const items = useMemo(() => {
    if (folderTab === "all") return allItems;
    return allItems.filter(item => (item.folder || "main") === folderTab);
  }, [allItems, folderTab]);
  const mainCount = allItems.filter(
    item => (item.folder || "main") === "main"
  ).length;
  const testCount = allItems.filter(item => item.folder === "test").length;

  useEffect(() => {
    setSelectedId(current =>
      items.some(item => item.id === current) ? current : items[0]?.id || ""
    );
  }, [items]);

  if (loading)
    return <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`} />;

  if (!session) {
    return (
      <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
        <ExperimentHeader />
        <main className="mx-auto max-w-3xl px-6 pt-32">
          <h1 className="text-3xl font-black text-white">Inbox</h1>
          <p className="mt-3 text-slate-400">Sign in to review buyer replies.</p>
          <Link
            href="/login?next=/inbox"
            className="mt-6 inline-flex rounded-xl bg-emerald-500 px-4 py-2 text-sm font-black text-slate-950 hover:bg-emerald-400"
          >
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  const selected = items.find(item => item.id === selectedId) || null;

  async function approveDraft(actionId: string) {
    if (!session?.access_token) return;
    setBusy(true);
    setErr("");
    try {
      const res = await fetch(
        `${getApiBase()}/api/sales/actions/${actionId}/automate`,
        liveFetchInit({
          method: "POST",
          headers: authHeader(session.access_token),
        })
      );
      if (!res.ok) throw new Error(await res.text());
      await loadInbox();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not send reply");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`min-h-screen bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
      <ExperimentHeader />
      <main className="admin-workspace mx-auto max-w-7xl px-6 pb-16 pt-8">
        <AdminNav variant="dark" />
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-emerald-400">
              Operator inbox
            </p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-white">Replies</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Buyer and robot-company replies land here before you decide
              whether to answer or take the thread over.
            </p>
          </div>
          <button
            onClick={() => void loadInbox()}
            disabled={busy}
            className="rounded-xl border border-slate-700/80 bg-slate-800/80 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
        {err && (
          <p className="mt-5 rounded-xl border border-red-400/40 bg-red-950/50 p-3 text-sm font-medium text-red-100">
            {err}
          </p>
        )}
        <section className="mt-8 grid gap-5 lg:grid-cols-[380px_1fr]">
          <aside className="rounded-2xl border border-slate-700/60 bg-[#0a1226] p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                Inbound replies
              </p>
              <span className="text-xs text-slate-400">{items.length}</span>
            </div>

            <div className="mt-3 flex items-center rounded-xl border border-slate-700/60 bg-[#081126] p-1">
              <button
                type="button"
                onClick={() => setFolderTab("all")}
                className={`flex-1 rounded-lg py-1.5 text-xs font-bold transition ${
                  folderTab === "all"
                    ? "bg-emerald-500/15 text-emerald-300"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                All ({allItems.length})
              </button>
              <button
                type="button"
                onClick={() => setFolderTab("main")}
                className={`flex-1 rounded-lg py-1.5 text-xs font-bold transition ${
                  folderTab === "main"
                    ? "bg-emerald-500/15 text-emerald-300"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Customer ({mainCount})
              </button>
              <button
                type="button"
                onClick={() => setFolderTab("test")}
                className={`flex-1 rounded-lg py-1.5 text-xs font-bold transition ${
                  folderTab === "test"
                    ? "bg-emerald-500/15 text-emerald-300"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                System ({testCount})
              </button>
            </div>
            <div className="mt-4 space-y-2">
              {items.map(item => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedId(item.id)}
                  className={`w-full rounded-xl border p-4 text-left transition ${
                    selectedId === item.id
                      ? "border-emerald-400 bg-[#0b162f]"
                      : "border-slate-700/60 bg-[#081126] hover:border-slate-500"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-bold text-slate-100">
                      {item.title}
                    </p>
                    <span className="rounded-full border border-slate-700/60 bg-slate-800/80 px-2 py-1 text-[10px] uppercase text-slate-400">
                      {item.opportunity_type}
                    </span>
                  </div>
                  <p className="mt-1 truncate text-xs text-slate-400">
                    {item.from_email || "Unknown sender"}
                  </p>
                  <p className="mt-2 line-clamp-2 text-xs text-slate-500">
                    {item.subject || item.body_text || "No preview"}
                  </p>
                </button>
              ))}
              {!items.length && !busy && (
                <p className="rounded-xl border border-slate-700/60 p-4 text-sm text-slate-400">
                  {allItems.length
                    ? "No messages in this folder."
                    : "No replies have been captured."}
                </p>
              )}
            </div>
          </aside>
          <section className="rounded-2xl border border-slate-700/60 bg-[#0a1226] p-5">
            {selected ? (
              <>
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-400">
                      {selected.opportunity_type} · {selected.current_stage}
                    </p>
                    <h2 className="mt-2 text-2xl font-black text-white">
                      {selected.title}
                    </h2>
                    <p className="mt-1 text-sm text-slate-400">
                      From {selected.from_email || "unknown"} ·{" "}
                      {formatDate(selected.received_at)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selected.thread_id ? (
                      <Link
                        href={`/sales-console?opportunity_id=${encodeURIComponent(selected.thread_id)}`}
                        className="rounded-lg border border-slate-700/80 bg-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 hover:text-white"
                      >
                        Open in Sales Console
                      </Link>
                    ) : null}
                    {selected.latest_action?.id &&
                    (selected.latest_action.status === "pending" ||
                      selected.latest_action.status === "drafted") ? (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() =>
                          void approveDraft(selected.latest_action!.id!)
                        }
                        className="rounded-lg bg-emerald-500 px-3 py-2 text-xs font-black text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
                      >
                        Approve &amp; send reply
                      </button>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => setReplyModalOpen(true)}
                      className="rounded-lg border border-emerald-500/50 bg-emerald-950/40 px-3 py-2 text-xs font-bold text-emerald-300 hover:bg-emerald-900/60 transition flex items-center gap-1.5"
                    >
                      <Mail className="w-3.5 h-3.5" />
                      Reply via Resend
                    </button>
                    {selected.thread_id ? (
                      <Link
                        href={scheduleHref(selected)}
                        className="rounded-lg border border-slate-700/80 bg-slate-800/80 px-3 py-2 text-xs font-bold text-slate-200 hover:text-white"
                      >
                        Schedule meeting
                      </Link>
                    ) : null}
                  </div>
                </div>
                <div className="mt-5 rounded-xl border border-slate-700/60 bg-[#081126] p-4">
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                    Incoming message
                  </p>
                  <p className="mt-2 text-sm font-bold text-slate-100">
                    {selected.subject || "No subject"}
                  </p>
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                    {selected.body_text || "No body captured."}
                  </p>
                </div>
                <div className="mt-5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
                  <p className="text-xs font-bold uppercase tracking-widest text-emerald-300">
                    Recommended next step
                  </p>
                  <p className="mt-2 text-sm text-slate-200">
                    {selected.next_best_action?.recommendation ||
                      "Review the reply and decide whether to respond or schedule a meeting."}
                  </p>
                  {selected.latest_action?.draft_body && (
                    <pre className="mt-3 max-h-60 overflow-y-auto whitespace-pre-wrap rounded-xl border border-slate-700/60 bg-[#081126] p-3 text-xs leading-relaxed text-slate-200">
                      {selected.latest_action.draft_body}
                    </pre>
                  )}
                </div>

                {selected && (
                  <ResendEmailModal
                    isOpen={replyModalOpen}
                    onClose={() => setReplyModalOpen(false)}
                    defaultTo={selected.from_email || ""}
                    defaultSubject={
                      selected.subject?.toLowerCase().startsWith("re:")
                        ? selected.subject
                        : `Re: ${selected.subject || selected.title}`
                    }
                    defaultBody={selected.latest_action?.draft_body || ""}
                    companyName={selected.title}
                    onSent={() => void loadInbox()}
                  />
                )}
              </>
            ) : (
              <p className="text-sm text-slate-400">Select a reply to review.</p>
            )}
          </section>
        </section>
      </main>
    </div>
  );
}
