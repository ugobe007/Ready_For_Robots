/**
 * Pipeline — ReadyForRobots
 * Two-panel layout: left = inline deal rows grouped by stage, right = selected deal detail + outreach draft
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 * Design: Linear/Raycast-inspired — dense, inline, data-forward
 */
import { useEffect, useState } from "react";
import {
  AlertTriangle, MapPin, Zap, Filter, ChevronRight,
  Copy, CheckCheck, ArrowRight, ArrowLeft, Mail,
  TrendingUp, Users, Clock, Target, X
} from "lucide-react";
import Header from "@/components/Header";
import { toast } from "sonner";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { mapApiLeadToDeal, type ApiLead } from "@/lib/pipelineLeadMap";

type Stage = "New Signal" | "Draft Ready" | "Outreach Sent" | "Qualified" | "Meeting Set";

interface Deal {
  id: number;
  company: string;
  location: string;
  industry: string;
  score: number;
  signal: string;
  signalType: string;
  signalColor: string;
  stage: Stage;
  updatedAt: string;
  contact?: string;
  contactTitle?: string;
  outreachSubject?: string;
  outreachBody?: string;
  notes?: string;
}

const STAGES: Stage[] = ["New Signal", "Draft Ready", "Outreach Sent", "Qualified", "Meeting Set"];

const STAGE_META: Record<Stage, { color: string; dot: string; label: string; desc: string }> = {
  "New Signal":    { color: "#a78bfa", dot: "#a78bfa", label: "New Signal",    desc: "Just detected" },
  "Draft Ready":   { color: "#60a5fa", dot: "#60a5fa", label: "Draft Ready",   desc: "Outreach drafted" },
  "Outreach Sent": { color: "#fb923c", dot: "#fb923c", label: "Outreach Sent", desc: "Awaiting reply" },
  "Qualified":     { color: "#34d399", dot: "#34d399", label: "Qualified",     desc: "Engaged buyer" },
  "Meeting Set":   { color: "#f472b6", dot: "#f472b6", label: "Meeting Set",   desc: "On the calendar" },
};

const scoreColor = (s: number) =>
  s >= 90 ? "#34d399" : s >= 75 ? "#a78bfa" : "#fb923c";

export default function Pipeline() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [filter, setFilter] = useState<string>("All");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [loadErr, setLoadErr] = useState("");

  useEffect(() => {
    const base = getApiBase();
    (async () => {
      setLoadingLeads(true);
      setLoadErr("");
      try {
        const r = await fetch(`${base}/api/leads?limit=24&exclude_junk=true&sort=score`, liveFetchInit());
        if (!r.ok) throw new Error(await r.text());
        const rows = (await r.json()) as ApiLead[];
        const mapped = Array.isArray(rows) ? rows.map(mapApiLeadToDeal) : [];
        setDeals(mapped);
        setSelectedId(mapped[0]?.id ?? null);
      } catch (e) {
        setLoadErr(e instanceof Error ? e.message : "Could not load pipeline");
        setDeals([]);
        setSelectedId(null);
      } finally {
        setLoadingLeads(false);
      }
    })();
  }, []);

  const industries = ["All", ...Array.from(new Set(deals.map((d) => d.industry)))];
  const filtered = filter === "All" ? deals : deals.filter((d) => d.industry === filter);
  const selected = deals.find((d) => d.id === selectedId) ?? null;

  const moveStage = (id: number, direction: 1 | -1) => {
    setDeals((prev) =>
      prev.map((d) => {
        if (d.id !== id) return d;
        const idx = STAGES.indexOf(d.stage);
        const next = STAGES[idx + direction];
        if (!next) return d;
        toast.success(`Moved "${d.company}" to ${next}`);
        return { ...d, stage: next, updatedAt: "just now" };
      })
    );
  };

  const copyDraft = () => {
    if (!selected?.outreachBody) return;
    navigator.clipboard.writeText(`Subject: ${selected.outreachSubject}\n\n${selected.outreachBody}`);
    setCopied(true);
    toast.success("Draft copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const totalDeals = filtered.length;
  const hotDeals = filtered.filter((d) => d.score >= 85).length;
  const meetingDeals = filtered.filter((d) => d.stage === "Meeting Set").length;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-20 pb-6 px-4 lg:px-6">
        <div className="max-w-[1500px] mx-auto flex flex-col gap-4">

          {/* ── Top bar ── */}
          {loadErr && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100/90">
              {loadErr}
            </div>
          )}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-0.5" style={{ color: "#a78bfa" }}>SCOUT</p>
                <h1 className="font-extrabold text-white text-xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Live pipeline
                </h1>
                <p className="text-[11px] text-white/35 mt-0.5 max-w-md">
                  SCOUT pulls scored leads from your database — find, engage, and book meetings from one surface.
                </p>
              </div>
              {/* Inline stats */}
              <div className="hidden sm:flex items-center gap-4 pl-4 border-l border-white/10">
                <span className="text-xs text-white/40"><span className="font-mono font-bold text-white/70 mr-1">{totalDeals}</span>deals</span>
                <span className="text-xs text-white/40"><span className="font-mono font-bold mr-1" style={{ color: "#34d399" }}>{hotDeals}</span>hot</span>
                <span className="text-xs text-white/40"><span className="font-mono font-bold mr-1" style={{ color: "#f472b6" }}>{meetingDeals}</span>meetings</span>
                <span className="flex items-center gap-1.5 text-xs text-white/30">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {loadingLeads ? "Loading…" : "SCOUT active"}
                </span>
              </div>
            </div>

            {/* Industry filter */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <Filter className="h-3 w-3 text-white/20" />
              {industries.map((ind) => (
                <button
                  key={ind}
                  onClick={() => setFilter(ind)}
                  className="text-[11px] font-semibold px-2.5 py-1 rounded-full border transition-all"
                  style={
                    filter === ind
                      ? { background: "#7c3aed", borderColor: "#7c3aed", color: "#fff" }
                      : { background: "rgba(255,255,255,0.03)", borderColor: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.35)" }
                  }
                >
                  {ind}
                </button>
              ))}
            </div>
          </div>

          {/* ── Two-panel layout ── */}
          <div className="flex gap-4" style={{ minHeight: "calc(100vh - 200px)" }}>

            {/* LEFT: Stage columns as inline row lists */}
            <div className="flex-1 flex flex-col gap-2 overflow-y-auto min-w-0">
              {STAGES.map((stage) => {
                const stageDeals = filtered.filter((d) => d.stage === stage);
                const meta = STAGE_META[stage];
                return (
                  <div key={stage}>
                    {/* Stage header row */}
                    <div className="flex items-center gap-2 px-3 py-2 mb-1">
                      <span className="h-2 w-2 rounded-full shrink-0" style={{ background: meta.dot }} />
                      <span className="text-xs font-bold" style={{ color: meta.color }}>{meta.label}</span>
                      <span className="text-[10px] text-white/25 ml-0.5">— {meta.desc}</span>
                      <span
                        className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded"
                        style={{ color: meta.color, background: `${meta.color}15` }}
                      >
                        {stageDeals.length}
                      </span>
                    </div>

                    {/* Inline deal rows */}
                    {stageDeals.length === 0 ? (
                      <div className="mx-1 mb-2 rounded-lg border border-dashed border-white/6 px-4 py-3">
                        <p className="text-[11px] text-white/20 italic">No deals in this stage</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-0.5 mb-2">
                        {stageDeals.map((deal) => {
                          const isSelected = deal.id === selectedId;
                          return (
                            <button
                              key={deal.id}
                              onClick={() => setSelectedId(deal.id)}
                              className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all group"
                              style={
                                isSelected
                                  ? { background: "rgba(124,58,237,0.12)", borderColor: "rgba(124,58,237,0.35)" }
                                  : { background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.05)" }
                              }
                            >
                              {/* Score ring */}
                              <div
                                className="h-7 w-7 rounded-full border flex items-center justify-center shrink-0"
                                style={{ borderColor: scoreColor(deal.score), background: `${scoreColor(deal.score)}10` }}
                              >
                                <span className="font-mono text-[10px] font-bold" style={{ color: scoreColor(deal.score), fontFamily: "'JetBrains Mono', monospace" }}>
                                  {deal.score}
                                </span>
                              </div>

                              {/* Company + signal inline */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-0.5">
                                  <span className="text-sm font-semibold text-white truncate">{deal.company}</span>
                                  <span className="text-[10px] text-white/30 shrink-0">{deal.location}</span>
                                  <span
                                    className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                    style={{ color: deal.signalColor, background: `${deal.signalColor}15` }}
                                  >
                                    {deal.signalType}
                                  </span>
                                </div>
                                <p className="text-[11px] text-white/40 truncate">{deal.signal}</p>
                              </div>

                              {/* Time + arrow */}
                              <div className="flex items-center gap-2 shrink-0">
                                <span className="text-[10px] text-white/20 font-mono hidden sm:block" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                                  {deal.updatedAt}
                                </span>
                                <ChevronRight
                                  className="h-3.5 w-3.5 transition-colors"
                                  style={{ color: isSelected ? "#a78bfa" : "rgba(255,255,255,0.15)" }}
                                />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* RIGHT: Deal detail + outreach draft */}
            <div
              className="w-[380px] xl:w-[420px] shrink-0 rounded-2xl border border-white/8 overflow-hidden flex flex-col"
              style={{ background: "rgba(255,255,255,0.025)", position: "sticky", top: "80px", maxHeight: "calc(100vh - 100px)" }}
            >
              {selected ? (
                <>
                  {/* Detail header */}
                  <div className="p-5 border-b border-white/8">
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div>
                        <p className="text-base font-bold text-white mb-0.5" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                          {selected.company}
                        </p>
                        <div className="flex items-center gap-2 text-[11px] text-white/35">
                          <MapPin className="h-3 w-3" />
                          {selected.location}
                          <span className="text-white/15">·</span>
                          {selected.industry}
                        </div>
                      </div>
                      <div
                        className="h-10 w-10 rounded-full border flex items-center justify-center shrink-0"
                        style={{ borderColor: scoreColor(selected.score), background: `${scoreColor(selected.score)}12` }}
                      >
                        <span className="font-mono text-sm font-bold" style={{ color: scoreColor(selected.score), fontFamily: "'JetBrains Mono', monospace" }}>
                          {selected.score}
                        </span>
                      </div>
                    </div>

                    {/* Stage + contact inline */}
                    <div className="flex items-center gap-3 flex-wrap">
                      <span
                        className="text-[10px] font-bold px-2 py-1 rounded-full"
                        style={{ color: STAGE_META[selected.stage].color, background: `${STAGE_META[selected.stage].color}15`, border: `1px solid ${STAGE_META[selected.stage].color}25` }}
                      >
                        {selected.stage}
                      </span>
                      {selected.contact && (
                        <span className="text-[11px] text-white/40">
                          <span className="text-white/60 font-medium">{selected.contact}</span> · {selected.contactTitle}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Signal block */}
                  <div className="px-5 py-3 border-b border-white/6">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">Trigger Signal</p>
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: selected.signalColor }} />
                      <div>
                        <p className="text-xs font-semibold mb-0.5" style={{ color: selected.signalColor }}>{selected.signalType}</p>
                        <p className="text-[11px] text-white/50 leading-relaxed">{selected.signal}</p>
                      </div>
                    </div>
                    {selected.notes && (
                      <p className="mt-2 text-[10px] text-white/25 italic leading-relaxed border-t border-white/5 pt-2">{selected.notes}</p>
                    )}
                  </div>

                  {/* Outreach draft */}
                  <div className="flex-1 overflow-y-auto px-5 py-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5">
                        <Mail className="h-3.5 w-3.5" style={{ color: "#7c3aed" }} />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-white/25">Outreach Draft</p>
                      </div>
                      <button
                        onClick={copyDraft}
                        className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded transition-all"
                        style={
                          copied
                            ? { background: "rgba(52,211,153,0.12)", color: "#34d399" }
                            : { background: "rgba(124,58,237,0.12)", color: "#a78bfa" }
                        }
                      >
                        {copied ? <CheckCheck className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                        {copied ? "Copied!" : "Copy draft"}
                      </button>
                    </div>

                    {selected.outreachSubject && (
                      <div className="mb-2 p-2.5 rounded-lg" style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.15)" }}>
                        <p className="text-[10px] text-white/30 mb-0.5 uppercase tracking-wide">Subject</p>
                        <p className="text-xs font-semibold text-white/80">{selected.outreachSubject}</p>
                      </div>
                    )}

                    {selected.outreachBody && (
                      <div className="p-3 rounded-lg" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <pre className="text-[11px] text-white/55 leading-relaxed whitespace-pre-wrap font-sans">
                          {selected.outreachBody}
                        </pre>
                      </div>
                    )}
                  </div>

                  {/* Action bar */}
                  <div className="p-4 border-t border-white/8 flex items-center gap-2">
                    {STAGES.indexOf(selected.stage) > 0 && (
                      <button
                        onClick={() => moveStage(selected.id, -1)}
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg border transition-all"
                        style={{ borderColor: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.4)", background: "rgba(255,255,255,0.03)" }}
                      >
                        <ArrowLeft className="h-3 w-3" />
                        Back
                      </button>
                    )}
                    <button
                      onClick={() => {
                        copyDraft();
                        toast.success("Draft copied — ready to send");
                      }}
                      className="flex-1 flex items-center justify-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg transition-all"
                      style={{ background: "rgba(124,58,237,0.2)", color: "#c4b5fd", border: "1px solid rgba(124,58,237,0.3)" }}
                    >
                      <Mail className="h-3.5 w-3.5" />
                      Approve &amp; Copy
                    </button>
                    {STAGES.indexOf(selected.stage) < STAGES.length - 1 && (
                      <button
                        onClick={() => moveStage(selected.id, 1)}
                        className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg transition-all"
                        style={{ background: "#7c3aed", color: "#fff", border: "1px solid #7c3aed" }}
                      >
                        Advance
                        <ArrowRight className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                  <Target className="h-8 w-8 text-white/10 mb-3" />
                  <p className="text-sm text-white/25">Select a deal to see details and outreach draft</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
