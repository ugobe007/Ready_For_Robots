/**
 * Daily Strategy Brief  Supabase-style dark design
 * Matches the main dashboard: no fills, stroke + text only, dark bg.
 */
import { useState, useEffect, useRef } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useAuth } from './_app'
import { authHeader, supabase } from '../lib/supabase'
import AuthPrompt from '../components/AuthPrompt'
import LoginModal from '../components/LoginModal'

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000')

// Design tokens (mirrors index.js)
const TIER_META = {
  HOT:  { text: 'text-red-400',    border: 'border-red-800',    accent: 'lead-hot',  dot: 'bg-red-500',    label: 'HOT'  },
  WARM: { text: 'text-yellow-400', border: 'border-yellow-800', accent: 'lead-warm', dot: 'bg-yellow-500', label: 'WARM' },
  COLD: { text: 'text-cyan-400',   border: 'border-cyan-900',   accent: 'lead-cold', dot: 'bg-cyan-600',   label: 'COLD' },
}

const SIGNAL_META = {
  funding_round:        { label: 'Funding',   border: 'border-violet-700', text: 'text-violet-400' },
  strategic_hire:       { label: 'Exec Hire', border: 'border-blue-700',   text: 'text-blue-400'   },
  capex:                { label: 'CapEx',     border: 'border-cyan-700',   text: 'text-cyan-400'   },
  ma_activity:          { label: 'M&A',       border: 'border-pink-700',   text: 'text-pink-400'   },
  expansion:            { label: 'Expand',    border: 'border-emerald-800',text: 'text-emerald-400'},
  job_posting:          { label: 'Hiring',    border: 'border-amber-700',  text: 'text-amber-400'  },
  labor_shortage:       { label: 'Labor Gap', border: 'border-red-800',    text: 'text-red-400'    },
  labor_pain:           { label: 'Labor Pain',border: 'border-red-800',    text: 'text-red-400'    },
  news:                   { label: 'News',         border: 'border-neutral-700', text: 'text-neutral-400' },
  automation_intent:      { label: 'Auto',          border: 'border-indigo-700',  text: 'text-indigo-400'  },
  equipment_integration:  { label: 'ERP/WMS',       border: 'border-teal-700',    text: 'text-teal-400'    },
  rfp_activity:           { label: 'RFP',           border: 'border-orange-700',  text: 'text-orange-400'  },
  competitor_displacement:{ label: 'Churn Signal',  border: 'border-amber-700',   text: 'text-amber-400'   },
  pilot_program:          { label: 'Pilot',         border: 'border-emerald-700', text: 'text-emerald-400' },
  regulatory_driver:      { label: 'Regulatory',    border: 'border-rose-800',    text: 'text-rose-400'    },
}

const ROBOT_META = {
  'Titan':          { border: 'border-blue-700',   text: 'text-blue-400'   },
  'Titan AMR Fleet':{ border: 'border-blue-700',   text: 'text-blue-400'   },
  'DUST-E':         { border: 'border-teal-700',   text: 'text-teal-400'   },
  'DUST-E SX':      { border: 'border-teal-700',   text: 'text-teal-400'   },
  'ADAM':           { border: 'border-violet-700', text: 'text-violet-400' },
  'Matradee L5':    { border: 'border-pink-700',   text: 'text-pink-400'   },
  'Matradee':       { border: 'border-pink-700',   text: 'text-pink-400'   },
  'Dex':            { border: 'border-orange-700', text: 'text-orange-400' },
}

function Bdg({ label, border, text }) {
  return <span className={`badge ${border} ${text}`}>{label}</span>
}

// ─── Email script generator ────────────────────────────────────────────────

// Generates 3 clean prospect-facing bullet points for the email body.
// We deliberately DO NOT use st.talking_points here because those are
// internal sales-intelligence notes (e.g. "signal detected", "capex confirms
// budget authority") that would confuse the prospect if sent verbatim.
function emailBullets(lead) {
  const st      = lead.strategy || {}
  const robot   = st.primary_robot || 'Titan'
  const industry = lead.industry || ''
  const emp     = lead.employee_estimate || 0

  const BULLETS = {
    'Hospitality':                 [`${robot} handles room-service and amenity delivery 24/7 — no sick days, no turnover`, `Guest satisfaction scores improve when delivery response time drops below 5 minutes`, `Typical ROI window: 12–18 months based on labor cost reduction alone`],
    'Food Service':                [`${robot} covers every delivery run so your team focuses on food quality and guest experience`, `Consistent delivery speed improves table turn rate by 12–18%`, `No callouts, no training ramp — ${robot} is operational from day one`],
    'Logistics':                   [`${robot} scales your pick-and-move throughput without adding headcount`, `Payback period under 18 months at standard DC volumes`, `Integrates with existing WMS — no rip-and-replace required`],
    'Healthcare':                  [`${robot} reduces nurse walking distance by an average of 1.2 miles per shift`, `Sterile, traceable supply delivery — consistent every run`, `Frees clinical staff to spend more time on patient care, not logistics`],
    'Automotive Dealerships':      [`${robot} moves parts from the warehouse to the service bay in under 2 minutes — eliminating runner labor`, `Fixed Ops directors report 30–40% reduction in parts-retrieval labor costs`, `Measurable ROI per service bay — we can model it for your store count`],
    'Automotive Manufacturing':    [`${robot} handles WIP and kitting runs so your line workers stay on value-add tasks`, `OEM-grade cycle-time data and traceability built in`, `Typical AMR fleet ROI closes inside 18 months at production volumes`],
    'Casinos & Gaming':            [`${robot} boosts F&B delivery speed — directly tied to spend-per-visit lift`, `Frees floor staff to focus on guest engagement, not running orders`, `Deployed in casino environments — quiet, safe, and brand-consistent`],
    'Senior Living':               [`${robot} handles meal rounds and supply delivery on a consistent schedule`, `Reduces staff walking burden so caregivers spend more time with residents`, `Families notice the difference — service consistency is a retention driver`],
    'Manufacturing':               [`${robot} automates kitting and intra-facility parts delivery`, `Operators stay on the line — no walking, no waiting`, `Modular fleet scales with your production volume`],
    'Real Estate & Facilities':    [`${robot} provides consistent floor cleaning and concierge delivery — 24/7`, `Reduces janitorial and logistics labor costs by up to 35%`, `Tenant satisfaction scores improve when common areas are consistently maintained`],
  }

  const base = BULLETS[industry] || [
    `${robot} reduces labor dependency in your highest-cost operational workflows`,
    `Typical deployment ROI: 12–18 months based on headcount reduction and throughput gains`,
    `Modular, scalable fleet — starts with ${Math.max(2, st.deal_est_units || 3)} units and grows with your operation`,
  ]

  return base
}

function generatePlainText(lead) {
  const st = lead.strategy || {}
  const contact = st.contact_role || 'Director of Operations'
  const robot = st.primary_robot || 'Titan'
  const company = lead.company_name || 'your organization'
  const topSigType = lead.signals?.[0]?.signal_type || ''
  const bullets = emailBullets(lead).map(p => `  • ${p}`).join('\n')

  const urgencyLine = (() => {
    if (topSigType === 'labor_shortage' || topSigType === 'labor_pain')
      return `I noticed ${company} is actively hiring to address labor gaps — this is exactly the problem our ${robot} was built to solve.`
    if (topSigType === 'strategic_hire')
      return `Congratulations on the recent leadership additions at ${company}. As you evaluate vendors in your first 90 days, I'd love to show you what our ${robot} can do.`
    if (topSigType === 'capex')
      return `It looks like ${company} has an open technology budget window right now — ideal timing to evaluate our ${robot}.`
    if (topSigType === 'expansion')
      return `With ${company}'s expansion underway, building automation in from day one with our ${robot} is significantly more cost-effective than retrofitting later.`
    if (topSigType === 'funding_round')
      return `Congratulations on the recent funding round at ${company}. We'd love to help you put a portion of that toward automation that pays for itself.`
    if (topSigType === 'ma_activity')
      return `M&A transitions create a unique window to reassess vendor relationships — we'd love to introduce Richtech Robotics to the ${company} team.`
    return `I've been following ${company} and believe our ${robot} is a strong fit for your operations.`
  })()

  return `Subject: ${robot} for ${company} — Reduce Labor Costs by 40%

Hi [${contact}],

${urgencyLine}

I'm reaching out from Richtech Robotics. We build autonomous mobile robots purpose-built for operations like yours — specifically the ${robot}, which handles ${st.use_case || 'intra-facility logistics'}.

Why ${company} is a strong fit:
${bullets}

Our typical ${st.deal_tier || 'Mid-Market'} deployment starts at ${st.deal_est_units || 5} units with measurable ROI inside 12–18 months.

I'd love to schedule a 20-minute call to walk you through a quick ROI model specific to ${company}'s footprint.

Are you available this week or next?

Best,
[Your Name]
Richtech Robotics
[Your Phone]
richtechrobotics.com`
}

function generateHtmlEmail(lead) {
  const st = lead.strategy || {}
  const robot = st.primary_robot || 'Titan'
  const company = lead.company_name || 'your organization'
  const contact = st.contact_role || 'Director of Operations'
  const bullets = emailBullets(lead).map(p =>
    `<li style="margin-bottom:6px;color:#374151;">${p}</li>`
  ).join('')
  const robots = (st.robots || [robot]).join(', ')
  const topSigType = lead.signals?.[0]?.signal_type || ''

  const urgencyLine = (() => {
    if (topSigType === 'labor_shortage' || topSigType === 'labor_pain')
      return `I noticed <strong>${company}</strong> is actively hiring to address labor gaps — this is exactly the problem our <strong>${robot}</strong> was built to solve.`
    if (topSigType === 'strategic_hire')
      return `Congratulations on the recent leadership additions at <strong>${company}</strong>. As you evaluate vendors in your first 90 days, I'd love to show you what our <strong>${robot}</strong> can do.`
    if (topSigType === 'capex')
      return `It looks like <strong>${company}</strong> has an open technology budget window right now — ideal timing to evaluate our <strong>${robot}</strong>.`
    if (topSigType === 'expansion')
      return `With <strong>${company}</strong>'s expansion underway, building automation in from day one with <strong>${robot}</strong> is significantly more cost-effective than retrofitting later.`
    if (topSigType === 'funding_round')
      return `Congratulations on the recent funding round at <strong>${company}</strong>. We'd love to help you put a portion of that toward automation that pays for itself.`
    if (topSigType === 'ma_activity')
      return `M&A transitions create a unique window to reassess vendor relationships — we'd love to introduce Richtech Robotics to the <strong>${company}</strong> team.`
    return `I've been following <strong>${company}</strong> and believe our <strong>${robot}</strong> is a strong fit for your operations.`
  })()

  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;border:1px solid #e5e7eb;overflow:hidden;max-width:600px;width:100%;">
        <!-- Header -->
        <tr>
          <td style="background:#09090b;padding:20px 28px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <p style="margin:0;color:#ffffff;font-size:15px;font-weight:700;letter-spacing:-0.3px;">Richtech Robotics</p>
                  <p style="margin:4px 0 0;color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Autonomous Mobile Robots</p>
                </td>
                <td align="right">
                  <span style="display:inline-block;background:#1e3a5f;color:#60a5fa;font-size:11px;font-weight:600;padding:4px 10px;border-radius:4px;border:1px solid #2563eb;">${robot}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:28px 28px 8px;">
            <p style="margin:0 0 16px;color:#111827;font-size:14px;line-height:1.6;">Hi [${contact}],</p>
            <p style="margin:0 0 16px;color:#374151;font-size:14px;line-height:1.6;">${urgencyLine}</p>
            <p style="margin:0 0 16px;color:#374151;font-size:14px;line-height:1.6;">
              I'm reaching out from <strong>Richtech Robotics</strong>. We build autonomous mobile robots purpose-built for operations like yours — specifically the <strong>${robots}</strong>, which handles <em>${st.use_case || 'intra-facility logistics'}</em>.
            </p>
          </td>
        </tr>
        <!-- Why it matters -->
        <tr>
          <td style="padding:0 28px 8px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;">
              <tr><td style="padding:16px 20px;">
                <p style="margin:0 0 10px;color:#64748b;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Why ${company} is a strong fit</p>
                <ul style="margin:0;padding:0 0 0 16px;">${bullets}</ul>
              </td></tr>
            </table>
          </td>
        </tr>
        <!-- Deal note -->
        <tr>
          <td style="padding:16px 28px 8px;">
            <p style="margin:0 0 16px;color:#374151;font-size:14px;line-height:1.6;">
              Our typical <strong>${st.deal_tier || 'Mid-Market'}</strong> deployment runs <strong>${st.deal_est_units || 5}–${(st.deal_est_units || 5) + 5} units</strong> with a measurable ROI inside 12–18 months.
            </p>
            <p style="margin:0 0 16px;color:#374151;font-size:14px;line-height:1.6;">
              I'd love to schedule a <strong>20-minute call</strong> to walk you through a quick ROI model specific to <strong>${company}</strong>'s footprint.
            </p>
            <p style="margin:0 0 24px;color:#111827;font-size:14px;font-weight:600;">Are you available this week or next?</p>
          </td>
        </tr>
        <!-- CTA -->
        <tr>
          <td style="padding:0 28px 24px;">
            <a href="https://richtechrobotics.com" style="display:inline-block;background:#2563eb;color:#ffffff;font-size:13px;font-weight:600;padding:10px 20px;border-radius:6px;text-decoration:none;">
              View Richtech Robotics →
            </a>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:16px 28px;border-top:1px solid #f3f4f6;">
            <p style="margin:0;color:#9ca3af;font-size:12px;line-height:1.5;">
              [Your Name] · Richtech Robotics · [Your Phone]<br>
              <a href="https://richtechrobotics.com" style="color:#6b7280;">richtechrobotics.com</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`
}

// ─── Email Modal ────────────────────────────────────────────────────────────

function EmailModal({ lead, onClose }) {
  const [tab, setTab] = useState('plain')   // 'plain' | 'html' | 'preview'
  const [copied, setCopied] = useState(false)
  const textRef = useRef(null)
  const plainText = generatePlainText(lead)
  const htmlText  = generateHtmlEmail(lead)
  const st = lead.strategy || {}
  const robot = st.primary_robot || 'Titan'
  const subject = `${robot} for ${lead.company_name} — Reduce Labor Costs by 40%`

  function copyText() {
    const content = tab === 'html' ? htmlText : plainText
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function sendMailto() {
    const body = encodeURIComponent(plainText)
    const subj = encodeURIComponent(subject)
    window.open(`mailto:?subject=${subj}&body=${body}`)
  }

  // Close on backdrop click or Escape
  function handleBackdrop(e) { if (e.target === e.currentTarget) onClose() }
  useEffect(() => {
    const fn = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', fn)
    return () => window.removeEventListener('keydown', fn)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={handleBackdrop}
    >
      <div className="w-full max-w-3xl max-h-[90vh] flex flex-col bg-[#0a0a0a] border border-neutral-800 rounded-lg overflow-hidden shadow-2xl">

        {/* Modal header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-[11px] font-bold text-white">✉ Email Script</span>
            <span className="text-neutral-800">·</span>
            <span className="label text-neutral-400 truncate">{lead.company_name}</span>
            <span className="label text-neutral-700 hidden sm:inline">→ {st.contact_role}</span>
          </div>
          <button onClick={onClose} className="text-neutral-600 hover:text-neutral-300 text-lg leading-none ml-4 shrink-0">×</button>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 px-4 pt-2 pb-0 border-b border-neutral-900 shrink-0">
          {[
            { key: 'plain',   label: 'Plain Text' },
            { key: 'html',    label: 'HTML Source' },
            { key: 'preview', label: 'Email Preview' },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-3 py-1.5 text-[11px] font-medium border-b-2 transition-colors -mb-px ${
                tab === t.key
                  ? 'border-indigo-500 text-indigo-300'
                  : 'border-transparent text-neutral-600 hover:text-neutral-400'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 min-h-0">
          {tab === 'plain' && (
            <textarea
              id="email-plain-text"
              ref={textRef}
              readOnly
              value={plainText}
              className="w-full h-full min-h-[28rem] resize-none bg-neutral-950 border border-neutral-800 rounded p-3 text-[12px] text-neutral-300 font-mono leading-relaxed focus:outline-none focus:border-neutral-700"
            />
          )}
          {tab === 'html' && (
            <textarea
              id="email-html-text"
              readOnly
              value={htmlText}
              className="w-full h-full min-h-[28rem] resize-none bg-neutral-950 border border-neutral-800 rounded p-3 text-[11px] text-neutral-400 font-mono leading-relaxed focus:outline-none focus:border-neutral-700"
            />
          )}
          {tab === 'preview' && (
            <div className="rounded border border-neutral-800 overflow-hidden">
              <iframe
                srcDoc={htmlText}
                title="Email preview"
                className="w-full border-0 bg-white"
                style={{ height: '32rem' }}
                sandbox="allow-same-origin"
              />
            </div>
          )}
        </div>

        {/* Modal footer actions */}
        <div className="flex items-center gap-2 px-4 py-3 border-t border-neutral-800 bg-neutral-950/60 shrink-0 flex-wrap">
          <button
            onClick={copyText}
            className={`btn text-xs ${copied ? 'border-emerald-700 text-emerald-400' : 'btn-ghost'}`}
          >
            {copied ? '✓ copied' : tab === 'html' ? 'copy html' : 'copy text'}
          </button>
          <button
            onClick={sendMailto}
            className="btn border-indigo-700 text-indigo-300 hover:border-indigo-500 hover:text-indigo-100 text-xs"
          >
            ↗ open in email client
          </button>
          <span className="text-[10px] text-neutral-700 hidden sm:inline">
            Opens your default mail app with subject + body pre-filled. Replace [brackets] before sending.
          </span>
          <button onClick={onClose} className="btn-ghost text-xs ml-auto">close</button>
        </div>
      </div>
    </div>
  )
}

function ScoreNum({ value }) {
  const v = Math.round(value ?? 0)
  return (
    <span className="inline-flex items-center border border-emerald-700 text-emerald-400 rounded px-1.5 leading-none tabular-nums font-mono font-semibold text-[10px]"
      style={{ paddingTop: '0.2rem', paddingBottom: '0.2rem' }}>
      {v}
    </span>
  )
}

// -- Toast notification -------------------------------------------------------
function Toast({ msg }) {
  if (!msg) return null;
  return (
    <div style={{
      position: 'fixed', bottom: '1.75rem', left: '50%', transform: 'translateX(-50%)',
      background: '#0f172a', border: '1px solid #34d399', color: '#34d399',
      borderRadius: '9999px', padding: '0.45rem 1.25rem', fontSize: '13px',
      fontWeight: 500, zIndex: 9999, pointerEvents: 'none', whiteSpace: 'nowrap',
      boxShadow: '0 0 18px rgba(52,211,153,0.18)',
    }}>
      {msg}
    </div>
  );
}

function OpportunityRow({ lead, rank }) {
  const { session } = useAuth()
  const [open, setOpen] = useState(false)
  const [emailOpen, setEmailOpen] = useState(false)
  const [followedUp, setFollowedUp] = useState(false)
  const [savingFollowUp, setSavingFollowUp] = useState(false)
  const [authPrompt, setAuthPrompt] = useState(false)
  const [rowToast, setRowToast] = useState('')
  const rowToastTimer = useRef(null)
  const tm   = TIER_META[lead.priority_tier] || TIER_META.COLD
  const st   = lead.strategy || {}
  const topSig = lead.signals?.[0]

  async function handleFollowUp(e) {
    e.stopPropagation()
    if (!session) { setAuthPrompt(true); return }
    if (followedUp || savingFollowUp) return
    setSavingFollowUp(true)
    // Optimistic — show toast immediately, revert on failure
    setFollowedUp(true)
    setRowToast('✓ Queued for follow-up'); clearTimeout(rowToastTimer.current); rowToastTimer.current = setTimeout(() => setRowToast(''), 2500)
    try {
      const resp = await fetch(`${API}/api/user/saved`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader(session.access_token) },
        body: JSON.stringify({
          company_id:   lead.id,
          company_name: lead.company_name,
          industry:     lead.industry || '',
          tier:         lead.priority_tier || 'COLD',
          score:        lead.score?.overall_score ?? 0,
          website:      lead.website || '',
          notes:        'Follow Up',
        }),
      })
      if (!resp.ok) setFollowedUp(false)
    } catch { setFollowedUp(false) }
    setSavingFollowUp(false)
  }
  const sigM = topSig ? (SIGNAL_META[topSig.signal_type] || { label: topSig.signal_type, border: 'border-neutral-700', text: 'text-neutral-400' }) : null
  const meta = [lead.industry, lead.location_city, lead.location_state].filter(Boolean).join('  ')

  return (
    <>
      <div
        className={`${tm.accent} grid items-center border-b border-neutral-900 hover:bg-neutral-900/40 transition-colors group cursor-pointer`}
        style={{ gridTemplateColumns: '2rem 1fr 9rem 9rem 6rem 4rem 5rem' }}
        onClick={() => setOpen(o => !o)}
      >
        <span className="text-[10px] text-neutral-700 group-hover:text-neutral-500 pl-3 tabular-nums">{rank}</span>

        <div className="px-3 py-2.5 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className={`text-[12px] font-semibold text-neutral-100 group-hover:${tm.text} transition-colors`}>
              {lead.company_name}
            </span>
            {lead.priority_tier === 'HOT' && <span className="hot-pulse" />}
            <span className={`badge ${tm.border} ${tm.text}`}>{tm.label}</span>
            <span className="text-[10px] text-neutral-700 truncate hidden sm:inline">{meta}</span>
          </div>
          {lead.employee_estimate && (
            <span className="text-[10px] text-neutral-600">
              {lead.employee_estimate.toLocaleString()} emp  {st.deal_tier}  ~{st.deal_est_units} units
            </span>
          )}
        </div>

        <div className="hidden md:flex items-center gap-1 px-2 flex-wrap">
          {(st.robots || []).slice(0, 2).map(r => {
            const rm = ROBOT_META[r] || { border: 'border-neutral-700', text: 'text-neutral-400' }
            return <Bdg key={r} label={r} border={rm.border} text={rm.text} />
          })}
        </div>

        <div className="hidden md:block px-2 min-w-0">
          {(() => {
            const verified = (lead.contacts || []).find(c => c.verified && c.linkedin)
            const possible = (lead.contacts || []).find(c => (c.confidence || 0) >= 70)
            const best = verified || possible
            return best
              ? <span className="text-[10px] text-neutral-200 truncate block leading-snug font-medium">{best.name}</span>
              : <span className="text-[10px] text-neutral-500 truncate block leading-snug">{st.contact_role}</span>
          })()}
        </div>

        <div className="hidden md:flex items-center px-2">
          {sigM
            ? <Bdg label={sigM.label} border={sigM.border} text={sigM.text} />
            : <span className="text-[10px] text-neutral-700"></span>}
        </div>

        <div className="flex items-center justify-end px-2">
          <ScoreNum value={lead.score?.overall_score ?? 0} />
        </div>

        <div className="flex items-center justify-center gap-1 pr-2">
          <button
            onClick={handleFollowUp}
            title={followedUp ? 'Follow-up queued' : 'Add to follow-ups'}
            style={{ background: 'transparent', border: 'none', color: followedUp ? '#34d399' : '#6b7280', cursor: followedUp ? 'default' : 'pointer', fontSize: '13px', padding: '2px 3px', lineHeight: 1 }}
          >
            {savingFollowUp ? '…' : followedUp ? '★' : '☆'}
          </button>
          <button
            onClick={e => { e.stopPropagation(); setEmailOpen(true) }}
            title="Generate email script"
            style={{ background: 'transparent', border: 'none', color: '#818cf8', cursor: 'pointer', fontSize: '17px', padding: '2px 3px', lineHeight: 1 }}
          >
            ✉
          </button>
          <span className="text-[10px] text-neutral-700 group-hover:text-neutral-400 transition-colors">
            {open ? '▲' : '▼'}
          </span>
        </div>
      </div>

      {open && (
        <div className={`${tm.accent} border-b border-neutral-900 bg-neutral-950/60`} style={{ paddingLeft: '2rem' }}>
          {/* action buttons — first thing visible when row expands */}
          <div style={{ padding: '8px 12px', borderBottom: '1px solid rgba(38,38,38,0.8)', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={e => { e.stopPropagation(); setEmailOpen(true) }}
              style={{ background: 'transparent', border: '1px solid #3730a3', color: '#818cf8', padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 500, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
            >
              ✉ email script
            </button>
            <button
              onClick={handleFollowUp}
              style={{ background: 'transparent', border: followedUp ? '1px solid #065f46' : '1px solid #374151', color: followedUp ? '#34d399' : '#9ca3af', padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 500, cursor: followedUp ? 'default' : 'pointer', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
            >
              {savingFollowUp ? '…' : followedUp ? '★ queued for follow up' : '☆ follow up'}
            </button>
            <span style={{ fontSize: '10px', color: '#6b7280' }}>ready-to-send outreach for {lead.company_name}</span>
          </div>
          <div className="px-3 py-3 grid grid-cols-1 md:grid-cols-3 gap-x-8 gap-y-2">
            <div>
              <span className="label block mb-1">Pitch Angle</span>
              <p className="text-[11px] text-neutral-300 leading-relaxed">{st.pitch_angle}</p>
            </div>
            <div>
              <span className="label block mb-1">Talking Points</span>
              <ul className="space-y-1">
                {(st.talking_points || []).map((pt, i) => (
                  <li key={i} className="flex gap-1.5 text-[11px] text-neutral-400">
                    <span className="text-emerald-700 font-bold mt-px"></span>
                    <span>{pt}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <span className="label block mb-1">Outreach Timing</span>
              <p className="text-[11px] text-amber-400 leading-snug mb-2">{st.outreach_timing}</p>
              <span className="label block mb-1">Use Case</span>
              <p className="text-[11px] text-neutral-500 leading-snug">{st.use_case}</p>
            </div>
          </div>
          {/* Named contacts discovered by contact scraper */}
          {lead.contacts?.length > 0 && (() => {
            const verified = lead.contacts.filter(c => c.verified && c.linkedin)
            const possible = lead.contacts.filter(c => (c.confidence || 0) >= 70 && !(c.verified && c.linkedin))
            return (
              <div className="px-3 pb-2 border-t border-neutral-800/50 pt-2">
                <span className="label block mb-1.5">Decision Makers</span>
                <div className="flex flex-wrap gap-x-6 gap-y-1">
                  {verified.map((ct, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      <a href={ct.linkedin} target="_blank" rel="noreferrer"
                        className="text-[11px] text-emerald-300 hover:text-emerald-100 font-medium"
                        onClick={e => e.stopPropagation()}>
                        {ct.name}
                      </a>
                      <span className="text-[10px] text-neutral-600">{ct.title}</span>
                      <span className="text-[10px] text-emerald-800 border border-emerald-900 rounded px-1">LinkedIn</span>
                    </div>
                  ))}
                  {possible.slice(0, 4).map((ct, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-neutral-600" />
                      <span className="text-[11px] text-neutral-300">{ct.name}</span>
                      <span className="text-[10px] text-neutral-600">{ct.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}

          {lead.signals?.length > 0 && (
            <div className="px-3 pb-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-neutral-800/50 pt-2">
              {lead.signals.slice(0, 4).map((sig, i) => {
                const sm = SIGNAL_META[sig.signal_type] || { label: sig.signal_type, border: 'border-neutral-700', text: 'text-neutral-400' }
                const snippet = (sig.raw_text || '').replace(/<[^>]*>/g, '').substring(0, 80)
                return (
                  <div key={i} className="flex items-baseline gap-1.5 min-w-0">
                    <Bdg label={sm.label} border={sm.border} text={sm.text} />
                    {snippet && (
                      <span className="text-[10px] text-neutral-600 truncate max-w-[26rem]">
                        {snippet}{snippet.length === 80 ? '' : ''}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
      {emailOpen && <EmailModal lead={lead} onClose={() => setEmailOpen(false)} />}
      {authPrompt && <AuthPrompt onClose={() => setAuthPrompt(false)} />}
      <Toast msg={rowToast} />
    </>
  )
}

function TierSection({ tier, leads, startRank }) {
  const [collapsed, setCollapsed] = useState(false)
  const tm = TIER_META[tier] || TIER_META.COLD
  const labels = { HOT: 'Act Now', WARM: 'Nurture & Sequence', COLD: 'Monitor' }

  return (
    <section className="mb-6">
      <div
        className="flex items-center gap-3 px-3 py-1.5 border-b border-neutral-800 cursor-pointer hover:bg-neutral-900/30 transition-colors"
        onClick={() => setCollapsed(c => !c)}
      >
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${tm.dot}`} />
        <span className={`label ${tm.text}`}>{tier}  {labels[tier]}</span>
        <span className="label text-neutral-700">{leads.length} opportunities</span>
        <span className="ml-auto text-[10px] text-neutral-700 hover:text-neutral-500">{collapsed ? '' : ''}</span>
      </div>

      {!collapsed && (
        <div className="border border-neutral-800 border-t-0 rounded-b overflow-hidden">
          <div
            className="hidden md:grid border-b border-neutral-800/60 bg-neutral-950"
            style={{ gridTemplateColumns: '2rem 1fr 9rem 9rem 6rem 4rem 5rem' }}
          >
            <span />
            <span className="label px-3 py-2">company</span>
            <span className="label px-2 py-2">robot</span>
            <span className="label px-2 py-2">contact</span>
            <span className="label px-2 py-2">signal</span>
            <span className="label px-2 py-2 text-right">score</span>
            <span />
          </div>
          {leads.map((lead, i) => (
            <OpportunityRow key={lead.id} lead={lead} rank={startRank + i} />
          ))}
        </div>
      )}
    </section>
  )
}

// ─── RichTech Growth Playbook ─────────────────────────────────────────────────

const PLAYBOOK = {
  narrative: {
    headline: 'Robots Built for the Business, Not the Boardroom.',
    tagline:  'Your Labor Problem, Solved by Shift One.',
    pillars: [
      {
        name:   'Operational First',
        detail: 'Designed around shift workers, not software teams. Trained in days, not months. No PhD required, no six-month integration, no robot-shaped showpieces gathering dust in a lobby.',
      },
      {
        name:   'Real Economy, Real ROI',
        detail: 'RichTech customers run hotels, warehouses, and dealerships. ROI is measured in labor hours saved per shift, not in innovation optics. Every pitch leads with payback period.',
      },
      {
        name:   'Partners in Scale',
        detail: 'Not a vendor that ships and disappears. WMS integrations, channel partnerships, and managed fleet programs let customers grow from 1 robot to 100 without switching vendors.',
      },
    ],
    retire: [
      { word: 'innovation',   replace: '"operational efficiency" or a specific metric' },
      { word: 'autonomous',   replace: '"runs without a handler" or "no dedicated operator required"' },
      { word: 'cutting-edge', replace: '"shift-ready in 72 hours" or "proven in your vertical"' },
    ],
  },
  gtm: [
    {
      title:    'Build a WMS API Integration Strategy',
      priority: 'HIGH',
      detail:   'Every logistics and distribution buyer runs a WMS. Without certified integrations, RichTech loses deals at the IT checkpoint before the sales conversation ends. Build and certify native connectors for the top 3 platforms — then pursue ISV partner listings to get in front of their existing customer bases.',
      partners: ['Manhattan Associates WM', 'Oracle WMS Cloud', 'Blue Yonder / JDA', 'Logiwa', 'Extensiv'],
      action:   'Target: 2 certified WMS integrations live by Q3 2026. Pursue ISV/partner marketplace listing in each.',
    },
    {
      title:    'Channel Partnership — Managed Services',
      priority: 'HIGH',
      detail:   'Aramark, Sodexo, and Compass Group manage food and facilities at tens of thousands of locations globally — all under the same labor pressure as your direct buyers. A single preferred vendor agreement converts RichTech\'s go-to-market from 1-deal-at-a-time to a channel that opens hundreds of locations simultaneously.',
      partners: ['Aramark', 'Sodexo', 'Compass Group', 'Marriott Bonvoy Vendor Program', 'Hilton Supply Management'],
      action:   'Target: preferred vendor agreement with one managed services firm by Q3 2026. Co-deploy model: their endorsement, your robots, shared services margin.',
    },
    {
      title:    'Channel Partnership — Hotel Brand Ecosystems',
      priority: 'MEDIUM',
      detail:   'A single preferred vendor designation with Marriott, IHG, or Hilton immediately legitimizes RichTech for every franchisee and property owner in their network. Hotel brands run annual vendor summits where approved vendors get direct access to hundreds of GMs and VP Ops simultaneously.',
      partners: ['Marriott International', 'IHG Hotels & Resorts', 'Hilton Worldwide', 'Choice Hotels', 'Wyndham Hotels'],
      action:   'Target: vendor program enrollment with one Tier-1 hotel brand in H2 2026.',
    },
  ],
  roadmap: [
    {
      title:    'Elevator & Multi-Level Integration Protocol',
      priority: 'HIGH',
      detail:   'Titan is locked to flat-floor environments. Hotels have service floors, hospitals have multi-level supply routes, distribution centers have mezzanine pick levels. Elevator API integration is largely a software effort — and it opens the entire vertical real estate sector.',
      systems:  ['Schindler PORT', 'Otis Compass 360', 'Kone FLOW', 'thyssenkrupp MAX'],
      unlock:   'Hotels, Hospitals, Multi-Story DCs, Mixed-Use Facilities',
    },
    {
      title:    'Elevated Reach Module for Titan',
      priority: 'MEDIUM',
      detail:   'A modular attachment allowing Titan to deposit and retrieve from standard warehouse racking without a human picker. Converts Titan from "transport cart" to "autonomous material handler" — a significantly larger TAM and a direct answer to why logistics buyers choose Locus over Titan today.',
      systems:  [],
      unlock:   'Automotive Parts High-Rack, Distribution Racking, Mezzanine Retrieval',
    },
  ],
  startupWatch: [
    {
      name:      'Slamtec (RPLIDAR)',
      category:  'Localization / Mapping',
      action:    'License',
      rationale: 'Their LiDAR SDK and fleet mapping package is already proven in production AMRs. Licensing RPLIDAR Pro + multi-robot coordination closes Titan\'s large-floor enterprise deployment gap at accessible cost.',
    },
    {
      name:      'Logiwa',
      category:  'Cloud WMS',
      action:    'Partner',
      rationale: 'Mid-market e-commerce fulfillment WMS. Customer base overlaps directly with Titan\'s logistics TAM. A native Titan integration + co-sell motion puts RichTech in front of every new Logiwa deployment.',
    },
    {
      name:      'Extensiv (3PL WMS)',
      category:  'Logistics Platform',
      action:    'Partner',
      rationale: '3PL-focused WMS. 3PLs are the fastest-growing segment in logistics automation adoption. Extensiv partnership gives RichTech a channel into hundreds of 3PL operators simultaneously.',
    },
    {
      name:      'Marble (Service Robot Nav IP)',
      category:  'Navigation / Autonomy',
      action:    'Acquire / License',
      rationale: 'Pivoted from last-mile delivery. Indoor/outdoor transition navigation and complex-environment autonomy apply directly to Titan deployments in campus and multi-building environments.',
    },
  ],
  university: [
    {
      name:    'Carnegie Mellon Robotics Institute',
      focus:   'Multi-robot SLAM & fleet coordination',
      app:     'Large-scale Titan fleet deployment in distribution centers — 50+ unit coordination, live rerouting, dynamic obstacle response.',
      contact: 'CMU Technology Transfer',
    },
    {
      name:    'Georgia Tech IRIM',
      focus:   'Healthcare robot interaction & proximity navigation',
      app:     'MEDBOT expansion into hospital systems and senior care — FDA-adjacent compliance, patient safety protocols, clinical environment navigation.',
      contact: 'Georgia Tech Research Corporation (GTRC)',
    },
    {
      name:    'Stanford HCI Group',
      focus:   'Social robotics & natural language guest interaction',
      app:     'ADAM and Matradee guest-facing interaction quality. Differentiates hospitality deployments at the brand narrative level.',
      contact: 'Stanford Office of Technology Licensing (OTL)',
    },
    {
      name:    'UC Berkeley AUTOLAB',
      focus:   'Bin picking & uncertainty-aware grasping',
      app:     'Automotive parts retrieval from bins — extends Titan into parts-picking, unlocking service-bay automation at dealerships.',
      contact: 'Berkeley Skydeck / IPIRA',
    },
  ],
}

function RichtechPlaybook() {
  const [section, setSection] = useState(null)
  function toggle(key) { setSection(s => s === key ? null : key) }

  const P_META = {
    HIGH:   { text: 'text-red-400',   border: 'border-red-900',   label: 'HIGH PRIORITY' },
    MEDIUM: { text: 'text-amber-400', border: 'border-amber-900', label: 'MEDIUM'        },
  }
  const A_META = {
    'License':           { text: 'text-violet-400', border: 'border-violet-800' },
    'Partner':           { text: 'text-cyan-400',   border: 'border-cyan-900'   },
    'Acquire / License': { text: 'text-red-400',    border: 'border-red-900'    },
  }
  const SECTIONS = [
    { key: 'narrative',  label: 'Brand Narrative',     sub: '3 pillars'                                    },
    { key: 'gtm',        label: 'Go-to-Market Moves',  sub: `${PLAYBOOK.gtm.length} actions`               },
    { key: 'roadmap',    label: 'Technology Roadmap',  sub: `${PLAYBOOK.roadmap.length} programs`           },
    { key: 'startups',   label: 'Startup Watch List',  sub: `${PLAYBOOK.startupWatch.length} targets`      },
    { key: 'university', label: 'University Pipeline', sub: `${PLAYBOOK.university.length} research groups` },
  ]

  return (
    <div className="mt-10 pt-6 border-t border-neutral-800 space-y-1">
      <div className="flex items-center gap-3 mb-5">
        <span className="text-[11px] font-semibold text-neutral-300 uppercase tracking-widest">RichTech Growth Playbook</span>
        <span className="text-neutral-800">·</span>
        <span className="label text-neutral-700">strategic recommendations · March 2026</span>
      </div>

      {SECTIONS.map(sec => (
        <div key={sec.key} className="border border-neutral-800 rounded overflow-hidden">
          <button
            onClick={() => toggle(sec.key)}
            className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-neutral-900/50 transition-colors"
          >
            <span className="flex items-center gap-3">
              <span className="text-[13px] font-semibold text-neutral-200">{sec.label}</span>
              <span className="label text-neutral-700">{sec.sub}</span>
            </span>
            <span className="text-neutral-700 text-[10px] font-mono">{section === sec.key ? '▲' : '▼'}</span>
          </button>

          {section === sec.key && (
            <div className="border-t border-neutral-800 px-4 pt-4 pb-5 space-y-4 bg-neutral-950/30">

              {sec.key === 'narrative' && (
                <div className="space-y-5">
                  <div className="space-y-1.5">
                    <p className="text-[18px] font-bold text-white leading-snug tracking-tight">&ldquo;{PLAYBOOK.narrative.headline}&rdquo;</p>
                    <p className="text-sm text-neutral-400 italic pl-1">{PLAYBOOK.narrative.tagline}</p>
                  </div>
                  <div className="grid sm:grid-cols-3 gap-3">
                    {PLAYBOOK.narrative.pillars.map(p => (
                      <div key={p.name} className="border border-emerald-900/50 rounded p-3 space-y-1.5 bg-emerald-950/10">
                        <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">{p.name}</p>
                        <p className="text-[11px] text-neutral-400 leading-relaxed">{p.detail}</p>
                      </div>
                    ))}
                  </div>
                  <div className="border border-neutral-800 rounded p-3 space-y-2">
                    <p className="label text-neutral-600 mb-2">language to retire from all materials</p>
                    <div className="space-y-2">
                      {PLAYBOOK.narrative.retire.map(r => (
                        <div key={r.word} className="flex items-start gap-3">
                          <span className="text-[11px] text-neutral-600 line-through shrink-0 w-28">{r.word}</span>
                          <span className="text-[11px] text-neutral-400">→ {r.replace}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {sec.key === 'gtm' && (
                <div className="space-y-3">
                  {PLAYBOOK.gtm.map(item => {
                    const pm = P_META[item.priority] || P_META.MEDIUM
                    return (
                      <div key={item.title} className={`border ${pm.border} rounded p-4 space-y-2.5 bg-neutral-950/20`}>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[12px] font-semibold text-neutral-100">{item.title}</span>
                          <span className={`badge ${pm.border} ${pm.text} text-[9px]`}>{pm.label}</span>
                        </div>
                        <p className="text-[11px] text-neutral-400 leading-relaxed">{item.detail}</p>
                        <div className="flex flex-wrap gap-1.5 items-center">
                          <span className="label text-neutral-700 shrink-0">target partners</span>
                          {item.partners.map(p => (
                            <span key={p} className="badge border-neutral-800 text-neutral-500 text-[9px]">{p}</span>
                          ))}
                        </div>
                        <p className="text-[11px] text-emerald-500 font-medium border-t border-neutral-800 pt-2">{item.action}</p>
                      </div>
                    )
                  })}
                </div>
              )}

              {sec.key === 'roadmap' && (
                <div className="space-y-3">
                  {PLAYBOOK.roadmap.map(item => {
                    const pm = P_META[item.priority] || P_META.MEDIUM
                    return (
                      <div key={item.title} className={`border ${pm.border} rounded p-4 space-y-2.5 bg-neutral-950/20`}>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[12px] font-semibold text-neutral-100">{item.title}</span>
                          <span className={`badge ${pm.border} ${pm.text} text-[9px]`}>{pm.label}</span>
                        </div>
                        <p className="text-[11px] text-neutral-400 leading-relaxed">{item.detail}</p>
                        {item.systems.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 items-center">
                            <span className="label text-neutral-700 shrink-0">integration targets</span>
                            {item.systems.map(s => (
                              <span key={s} className="badge border-neutral-800 text-neutral-500 text-[9px]">{s}</span>
                            ))}
                          </div>
                        )}
                        <p className="text-[11px] text-cyan-500 font-medium border-t border-neutral-800 pt-2">Unlocks: <span className="text-cyan-400">{item.unlock}</span></p>
                      </div>
                    )
                  })}
                </div>
              )}

              {sec.key === 'startups' && (
                <div className="space-y-2">
                  {PLAYBOOK.startupWatch.map(item => {
                    const am = A_META[item.action] || { text: 'text-neutral-400', border: 'border-neutral-800' }
                    return (
                      <div key={item.name} className="border border-neutral-800 rounded p-3 space-y-1.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[12px] font-semibold text-neutral-100">{item.name}</span>
                          <span className="badge border-neutral-800 text-neutral-600 text-[9px]">{item.category}</span>
                          <span className={`badge ${am.border} ${am.text} text-[9px]`}>{item.action}</span>
                        </div>
                        <p className="text-[11px] text-neutral-400 leading-relaxed">{item.rationale}</p>
                      </div>
                    )
                  })}
                </div>
              )}

              {sec.key === 'university' && (
                <div className="space-y-2">
                  {PLAYBOOK.university.map(item => (
                    <div key={item.name} className="border border-neutral-800 rounded p-3 space-y-1.5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[12px] font-semibold text-neutral-100">{item.name}</span>
                        <span className="badge border-indigo-900 text-indigo-500 text-[9px]">{item.focus}</span>
                      </div>
                      <p className="text-[11px] text-neutral-400 leading-relaxed">{item.app}</p>
                      <p className="text-[10px] text-neutral-600 border-t border-neutral-900 pt-1.5">Contact via: {item.contact}</p>
                    </div>
                  ))}
                </div>
              )}

            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function StrategyPage() {
  const { session } = useAuth()
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [loginModal, setLoginModal] = useState(false)

  const fetchStrategy = () => {
    setLoading(true)
    setError(null)
    fetch(`${API}/api/strategy/today`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }

  useEffect(() => { fetchStrategy() }, [])

  const hot  = data?.opportunities?.filter(o => o.priority_tier === 'HOT')  || []
  const warm = data?.opportunities?.filter(o => o.priority_tier === 'WARM') || []
  const cold = data?.opportunities?.filter(o => o.priority_tier === 'COLD') || []

  return (
    <>
      <Head>
        <title>Daily Strategy Brief  Ready for Robots</title>
      </Head>

      <div className="min-h-screen bg-[#080808] flex flex-col">

        <header className="sticky top-0 z-40 bg-[#080808]/95 backdrop-blur-md border-b border-neutral-800/80 px-4 md:px-6 h-12 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-neutral-700 hover:text-neutral-300 text-xs transition-colors"> dashboard</Link>
            <span className="text-neutral-800">|</span>
            <Link href="/intelligence" className="text-neutral-700 hover:text-pink-300 text-xs transition-colors">intelligence</Link>
            <span className="text-neutral-800">|</span>
            <h1 className="text-sm font-bold text-white tracking-tight">Daily Strategy Brief</h1>
            {data && (
              <span className="label border border-neutral-800 rounded px-1.5 py-0.5 text-neutral-500 hidden sm:inline">
                {data.report_date}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            {data && (
              <div className="hidden sm:flex items-center gap-3 mr-2">
                <span className="flex items-center gap-1 text-[10px] text-red-500">
                  <span className="hot-pulse" />{hot.length} hot
                </span>
                <span className="flex items-center gap-1 text-[10px] text-yellow-500">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-yellow-500" />{warm.length} warm
                </span>
                <span className="flex items-center gap-1 text-[10px] text-neutral-600">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-neutral-600" />{cold.length} cold
                </span>
              </div>
            )}
            {data?.source && (
              <span className={`label px-1.5 py-0.5 border rounded text-[10px] hidden sm:inline ${
                data.source === 'published' ? 'border-emerald-900 text-emerald-600' : 'border-neutral-800 text-neutral-600'
              }`}>
                {data.source === 'published' ? '✓ published' : 'live'}
              </span>
            )}
            {data?.contacts_found > 0 && (
              <span className="label text-neutral-600 hidden sm:inline">{data.contacts_found} contacts</span>
            )}
            <button onClick={() => fetchStrategy()} className="btn-ghost text-neutral-600" title="Refresh"></button>
            <button onClick={() => window.print()} className="btn-ghost text-neutral-500 hidden sm:inline-flex">print</button>
            {session ? (
              <>
                <Link href="/profile" className="label text-neutral-500 hover:text-neutral-200 transition-colors hidden md:inline" title={session.user.email}>
                  {session.user.email.split('@')[0]}
                </Link>
                <Link href="/profile" className="btn-ghost border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-200 text-xs">My Profile</Link>
                <button
                  onClick={() => supabase.auth.signOut()}
                  className="btn-ghost text-xs border-neutral-800 text-neutral-600 hover:border-red-900 hover:text-red-500">
                  sign out
                </button>
              </>
            ) : (
              <>
                <Link href="/profile" className="btn-ghost border-neutral-800 text-neutral-600 hover:border-neutral-600 text-xs">My Profile</Link>
                <button
                  onClick={() => setLoginModal(true)}
                  className="btn-ghost text-xs border-emerald-900 text-emerald-500 hover:border-emerald-600 font-medium">
                  Log In
                </button>
              </>
            )}
            {loginModal && <LoginModal onClose={() => setLoginModal(false)} />}
          </div>
        </header>

        <main className="flex-1 px-4 md:px-6 py-4">

          {loading && (
            <div className="flex items-center justify-center py-24">
              <div className="text-center">
                <div className="w-6 h-6 border border-emerald-700 border-t-emerald-400 rounded-full animate-spin mx-auto mb-3" />
                <p className="label">loading strategy brief</p>
              </div>
            </div>
          )}

          {error && (
            <div className="border border-red-900 rounded p-4 mt-4">
              <span className="label text-red-500">error  </span>
              <span className="text-[11px] text-neutral-400">{error}</span>
              <button onClick={() => fetchStrategy()} className="btn-danger ml-4">retry</button>
            </div>
          )}

          {!loading && !error && data && (
            <>
              <div className="flex items-center gap-4 mb-4 border-b border-neutral-900 pb-3">
                <span className="label">richtech robotics</span>
                <span className="text-neutral-800 text-xs"></span>
                <span className="label">{data.opportunity_count} opportunities</span>
                <span className="text-neutral-800 text-xs"></span>
                <span className="label">click any row to expand strategy</span>
              </div>

              {hot.length > 0 && <TierSection tier="HOT"  leads={hot}  startRank={1} />}
              {warm.length > 0 && <TierSection tier="WARM" leads={warm} startRank={hot.length + 1} />}
              {cold.length > 0 && <TierSection tier="COLD" leads={cold} startRank={hot.length + warm.length + 1} />}

              {data.opportunities.length === 0 && (
                <div className="py-16 text-center">
                  <p className="label">no opportunities  run scoring engine to populate data</p>
                </div>
              )}

              <RichtechPlaybook />

              <div className="mt-8 pt-4 border-t border-neutral-900 flex items-center gap-3">
                <span className="label">richtech robotics · built for the business, not the boardroom · {data.report_date}</span>
              </div>
            </>
          )}
        </main>
      </div>

      <style jsx global>{`
        @media print {
          @page { margin: 1cm; }
          .sticky { position: relative; }
        }
      `}</style>
    </>
  )
}
