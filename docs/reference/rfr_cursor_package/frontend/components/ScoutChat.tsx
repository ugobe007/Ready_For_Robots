/**
 * ScoutChat — ReadyForRobots
 * Persistent AI sales agent chat with skills-based architecture.
 *
 * Features:
 * - Browser fingerprint stored in localStorage for anonymous persistence
 * - Session loaded from DB on open — returning users get a personalised greeting
 * - Scripted intro for new users; live LLM for returning users
 * - Skill invocation: scanCompany, findProspects, findPartners, draftOutreach
 * - Structured skill output cards rendered inline
 * - Full conversation history persisted to DB
 *
 * Color system: #0d0520 bg · #7c3aed purple (brand) · #03DAC5 teal (action/live)
 * Trigger button: outline/stroke only — no fill, teal text + border
 */
import { useState, useEffect, useRef, createContext, useContext, useCallback } from "react";
import {
  X, ArrowRight, RotateCcw, MessageSquare, Send,
  Search, Users, Handshake, FileText, Star, MapPin, Zap,
} from "lucide-react";
import { trpc } from "@/lib/trpc";

// ── Fingerprint ────────────────────────────────────────────────────────────────
function getFingerprint(): string {
  const key = "scout_fp";
  let fp = localStorage.getItem(key);
  if (!fp) {
    fp = `fp_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(key, fp);
  }
  return fp;
}

// ── Context ────────────────────────────────────────────────────────────────────
type ScoutChatCtx = { openChat: () => void };
const ScoutChatContext = createContext<ScoutChatCtx>({ openChat: () => {} });
export function useScoutChat() { return useContext(ScoutChatContext); }

// ── Types ──────────────────────────────────────────────────────────────────────
type SkillCard =
  | { type: "scan"; data: ScanResult }
  | { type: "prospects"; data: ProspectsResult }
  | { type: "partners"; data: PartnersResult }
  | { type: "outreach"; data: OutreachResult };

type ScanResult = {
  url: string; score: number; signals: string[]; summary: string; recommendation: string;
};
type ProspectsResult = {
  prospects: Array<{ company: string; industry: string; signal: string; score: number; outreachAngle: string }>;
  totalTracked: number; hotCount: number;
};
type PartnersResult = {
  partners: Array<{ company: string; type: string; territory: string; signal: string; score: number; outreachAngle: string }>;
  totalTracked: number;
};
type OutreachResult = { subject: string; body: string };

type ChatMessage = {
  id: number;
  role: "scout" | "user";
  text: string;
  typing?: boolean;
  skillCard?: SkillCard;
};
type UserChoice = { label: string; value: string };

// ── Scripted intro (new users only) ───────────────────────────────────────────
type ScoutTurn = { role: "scout"; text: string; delay?: number };
type ChoiceTurn = { role: "user-choices"; choices: UserChoice[] };
type Turn = ScoutTurn | ChoiceTurn;

const INTRO: Turn[] = [
  { role: "scout", text: "Hey — I'm SCOUT, ReadyForRobots' AI sales & partnership agent.", delay: 400 },
  { role: "scout", text: "I monitor 150+ sources 24/7 to find companies ready to buy robots and identify strategic partners — integrators, distributors, VARs — who can carry your product. Then I draft the outreach.", delay: 900 },
  { role: "scout", text: "What kind of robots do you sell?", delay: 600 },
  {
    role: "user-choices",
    choices: [
      { label: "Warehouse / AMR", value: "amr" },
      { label: "Industrial arms", value: "industrial" },
      { label: "Service robots", value: "service" },
      { label: "Food & beverage automation", value: "food" },
      { label: "Healthcare robots", value: "healthcare" },
      { label: "Finding SI / distributor partners", value: "partnerships" },
      { label: "Something else", value: "other" },
    ],
  },
];

const CATEGORY_LABELS: Record<string, string> = {
  amr: "Warehouse / AMR",
  industrial: "Industrial arms",
  service: "Service robots",
  food: "Food & beverage automation",
  healthcare: "Healthcare robots",
  partnerships: "SI / distributor partnerships",
  other: "General automation",
};

const BRANCH: Record<string, Turn[]> = {
  amr: [
    { role: "scout", text: "Good fit. Warehouse AMRs are one of our strongest signal categories.", delay: 500 },
    { role: "scout", text: "I watch for: facility expansions, new DC announcements, labor shortage mentions in earnings calls, and automation engineer job postings.", delay: 900 },
    { role: "scout", text: "Right now I'm tracking 247 active warehouse prospects — 38 are in a hot decision window.", delay: 700 },
  ],
  industrial: [
    { role: "scout", text: "Industrial arms — great. I focus on OSHA safety filings, CapEx announcements, and 'process improvement' hiring patterns.", delay: 500 },
    { role: "scout", text: "Manufacturing companies often signal 6–12 months before they issue an RFP. I find them in that window.", delay: 900 },
    { role: "scout", text: "I currently have 94 active manufacturing prospects flagged for industrial automation.", delay: 700 },
  ],
  service: [
    { role: "scout", text: "Service robots — hospitality, retail, facilities. I track labor vacancy rates, Glassdoor reviews, and overnight staffing complaints.", delay: 500 },
    { role: "scout", text: "The signal is usually a GM or VP of Operations saying they 'can't staff overnight shifts' — that's when they're ready to talk.", delay: 900 },
    { role: "scout", text: "I have 61 active service robot prospects right now, mostly in hospitality and healthcare.", delay: 700 },
  ],
  food: [
    { role: "scout", text: "Food & beverage automation — one of the fastest-growing categories. FDA regulatory changes are a big trigger right now.", delay: 500 },
    { role: "scout", text: "I also watch for CapEx budget announcements, facility expansions, and food safety incident filings.", delay: 900 },
    { role: "scout", text: "73 active food processing prospects in the pipeline, 18 with active decision signals.", delay: 700 },
  ],
  healthcare: [
    { role: "scout", text: "Healthcare robots — pharmacy automation, patient transport, surgical assist. Strong growth signals right now.", delay: 500 },
    { role: "scout", text: "I track nursing shortage data, hospital expansion permits, and 'automation' mentions in health system earnings calls.", delay: 900 },
    { role: "scout", text: "52 active healthcare prospects flagged, with 11 in an active buying window.", delay: 700 },
  ],
  partnerships: [
    { role: "scout", text: "Partnership development — this is one of my most powerful modes.", delay: 500 },
    { role: "scout", text: "I identify system integrators, distributors, and VARs who are actively expanding their robotics portfolio — before they sign with a competitor.", delay: 900 },
    { role: "scout", text: "I watch for: SI RFPs seeking AMR vendors, distributor job postings for robotics product managers, trade show exhibitor lists, and OEM partnership announcements.", delay: 1000 },
    { role: "scout", text: "Right now I'm tracking 43 active partner prospects — 12 are in an active evaluation window. Want me to show you what a partner pipeline looks like?", delay: 800 },
  ],
  other: [
    { role: "scout", text: "No problem — I can tune signals for any robot category with a B2B sales motion.", delay: 500 },
    { role: "scout", text: "Tell me more about what you sell and I'll explain how I'd find your buyers.", delay: 800 },
  ],
};

const FOLLOWUP_CHOICES: UserChoice[] = [
  { label: "Show me prospect examples", value: "show_prospects" },
  { label: "How does outreach work?", value: "how_outreach" },
  { label: "Find partner opportunities", value: "find_partners" },
  { label: "Scan my company URL", value: "scan_url" },
  { label: "See pricing", value: "pricing" },
];

const FOLLOWUP_BRANCH: Record<string, Turn[]> = {
  show_prospects: [
    { role: "scout", text: "I'll pull 3 live examples for your category. Give me a territory — or I'll default to North America.", delay: 600 },
  ],
  how_outreach: [
    { role: "scout", text: "When I detect a signal, I draft a personalised email referencing the exact trigger — not a generic template.", delay: 600 },
    { role: "scout", text: "You review it, edit if needed, and approve. In Auto mode I send it directly. In Assisted mode you're always the last click.", delay: 800 },
    { role: "scout", text: "Want me to draft a sample outreach for a real company in your vertical?", delay: 600 },
  ],
  find_partners: [
    { role: "scout", text: "On it. What type of partner are you looking for — system integrator, distributor, or VAR?", delay: 600 },
  ],
  scan_url: [
    { role: "scout", text: "Sure — paste your company URL and I'll score it for automation readiness and identify the best outreach angle.", delay: 600 },
  ],
  pricing: [
    { role: "scout", text: "We have three tiers: Starter (signals + scoring), Growth (signals + outreach + partnerships), and Enterprise (full automation + custom integrations).", delay: 600 },
    { role: "scout", text: "Most robotics sales teams start on Growth. Want me to walk you through what's included?", delay: 700 },
  ],
};

const LIVE_HANDOFF: Turn[] = [
  { role: "scout", text: "Ask me anything — I'm live now. What do you want to know?", delay: 600 },
];

// ── Helpers ────────────────────────────────────────────────────────────────────
function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

function scoreColor(score: number): string {
  if (score >= 85) return "#03DAC5";
  if (score >= 70) return "#a78bfa";
  return "#f59e0b";
}

// ── Skill Card Components ──────────────────────────────────────────────────────
function ScanCard({ data }: { data: ScanResult }) {
  return (
    <div className="mt-2 rounded-xl border overflow-hidden" style={{ borderColor: "rgba(3,218,197,0.25)", background: "rgba(3,218,197,0.05)" }}>
      <div className="px-3 py-2 flex items-center justify-between border-b" style={{ borderColor: "rgba(3,218,197,0.15)" }}>
        <div className="flex items-center gap-1.5">
          <Search className="h-3 w-3" style={{ color: "#03DAC5" }} />
          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#03DAC5" }}>Company Scan</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="font-mono text-sm font-bold" style={{ color: scoreColor(data.score) }}>{data.score}</span>
          <span className="text-[10px] text-white/30">/100</span>
        </div>
      </div>
      <div className="px-3 py-2.5 space-y-2">
        <p className="text-[11px] text-white/60 leading-relaxed">{data.summary}</p>
        <div className="space-y-1">
          {data.signals.map((s, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <span className="h-1 w-1 rounded-full mt-1.5 shrink-0" style={{ background: "#03DAC5" }} />
              <span className="text-[10px] text-white/50">{s}</span>
            </div>
          ))}
        </div>
        <div className="pt-1 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <p className="text-[10px] font-semibold" style={{ color: "#a78bfa" }}>Outreach angle: <span className="font-normal text-white/50">{data.recommendation}</span></p>
        </div>
      </div>
    </div>
  );
}

function ProspectsCard({ data }: { data: ProspectsResult }) {
  return (
    <div className="mt-2 rounded-xl border overflow-hidden" style={{ borderColor: "rgba(124,58,237,0.25)", background: "rgba(124,58,237,0.05)" }}>
      <div className="px-3 py-2 flex items-center justify-between border-b" style={{ borderColor: "rgba(124,58,237,0.15)" }}>
        <div className="flex items-center gap-1.5">
          <Users className="h-3 w-3" style={{ color: "#a78bfa" }} />
          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#a78bfa" }}>Prospects Found</span>
        </div>
        <span className="text-[10px] text-white/30">{data.totalTracked} tracked · {data.hotCount} hot</span>
      </div>
      <div className="divide-y" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        {data.prospects.map((p, i) => (
          <div key={i} className="px-3 py-2.5">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-white">{p.company}</span>
              <span className="font-mono text-xs font-bold" style={{ color: scoreColor(p.score) }}>{p.score}</span>
            </div>
            <p className="text-[10px] text-white/35 mb-1">{p.industry}</p>
            <p className="text-[10px] text-white/50 italic">"{p.signal}"</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function PartnersCard({ data }: { data: PartnersResult }) {
  return (
    <div className="mt-2 rounded-xl border overflow-hidden" style={{ borderColor: "rgba(3,218,197,0.25)", background: "rgba(3,218,197,0.04)" }}>
      <div className="px-3 py-2 flex items-center justify-between border-b" style={{ borderColor: "rgba(3,218,197,0.15)" }}>
        <div className="flex items-center gap-1.5">
          <Handshake className="h-3 w-3" style={{ color: "#03DAC5" }} />
          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#03DAC5" }}>Partner Matches</span>
        </div>
        <span className="text-[10px] text-white/30">{data.totalTracked} tracked</span>
      </div>
      <div className="divide-y" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        {data.partners.map((p, i) => (
          <div key={i} className="px-3 py-2.5">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-white">{p.company}</span>
              <span className="font-mono text-xs font-bold" style={{ color: scoreColor(p.score) }}>{p.score}</span>
            </div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px]" style={{ color: "#03DAC5" }}>{p.type}</span>
              <span className="text-white/15">·</span>
              <span className="flex items-center gap-0.5 text-[10px] text-white/35"><MapPin className="h-2.5 w-2.5" />{p.territory}</span>
            </div>
            <p className="text-[10px] text-white/50 italic">"{p.signal}"</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function OutreachCard({ data }: { data: OutreachResult }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(`Subject: ${data.subject}\n\n${data.body}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="mt-2 rounded-xl border overflow-hidden" style={{ borderColor: "rgba(124,58,237,0.25)", background: "rgba(124,58,237,0.05)" }}>
      <div className="px-3 py-2 flex items-center justify-between border-b" style={{ borderColor: "rgba(124,58,237,0.15)" }}>
        <div className="flex items-center gap-1.5">
          <FileText className="h-3 w-3" style={{ color: "#a78bfa" }} />
          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#a78bfa" }}>Outreach Draft</span>
        </div>
        <button onClick={copy} className="text-[10px] font-semibold px-2 py-0.5 rounded transition-all"
          style={copied ? { background: "rgba(52,211,153,0.12)", color: "#34d399" } : { background: "rgba(124,58,237,0.12)", color: "#a78bfa" }}>
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div className="px-3 py-2.5">
        <p className="text-[10px] text-white/30 mb-0.5 uppercase tracking-wide">Subject</p>
        <p className="text-xs font-semibold text-white/80 mb-2">{data.subject}</p>
        <pre className="text-[10px] text-white/50 leading-relaxed whitespace-pre-wrap font-sans">{data.body}</pre>
      </div>
    </div>
  );
}

// ── Inner Panel ────────────────────────────────────────────────────────────────
function ScoutPanel({ onClose }: { onClose: () => void }) {
  const [messages, setMessages]     = useState<ChatMessage[]>([]);
  const [choices, setChoices]       = useState<UserChoice[] | null>(null);
  const [phase, setPhase]           = useState<"loading" | "intro" | "live">("loading");
  const [busy, setBusy]             = useState(false);
  const [inputText, setInputText]   = useState("");
  const [sessionCtx, setSessionCtx] = useState<{
    sessionId?: number;
    robotCategory?: string;
    vertical?: string;
    territory?: string;
    companyName?: string;
    isReturning?: boolean;
  }>({});

  const idCounter  = useRef(0);
  const bottomRef  = useRef<HTMLDivElement>(null);
  const hasStarted = useRef(false);
  const inputRef   = useRef<HTMLInputElement>(null);
  const fingerprint = useRef(getFingerprint());

  // LLM history for the live phase
  const llmHistory = useRef<Array<{ role: "user" | "assistant"; content: string }>>([]);

  const getSessionMutation  = trpc.scout.getSession.useMutation();
  const chatMutation        = trpc.scout.chat.useMutation();
  const updateSessionMut    = trpc.scout.updateSession.useMutation();
  const scanCompanyMut      = trpc.scout.scanCompany.useMutation();
  const findProspectsMut    = trpc.scout.findProspects.useMutation();
  const findPartnersMut     = trpc.scout.findPartners.useMutation();
  const draftOutreachMut    = trpc.scout.draftOutreach.useMutation();
  const getSignalUpdateMut  = trpc.scout.getSignalUpdate.useMutation();

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, choices]);
  useEffect(() => {
    if (phase === "live") setTimeout(() => inputRef.current?.focus(), 100);
  }, [phase]);

  const nextId = useCallback(() => idCounter.current++, []);

  // ── Load session on mount ──────────────────────────────────────────────────
  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    getSessionMutation.mutateAsync({ fingerprint: fingerprint.current }).then(({ session, history, isNew }) => {
      const ctx = {
        sessionId: session.id,
        robotCategory: session.robotCategory ?? undefined,
        vertical: session.vertical ?? undefined,
        territory: session.territory ?? undefined,
        companyName: session.companyName ?? undefined,
        isReturning: !isNew && session.conversationCount > 0,
      };
      setSessionCtx(ctx);

      if (!isNew && history.length > 0) {
        // Returning user — restore history and greet with context
        const restored: ChatMessage[] = history.map(m => ({
          id: nextId(),
          role: m.role,
          text: m.content,
          skillCard: m.skillData ? parseSkillCard(m.skillInvoked, m.skillData) : undefined,
        }));
        setMessages(restored);

        // Build LLM history from DB messages
        llmHistory.current = history
          .filter(m => m.role === "user" || m.role === "scout")
          .map(m => ({ role: m.role === "user" ? "user" as const : "assistant" as const, content: m.content }));

        // Personalised returning greeting with proactive signal update
        const categoryLabel = session.robotCategory ? CATEGORY_LABELS[session.robotCategory] ?? session.robotCategory : null;
        const greetingParts = ["Welcome back."];
        if (categoryLabel) greetingParts.push(`Last time you were focused on ${categoryLabel}.`);
        if (session.companyName) greetingParts.push(`I've been watching signals for ${session.companyName}.`);
        greetingParts.push("What would you like to work on?");
        // Calculate hours since last visit for proactive signal update
        const lastSeenMs = session.lastSeenAt ? new Date(session.lastSeenAt as unknown as string).getTime() : 0;
        const hoursSince = lastSeenMs > 0 ? (Date.now() - lastSeenMs) / (1000 * 60 * 60) : 0;
        const shouldShowSignalUpdate = hoursSince >= 4 && !!session.robotCategory;

        setTimeout(async () => {
          setMessages(prev => [...prev, { id: nextId(), role: "scout", text: greetingParts.join(" ") }]);
          setPhase("live");
          if (shouldShowSignalUpdate) {
            const typingId = nextId();
            await new Promise(r => setTimeout(r, 600));
            setMessages(prev => [...prev, { id: typingId, role: "scout", text: "", typing: true }]);
            try {
              const { message } = await getSignalUpdateMut.mutateAsync({
                fingerprint: fingerprint.current,
                robotCategory: session.robotCategory ?? undefined,
                vertical: session.vertical ?? undefined,
                territory: session.territory ?? undefined,
                companyName: session.companyName ?? undefined,
                hoursSinceLastVisit: hoursSince,
              });
              setMessages(prev => prev.map(m => m.id === typingId ? { ...m, text: message, typing: false } : m));
            } catch {
              setMessages(prev => prev.filter(m => m.id !== typingId));
            }
          }
          setChoices(FOLLOWUP_CHOICES);
        }, 400);
      } else {
        // New user — run scripted intro
        runTurns(INTRO);
      }
    }).catch(() => {
      // Fallback to scripted intro if session load fails
      runTurns(INTRO);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function parseSkillCard(skillInvoked: string | null, skillData: unknown): SkillCard | undefined {
    if (!skillInvoked || !skillData) return undefined;
    if (skillInvoked === "scanCompany") return { type: "scan", data: skillData as ScanResult };
    if (skillInvoked === "findProspects") return { type: "prospects", data: skillData as ProspectsResult };
    if (skillInvoked === "findPartners") return { type: "partners", data: skillData as PartnersResult };
    if (skillInvoked === "draftOutreach") return { type: "outreach", data: skillData as OutreachResult };
    return undefined;
  }

  async function runTurns(turns: Turn[]) {
    setBusy(true); setChoices(null);
    for (const turn of turns) {
      if (turn.role === "scout") {
        await playScoutMessage(turn.text, turn.delay ?? 500);
      } else if (turn.role === "user-choices") {
        setBusy(false);
        setChoices(turn.choices);
        return;
      }
    }
    setBusy(false);
  }

  async function playScoutMessage(text: string, delay: number) {
    await sleep(delay);
    const id = nextId();
    setMessages(prev => [...prev, { id, role: "scout", text: "", typing: true }]);
    await sleep(Math.min(text.length * 16, 1100));
    setMessages(prev => prev.map(m => m.id === id ? { ...m, text, typing: false } : m));
  }

  async function handleChoice(choice: UserChoice) {
    setChoices(null);
    const userMsg: ChatMessage = { id: nextId(), role: "user", text: choice.label };
    setMessages(prev => [...prev, userMsg]);

    // Update session with robot category if this is the intro choice
    if (BRANCH[choice.value]) {
      const newCtx = { ...sessionCtx, robotCategory: choice.value };
      setSessionCtx(newCtx);
      await updateSessionMut.mutateAsync({
        fingerprint: fingerprint.current,
        robotCategory: choice.value,
        vertical: CATEGORY_LABELS[choice.value],
      });
    }

    if (choice.value === "show_prospects") {
      await runTurns(FOLLOWUP_BRANCH.show_prospects);
      // Invoke skill after prompt
      setTimeout(() => invokeSkillFindProspects(), 1200);
      return;
    }
    if (choice.value === "find_partners") {
      await runTurns(FOLLOWUP_BRANCH.find_partners);
      setTimeout(() => invokeSkillFindPartners(), 1200);
      return;
    }
    if (choice.value === "scan_url") {
      await runTurns(FOLLOWUP_BRANCH.scan_url);
      setPhase("live");
      return;
    }

    const branch = BRANCH[choice.value] ?? FOLLOWUP_BRANCH[choice.value];
    if (branch) {
      await runTurns(branch);
      // After branch, show follow-up choices then go live
      await sleep(400);
      setChoices(FOLLOWUP_CHOICES);
      return;
    }

    // Go live
    await runTurns(LIVE_HANDOFF);
    setPhase("live");
  }

  // ── Skill invocations ────────────────────────────────────────────────────────
  async function invokeSkillFindProspects() {
    setBusy(true);
    const id = nextId();
    setMessages(prev => [...prev, { id, role: "scout", text: "", typing: true }]);
    try {
      const result = await findProspectsMut.mutateAsync({
        fingerprint: fingerprint.current,
        category: sessionCtx.robotCategory ?? "general",
        territory: sessionCtx.territory ?? "North America",
      });
      setMessages(prev => prev.map(m => m.id === id ? {
        ...m, text: `Here are 3 active prospects I'm tracking for you right now:`,
        typing: false, skillCard: { type: "prospects" as const, data: result },
      } : m));
    } catch {
      setMessages(prev => prev.map(m => m.id === id ? { ...m, text: "I hit a snag pulling prospects. Try again in a moment.", typing: false } : m));
    }
    setBusy(false);
    setPhase("live");
  }

  async function invokeSkillFindPartners() {
    setBusy(true);
    const id = nextId();
    setMessages(prev => [...prev, { id, role: "scout", text: "", typing: true }]);
    try {
      const result = await findPartnersMut.mutateAsync({
        fingerprint: fingerprint.current,
        partnerType: "system integrator",
        region: sessionCtx.territory ?? "North America",
      });
      setMessages(prev => prev.map(m => m.id === id ? {
        ...m, text: `Here are 3 partner prospects actively expanding their robotics portfolio:`,
        typing: false, skillCard: { type: "partners" as const, data: result },
      } : m));
    } catch {
      setMessages(prev => prev.map(m => m.id === id ? { ...m, text: "Couldn't pull partner data right now. Try again shortly.", typing: false } : m));
    }
    setBusy(false);
    setPhase("live");
  }

  async function invokeSkillScanUrl(url: string) {
    setBusy(true);
    const id = nextId();
    setMessages(prev => [...prev, { id, role: "scout", text: "", typing: true }]);
    try {
      const result = await scanCompanyMut.mutateAsync({
        fingerprint: fingerprint.current,
        url,
        robotCategory: sessionCtx.robotCategory,
      });
      setMessages(prev => prev.map(m => m.id === id ? {
        ...m, text: `Scan complete for ${url}:`,
        typing: false, skillCard: { type: "scan" as const, data: result },
      } : m));
    } catch {
      setMessages(prev => prev.map(m => m.id === id ? { ...m, text: "Scan failed. Check the URL and try again.", typing: false } : m));
    }
    setBusy(false);
  }

  async function invokeSkillDraftOutreach(company: string, signal: string) {
    setBusy(true);
    const id = nextId();
    setMessages(prev => [...prev, { id, role: "scout", text: "", typing: true }]);
    try {
      const result = await draftOutreachMut.mutateAsync({
        fingerprint: fingerprint.current,
        company,
        signal,
        robotCategory: sessionCtx.robotCategory ?? "automation",
        senderCompany: sessionCtx.companyName,
      });
      setMessages(prev => prev.map(m => m.id === id ? {
        ...m, text: `Here's your outreach draft for ${company}:`,
        typing: false, skillCard: { type: "outreach" as const, data: result },
      } : m));
    } catch {
      setMessages(prev => prev.map(m => m.id === id ? { ...m, text: "Draft failed. Try again in a moment.", typing: false } : m));
    }
    setBusy(false);
  }

  // ── Live chat send ───────────────────────────────────────────────────────────
  async function sendMessage(text: string) {
    if (!text.trim() || busy) return;
    setInputText("");
    setChoices(null);

    const userMsg: ChatMessage = { id: nextId(), role: "user", text };
    setMessages(prev => [...prev, userMsg]);
    llmHistory.current.push({ role: "user", content: text });

    // Detect skill triggers in user message
    const lower = text.toLowerCase();
    const urlMatch = text.match(/https?:\/\/[^\s]+|[a-z0-9-]+\.[a-z]{2,}(?:\/[^\s]*)?/i);

    if (urlMatch && (lower.includes("scan") || lower.includes("check") || lower.includes("analyze") || lower.includes("analyse"))) {
      await invokeSkillScanUrl(urlMatch[0]);
      return;
    }
    if (lower.includes("find prospect") || lower.includes("show prospect") || lower.includes("find buyer") || lower.includes("find lead")) {
      await invokeSkillFindProspects();
      return;
    }
    if (lower.includes("find partner") || lower.includes("show partner") || lower.includes("integrator") || lower.includes("distributor")) {
      await invokeSkillFindPartners();
      return;
    }
    if (lower.includes("draft") || lower.includes("write email") || lower.includes("outreach for ")) {
      // Extract company name after "for"
      const forMatch = text.match(/(?:draft|outreach)\s+(?:for\s+)?([A-Z][a-zA-Z\s&]+)/);
      if (forMatch) {
        await invokeSkillDraftOutreach(forMatch[1].trim(), "general buying signal");
        return;
      }
    }

    // Standard LLM chat
    setBusy(true);
    const id = nextId();
    setMessages(prev => [...prev, { id, role: "scout", text: "", typing: true }]);

    try {
      const { reply } = await chatMutation.mutateAsync({
        fingerprint: fingerprint.current,
        messages: [...llmHistory.current],
        sessionContext: {
          robotCategory: sessionCtx.robotCategory,
          vertical: sessionCtx.vertical,
          territory: sessionCtx.territory,
          companyName: sessionCtx.companyName,
        },
      });
      llmHistory.current.push({ role: "assistant", content: reply });
      setMessages(prev => prev.map(m => m.id === id ? { ...m, text: reply, typing: false } : m));
    } catch {
      setMessages(prev => prev.map(m => m.id === id ? { ...m, text: "Something went wrong. Try again.", typing: false } : m));
    }
    setBusy(false);
  }

  function handleReset() {
    setMessages([]);
    setChoices(null);
    setPhase("intro");
    setBusy(false);
    llmHistory.current = [];
    hasStarted.current = false;
    idCounter.current = 0;
    // Re-run intro
    setTimeout(() => {
      hasStarted.current = true;
      runTurns(INTRO);
    }, 100);
  }

  return (
    <div
      className="fixed bottom-20 right-4 z-50 flex flex-col rounded-2xl overflow-hidden shadow-2xl"
      style={{
        width: "min(380px, calc(100vw - 2rem))",
        height: "min(560px, calc(100vh - 6rem))",
        background: "rgba(13,5,32,0.97)",
        border: "1px solid rgba(124,58,237,0.25)",
        backdropFilter: "blur(24px)",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0" style={{ borderColor: "rgba(124,58,237,0.2)", background: "rgba(124,58,237,0.08)" }}>
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-lg flex items-center justify-center" style={{ background: "#7c3aed" }}>
            <Zap className="h-3.5 w-3.5 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-none">SCOUT</p>
            <p className="text-[10px] text-white/35 mt-0.5">
              {sessionCtx.isReturning ? "Remembers your context" : "AI Sales & Partnership Agent"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {sessionCtx.robotCategory && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full" style={{ background: "rgba(3,218,197,0.1)", border: "1px solid rgba(3,218,197,0.2)" }}>
              <Star className="h-2.5 w-2.5" style={{ color: "#03DAC5" }} />
              <span className="text-[9px] font-bold" style={{ color: "#03DAC5" }}>{CATEGORY_LABELS[sessionCtx.robotCategory] ?? sessionCtx.robotCategory}</span>
            </div>
          )}
          <div className="flex items-center gap-1 text-[10px] font-bold" style={{ color: "#03DAC5" }}>
            <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
            LIVE
          </div>
          <button onClick={handleReset} className="p-1 rounded-lg text-white/25 hover:text-white/60 transition-colors" title="Reset conversation">
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
          <button onClick={onClose} className="p-1 rounded-lg text-white/25 hover:text-white/60 transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {phase === "loading" && (
          <div className="flex items-center gap-2 mt-4">
            <div className="h-6 w-6 rounded-lg flex items-center justify-center shrink-0" style={{ background: "rgba(124,58,237,0.2)" }}>
              <Zap className="h-3 w-3" style={{ color: "#a78bfa" }} />
            </div>
            <div className="flex gap-1">
              {[0,1,2].map(i => (
                <span key={i} className="h-1.5 w-1.5 rounded-full animate-bounce" style={{ background: "#7c3aed", animationDelay: `${i * 150}ms` }} />
              ))}
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            {msg.role === "scout" && (
              <div className="h-6 w-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style={{ background: "rgba(124,58,237,0.2)" }}>
                <Zap className="h-3 w-3" style={{ color: "#a78bfa" }} />
              </div>
            )}
            <div className={`max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
              <div
                className="px-3 py-2 rounded-xl text-sm leading-relaxed"
                style={msg.role === "scout"
                  ? { background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.85)", border: "1px solid rgba(255,255,255,0.07)" }
                  : { background: "rgba(3,218,197,0.12)", color: "#03DAC5", border: "1px solid rgba(3,218,197,0.25)" }
                }
              >
                {msg.typing ? (
                  <div className="flex gap-1 py-0.5">
                    {[0,1,2].map(i => (
                      <span key={i} className="h-1.5 w-1.5 rounded-full animate-bounce" style={{ background: "#7c3aed", animationDelay: `${i * 150}ms` }} />
                    ))}
                  </div>
                ) : msg.text}
              </div>
              {msg.skillCard && (
                <div className="w-full">
                  {msg.skillCard.type === "scan" && <ScanCard data={msg.skillCard.data} />}
                  {msg.skillCard.type === "prospects" && <ProspectsCard data={msg.skillCard.data} />}
                  {msg.skillCard.type === "partners" && <PartnersCard data={msg.skillCard.data} />}
                  {msg.skillCard.type === "outreach" && <OutreachCard data={msg.skillCard.data} />}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Choice chips */}
        {choices && !busy && (
          <div className="flex flex-wrap gap-2 pt-1 pl-8">
            {choices.map((c) => (
              <button
                key={c.value}
                onClick={() => handleChoice(c)}
                className="text-xs font-semibold px-3 py-1.5 rounded-xl transition-all hover:-translate-y-0.5"
                style={{ background: "rgba(124,58,237,0.12)", color: "#c4b5fd", border: "1px solid rgba(124,58,237,0.3)" }}
              >
                {c.label}
              </button>
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      {(phase === "live" || phase === "loading") && (
        <div className="px-3 pb-3 pt-2 shrink-0 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <form
            onSubmit={(e) => { e.preventDefault(); sendMessage(inputText); }}
            className="flex items-center gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask SCOUT anything…"
              disabled={busy}
              className="flex-1 px-3 py-2 text-sm text-white rounded-xl border bg-white/5 placeholder:text-white/20 focus:outline-none focus:ring-1 disabled:opacity-40 transition"
              style={{ borderColor: "rgba(255,255,255,0.1)" }}
            />
            <button
              type="submit"
              disabled={busy || !inputText.trim()}
              className="h-9 w-9 flex items-center justify-center rounded-xl transition-all disabled:opacity-30"
              style={{ background: "#03DAC5" }}
            >
              <Send className="h-3.5 w-3.5 text-black" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

// ── Outer wrapper with context + floating trigger ──────────────────────────────
export function ScoutChat({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <ScoutChatContext.Provider value={{ openChat: () => setOpen(true) }}>
      {children}
      {open && <ScoutPanel onClose={() => setOpen(false)} />}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-4 right-4 z-50 flex items-center gap-2 text-sm font-semibold px-4 py-2.5 rounded-xl transition-all hover:-translate-y-0.5"
          style={{
            color: "#03DAC5",
            border: "1.5px solid rgba(3,218,197,0.5)",
            background: "rgba(13,5,32,0.85)",
            backdropFilter: "blur(12px)",
            boxShadow: "0 4px 20px rgba(3,218,197,0.12)",
          }}
        >
          <MessageSquare className="h-4 w-4" />
          Talk to SCOUT
          <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
        </button>
      )}
    </ScoutChatContext.Provider>
  );
}
