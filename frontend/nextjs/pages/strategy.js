/**
 * Daily Strategy Brief  Supabase-style dark design
 * Matches the main dashboard: no fills, stroke + text only, dark bg.
 */
import { useState, useEffect, useRef } from 'react'
import Head from 'next/head'
import Link from 'next/link'

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
  news:                 { label: 'News',      border: 'border-neutral-700',text: 'text-neutral-400'},
  automation_intent:    { label: 'Auto',      border: 'border-indigo-700', text: 'text-indigo-400' },
  equipment_integration:{ label: 'ERP/WMS',  border: 'border-teal-700',   text: 'text-teal-400'   },
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

function generatePlainText(lead) {
  const st = lead.strategy || {}
  const contact = st.contact_role || 'Director of Operations'
  const robot = st.primary_robot || 'Titan'
  const company = lead.company_name || 'your organization'
  const points = (st.talking_points || []).map(p => `  • ${p}`).join('\n')
  const topSigType = lead.signals?.[0]?.signal_type || ''
  const topSigSnippet = (lead.signals?.[0]?.raw_text || '').replace(/<[^>]*>/g, '').substring(0, 100)

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

Why it matters for ${company}:
${points}

Our typical ${st.deal_tier || 'Mid-Market'} deployment runs ${st.deal_est_units || 5}–${(st.deal_est_units || 5) + 5} units with a measurable ROI inside 12–18 months.

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
  const points = (st.talking_points || []).map(p =>
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
                <p style="margin:0 0 10px;color:#64748b;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Why it matters for ${company}</p>
                <ul style="margin:0;padding:0 0 0 16px;">${points}</ul>
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
              ref={textRef}
              readOnly
              value={plainText}
              className="w-full h-full min-h-[28rem] resize-none bg-neutral-950 border border-neutral-800 rounded p-3 text-[12px] text-neutral-300 font-mono leading-relaxed focus:outline-none focus:border-neutral-700"
            />
          )}
          {tab === 'html' && (
            <textarea
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

function OpportunityRow({ lead, rank }) {
  const [open, setOpen] = useState(false)
  const [emailOpen, setEmailOpen] = useState(false)
  const tm   = TIER_META[lead.priority_tier] || TIER_META.COLD
  const st   = lead.strategy || {}
  const topSig = lead.signals?.[0]
  const sigM = topSig ? (SIGNAL_META[topSig.signal_type] || { label: topSig.signal_type, border: 'border-neutral-700', text: 'text-neutral-400' }) : null
  const meta = [lead.industry, lead.location_city, lead.location_state].filter(Boolean).join('  ')

  return (
    <>
      <div
        className={`${tm.accent} grid items-center border-b border-neutral-900 hover:bg-neutral-900/40 transition-colors group cursor-pointer`}
        style={{ gridTemplateColumns: '2rem 1fr 9rem 9rem 6rem 4rem 3.5rem' }}
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
          <span className="text-[10px] text-neutral-400 truncate block leading-snug">{st.contact_role}</span>
        </div>

        <div className="hidden md:flex items-center px-2">
          {sigM
            ? <Bdg label={sigM.label} border={sigM.border} text={sigM.text} />
            : <span className="text-[10px] text-neutral-700"></span>}
        </div>

        <div className="flex items-center justify-end px-2">
          <ScoreNum value={lead.score?.overall_score ?? 0} />
        </div>

        <div className="flex items-center justify-center pr-3">
          <span className="text-[10px] text-neutral-700 group-hover:text-neutral-400 transition-colors">
            {open ? '' : ''}
          </span>
        </div>
      </div>

      {open && (
        <div className={`${tm.accent} border-b border-neutral-900 bg-neutral-950/60`} style={{ paddingLeft: '2rem' }}>
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
          {/* Email script action bar */}
          <div className="px-3 py-2.5 border-t border-neutral-800/50 flex items-center gap-3">
            <button
              onClick={e => { e.stopPropagation(); setEmailOpen(true) }}
              className="btn border-indigo-800 text-indigo-400 hover:border-indigo-500 hover:text-indigo-200 text-xs"
            >
              ✉ email script
            </button>
            <span className="text-[10px] text-neutral-700">generate outreach email for {lead.company_name}</span>
          </div>
        </div>
      )}
      {emailOpen && <EmailModal lead={lead} onClose={() => setEmailOpen(false)} />}
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
            style={{ gridTemplateColumns: '2rem 1fr 9rem 9rem 6rem 4rem 3.5rem' }}
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

export default function StrategyPage() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [limit, setLimit]     = useState(25)

  const fetchStrategy = (lmt) => {
    setLoading(true)
    setError(null)
    fetch(`${API}/api/strategy?limit=${lmt}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }

  useEffect(() => { fetchStrategy(limit) }, [])

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
            <select
              value={limit}
              onChange={e => { const v = Number(e.target.value); setLimit(v); fetchStrategy(v) }}
              className="btn-ghost text-xs appearance-none bg-transparent cursor-pointer"
            >
              <option value={10} style={{background:'#080808'}}>top 10</option>
              <option value={25} style={{background:'#080808'}}>top 25</option>
              <option value={50} style={{background:'#080808'}}>top 50</option>
            </select>
            <button onClick={() => fetchStrategy(limit)} className="btn-ghost text-neutral-600" title="Refresh"></button>
            <button onClick={() => window.print()} className="btn-ghost text-neutral-500 hidden sm:inline-flex">print</button>
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
              <button onClick={() => fetchStrategy(limit)} className="btn-danger ml-4">retry</button>
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

              <div className="mt-8 pt-4 border-t border-neutral-900 flex items-center gap-3">
                <span className="label">richtech robotics  ready for robots intelligence platform  {data.report_date}</span>
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
