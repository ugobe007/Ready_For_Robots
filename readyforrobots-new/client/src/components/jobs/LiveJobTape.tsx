/**
 * Live job tape — 12 classified rows at 58px. Rows are absolutely
 * positioned for the rotate animation, so the list viewport must set
 * its own height. Do not size it with h-full of a parent pane.
 * Exact row grid: 48 | 34 | 1fr | 24. Reveal mode: rapid 0001→N after robot submit.
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
/** Rows are `position: absolute`; this is the only height the list has. */
export const TAPE_VISIBLE_ROWS = VISIBLE;
export const TAPE_ROW_PX = ROW_PX;
export const TAPE_VIEWPORT_PX = VISIBLE * ROW_PX;
const SHIFT_MS = 200;
const NEW_HOLD_MS = 1500;
const INTERVAL_MIN = 5000;
const INTERVAL_MAX = 7000;
/** 16×16 map → 24px (fits 34px icon column; stronger Kare presence) */
const ICON_SCALE = 24 / 16;
/** Discovery reveal: keep whole theater under ~2.5s for the count-up leg. */
const REVEAL_BUDGET_MS = 2200;
const REVEAL_MIN_STEP_MS = 45;
const REVEAL_MAX_STEP_MS = 120;

type Row = TapeJob & {
  instanceId: string;
  seq: number;
  isNew: boolean;
};

type Props = {
  title: string;
  /** Optional customer-facing note under the title (e.g. corpus match disclaimer). */
  subtitle?: string | null;
  corpus: TapeJob[];
  baseCount: number;
  running?: boolean;
  statusLines?: string[];
  /** When set, empty board then count 1→target with rapid row arrivals. */
  revealTarget?: number | null;
  onRevealComplete?: () => void;
  onSelect?: (job: TapeJob) => void;
  selectedKey?: string | null;
};

function padCount(n: number): string {
  return String(Math.max(0, n)).padStart(4, "0");
}

function jobsFoundLabel(n: number): string {
  if (n === 1) return `${padCount(1)} Job Found`;
  return `${padCount(n)} Jobs Found`;
}

function nextInterval(): number {
  return INTERVAL_MIN + Math.floor(Math.random() * (INTERVAL_MAX - INTERVAL_MIN));
}

function revealStepMs(target: number): number {
  if (target <= 1) return REVEAL_BUDGET_MS;
  const raw = Math.floor(REVEAL_BUDGET_MS / target);
  return Math.min(REVEAL_MAX_STEP_MS, Math.max(REVEAL_MIN_STEP_MS, raw));
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
  subtitle = null,
  corpus,
  baseCount,
  running = true,
  statusLines,
  revealTarget = null,
  onRevealComplete,
  onSelect,
  selectedKey,
}: Props) {
  const revealing = typeof revealTarget === "number" && revealTarget > 0;
  const [rows, setRows] = useState<Row[]>(() => (revealing ? [] : seedRows(corpus, baseCount)));
  const [foundCount, setFoundCount] = useState(revealing ? 0 : baseCount);
  const [offsetY, setOffsetY] = useState(0);
  const [animate, setAnimate] = useState(false);
  const [iconActive, setIconActive] = useState(false);
  const cursorRef = useRef(0);
  const seqRef = useRef(revealing ? 0 : baseCount);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const arriving = useRef(false);
  const revealDone = useRef(false);
  const seededKey = useRef(`${revealing}:${baseCount}`);
  const onRevealCompleteRef = useRef(onRevealComplete);
  onRevealCompleteRef.current = onRevealComplete;

  useEffect(() => {
    const key = `${revealing}:${baseCount}:${corpus.length}`;
    if (revealing) {
      setRows([]);
      setFoundCount(0);
      seqRef.current = 0;
      cursorRef.current = 0;
      revealDone.current = false;
      setOffsetY(0);
      setAnimate(false);
      seededKey.current = key;
      return;
    }
    if (seededKey.current === key && rows.length > 0) return;
    seededKey.current = key;
    setRows(seedRows(corpus, baseCount));
    setFoundCount(baseCount);
    seqRef.current = baseCount;
    cursorRef.current = VISIBLE % Math.max(corpus.length, 1);
    setOffsetY(0);
    setAnimate(false);
    // rows.length is only a skip-on-mount guard; do not re-seed every paint.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [corpus, baseCount, revealing, revealTarget]);

  useEffect(() => {
    return () => {
      timers.current.forEach(clearTimeout);
    };
  }, []);

  /** Market live feed — paused during status/reveal. */
  useEffect(() => {
    if (revealing || !running || corpus.length === 0) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    const schedule = () => {
      timeoutId = setTimeout(() => {
        if (cancelled) return;
        arrive(false);
        schedule();
      }, nextInterval());
    };

    schedule();
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, corpus, revealing]);

  /** Discovery reveal — rapid count-up. */
  useEffect(() => {
    if (!revealing || !revealTarget || corpus.length === 0) return;

    let cancelled = false;
    const step = revealStepMs(revealTarget);
    let n = 0;

    const tick = () => {
      if (cancelled) return;
      n += 1;
      arrive(true, n);
      if (n >= revealTarget) {
        later(() => {
          if (cancelled || revealDone.current) return;
          revealDone.current = true;
          onRevealCompleteRef.current?.();
        }, SHIFT_MS + 80);
        return;
      }
      later(tick, step);
    };

    later(tick, 40);
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revealing, revealTarget, corpus]);

  function later(fn: () => void, ms: number) {
    const id = setTimeout(fn, ms);
    timers.current.push(id);
  }

  function arrive(fromReveal: boolean, forcedSeq?: number) {
    if (corpus.length === 0) return;
    if (!fromReveal && arriving.current) return;
    if (!fromReveal) arriving.current = true;

    const job = corpus[cursorRef.current % corpus.length];
    cursorRef.current = (cursorRef.current + 1) % corpus.length;
    const nextSeq = forcedSeq ?? seqRef.current + 1;
    seqRef.current = nextSeq;
    const instanceId = `${job.key}_${nextSeq}_${Date.now()}`;

    setIconActive(true);
    setFoundCount(nextSeq);

    setAnimate(false);
    setOffsetY(-ROW_PX);
    setRows((prev) => {
      const cleared = prev.map((r) => ({ ...r, isNew: false }));
      const incoming: Row = { ...job, instanceId, seq: nextSeq, isNew: true };
      return [incoming, ...cleared].slice(0, VISIBLE + 1);
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
      if (!fromReveal) arriving.current = false;
    }, fromReveal ? Math.min(SHIFT_MS, 90) : SHIFT_MS);
    later(() => setIconActive(false), fromReveal ? 160 : 420);
    if (!fromReveal) {
      later(() => {
        setRows((prev) => prev.map((r) => (r.instanceId === instanceId ? { ...r, isNew: false } : r)));
      }, NEW_HOLD_MS);
    }
  }

  const showStatus = Boolean(statusLines?.length) && !revealing;

  return (
    <div className="flex flex-col bg-[#081126]">
      <div className="shrink-0 border-b border-slate-600 px-4 py-2.5">
        <div className="flex items-center justify-between gap-3">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-100 sm:text-[12px]">
            {title}
          </p>
          <p className="font-mono text-[13px] font-bold uppercase tracking-[0.08em] tabular-nums text-emerald-400 sm:text-[14px]">
            <span>{jobsFoundLabel(foundCount)}</span>
          </p>
        </div>
        <p className="mt-0.5 font-mono text-[9px] font-semibold uppercase tracking-[0.16em] text-slate-600">
          {revealing ? "Matching work to your robot" : "Live robot work"}
        </p>
        {subtitle ? (
          <p className="mt-1.5 max-w-xl text-[11px] leading-snug normal-case tracking-normal text-slate-500">
            {subtitle}
          </p>
        ) : null}
      </div>

      {showStatus ? (
        <div
          className="flex flex-col justify-center gap-2 px-5 py-8 font-mono text-[12px] font-semibold uppercase tracking-[0.1em] text-slate-400"
          style={{ minHeight: TAPE_VIEWPORT_PX }}
        >
          {statusLines!.map((line) => (
            <p
              key={line}
              className={
                line.includes("✓") || line.startsWith(">") ? "text-emerald-400" : undefined
              }
            >
              {line}
            </p>
          ))}
        </div>
      ) : (
        <div
          className="relative overflow-hidden"
          style={{ height: TAPE_VIEWPORT_PX }}
        >
          <ul
            className="absolute inset-x-0 top-0"
            style={{
              transform: `translateY(${offsetY}px)`,
              transition: animate
                ? `transform ${revealing ? 90 : SHIFT_MS}ms linear`
                : "none",
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
                    <span
                      className={`font-mono text-[10px] font-semibold leading-4 tabular-nums ${
                        row.isNew ? "text-emerald-400" : "text-slate-500"
                      }`}
                    >
                      {row.isNew ? "NEW" : padCount(row.seq).slice(-3)}
                    </span>

                    <span className="flex h-[46px] items-center justify-center self-center">
                      <PixelIcon
                        map={map}
                        scale={ICON_SCALE}
                        fill={FACE_EMERALD}
                        background="transparent"
                      />
                    </span>

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
