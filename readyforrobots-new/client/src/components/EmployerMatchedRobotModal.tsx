/**
 * Catalog robot facts for employer MATCH. Named SKU only. No invented specs.
 */
import { useEffect } from "react";
import {
  EMPLOYER_EXAMINE_CLOSE,
  EMPLOYER_EXAMINE_EMPTY,
  EMPLOYER_SHORTLIST_ADD,
  EMPLOYER_SHORTLIST_DROP,
} from "@/lib/jobsLanding";
import { JOBS_EYEBROW_CLASS, JOBS_FIND_CTA_CLASS } from "@/lib/jobsWorkflow";
import {
  catalogHttpUrl,
  catalogSpecRows,
  type EmployerMatchedRobot,
} from "@/lib/employerRobotMatch";

type Props = {
  robot: EmployerMatchedRobot;
  shortlisted: boolean;
  onToggleShortlist: () => void;
  onClose: () => void;
};

export default function EmployerMatchedRobotModal({
  robot,
  shortlisted,
  onToggleShortlist,
  onClose,
}: Props) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const productUrl = catalogHttpUrl(robot.product_url);
  const vendorUrl = catalogHttpUrl(robot.vendor_url);
  const imageUrl = catalogHttpUrl(robot.image_url);
  const specs = catalogSpecRows(robot.specs);
  const classLabel = robot.robot_class
    ? robot.robot_class.replace(/_/g, " ")
    : null;
  const hasFacts = Boolean(
    robot.description || robot.task || robot.setting || specs.length || imageUrl
  );

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center overflow-y-auto p-4 sm:p-6">
      <div
        className="fixed inset-0 bg-slate-950/80"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Catalog robot"
        className="relative z-10 my-auto w-full max-w-xl border border-slate-600 bg-[#0b162f] text-slate-100"
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-600 bg-[#081126] px-5 py-4">
          <div className="min-w-0">
            <p className={JOBS_EYEBROW_CLASS}>Catalog robot</p>
            <h2 className="mt-1 font-display text-xl font-bold text-slate-100">
              {robot.name}
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              {robot.vendor_name}
              {classLabel ? ` · ${classLabel}` : ""}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400 hover:text-slate-200"
          >
            {EMPLOYER_EXAMINE_CLOSE}
          </button>
        </div>
        <div className="space-y-4 px-5 py-5">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt=""
              className="max-h-48 w-full object-contain bg-[#081126]"
            />
          ) : null}
          {robot.description ? (
            <p className="text-sm leading-snug text-slate-200">
              {robot.description}
            </p>
          ) : null}
          {robot.task || robot.setting ? (
            <dl className="space-y-2 text-sm">
              {robot.task ? (
                <div className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3">
                  <dt className="text-slate-500">Work</dt>
                  <dd className="text-slate-100">{robot.task}</dd>
                </div>
              ) : null}
              {robot.setting ? (
                <div className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3">
                  <dt className="text-slate-500">Setting</dt>
                  <dd className="text-slate-100">{robot.setting}</dd>
                </div>
              ) : null}
            </dl>
          ) : null}
          {specs.length ? (
            <dl className="space-y-2 text-sm">
              {specs.map(row => (
                <div
                  key={row.label}
                  className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3"
                >
                  <dt className="text-slate-500">{row.label}</dt>
                  <dd className="text-slate-100">{row.value}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          {!hasFacts ? (
            <p className="text-sm leading-snug text-slate-400">
              {EMPLOYER_EXAMINE_EMPTY}
            </p>
          ) : null}
          {productUrl || vendorUrl ? (
            <ul className="space-y-1 text-sm">
              {productUrl ? (
                <li>
                  <a
                    href={productUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-300 hover:text-emerald-200"
                  >
                    Product page →
                  </a>
                </li>
              ) : null}
              {vendorUrl && vendorUrl !== productUrl ? (
                <li>
                  <a
                    href={vendorUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-300 hover:text-slate-100"
                  >
                    OEM site →
                  </a>
                </li>
              ) : null}
            </ul>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-600 px-5 py-4">
          <button
            type="button"
            onClick={onToggleShortlist}
            className="font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-300 hover:text-slate-100"
          >
            {shortlisted ? EMPLOYER_SHORTLIST_DROP : EMPLOYER_SHORTLIST_ADD}
          </button>
          <button
            type="button"
            onClick={onClose}
            className={JOBS_FIND_CTA_CLASS}
          >
            {EMPLOYER_EXAMINE_CLOSE}
          </button>
        </div>
      </div>
    </div>
  );
}
