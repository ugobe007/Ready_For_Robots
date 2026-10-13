import { useCallback, useEffect, useState } from "react";
import { Mail, Trash2 } from "lucide-react";

export type DeskMessage = {
  id: string;
  title?: string | null;
  direction?: string | null;
  from_email?: string | null;
  to_email?: string | null;
  subject?: string | null;
  body_text?: string | null;
  received_at?: string | null;
  detected_intent?: string | null;
};

export type ReadyOutreach = {
  crm_account_id: string;
  opportunity_id?: string | null;
  company: string;
  industry?: string | null;
  contact_email?: string | null;
  stage?: string | null;
  subject: string;
  body: string;
};

type AuthFetch = (path: string, init?: RequestInit) => Promise<unknown>;

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "Unknown time";
}

export default function SalesConsoleDesk({
  authFetch,
  phelanEnabled,
  onPrepare,
  preparing,
  onUseMessage,
}: {
  authFetch: AuthFetch;
  phelanEnabled: boolean;
  onPrepare: () => Promise<void>;
  preparing: boolean;
  onUseMessage: (item: ReadyOutreach) => void;
}) {
  const [tab, setTab] = useState<"inbox" | "ready" | "deleted">("inbox");
  const [messages, setMessages] = useState<DeskMessage[]>([]);
  const [ready, setReady] = useState<ReadyOutreach[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [readyId, setReadyId] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const folder = tab === "deleted" ? "deleted" : "all";
      const [inboxRaw, readyRaw] = await Promise.all([
        authFetch(`/api/sales/inbox?folder=${folder}&direction=all`),
        authFetch("/api/sales/outreach-ready"),
      ]);
      const inbox = Array.isArray(inboxRaw) ? (inboxRaw as DeskMessage[]) : [];
      const queue = Array.isArray(readyRaw) ? (readyRaw as ReadyOutreach[]) : [];
      setMessages(inbox);
      setReady(queue);
      setSelectedId(current =>
        inbox.some(item => item.id === current) ? current : inbox[0]?.id || ""
      );
      setReadyId(current =>
        queue.some(item => item.crm_account_id === current)
          ? current
          : queue[0]?.crm_account_id || ""
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not load the desk");
    } finally {
      setLoading(false);
    }
  }, [authFetch, tab]);

  useEffect(() => {
    void load();
  }, [load]);

  async function discard(id: string) {
    setErr("");
    try {
      await authFetch(`/api/sales/messages/${id}/discard`, { method: "POST" });
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not delete that message");
    }
  }

  async function restore(id: string) {
    setErr("");
    try {
      await authFetch(`/api/sales/messages/${id}/restore`, { method: "POST" });
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not restore that message");
    }
  }

  const selected = messages.find(item => item.id === selectedId) || null;
  const selectedReady = ready.find(item => item.crm_account_id === readyId) || null;

  return (
    <section className="mt-6 rounded-2xl border border-slate-700/60 bg-[#0c192e] p-5 shadow-xl">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-emerald-400">
            Phelan desk
          </p>
          <p className="mt-2 max-w-2xl text-sm text-slate-300">
            {phelanEnabled
              ? "Phelan autopilot is on. Review the draft before it goes out."
              : "Automatic sending is off. Phelan writes a draft when you prepare one. Nothing is sent until you use the message."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void onPrepare().then(() => load())}
          disabled={preparing}
          className="rounded-xl bg-emerald-500 px-4 py-2 text-xs font-black uppercase tracking-wide text-slate-950 disabled:opacity-50"
        >
          {preparing ? "Preparing…" : "Prepare drafts"}
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {(
          [
            ["inbox", "Inbox"],
            ["ready", `Ready for outreach (${ready.length})`],
            ["deleted", "Deleted"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`rounded-full px-3 py-1 text-xs font-bold ${
              tab === key
                ? "bg-emerald-500 text-slate-950"
                : "border border-slate-700 text-slate-300"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {err ? (
        <p className="mt-3 rounded-xl border border-red-500/40 bg-red-950/40 p-3 text-sm text-red-200">
          {err}
        </p>
      ) : null}

      {tab === "ready" ? (
        <div className="mt-4 grid gap-4 lg:grid-cols-[320px_1fr]">
          <div className="space-y-2">
            {ready.map(item => (
              <button
                key={item.crm_account_id}
                type="button"
                onClick={() => setReadyId(item.crm_account_id)}
                className={`w-full rounded-xl border p-3 text-left ${
                  readyId === item.crm_account_id
                    ? "border-emerald-400 bg-emerald-950/40"
                    : "border-slate-700 bg-slate-950/40"
                }`}
              >
                <p className="truncate text-sm font-bold text-white">{item.company}</p>
                <p className="mt-1 truncate text-xs text-slate-400">
                  {item.contact_email || "No recipient yet"}
                </p>
              </button>
            ))}
            {!ready.length && !loading ? (
              <p className="rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-400">
                Nothing is waiting. Prepare drafts to fill this list.
              </p>
            ) : null}
          </div>
          <div className="rounded-xl border border-slate-700 bg-[#081126] p-4">
            {selectedReady ? (
              <>
                <p className="text-xs uppercase tracking-widest text-slate-400">
                  Proposed message · {selectedReady.stage || "ready"}
                </p>
                <h3 className="mt-2 text-xl font-black text-white">{selectedReady.company}</h3>
                <p className="mt-1 text-sm text-slate-400">
                  To {selectedReady.contact_email || "no recipient on file"}
                  {selectedReady.industry ? ` · ${selectedReady.industry}` : ""}
                </p>
                <p className="mt-4 text-sm font-bold text-slate-100">{selectedReady.subject}</p>
                <pre className="mt-3 max-h-80 overflow-y-auto whitespace-pre-wrap rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm leading-relaxed text-slate-200">
                  {selectedReady.body || "No message body."}
                </pre>
                <button
                  type="button"
                  onClick={() => onUseMessage(selectedReady)}
                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white"
                >
                  <Mail className="h-3.5 w-3.5" />
                  Use this message
                </button>
              </>
            ) : (
              <p className="text-sm text-slate-400">Select a company to read the draft.</p>
            )}
          </div>
        </div>
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-[320px_1fr]">
          <div className="max-h-[420px] space-y-2 overflow-y-auto">
            {messages.map(item => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelectedId(item.id)}
                className={`w-full rounded-xl border p-3 text-left ${
                  selectedId === item.id
                    ? "border-emerald-400 bg-emerald-950/40"
                    : "border-slate-700 bg-slate-950/40"
                }`}
              >
                <p className="truncate text-sm font-bold text-white">
                  {item.title || item.subject || "Message"}
                </p>
                <p className="mt-1 truncate text-xs text-slate-400">
                  {item.direction === "outbound" ? "Outbound" : "Inbound"} ·{" "}
                  {item.from_email || item.to_email || "unknown"}
                </p>
              </button>
            ))}
            {!messages.length && !loading ? (
              <p className="rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-400">
                {tab === "deleted" ? "The delete box is empty." : "No messages to review."}
              </p>
            ) : null}
          </div>
          <div className="rounded-xl border border-slate-700 bg-[#081126] p-4">
            {selected ? (
              <>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-400">
                      {selected.direction || "inbound"} · {formatDate(selected.received_at)}
                    </p>
                    <h3 className="mt-2 text-xl font-black text-white">
                      {selected.subject || selected.title || "No subject"}
                    </h3>
                    <p className="mt-1 text-sm text-slate-400">
                      From {selected.from_email || "unknown"}
                      {selected.to_email ? ` · To ${selected.to_email}` : ""}
                    </p>
                  </div>
                  {tab === "deleted" ? (
                    <button
                      type="button"
                      onClick={() => void restore(selected.id)}
                      className="rounded-lg border border-slate-600 px-3 py-2 text-xs font-bold text-slate-200"
                    >
                      Restore
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => void discard(selected.id)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/40 bg-red-950/40 px-3 py-2 text-xs font-bold text-red-200"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </button>
                  )}
                </div>
                <pre className="mt-4 max-h-80 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-200">
                  {selected.body_text || "No message body."}
                </pre>
              </>
            ) : (
              <p className="text-sm text-slate-400">Select a message to read it.</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
