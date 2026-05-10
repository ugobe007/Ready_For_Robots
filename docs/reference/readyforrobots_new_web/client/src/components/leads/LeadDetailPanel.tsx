/**
 * Expandable lead body — aligned with Next.js search/dashboard CRM highlights + API fields.
 */

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CrmMetadata, GtmPayload, LeadRow, LeadSignal } from "@/lib/leadTypes";
import { scoreNum, signalDisplayExcerpt, signalStrengthPct } from "@/lib/leadTypes";
import { Link } from "wouter";
import { useState } from "react";

function safeJson(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function isGtm(g: unknown): g is GtmPayload {
  return typeof g === "object" && g !== null;
}

const GTM_MOTION_ICON: Record<string, string> = {
  "direct outreach": "📞",
  "demo request": "🖥️",
  "event follow-up": "🎪",
  "partner channel": "🤝",
  "content play": "📄",
};

function motionIconFor(motion: string | undefined): string {
  if (!motion) return "→";
  const low = motion.toLowerCase();
  const hit = Object.keys(GTM_MOTION_ICON).find((k) => low.includes(k));
  return hit ? GTM_MOTION_ICON[hit]! : "→";
}

type Density = "default" | "compact";

type Props = {
  lead: LeadRow;
  density?: Density;
  /** Show deep-link to dashboard (matches Next.js “Full analysis →”). */
  showFullAnalysisLink?: boolean;
};

export default function LeadDetailPanel({ lead, density = "default", showFullAnalysisLink = true }: Props) {
  const [showAutomationJson, setShowAutomationJson] = useState(false);
  const compact = density === "compact";
  const scorePayload = lead.score as Record<string, unknown> | undefined;
  const textMain = compact ? "text-xs" : "text-sm";
  const labelCls = "text-[10px] font-semibold uppercase tracking-wide text-gray-500";
  const crm = lead.crm_metadata as CrmMetadata | null | undefined;
  const gtm = isGtm(lead.gtm) ? lead.gtm : null;
  const whyNow = gtm?.why_now;
  const whyLines = Array.isArray(whyNow) ? whyNow : whyNow ? [String(whyNow)] : [];

  const sc = lead.score as Record<string, unknown> | undefined;
  const scoreGrid = [
    { label: "Automation", val: scoreNum(lead, "automation_score") },
    { label: "Labor pain", val: scoreNum(lead, "labor_pain_score") },
    { label: "Expansion", val: scoreNum(lead, "expansion_score") },
    { label: "Market fit", val: scoreNum(lead, "market_fit_score") },
  ];

  const sigScore = Math.round(scoreNum(lead, "signal_score"));
  const valScore = Math.round(scoreNum(lead, "lead_value_score"));
  const intentScore = Math.round(scoreNum(lead, "overall_score"));

  return (
    <div className={`space-y-4 text-gray-800 ${compact ? "py-1" : "py-2"} ${textMain}`}>
      {/* CRM highlights (GTM) — same idea as frontend/nextjs/pages/search.js LeadPanel */}
      {(gtm?.readiness_label ||
        gtm?.suggested_motion ||
        whyLines.length > 0 ||
        (lead.priority_reasons && lead.priority_reasons.length > 0)) && (
        <div className="rounded-lg border border-gray-300 bg-transparent px-3 py-3">
          <p className={`${labelCls} text-gray-700 mb-2`}>CRM highlights</p>
          <div className="flex flex-wrap gap-4">
            {gtm?.readiness_label ? (
              <div className="min-w-[120px]">
                <span className={`${labelCls} block mb-0.5`}>Readiness</span>
                <span
                  className={`font-semibold ${
                    gtm.readiness_label.toLowerCase().includes("active") ||
                    gtm.readiness_label.toLowerCase().includes("deploy")
                      ? "text-orange-700"
                      : gtm.readiness_label.toLowerCase().includes("warm") ||
                          gtm.readiness_label.toLowerCase().includes("evaluat")
                        ? "text-amber-700"
                        : "text-sky-800"
                  }`}
                >
                  {gtm.readiness_label}
                </span>
              </div>
            ) : null}
            {gtm?.suggested_motion ? (
              <div className="min-w-[130px]">
                <span className={`${labelCls} block mb-0.5`}>Sales motion</span>
                <span className="text-gray-800">
                  {motionIconFor(gtm.suggested_motion)} {gtm.suggested_motion}
                </span>
              </div>
            ) : null}
            {whyLines.length > 0 ? (
              <div className="min-w-[160px] flex-1">
                <span className={`${labelCls} block mb-0.5`}>Why now</span>
                <ul className="list-disc list-inside text-gray-700 space-y-0.5">
                  {whyLines.slice(0, 4).map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
          {lead.priority_reasons && lead.priority_reasons.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {lead.priority_reasons.slice(0, 6).map((reason, i) => (
                <span
                  key={i}
                  className="text-[10px] px-2 py-0.5 rounded border border-gray-200 bg-white text-gray-600"
                >
                  {reason}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      )}

      {/* Intent score breakdown (matches homepage expanded deal) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {scoreGrid.map(({ label, val }) => (
          <div key={label} className="rounded-md border border-gray-200 bg-transparent p-2 text-center">
            <div className={`font-bold tabular-nums ${compact ? "text-sm" : "text-base"} text-gray-900`}>
              {Math.round(val)}
            </div>
            <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-3 text-xs text-gray-600 border-b border-gray-100 pb-3">
        <span>
          <span className={labelCls}>Signal</span>{" "}
          <strong className="text-amber-800 tabular-nums">{sigScore}</strong>
        </span>
        <span>
          <span className={labelCls}>Value</span>{" "}
          <strong className="text-sky-800 tabular-nums">{valScore}</strong>
        </span>
        <span>
          <span className={labelCls}>Intent</span>{" "}
          <strong className="text-indigo-900 tabular-nums">{intentScore}</strong>
        </span>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <div>
          <span className={labelCls}>Website / link</span>
          <p className="mt-0.5">
            {lead.primary_link_url ? (
              <a
                href={lead.primary_link_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-700 underline break-all"
              >
                {lead.primary_link_url}
              </a>
            ) : lead.website ? (
              <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-emerald-700 underline break-all">
                {lead.website}
              </a>
            ) : (
              <span className="text-gray-500">—</span>
            )}
            {lead.primary_link_kind ? (
              <span className="ml-2 text-[10px] text-gray-500">({lead.primary_link_kind})</span>
            ) : null}
          </p>
        </div>
        <div>
          <span className={labelCls}>Location & scale</span>
          <p className="mt-0.5">
            {[lead.location_city, lead.location_state].filter(Boolean).join(", ") || "—"}
            {lead.employee_estimate != null && lead.employee_estimate > 0 ? (
              <span className="text-gray-600"> · ~{lead.employee_estimate.toLocaleString()} employees</span>
            ) : null}
          </p>
          {lead.source ? <p className="text-[10px] text-gray-500 mt-1">Source: {lead.source}</p> : null}
        </div>
      </div>

      {lead.procurement_hints && lead.procurement_hints.length > 0 ? (
        <div>
          <span className={labelCls}>Procurement hints</span>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {lead.procurement_hints.map((h, i) => (
              <Badge key={i} variant="outline" className="text-[10px] font-normal">
                {h}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {lead.junk_reason ? (
        <p className="text-amber-900 bg-amber-50 border border-amber-100 rounded-md px-3 py-2 text-xs">
          <strong>Quality flag:</strong> {lead.junk_reason}
        </p>
      ) : null}

      {lead.core_need ? (
        <div>
          <span className={labelCls}>Core need</span>
          <p className="mt-1 text-gray-900 font-medium leading-relaxed">{lead.core_need}</p>
        </div>
      ) : null}

      {lead.share_summary ? (
        <div>
          <span className={labelCls}>Intelligence brief</span>
          <p className="mt-1 text-gray-700 leading-relaxed">{lead.share_summary}</p>
        </div>
      ) : null}

      {lead.signals && lead.signals.length > 0 ? (
        <div>
          <span className={labelCls}>
            Signal intelligence
            {lead.signal_count != null && lead.signal_count > lead.signals.length ? (
              <span className="ml-1 font-normal normal-case text-gray-400">
                ({lead.signal_count} on file, top {lead.signals.length} shown)
              </span>
            ) : null}
          </span>
          <ul className="mt-2 space-y-2">
            {lead.signals.map((s: LeadSignal, i: number) => {
              const pct = signalStrengthPct(s);
              const excerpt = signalDisplayExcerpt(s);
              return (
                <li key={i} className="border border-gray-100 rounded-md p-2 bg-white">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                    <Badge variant="outline" className="text-xs">
                      {s.signal_label || s.signal_type}
                    </Badge>
                    <div className="flex items-center gap-2 min-w-[88px]">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden max-w-[72px]">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-[10px] text-gray-500 tabular-nums w-8">{pct}%</span>
                    </div>
                  </div>
                  {excerpt ? <p className="text-gray-700 text-xs leading-relaxed">{excerpt}</p> : null}
                  {s.source_url ? (
                    <a
                      href={s.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-emerald-700 underline mt-1 inline-block break-all"
                    >
                      Source →
                    </a>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <div>
        <span className={labelCls}>CRM (extracted)</span>
        {!crm || Object.keys(crm).length === 0 ? (
          <p className="mt-1 text-gray-500 text-xs">
            No extracted CRM block yet — run the enrichment worker in production for budget, timing, and decision
            makers.
          </p>
        ) : (
          <div className="mt-2 space-y-3 border border-gray-100 rounded-md p-3 bg-white">
            {crm.budget?.top_amount || (crm.budget?.signals && crm.budget.signals.length) ? (
              <div>
                <p className="text-xs font-medium text-gray-600">Budget</p>
                {crm.budget?.top_amount ? <p className="text-gray-800">{crm.budget.top_amount}</p> : null}
              </div>
            ) : null}
            {crm.timing?.top_window || (crm.timing?.signals && crm.timing.signals.length) ? (
              <div>
                <p className="text-xs font-medium text-gray-600">Timing</p>
                {crm.timing?.top_window ? <p className="text-gray-800">{crm.timing.top_window}</p> : null}
              </div>
            ) : null}
            {crm.automation_requirements ? (
              <div>
                <p className="text-xs font-medium text-gray-600">Automation requirements</p>
                <p className="text-gray-800 whitespace-pre-wrap text-xs">{crm.automation_requirements}</p>
              </div>
            ) : null}
            {crm.decision_makers && crm.decision_makers.length > 0 ? (
              <div>
                <p className="text-xs font-medium text-gray-600">Decision makers</p>
                <ul className="mt-1 space-y-1">
                  {crm.decision_makers.map((dm, i) => (
                    <li key={i} className="text-xs">
                      <span className="font-medium">{dm.name || "—"}</span>
                      {dm.title ? <span className="text-gray-600"> — {dm.title}</span> : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {crm.quality_flags && Object.keys(crm.quality_flags).length > 0 ? (
              <pre
                className={`text-[10px] overflow-auto bg-gray-50 rounded p-2 border border-gray-100 ${
                  compact ? "max-h-28" : "max-h-36"
                }`}
              >
                {safeJson(crm.quality_flags)}
              </pre>
            ) : null}
          </div>
        )}
      </div>

      {lead.automation_profile && Object.keys(lead.automation_profile).length > 0 ? (
        <div className="space-y-2">
          <span className={labelCls}>Automation profile</span>
          {(() => {
            const ap = lead.automation_profile as Record<string, unknown>;
            const conf = typeof ap.confidence === "string" ? ap.confidence : "";
            const notes = typeof ap.sizing_notes === "string" ? ap.sizing_notes : "";
            const cats = Array.isArray(ap.robot_categories) ? ap.robot_categories.map(String) : [];
            const apps = Array.isArray(ap.application_areas) ? ap.application_areas.map(String) : [];
            const dep = Array.isArray(ap.deployment_contexts) ? ap.deployment_contexts.map(String) : [];
            const hrc = typeof ap.human_robot_collaboration === "string" ? ap.human_robot_collaboration : "";
            return (
              <div className="rounded-lg border border-gray-300 bg-transparent p-3 space-y-2">
                <div className="flex flex-wrap gap-2 items-center text-xs">
                  {conf ? (
                    <span className="rounded-md border border-gray-400 px-2 py-0.5 font-medium text-gray-800">
                      Confidence: {conf}
                    </span>
                  ) : null}
                  {typeof ap.source === "string" ? (
                    <span className="rounded-md border border-gray-300 px-2 py-0.5 text-gray-600">{ap.source}</span>
                  ) : null}
                </div>
                {notes ? <p className="text-xs text-gray-700 leading-relaxed">{notes}</p> : null}
                {cats.length ? (
                  <div>
                    <span className={labelCls}>Robot categories</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {cats.map((c) => (
                        <span key={c} className="text-[10px] rounded-md border border-gray-300 px-2 py-0.5 text-gray-800">
                          {c.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {apps.length ? (
                  <div>
                    <span className={labelCls}>Application areas</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {apps.map((c) => (
                        <span key={c} className="text-[10px] rounded-md border border-gray-300 px-2 py-0.5 text-gray-700">
                          {c.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {dep.length ? (
                  <div>
                    <span className={labelCls}>Deployment contexts</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {dep.map((c) => (
                        <span key={c} className="text-[10px] rounded-md border border-gray-300 px-2 py-0.5 text-gray-700">
                          {c.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {hrc ? (
                  <p className="text-xs text-gray-600">
                    <span className={labelCls}>Human–robot collaboration</span> {hrc}
                  </p>
                ) : null}
                <div className="pt-1">
                  <button
                    type="button"
                    onClick={() => setShowAutomationJson((v) => !v)}
                    className="text-xs font-medium text-gray-600 hover:text-gray-900 underline-offset-2 hover:underline"
                  >
                    {showAutomationJson ? "Hide machine-readable JSON" : "Show machine-readable JSON"}
                  </button>
                  {showAutomationJson ? (
                    <pre
                      className={`mt-2 text-[10px] overflow-auto rounded-md p-2 border border-gray-200 bg-white font-mono ${
                        compact ? "max-h-28" : "max-h-40"
                      }`}
                    >
                      {safeJson(lead.automation_profile)}
                    </pre>
                  ) : null}
                </div>
              </div>
            );
          })()}
        </div>
      ) : null}

      {scorePayload && Object.keys(scorePayload).length > 0 && !compact ? (
        <details className="rounded-md border border-gray-100 bg-gray-50/50 px-3 py-2">
          <summary className="text-xs font-medium text-gray-600 cursor-pointer">Raw score payload</summary>
          <pre className="mt-2 text-[10px] overflow-auto max-h-40">{safeJson(scorePayload)}</pre>
        </details>
      ) : null}

      {showFullAnalysisLink && lead.id > 0 ? (
        <div className="pt-1">
          <Button variant="outline" size="sm" className="border-emerald-200 text-emerald-900" asChild>
            <Link href={`/dashboard?analyze=${lead.id}`}>Open in dashboard (deep link) →</Link>
          </Button>
        </div>
      ) : null}
    </div>
  );
}
