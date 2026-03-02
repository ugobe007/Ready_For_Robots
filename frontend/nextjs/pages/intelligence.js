/**
 * Strategic Intelligence — Ready for Robots
 * Daily-refreshed M&A, humanoid, competitor, market & industry news feed.
 * Supabase-style dark design: no fills, stroke + text, emerald/cyan accents.
 */
import { useState, useEffect, useCallback } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useAuth } from './_app'
import { supabase } from '../lib/supabase'
import LoginModal from '../components/LoginModal'

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000')

// ── Category metadata ────────────────────────────────────────────────────────

const CAT_META = {
  MA_WATCH:   { label: 'M&A Watch',              color: 'text-pink-400',    border: 'border-pink-800',    dot: 'bg-pink-500',    desc: 'Acquisition targets & deal activity' },
  HUMANOID:   { label: 'Humanoid Market',         color: 'text-violet-400',  border: 'border-violet-800',  dot: 'bg-violet-500',  desc: 'Humanoid robot companies & deployments' },
  COMPETITOR: { label: 'Competitor Landscape',    color: 'text-cyan-400',    border: 'border-cyan-800',    dot: 'bg-cyan-500',    desc: 'Bear Robotics, Pudu, Keenon & others' },
  MARKET:     { label: 'Market Signals',          color: 'text-emerald-400', border: 'border-emerald-800', dot: 'bg-emerald-500', desc: 'Funding rounds, deals, market growth' },
  INDUSTRY:   { label: 'Industry Trends',         color: 'text-amber-400',   border: 'border-amber-800',   dot: 'bg-amber-500',   desc: 'Labor shortage, automation adoption' },
  PARTNER:    { label: 'Partner & Tech Ecosystem',color: 'text-blue-400',    border: 'border-blue-800',    dot: 'bg-blue-500',    desc: 'NVIDIA, Microsoft, Apple, integration news' },
  FOUNDATION: { label: 'VLA & Foundation Models', color: 'text-orange-400',  border: 'border-orange-800',  dot: 'bg-orange-500',  desc: 'VLA, locomotion, world models — companies & universities' },
}

const CAT_ORDER = ['MA_WATCH', 'HUMANOID', 'COMPETITOR', 'MARKET', 'INDUSTRY', 'PARTNER', 'FOUNDATION']

// ── Tiny components ──────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex items-center justify-center py-24">
      <div className="text-center">
        <div className="w-6 h-6 border border-emerald-700 border-t-emerald-400 rounded-full animate-spin mx-auto mb-3" />
        <p className="label">loading intelligence feed…</p>
      </div>
    </div>
  )
}

function CatBadge({ category }) {
  const m = CAT_META[category] || { label: category, color: 'text-neutral-400', border: 'border-neutral-700' }
  return (
    <span className={`inline-flex items-center border text-[9px] font-medium px-1.5 py-0.5 uppercase tracking-wider ${m.border} ${m.color}`}>
      {m.label}
    </span>
  )
}

function TagBadge({ tag }) {
  return (
    <span className="inline-flex border border-neutral-800 text-neutral-500 text-[9px] px-1.5 py-0.5">
      {tag}
    </span>
  )
}

function RelDate({ iso }) {
  if (!iso) return null
  const d = new Date(iso)
  const now = Date.now()
  const diffMs = now - d.getTime()
  const diffH  = Math.floor(diffMs / 3_600_000)
  const diffD  = Math.floor(diffMs / 86_400_000)
  const label  = diffH < 1  ? 'just now'
               : diffH < 24 ? `${diffH}h ago`
               : diffD < 14 ? `${diffD}d ago`
               : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  return <span className="text-[10px] text-neutral-600 tabular-nums whitespace-nowrap">{label}</span>
}

// ── News item card ───────────────────────────────────────────────────────────

function NewsCard({ item }) {
  const [expanded, setExpanded] = useState(false)
  const hasSummary = item.summary && item.summary.trim().length > 0

  return (
    <div
      className="border-b border-neutral-900 hover:bg-neutral-900/30 transition-colors"
    >
      <div
        className="px-4 py-3 flex flex-col gap-1 cursor-pointer"
        onClick={() => hasSummary && setExpanded(e => !e)}
      >
        <div className="flex items-start gap-2 flex-wrap">
          {/* Title + external link */}
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[12px] font-medium text-neutral-100 hover:text-emerald-400 transition-colors leading-snug flex-1 min-w-0"
            onClick={e => e.stopPropagation()}
          >
            {item.title}
          </a>
        </div>

        <div className="flex items-center gap-2 flex-wrap mt-0.5">
          {item.source_name && (
            <span className="text-[10px] text-neutral-600">{item.source_name}</span>
          )}
          <RelDate iso={item.pub_date || item.fetched_at} />
          {item.tag && <TagBadge tag={item.tag} />}
          {hasSummary && (
            <span className="text-[10px] text-neutral-700 ml-auto">
              {expanded ? '▲ hide' : '▼ more'}
            </span>
          )}
        </div>
      </div>

      {expanded && hasSummary && (
        <div className="px-4 pb-3">
          <p className="text-[11px] text-neutral-500 leading-relaxed border-l-2 border-neutral-800 pl-3">
            {item.summary.replace(/<[^>]*>/g, '').substring(0, 400)}
            {item.summary.length > 400 ? '…' : ''}
          </p>
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] text-emerald-600 hover:text-emerald-400 mt-1 inline-block"
          >
            read full article ↗
          </a>
        </div>
      )}
    </div>
  )
}

// ── Category section ─────────────────────────────────────────────────────────

function CategorySection({ catKey, items, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const [showAll, setShowAll] = useState(false)
  const LIMIT = 5
  const m = CAT_META[catKey] || { label: catKey, color: 'text-neutral-400', border: 'border-neutral-700', dot: 'bg-neutral-500', desc: '' }
  const visible = showAll ? items : items.slice(0, LIMIT)
  const overflow = items.length - LIMIT

  return (
    <section className="mb-4">
      {/* Section header */}
      <div
        className="flex items-center gap-3 px-4 py-2 border border-neutral-800 hover:bg-neutral-900/40 cursor-pointer transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${m.dot}`} />
        <span className={`text-xs font-semibold tracking-wide ${m.color}`}>{m.label}</span>
        <span className="text-[10px] text-neutral-600">{m.desc}</span>
        <span className="ml-auto flex items-center gap-2">
          <span className={`text-[10px] px-1.5 py-0.5 border ${m.border} ${m.color}`}>
            {items.length} items
          </span>
          <span className="text-[10px] text-neutral-700">{open ? '▲' : '▼'}</span>
        </span>
      </div>

      {open && (
        <div className="border border-neutral-800 border-t-0 rounded-b overflow-hidden">
          {items.length === 0 ? (
            <p className="px-4 py-6 text-[11px] text-neutral-700 text-center">
              No items yet — refresh to fetch latest intelligence.
            </p>
          ) : (
            <>
              {visible.map(item => <NewsCard key={item.id} item={item} />)}
              {overflow > 0 && (
                <button
                  onClick={() => setShowAll(s => !s)}
                  className="w-full px-4 py-2 text-[10px] text-neutral-600 hover:text-neutral-400 hover:bg-neutral-900/40 transition-colors border-t border-neutral-900 text-left"
                >
                  {showAll ? '▲ show less' : `▼ show ${overflow} more`}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </section>
  )
}

// ── Summary bar ──────────────────────────────────────────────────────────────

function SummaryBar({ summary }) {
  if (!summary) return null
  return (
    <div className="flex items-center gap-4 flex-wrap mb-4 px-1">
      {(summary.categories || []).map(cat => {
        const m = CAT_META[cat.key] || {}
        return (
          <div key={cat.key} className="flex items-center gap-1.5">
            <span className={`inline-block h-1.5 w-1.5 rounded-full ${m.dot || 'bg-neutral-500'}`} />
            <span className={`text-[10px] font-medium ${m.color || 'text-neutral-400'}`}>{cat.label}</span>
            <span className="text-[10px] text-neutral-700">{cat.count}</span>
          </div>
        )
      })}
      {summary.last_fetched && (
        <span className="text-[10px] text-neutral-700 ml-auto hidden sm:inline">
          last refresh: <RelDate iso={summary.last_fetched} />
        </span>
      )}
    </div>
  )
}

// ── Daily Briefing drawer ────────────────────────────────────────────────────

function faviconUrl(url) {
  if (!url) return null
  try {
    const domain = new URL(url).hostname
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=64`
  } catch { return null }
}

function StoryTile({ s, idx }) {
  const m   = CAT_META[s.category] || { color: 'text-neutral-400', dot: 'bg-neutral-500', border: 'border-neutral-800', label: s.category }
  const img = faviconUrl(s.source_url)
  return (
    <a
      href={s.source_url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={e => e.stopPropagation()}
      className="flex items-start gap-3 px-3 py-2.5 rounded border border-neutral-800/60 hover:border-neutral-700 hover:bg-neutral-900/50 transition-all group"
    >
      {/* Favicon / letter avatar */}
      <div className={`shrink-0 w-8 h-8 rounded border ${m.border} bg-neutral-900/80 flex items-center justify-center overflow-hidden`}>
        {img && (
          <img
            src={img}
            alt=""
            width={20}
            height={20}
            className="opacity-75 group-hover:opacity-100 transition-opacity"
            onError={e => { e.currentTarget.style.display = 'none' }}
          />
        )}
      </div>

      <div className="min-w-0 flex-1">
        <p className={`text-[11px] font-medium leading-snug ${m.color} group-hover:underline mb-1`}>
          {s.title}
        </p>
        <div className="flex items-center gap-1.5 flex-wrap">
          {s.source_name && <span className="text-[9px] text-neutral-700">{s.source_name}</span>}
          {s.tag && <TagBadge tag={s.tag} />}
          <RelDate iso={s.pub_date} />
          <span className={`text-[9px] font-semibold uppercase tracking-wide opacity-50 ${m.color}`}>{m.label}</span>
        </div>
      </div>

      <span className="text-[11px] text-neutral-800 group-hover:text-neutral-400 shrink-0 self-center transition-colors">↗</span>
    </a>
  )
}

function DailyBriefing({ briefing, activeFilter, onFilter }) {
  const [open,          setOpen]          = useState(false)
  const [showAllStories, setShowAllStories] = useState(false)
  if (!briefing) return null

  const dateLabel = briefing.date
    ? new Date(briefing.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    : 'Today'

  const allStories  = briefing.spotlight || []
  const topStories  = allStories.slice(0, 5)
  const moreStories = allStories.slice(5)
  const visible     = showAllStories ? allStories : topStories
  const tags        = (briefing.trending_tags || []).slice(0, 10)
  const byCat       = briefing.by_category || {}
  const teaser      = allStories[0]

  function handleCatClick(cat) {
    onFilter(activeFilter === cat ? null : cat)
    setTimeout(() => {
      document.getElementById('intel-feed')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 60)
  }

  function toggleOpen() {
    setOpen(o => !o)
    if (open) setShowAllStories(false)
  }

  return (
    <section className="mb-5 border border-neutral-800 rounded-lg overflow-hidden">

      {/* ── Drawer handle ── */}
      <div
        className={`cursor-pointer transition-colors select-none ${open ? 'bg-neutral-900/50' : 'hover:bg-neutral-900/30'}`}
        onClick={toggleOpen}
      >
        {/* Top bar */}
        <div className={`flex items-center gap-3 px-4 py-3 ${open ? 'border-b border-neutral-800/60' : ''}`}>
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
          <span className="text-xs font-semibold text-emerald-400 tracking-wide">Daily Briefing</span>
          <span className="text-[10px] text-neutral-600 hidden sm:inline">{dateLabel}</span>

          {briefing.new_today > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 border border-emerald-900/60 text-emerald-500 rounded">
              +{briefing.new_today} new
            </span>
          )}

          {/* Mini category count pills */}
          <div className="hidden md:flex items-center gap-1 ml-1">
            {CAT_ORDER.filter(c => (byCat[c]?.count || 0) > 0).map(cat => {
              const m = CAT_META[cat]
              return (
                <span key={cat} className={`text-[9px] px-1.5 py-0.5 border ${m.border} ${m.color} rounded`}>
                  {byCat[cat].count}
                </span>
              )
            })}
          </div>

          <div className="ml-auto flex items-center gap-2">
            {activeFilter && (
              <button
                onClick={e => { e.stopPropagation(); onFilter(null) }}
                className="text-[10px] px-1.5 py-0.5 border border-neutral-700 text-neutral-500 hover:text-neutral-300 hover:border-neutral-600 rounded transition-colors"
              >
                ✕ {CAT_META[activeFilter]?.label || activeFilter}
              </button>
            )}
            <span className={`text-[9px] text-neutral-600 transition-transform duration-200 inline-block ${open ? '-rotate-180' : ''}`}>▼</span>
          </div>
        </div>

        {/* Teaser row — visible only when collapsed */}
        {!open && teaser && (
          <div className="flex items-center gap-2.5 px-4 py-2.5 border-t border-neutral-900">
            {faviconUrl(teaser.source_url) && (
              <img
                src={faviconUrl(teaser.source_url)}
                alt=""
                width={14}
                height={14}
                className="rounded opacity-50 shrink-0"
                onError={e => { e.currentTarget.style.display = 'none' }}
              />
            )}
            <span className="text-[11px] text-neutral-500 truncate flex-1 leading-snug">{teaser.title}</span>
            <span className="text-[10px] text-neutral-700 shrink-0 whitespace-nowrap">{allStories.length} stories ›</span>
          </div>
        )}
      </div>

      {/* ── Drawer body ── */}
      {open && (
        <div className="divide-y divide-neutral-900">

          {/* Stories */}
          <div className="px-4 pt-4 pb-3">
            <p className="text-[9px] uppercase tracking-widest text-neutral-600 font-semibold mb-3">
              Top Stories &mdash; {allStories.length} total
            </p>
            <div className="flex flex-col gap-1.5">
              {visible.map((s, i) => <StoryTile key={i} s={s} idx={i} />)}
            </div>

            {moreStories.length > 0 && (
              <button
                onClick={e => { e.stopPropagation(); setShowAllStories(v => !v) }}
                className="mt-2.5 w-full text-[10px] text-neutral-600 hover:text-neutral-300 py-2 border border-neutral-800 hover:border-neutral-700 rounded transition-colors"
              >
                {showAllStories ? '▲ show fewer' : `▼ show ${moreStories.length} more stories`}
              </button>
            )}
          </div>

          {/* Category stat boxes */}
          <div className="p-3">
            <p className="text-[9px] uppercase tracking-widest text-neutral-600 font-semibold mb-2.5 px-1">By Category</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {CAT_ORDER.map(cat => {
                const m      = CAT_META[cat] || { label: cat, color: 'text-neutral-400', border: 'border-neutral-800' }
                const info   = byCat[cat] || { count: 0, top: null }
                const active = activeFilter === cat
                return (
                  <button
                    key={cat}
                    onClick={e => { e.stopPropagation(); handleCatClick(cat) }}
                    className={[
                      'group text-left border rounded px-3 py-2.5 transition-all w-full',
                      active
                        ? `${m.border} bg-neutral-800/60 ring-1 ring-inset ring-neutral-700/50`
                        : 'border-neutral-800 hover:border-neutral-700 hover:bg-neutral-900/60',
                    ].join(' ')}
                  >
                    <div className="flex items-baseline justify-between gap-1 mb-1">
                      <span className={`text-[9px] font-semibold tracking-wide truncate ${m.color}`}>{m.label}</span>
                      <span className={`text-base font-bold tabular-nums shrink-0 transition-colors ${active ? 'text-white' : 'text-neutral-300 group-hover:text-white'}`}>
                        {info.count}
                      </span>
                    </div>
                    {info.top
                      ? <p className={`text-[9px] leading-tight truncate transition-colors ${active ? 'text-neutral-400' : 'text-neutral-700 group-hover:text-neutral-500'}`}>
                          {info.top.title}
                        </p>
                      : <p className="text-[9px] text-neutral-800">no items</p>
                    }
                  </button>
                )
              })}
            </div>
            {activeFilter && (
              <p className="text-[9px] text-neutral-700 mt-2.5 text-center">
                Filtered to <span className={CAT_META[activeFilter]?.color}>{CAT_META[activeFilter]?.label}</span>
                {' — '}
                <button onClick={e => { e.stopPropagation(); onFilter(null) }} className="text-neutral-600 hover:text-neutral-400 underline transition-colors">
                  show all
                </button>
              </p>
            )}
          </div>

          {/* Trending tags */}
          {tags.length > 0 && (
            <div className="px-4 py-3">
              <p className="text-[9px] uppercase tracking-widest text-neutral-700 font-semibold mb-2">Trending Topics</p>
              <div className="flex flex-wrap gap-1.5">
                {tags.map(tag => <TagBadge key={tag} tag={tag} />)}
              </div>
            </div>
          )}

        </div>
      )}
    </section>
  )
}

// ── Filter bar ───────────────────────────────────────────────────────────────────

function FilterBar({ activeFilter, onFilter, days, onDays }) {
  const filters = [{ key: null, label: 'All' }, ...CAT_ORDER.map(k => ({ key: k, label: CAT_META[k]?.label || k }))]

  return (
    <div className="flex items-center gap-2 flex-wrap mb-4">
      <div className="flex gap-1 flex-wrap">
        {filters.map(f => (
          <button
            key={f.key ?? 'all'}
            onClick={() => onFilter(f.key)}
            className={`text-[10px] px-2.5 py-1 border transition-colors ${
              activeFilter === f.key
                ? 'border-emerald-700 text-emerald-400 bg-emerald-950/30'
                : 'border-neutral-800 text-neutral-600 hover:border-neutral-600 hover:text-neutral-400'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
      <select
        value={days}
        onChange={e => onDays(Number(e.target.value))}
        className="ml-auto text-[10px] bg-transparent border border-neutral-800 text-neutral-600 px-2 py-1 cursor-pointer"
        style={{ background: '#080808' }}
      >
        <option value={3}  style={{ background: '#080808' }}>last 3 days</option>
        <option value={7}  style={{ background: '#080808' }}>last 7 days</option>
        <option value={14} style={{ background: '#080808' }}>last 14 days</option>
        <option value={30} style={{ background: '#080808' }}>last 30 days</option>
      </select>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function IntelligencePage() {
  const { session } = useAuth()
  const [data,      setData]      = useState(null)
  const [summary,   setSummary]   = useState(null)
  const [briefing,  setBriefing]  = useState(null)
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState(null)
  const [filter,    setFilter]    = useState(null)   // null = all categories
  const [days,      setDays]      = useState(7)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshMsg, setRefreshMsg] = useState(null)
  const [loginModal, setLoginModal] = useState(false)

  const fetchData = useCallback((d, cat) => {
    setLoading(true)
    setError(null)
    const params = new URLSearchParams({ days: d, limit: 300 })
    if (cat) params.set('category', cat)
    Promise.all([
      fetch(`${API}/api/intelligence?${params}`).then(r => r.json()),
      fetch(`${API}/api/intelligence/summary`).then(r => r.json()),
      fetch(`${API}/api/intelligence/daily-briefing`).then(r => r.ok ? r.json() : null).catch(() => null),
    ])
      .then(([feed, sum, brief]) => { setData(feed); setSummary(sum); setBriefing(brief); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  useEffect(() => { fetchData(days, filter) }, [days, filter])

  function handleRefresh() {
    setRefreshing(true)
    setRefreshMsg(null)
    fetch(`${API}/api/intelligence/refresh`, { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        setRefreshMsg(`Fetched ${d.new ?? 0} new items`)
        setRefreshing(false)
        fetchData(days, filter)
      })
      .catch(e => { setRefreshMsg(`Error: ${e.message}`); setRefreshing(false) })
  }

  // Build displayed categories — filtered or all
  const byCategory = data?.by_category || {}
  const visibleCats = filter ? [filter] : CAT_ORDER

  const totalItems = data?.total ?? 0

  return (
    <>
      <Head>
        <title>Strategic Intelligence — Ready for Robots</title>
      </Head>

      <div className="min-h-screen bg-[#080808] flex flex-col">

        {/* ── Top nav ── */}
        <header className="sticky top-0 z-40 bg-[#080808]/95 backdrop-blur-md border-b border-neutral-800/80 px-4 md:px-6 h-12 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-neutral-700 hover:text-neutral-300 text-xs transition-colors">← dashboard</Link>
            <span className="text-neutral-800">|</span>
            <Link href="/strategy" className="text-neutral-700 hover:text-neutral-300 text-xs transition-colors">strategy</Link>
            <span className="text-neutral-800">|</span>
            <h1 className="text-sm font-bold text-white tracking-tight">Strategic Intelligence</h1>
            {!loading && (
              <span className="label border border-neutral-800 rounded px-1.5 py-0.5 text-neutral-500 hidden sm:inline">
                {totalItems} items
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            {refreshMsg && (
              <span className="text-[10px] text-emerald-500 hidden sm:inline mr-2">{refreshMsg}</span>
            )}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="btn-ghost text-xs border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-200 disabled:opacity-50"
              title="Fetch latest intelligence now"
            >
              {refreshing ? (
                <span className="inline-flex items-center gap-1">
                  <span className="w-2.5 h-2.5 border border-neutral-500 border-t-cyan-400 rounded-full animate-spin" />
                  fetching…
                </span>
              ) : '↻ refresh'}
            </button>
            <button onClick={() => fetchData(days, filter)} className="btn-ghost text-neutral-700" title="Reload">⟳</button>

            {session ? (
              <>
                <Link href="/profile" className="btn-ghost border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-200 text-xs hidden md:inline-flex">My Profile</Link>
                <button
                  onClick={() => supabase.auth.signOut()}
                  className="btn-ghost text-xs border-neutral-800 text-neutral-600 hover:border-red-900 hover:text-red-500">
                  sign out
                </button>
              </>
            ) : (
              <button
                onClick={() => setLoginModal(true)}
                className="btn-ghost text-xs border-emerald-900 text-emerald-500 hover:border-emerald-600 font-medium">
                Log In
              </button>
            )}
          </div>
        </header>

        <main className="flex-1 px-4 md:px-6 py-4 max-w-5xl mx-auto w-full">

          {/* Page intro */}
          <div className="mb-5 flex flex-col gap-1">
            <p className="text-[11px] text-neutral-600">
              Daily-refreshed strategic intelligence — M&A targets, humanoid market, competitor moves, market signals, and industry trends. Scraped fresh every morning at 07:00 UTC.
            </p>
          </div>

          {/* Daily Briefing */}
          {!loading && briefing && <DailyBriefing briefing={briefing} activeFilter={filter} onFilter={setFilter} />}

          {/* Summary counts */}
          {summary && <SummaryBar summary={summary} />}

          {/* Filter bar */}
          <FilterBar
            activeFilter={filter}
            onFilter={setFilter}
            days={days}
            onDays={v => { setDays(v) }}
          />

          {/* Content */}
          {loading && <Spinner />}

          {error && (
            <div className="border border-red-900 rounded p-4 mt-4">
              <span className="label text-red-500">error  </span>
              <span className="text-[11px] text-neutral-400">{error}</span>
              <button onClick={() => fetchData(days, filter)} className="btn-ghost ml-4 text-xs border-neutral-700">retry</button>
            </div>
          )}

          {!loading && !error && (
            <>
              <div id="intel-feed" />
              {totalItems === 0 && (
                <div className="py-16 text-center border border-neutral-800 rounded">
                  <p className="label mb-2">No intelligence items found</p>
                  <p className="text-[11px] text-neutral-700 mb-4">Click ↻ refresh to fetch the latest strategic intelligence now.</p>
                  <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="btn-ghost text-xs border-emerald-900 text-emerald-500 hover:border-emerald-600"
                  >
                    {refreshing ? 'fetching…' : '↻ fetch intelligence now'}
                  </button>
                </div>
              )}

              {totalItems > 0 && visibleCats.map((catKey, idx) => {
                const items = byCategory[catKey] || []
                if (filter && items.length === 0) return null
                return (
                  <CategorySection
                    key={catKey}
                    catKey={catKey}
                    items={items}
                    defaultOpen={idx < 2}
                  />
                )
              })}

              {totalItems > 0 && (
                <div className="mt-8 pt-4 border-t border-neutral-900">
                  <p className="text-[10px] text-neutral-700">
                    {totalItems} items · last {days} days · auto-refreshes daily 07:00 UTC ·{' '}
                    {summary?.last_fetched ? (
                      <>last fetched <RelDate iso={summary.last_fetched} /></>
                    ) : 'not yet fetched'}
                  </p>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {loginModal && <LoginModal onClose={() => setLoginModal(false)} />}
    </>
  )
}
