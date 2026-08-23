import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import { Check, ExternalLink, Loader2, Plus } from "lucide-react";

type CrmTask = {
  id: string;
  title: string;
  body?: string | null;
  status: string;
  priority?: string | null;
  due_at?: string | null;
  source?: string | null;
};

type CrmNote = {
  id: string;
  body: string;
  source?: string | null;
  created_at?: string | null;
};

type OutreachRow = {
  id: string;
  to_email: string;
  subject: string;
  status: string;
  sent_at?: string | null;
};

type TimelineItem = {
  type: string;
  label: string;
  at?: string | null;
};

type Engagement = {
  id: string;
  stage: string;
  status: string;
  name: string;
};

type AccountDetail = {
  account: {
    id: string;
    name: string;
    company_id?: number | null;
    outreach_stage?: string | null;
    outreach_sent_at?: string | null;
    pipeline_priority_tier?: string | null;
  };
  engagement?: Engagement | null;
  tasks: CrmTask[];
  notes: CrmNote[];
  outreach_history: OutreachRow[];
  timeline: TimelineItem[];
};

const ENGAGEMENT_STAGES = [
  { value: "qualification", label: "Qualification" },
  { value: "outreach", label: "Outreach" },
  { value: "discovery", label: "Discovery" },
  { value: "meeting", label: "Meeting" },
  { value: "proposal", label: "Proposal" },
  { value: "negotiation", label: "Negotiation" },
  { value: "closed_won", label: "Closed won" },
  { value: "closed_lost", label: "Closed lost" },
];

type Props = {
  accountId: string;
  authFetch: (path: string, init?: RequestInit) => Promise<unknown>;
  onStageChange?: (outreachStage: string) => void;
};

function fmtWhen(value?: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  } catch {
    return value;
  }
}

export default function CrmAccountWorkspace({ accountId, authFetch, onStageChange }: Props) {
  const [detail, setDetail] = useState<AccountDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noteBody, setNoteBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [sequenceName, setSequenceName] = useState<string | null>(null);
  const [sequenceSteps, setSequenceSteps] = useState<number>(0);
  const [enrollmentStatus, setEnrollmentStatus] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!accountId) return;
    setLoading(true);
    setError(null);
    try {
      const data = (await authFetch(`/api/crm/accounts/${accountId}`)) as AccountDetail;
      setDetail(data);
      try {
        const seqPayload = (await authFetch("/api/sales/sequences")) as {
          sequences?: Array<{ name: string; is_default?: boolean; steps?: unknown[] }>;
        };
        const seq = (seqPayload.sequences || []).find((s) => s.is_default) || seqPayload.sequences?.[0];
        if (seq) {
          setSequenceName(seq.name);
          setSequenceSteps(seq.steps?.length ?? 0);
        }
      } catch {
        /* sequences optional */
      }
    } catch (e) {
      setDetail(null);
      setError(e instanceof Error ? e.message : "Could not load account workspace");
    } finally {
      setLoading(false);
    }
  }, [accountId, authFetch]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function patchEngagementStage(stage: string) {
    if (!detail?.engagement?.id) return;
    setBusy(true);
    try {
      await authFetch(`/api/crm/engagements/${detail.engagement.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage }),
      });
      await reload();
      onStageChange?.(stage);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stage update failed");
    } finally {
      setBusy(false);
    }
  }

  async function toggleTask(task: CrmTask) {
    setBusy(true);
    try {
      await authFetch(`/api/crm/tasks/${task.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: task.status === "done" ? "todo" : "done" }),
      });
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Task update failed");
    } finally {
      setBusy(false);
    }
  }

  async function enrollSequence() {
    setBusy(true);
    try {
      const result = (await authFetch("/api/sales/sequences/enroll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ crm_account_id: accountId }),
      })) as { status?: string; current_step?: number };
      setEnrollmentStatus(result.status || "active");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not enroll in sequence");
    } finally {
      setBusy(false);
    }
  }

  async function addNote(e: React.FormEvent) {
    e.preventDefault();
    if (!noteBody.trim()) return;
    setBusy(true);
    try {
      await authFetch(`/api/crm/accounts/${accountId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: noteBody.trim() }),
      });
      setNoteBody("");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save note");
    } finally {
      setBusy(false);
    }
  }

  if (loading && !detail) {
    return (
      <div className="flex items-center gap-2 p-3 text-xs text-gray-500">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Loading workspace…
      </div>
    );
  }

  if (error && !detail) {
    return <p className="p-3 text-xs text-amber-800">{error}</p>;
  }

  if (!detail) return null;

  const openTasks = detail.tasks.filter((t) => t.status !== "done");

  return (
    <div className="space-y-3">
      <div className=" border border-slate-600 bg-[#0b162f] p-2.5">
        <p className="sb-kicker">Account workspace</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
          <span className=" bg-[#081126] px-1.5 py-0.5 font-mono text-slate-200">
            {detail.account.outreach_stage || "new"}
          </span>
          {detail.account.pipeline_priority_tier && (
            <span className=" bg-emerald-400/10 px-1.5 py-0.5 text-emerald-300">
              {detail.account.pipeline_priority_tier}
            </span>
          )}
          {detail.account.company_id ? (
            <Link
              href={`/pipeline?company=${detail.account.company_id}`}
              className="inline-flex items-center gap-1 font-semibold text-emerald-400 hover:underline"
            >
              Pipeline lead #{detail.account.company_id}
              <ExternalLink className="h-3 w-3" />
            </Link>
          ) : null}
        </div>
        {detail.engagement ? (
          <label className="mt-2 block">
            <span className="sb-label mb-1 block">Deal stage</span>
            <select
              value={detail.engagement.stage}
              disabled={busy}
              onChange={(e) => void patchEngagementStage(e.target.value)}
              className="sb-input text-xs"
            >
              {ENGAGEMENT_STAGES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      <div className=" border border-slate-600 bg-[#0b162f] p-2.5">
        <div className="flex items-center justify-between gap-2">
          <p className="sb-kicker">Tasks</p>
          <span className="text-[10px] text-slate-500">{openTasks.length} open</span>
        </div>
        {openTasks.length === 0 ? (
          <p className="mt-2 text-[11px] text-slate-500">No open tasks — run Generate sales plan to create some.</p>
        ) : (
          <ul className="mt-2 space-y-1.5">
            {openTasks.slice(0, 8).map((task) => (
              <li key={task.id} className="flex items-start gap-2  border border-slate-700 bg-[#081126] p-1.5">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void toggleTask(task)}
                  className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center  border border-slate-500 bg-[#0b162f] hover:border-emerald-400"
                  aria-label={`Mark ${task.title} done`}
                >
                  {task.status === "done" ? <Check className="h-3 w-3 text-emerald-400" /> : null}
                </button>
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold text-slate-100">{task.title}</p>
                  {task.body ? <p className="text-[10px] text-slate-400">{task.body}</p> : null}
                  {task.due_at ? <p className="text-[10px] text-slate-500">Due {fmtWhen(task.due_at)}</p> : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {sequenceName ? (
        <div className=" border border-slate-600 bg-[#0b162f] p-2.5">
          <p className="sb-kicker">Outreach sequence</p>
          <p className="mt-1 text-[11px] text-slate-300">
            {sequenceName} · {sequenceSteps} steps
          </p>
          {enrollmentStatus ? (
            <p className="mt-1 text-[10px] font-semibold text-emerald-400">Enrolled · {enrollmentStatus}</p>
          ) : (
            <button type="button" disabled={busy} onClick={() => void enrollSequence()} className="sb-btn mt-2 text-xs">
              Enroll in cadence
            </button>
          )}
        </div>
      ) : null}

      <div className=" border border-slate-600 bg-[#0b162f] p-2.5">
        <p className="sb-kicker">Notes</p>
        <form onSubmit={(e) => void addNote(e)} className="mt-2 flex gap-1.5">
          <input
            value={noteBody}
            onChange={(e) => setNoteBody(e.target.value)}
            placeholder="Add a note…"
            className="sb-input flex-1 text-xs"
          />
          <button type="submit" disabled={busy || !noteBody.trim()} className="sb-btn shrink-0 px-2">
            <Plus className="h-3.5 w-3.5" />
          </button>
        </form>
        <ul className="mt-2 max-h-32 space-y-1 overflow-y-auto">
          {detail.notes.slice(0, 6).map((note) => (
            <li key={note.id} className=" border border-slate-700 bg-[#081126] p-1.5 text-[10px] text-slate-300">
              {note.body}
              <span className="mt-0.5 block text-slate-500">{fmtWhen(note.created_at)}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className=" border border-slate-600 bg-[#0b162f] p-2.5">
        <p className="sb-kicker">Outreach history</p>
        {detail.outreach_history.length === 0 ? (
          <p className="mt-2 text-[11px] text-slate-500">No outreach sent yet.</p>
        ) : (
          <ul className="mt-2 space-y-1">
            {detail.outreach_history.slice(0, 5).map((row) => (
              <li key={row.id} className="text-[10px] text-slate-300">
                <span className="font-semibold">{row.to_email}</span>
                <span className="text-slate-500"> · {row.status}</span>
                <span className="block truncate text-slate-500">{row.subject}</span>
                <span className="text-slate-500">{fmtWhen(row.sent_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className=" border border-slate-600 bg-[#0b162f] p-2.5">
        <p className="sb-kicker">Activity timeline</p>
        <ul className="mt-2 max-h-36 space-y-1 overflow-y-auto">
          {detail.timeline.slice(0, 10).map((item, idx) => (
            <li key={`${item.type}-${item.at}-${idx}`} className="flex gap-2 text-[10px]">
              <span className="shrink-0 text-slate-500">{fmtWhen(item.at)}</span>
              <span className="text-slate-300">{item.label}</span>
            </li>
          ))}
        </ul>
      </div>

      {error ? <p className="text-[11px] text-amber-800">{error}</p> : null}
    </div>
  );
}
