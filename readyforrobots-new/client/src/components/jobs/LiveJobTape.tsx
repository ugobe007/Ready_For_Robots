/**
 * Live job tape — fixed 58px classified rows; 12 visible; feed rotates behind.
 * Exact row grid: 48 | 34 | 1fr | 24. No absolute text stacking.
 */
import { useEffect, useRef, useState } from "react";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD } from "@/lib/kareIcons";
import {
  TAPE_ICONS,
  TAPE_ICONS_ACTIVE,
  type TapeJob,
} from "@/lib/jobsTapeCorpus";

const VISIBLE = 12;
/** Fixed row height — animation translates by this amount only. */
const ROW_PX = 58;
const SHIFT_MS = 200;
const NEW_HOLD_MS = 1500;
const HEADER_FLASH_MS = 1100;
const INTERVAL_MIN = 5000;
const INTERVAL_MAX = 7000;
/** 16×16 map → 24px (fits 34px icon column; stronger Kare presence) */
const ICON_SCALE = 24 / 16;

type Row = TapeJob & {
  instanceId: string;
  seq: number;
  isNew: boolean;
};

type Props = {
  title: string;
  corpus: TapeJob[];
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

/** Title Case for human-readable job names (not mono/all-caps). */
function toTitleCase(s: string): string {
  return s
    .trim()
    .toLowerCase()
    .replace(/\b([a-z])/g, (c) => c.toUpperCase());
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
      <div className="shrink-0 border-b border-slate-600 px-4 py-2.5">
        <div className="flex items-center justify-between gap-3">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-100 sm:text-[12px]">
            {title}
          </p>
          <p className="font-mono text-[13px] font-bold uppercase tracking-[0.08em] tabular-nums text-emerald-400 sm:text-[14px]">
            {headerFlash ? (
              <span>● New Job</span>
            ) : (
              <span>{padCount(foundCount)} Jobs Found</span>
            )}
          </p>
        </div>
        <p className="mt-0.5 font-mono text-[9px] font-semibold uppercase tracking-[0.16em] text-slate-600">
          Live robot work
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
                  className={`box-border border-b border-slate-800/90 ${
                    row.isNew ? "bg-emerald-500/15" : selected ? "bg-slate-800/50" : ""
                  }`}
                  style={{ height: ROW_PX, minHeight: ROW_PX }}
                >
                  <button
                    type="button"
                    onClick={() => onSelect?.(row)}
                    className="group grid h-full w-full items-start px-3 text-left"
                    style={{
                      gridTemplateColumns: "48px 34px 1fr 24px",
                      paddingTop: 6,
                      paddingBottom: 6,
                    }}
                  >
                    {/* NUMBER — top-aligned with title */}
                    <span
                      className={`font-mono text-[10px] font-semibold leading-4 tabular-nums ${
                        row.isNew ? "text-emerald-400" : "text-slate-500"
                      }`}
                    >
                      {row.isNew ? "NEW" : padCount(row.seq).slice(-3)}
                    </span>

                    {/* ICON — vertically centered in row */}
                    <span className="flex h-[46px] items-center justify-center self-center">
                      <PixelIcon
                        map={map}
                        scale={ICON_SCALE}
                        fill={FACE_EMERALD}
                        background="transparent"
                      />
                    </span>

                    {/* JOB CONTENT — three normal-flow lines, no absolute */}
                    <span className="min-w-0 overflow-hidden">
                      <span
                        className="block overflow-hidden text-ellipsis whitespace-nowrap font-sans text-[14px] font-bold text-white"
                        style={{ lineHeight: "16px", letterSpacing: 0 }}
                      >
                        {toTitleCase(row.title)}
                      </span>
                      <span
                        className="block overflow-hidden text-ellipsis whitespace-nowrap font-sans font-normal text-slate-400"
                        style={{ fontSize: 11, lineHeight: "14px", marginTop: 2 }}
                      >
                        {row.industry}
                      </span>
                      <span
                        className="block overflow-hidden text-ellipsis whitespace-nowrap font-mono uppercase text-emerald-400"
                        style={{
                          fontSize: 10,
                          lineHeight: "12px",
                          marginTop: 2,
                          letterSpacing: "0.08em",
                        }}
                      >
                        {row.path}
                      </span>
                    </span>

                    {/* ARROW — vertically centered */}
                    <span
                      className={`flex h-[46px] items-center justify-center self-center font-mono text-[11px] transition ${
                        row.isNew
                          ? "text-emerald-400"
                          : "text-slate-600 group-hover:text-emerald-400"
                      }`}
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
