/**
 * Live job tape — discrete terminal arrivals, not a ticker.
 * Dense 15-row board; mechanical ~200ms shift; 5–7s between arrivals.
 */
import { useEffect, useRef, useState } from "react";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD } from "@/lib/kareIcons";
import {
  TAPE_ICONS,
  TAPE_ICONS_ACTIVE,
  type TapeJob,
} from "@/lib/jobsTapeCorpus";

const VISIBLE = 15;
const ROW_PX = 36;
const SHIFT_MS = 200;
const NEW_HOLD_MS = 2800;
const HEADER_FLASH_MS = 900;
const INTERVAL_MIN = 5000;
const INTERVAL_MAX = 7000;

type Row = TapeJob & {
  instanceId: string;
  seq: number;
  isNew: boolean;
};

type Props = {
  title: string;
  corpus: TapeJob[];
  /** Starting found counter. Increments on each arrival while running. */
  baseCount: number;
  running?: boolean;
  statusLines?: string[];
  onSelect?: (job: TapeJob) => void;
  selectedKey?: string | null;
};

function padCount(n: number): string {
  return String(Math.max(0, n)).padStart(4, "0");
}

function nextInterval(): number {
  return INTERVAL_MIN + Math.floor(Math.random() * (INTERVAL_MAX - INTERVAL_MIN));
}

export default function LiveJobTape({
  title,
  corpus,
  baseCount,
  running = true,
  statusLines,
  onSelect,
  selectedKey,
}: Props) {
  const [rows, setRows] = useState<Row[]>(() => seedRows(corpus, baseCount));
  const [foundCount, setFoundCount] = useState(baseCount);
  const [offsetY, setOffsetY] = useState(0);
  const [animate, setAnimate] = useState(false);
  const [headerFlash, setHeaderFlash] = useState(false);
  const [iconActive, setIconActive] = useState(false);
  const cursorRef = useRef(VISIBLE % Math.max(corpus.length, 1));
  const seqRef = useRef(baseCount);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const arriving = useRef(false);

  useEffect(() => {
    setRows(seedRows(corpus, baseCount));
    setFoundCount(baseCount);
    seqRef.current = baseCount;
    cursorRef.current = VISIBLE % Math.max(corpus.length, 1);
    setOffsetY(0);
    setAnimate(false);
  }, [corpus, baseCount]);

  useEffect(() => {
    return () => {
      timers.current.forEach(clearTimeout);
    };
  }, []);

  useEffect(() => {
    if (!running || corpus.length === 0) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    const schedule = () => {
      timeoutId = setTimeout(() => {
        if (cancelled) return;
        arrive();
        schedule();
      }, nextInterval());
    };

    schedule();
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, corpus]);

  function later(fn: () => void, ms: number) {
    const id = setTimeout(fn, ms);
    timers.current.push(id);
  }

  function arrive() {
    if (corpus.length === 0 || arriving.current) return;
    arriving.current = true;

    const job = corpus[cursorRef.current % corpus.length];
    cursorRef.current = (cursorRef.current + 1) % corpus.length;
    seqRef.current += 1;
    const nextSeq = seqRef.current;
    const instanceId = `${job.key}_${nextSeq}_${Date.now()}`;

    setHeaderFlash(true);
    setIconActive(true);
    setFoundCount(nextSeq);

    setAnimate(false);
    setOffsetY(-ROW_PX);
    setRows((prev) => {
      const cleared = prev.map((r) => ({ ...r, isNew: false }));
      const incoming: Row = { ...job, instanceId, seq: nextSeq, isNew: true };
      return [incoming, ...cleared];
    });

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setAnimate(true);
        setOffsetY(0);
      });
    });

    later(() => {
      setAnimate(false);
      setRows((prev) => prev.slice(0, VISIBLE));
      arriving.current = false;
    }, SHIFT_MS);
    later(() => setHeaderFlash(false), HEADER_FLASH_MS);
    later(() => setIconActive(false), 420);
    later(() => {
      setRows((prev) => prev.map((r) => (r.instanceId === instanceId ? { ...r, isNew: false } : r)));
    }, NEW_HOLD_MS);
  }

  const showStatus = Boolean(statusLines?.length);

  return (
    <div className="flex h-full min-h-0 flex-col bg-[#081126]">
      <div className="flex h-7 shrink-0 items-center justify-between border-b border-slate-600 px-3">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-200">
          {title}
        </p>
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">
          {headerFlash ? (
            <span className="text-emerald-400">&gt; New Job Found</span>
          ) : (
            <span>{padCount(foundCount)} Jobs</span>
          )}
        </p>
      </div>

      {showStatus ? (
        <div className="flex flex-1 flex-col justify-center gap-2 px-5 py-8 font-mono text-[12px] font-semibold uppercase tracking-[0.1em] text-slate-400">
          {statusLines!.map((line) => (
            <p key={line} className={line.startsWith(">") ? "text-emerald-400" : undefined}>
              {line}
            </p>
          ))}
        </div>
      ) : (
        <div className="relative min-h-0 flex-1 overflow-hidden">
          <ul
            className="absolute inset-x-0 top-0"
            style={{
              transform: `translateY(${offsetY}px)`,
              transition: animate ? `transform ${SHIFT_MS}ms linear` : "none",
            }}
          >
            {rows.map((row) => {
              const idle = TAPE_ICONS[row.family];
              const active = TAPE_ICONS_ACTIVE[row.family];
              const map = row.isNew && iconActive ? active : idle;
              const selected = selectedKey === row.key;
              return (
                <li
                  key={row.instanceId}
                  className={`flex h-9 items-center border-b border-slate-800 px-3 ${
                    row.isNew ? "bg-emerald-500/15" : selected ? "bg-slate-800/50" : ""
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onSelect?.(row)}
                    className="group flex w-full items-center gap-2 text-left"
                  >
                    <span
                      className={`w-7 shrink-0 font-mono text-[9px] font-semibold ${
                        row.isNew ? "text-emerald-400" : "text-slate-500"
                      }`}
                    >
                      {row.isNew ? "NEW" : padCount(row.seq).slice(-3)}
                    </span>
                    <span className="shrink-0">
                      <PixelIcon map={map} scale={1} fill={FACE_EMERALD} background="transparent" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-display text-[11px] font-bold uppercase leading-tight tracking-tight text-slate-100">
                        {row.title}
                      </span>
                      <span className="mt-0.5 block truncate font-mono text-[8px] font-semibold tracking-[0.06em] text-slate-400">
                        {row.industry}
                        <span className="text-slate-600"> · </span>
                        {row.path}
                      </span>
                    </span>
                    <span
                      className="shrink-0 font-mono text-[11px] text-slate-600 transition group-hover:text-emerald-400"
                      aria-hidden
                    >
                      →
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

function seedRows(corpus: TapeJob[], baseCount: number): Row[] {
  if (!corpus.length) return [];
  const out: Row[] = [];
  for (let i = 0; i < Math.min(VISIBLE, corpus.length); i++) {
    const job = corpus[i % corpus.length];
    const seq = baseCount - i;
    out.push({
      ...job,
      instanceId: `seed_${job.key}_${i}`,
      seq: Math.max(1, seq),
      isNew: false,
    });
  }
  return out;
}
