/**
 * Shared table + row expansion for pipeline / home / dashboard-style lead lists.
 */

import LeadDetailPanel from "@/components/leads/LeadDetailPanel";
import SignupLeadsBlur from "@/components/leads/SignupLeadsBlur";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { LeadRow } from "@/lib/leadTypes";
import { scoreNum } from "@/lib/leadTypes";
import { cn } from "@/lib/utils";
import { ChevronDownIcon } from "lucide-react";
import { Fragment, useEffect, useMemo } from "react";
import { Link } from "wouter";

function initialDot(lead: LeadRow): { ch: string; bg: string } {
  const n = (lead.company_name || "?").trim();
  const ch = n.charAt(0).toUpperCase() || "?";
  const tier = lead.priority_tier;
  if (tier === "HOT") return { ch, bg: "oklch(0.627 0.163 66.5)" };
  if (tier === "WARM") return { ch, bg: "oklch(0.55 0.12 250)" };
  return { ch, bg: "oklch(0.488 0.243 264.376)" };
}

function pipelineStatusLabel(lead: LeadRow): { label: string; warm: boolean } {
  const g = lead.gtm as { readiness_label?: string } | null | undefined;
  const r = g?.readiness_label?.trim();
  if (r) {
    const low = r.toLowerCase();
    const warm = low.includes("nurture") || low.includes("early") || lead.priority_tier === "WARM";
    return { label: r, warm };
  }
  if (lead.priority_tier === "WARM") return { label: "Warm Lead", warm: true };
  if (lead.priority_tier === "HOT") return { label: "Hot Lead", warm: false };
  return { label: "Emerging", warm: true };
}

function statusBadge(label: string, warm: boolean) {
  if (warm && !label.toLowerCase().includes("eval") && !label.toLowerCase().includes("active")) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-sky-400 bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-950">
        {label}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-amber-400 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-950">
      🔥 {label}
    </span>
  );
}

function tierBadgeVariant(_tier: string | undefined): "default" | "secondary" | "outline" | "destructive" {
  return "outline";
}

function tierBadgeClass(tier: string | undefined): string {
  if (tier === "HOT") return "border-orange-400 text-orange-950 bg-orange-50 font-semibold";
  if (tier === "WARM") return "border-sky-400 text-sky-950 bg-sky-50 font-semibold";
  return "border-gray-400 text-gray-900 bg-gray-50 font-semibold";
}

type Props = {
  leads: LeadRow[];
  loading: boolean;
  error: string | null;
  expandedId: number | null;
  onToggle: (id: number | null) => void;
  /** Browser chrome URL bar text */
  urlBar?: string;
  /** e.g. "12 ACTIVE · 8 HOT · 120 SIGNALS" */
  statsLine?: string | null;
  density?: "default" | "compact";
  /** Full rows shown without blur; remainder is blurred with signup CTA. */
  previewLimit?: number;
  showSignupBlur?: boolean;
  signupHref?: string;
  /** Per-row primary CTA (contrast + affordance). */
  showAnalyzeCta?: boolean;
};

export default function ExpandableLeadsTable({
  leads,
  loading,
  error,
  expandedId,
  onToggle,
  urlBar = "readyforrobots.com/pipeline",
  statsLine,
  density = "default",
  previewLimit = 10,
  showSignupBlur = true,
  signupHref = "/login",
  showAnalyzeCta = true,
}: Props) {
  const compact = density === "compact";
  const hotN = leads.filter((l) => l.priority_tier === "HOT").length;
  const totalSig = leads.reduce((a, l) => a + (l.signal_count || (l.signals || []).length || 0), 0);
  const unlocked = useMemo(
    () => (showSignupBlur ? leads.slice(0, previewLimit) : leads),
    [leads, previewLimit, showSignupBlur]
  );
  const hasWall = showSignupBlur && leads.length > previewLimit;

  useEffect(() => {
    if (expandedId == null) return;
    if (!unlocked.some((l) => l.id === expandedId)) {
      onToggle(null);
    }
  }, [expandedId, unlocked, onToggle]);

  const line =
    statsLine ??
    (leads.length
      ? hasWall
        ? `${previewLimit} unlocked preview · ${leads.length - previewLimit} locked · ${hotN} HOT · ${totalSig} signals`
        : `${leads.length} ACTIVE · ${hotN} HOT · ${totalSig} SIGNALS`
      : null);

  if (error) {
    return <p className="text-sm text-amber-800 bg-amber-50 border border-amber-100 rounded-md p-4">{error}</p>;
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-300 bg-white p-6 space-y-2 shadow-md">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!leads.length) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
        No leads returned. Check the API or filters.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-300 bg-white overflow-hidden shadow-lg ring-1 ring-black/5">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-200 bg-gray-50/90">
        <span className="flex gap-1.5">
          <span className="h-3 w-3 rounded-full bg-red-400/90" />
          <span className="h-3 w-3 rounded-full bg-amber-400/90" />
          <span className="h-3 w-3 rounded-full bg-emerald-400/90" />
        </span>
        <div className="flex-1 flex justify-center px-4">
          <div className="w-full max-w-md rounded-md border border-dashed border-gray-400 bg-white px-3 py-1.5 text-xs text-gray-700 font-mono text-center truncate">
            {urlBar}
          </div>
        </div>
      </div>

      {line ? (
        <div className="px-4 py-2.5 border-b border-gray-200 flex flex-wrap items-center justify-end gap-2 text-xs bg-gray-50/60">
          <span className="inline-flex items-center gap-1.5 font-semibold text-gray-800">
            <span className="h-2 w-2 rounded-full bg-emerald-600 shadow-[0_0_0_2px_rgba(5,150,105,0.25)]" />
            {line}
          </span>
        </div>
      ) : null}

      <div className="overflow-x-auto px-3 sm:px-5 pb-2">
        <Table className="min-w-[720px]">
          <TableHeader>
            <TableRow className="hover:bg-transparent border-b-2 border-gray-200 bg-gray-100/95">
              <TableHead className="w-10" aria-label="Expand" />
              <TableHead className="text-[11px] uppercase tracking-wide text-gray-800 font-bold">Company</TableHead>
              <TableHead className="text-[11px] uppercase tracking-wide text-gray-800 font-bold">Tier</TableHead>
              <TableHead className="text-[11px] uppercase tracking-wide text-gray-800 font-bold">Status</TableHead>
              <TableHead className="text-[11px] uppercase tracking-wide text-gray-800 font-bold text-right w-16">
                Sig
              </TableHead>
              <TableHead className="text-[11px] uppercase tracking-wide text-gray-800 font-bold text-right w-16">
                Val
              </TableHead>
              <TableHead className="text-[11px] uppercase tracking-wide text-gray-800 font-bold text-right w-20">
                Intent
              </TableHead>
              {showAnalyzeCta ? (
                <TableHead className="text-[11px] uppercase tracking-wide text-gray-800 font-bold text-right w-[7.5rem] pr-1 sm:pr-2">
                  Action
                </TableHead>
              ) : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {unlocked.map((lead) => {
              const dot = initialDot(lead);
              const st = pipelineStatusLabel(lead);
              const sig = Math.round(scoreNum(lead, "signal_score"));
              const val = Math.round(scoreNum(lead, "lead_value_score"));
              const intent = Math.round(scoreNum(lead, "overall_score"));
              const open = expandedId === lead.id;
              return (
                <Fragment key={lead.id}>
                  <TableRow className={open ? "bg-emerald-50/40" : "hover:bg-gray-50/90 border-b border-gray-100"}>
                    <TableCell className="align-middle py-2.5">
                      <button
                        type="button"
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border-2 border-gray-300 bg-white text-gray-800 hover:border-gray-500 hover:bg-gray-50"
                        aria-expanded={open}
                        aria-label={open ? "Collapse row" : "Expand row"}
                        onClick={() => onToggle(open ? null : lead.id)}
                      >
                        <ChevronDownIcon className={cn("h-4 w-4 transition-transform", open && "rotate-180")} />
                      </button>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div
                          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm ring-2 ring-white"
                          style={{ backgroundColor: dot.bg }}
                        >
                          {dot.ch}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-950">{lead.company_name || "—"}</div>
                          <div className="text-xs text-gray-600">{lead.industry || "—"}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={tierBadgeVariant(lead.priority_tier)} className={tierBadgeClass(lead.priority_tier)}>
                        {lead.priority_tier || "—"}
                      </Badge>
                    </TableCell>
                    <TableCell>{statusBadge(st.label, st.warm)}</TableCell>
                    <TableCell className="text-right font-mono text-sm font-semibold text-amber-700 tabular-nums">
                      {sig}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm font-semibold text-sky-700 tabular-nums">
                      {val}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm font-semibold text-indigo-900 tabular-nums">
                      {intent}
                    </TableCell>
                    {showAnalyzeCta ? (
                      <TableCell className="text-right align-middle py-2.5 pr-1 sm:pr-2">
                        <Link
                          href={signupHref}
                          className="btn-marketing-row"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Analyze
                          <span aria-hidden>→</span>
                        </Link>
                      </TableCell>
                    ) : null}
                  </TableRow>
                  {open ? (
                    <TableRow className="bg-gray-50/40 hover:bg-gray-50/40 border-t border-gray-100">
                      <TableCell colSpan={showAnalyzeCta ? 8 : 7} className={compact ? "p-3 md:p-4" : "p-4 md:p-6"}>
                        <LeadDetailPanel lead={lead} density={compact ? "compact" : "default"} />
                      </TableCell>
                    </TableRow>
                  ) : null}
                </Fragment>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {hasWall ? <SignupLeadsBlur leads={leads} previewLimit={previewLimit} signupHref={signupHref} /> : null}
    </div>
  );
}
