/**
 * Ready for Robots — Saved Profile Page
 * All data stored in localStorage under key "rfr_saved".
 * No backend auth or payment needed.
 */
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

const TIER_META = {
  HOT:  { text: 'text-red-400',    border: 'border-red-800'   },
  WARM: { text: 'text-yellow-400', border: 'border-yellow-800'},
  COLD: { text: 'text-cyan-400',   border: 'border-cyan-900'  },
};

function TierBadge({ tier }) {
  const m = TIER_META[tier] || TIER_META.COLD;
  return (
    <span className={`inline-flex items-center border ${m.border} ${m.text} rounded px-1.5 py-0.5 text-[10px] font-semibold leading-none`}>
      {tier}
    </span>
  );
}

function ScoreNum({ value }) {
  return (
    <span className="inline-flex items-center border border-emerald-700 text-emerald-400 rounded px-1.5 leading-none tabular-nums font-mono font-semibold text-[10px]"
      style={{ paddingTop: '0.2rem', paddingBottom: '0.2rem' }}>
      {Math.round(value ?? 0)}
    </span>
  );
}

function formatDate(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }); }
  catch { return '—'; }
}

// ── empty state ─────────────────────────────────────────────────────────────
function EmptyState({ text }) {
  return (
    <div className="border border-neutral-800 rounded-lg px-6 py-10 text-center">
      <p className="text-sm text-neutral-700">{text}</p>
    </div>
  );
}

// ── Company card ─────────────────────────────────────────────────────────────
function CompanyCard({ company, onRemove, onAnalyze }) {
  const tm = TIER_META[company.tier] || TIER_META.COLD;
  return (
    <div className={`border ${tm.border} rounded-lg p-4 flex flex-col gap-3 hover:border-opacity-80 transition-all`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-neutral-100 truncate">{company.name}</p>
          <p className="text-xs text-neutral-500 mt-0.5">{company.industry || '—'}</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <TierBadge tier={company.tier} />
          {company.score != null && <ScoreNum value={company.score} />}
        </div>
      </div>
      <div className="flex items-center gap-1.5 text-[10px] text-neutral-600">
        <span>saved {formatDate(company.saved_at)}</span>
        {company.website && (
          <>
            <span>·</span>
            <a href={company.website} target="_blank" rel="noreferrer"
              className="text-cyan-800 hover:text-cyan-500 truncate max-w-[9rem]">
              {company.website.replace(/^https?:\/\//, '')}
            </a>
          </>
        )}
      </div>
      <div className="flex gap-2">
        <button
          onClick={onAnalyze}
          className="flex-1 text-xs border border-emerald-900 text-emerald-400 rounded px-2 py-1.5 hover:border-emerald-700 transition-colors">
          ▲ AI Analysis
        </button>
        <button
          onClick={onRemove}
          className="text-xs border border-neutral-800 text-neutral-600 rounded px-2 py-1.5 hover:border-red-900 hover:text-red-500 transition-colors">
          remove
        </button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ProfilePage() {
  const [store, setStore]           = useState({ companies: [], lists: [] });
  const [newListName, setNewListName] = useState('');
  const [activeList, setActiveList] = useState(null);   // list id being viewed
  const [addToListId, setAddToListId] = useState(null); // company id being added to list
  const [analyzeId, setAnalyzeId]   = useState(null);   // company id → open modal
  const [mounted, setMounted]       = useState(false);

  // load from localStorage (must run client-side only)
  const loadStore = useCallback(() => {
    try {
      const s = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[],"lists":[]}');
      if (!s.companies) s.companies = [];
      if (!s.lists) s.lists = [];
      setStore(s);
    } catch {
      setStore({ companies: [], lists: [] });
    }
  }, []);

  useEffect(() => { setMounted(true); loadStore(); }, [loadStore]);

  function saveStore(updated) {
    localStorage.setItem('rfr_saved', JSON.stringify(updated));
    setStore({ ...updated });
  }

  function removeCompany(id) {
    const updated = {
      ...store,
      companies: store.companies.filter(c => c.id !== id),
      // also remove from all lists
      lists: store.lists.map(l => ({ ...l, company_ids: l.company_ids.filter(cid => cid !== id) })),
    };
    saveStore(updated);
  }

  function createList() {
    const name = newListName.trim();
    if (!name) return;
    const updated = {
      ...store,
      lists: [...store.lists, {
        id:          Date.now().toString(),
        name,
        created_at:  new Date().toISOString(),
        company_ids: [],
      }],
    };
    saveStore(updated);
    setNewListName('');
  }

  function deleteList(listId) {
    saveStore({ ...store, lists: store.lists.filter(l => l.id !== listId) });
    if (activeList === listId) setActiveList(null);
  }

  function addToList(listId, companyId) {
    saveStore({
      ...store,
      lists: store.lists.map(l =>
        l.id === listId && !l.company_ids.includes(companyId)
          ? { ...l, company_ids: [...l.company_ids, companyId] }
          : l
      ),
    });
    setAddToListId(null);
  }

  function removeFromList(listId, companyId) {
    saveStore({
      ...store,
      lists: store.lists.map(l =>
        l.id === listId ? { ...l, company_ids: l.company_ids.filter(id => id !== companyId) } : l
      ),
    });
  }

  const currentList = store.lists.find(l => l.id === activeList);
  const listCompanies = currentList
    ? store.companies.filter(c => currentList.company_ids.includes(c.id))
    : [];

  // Inline modal re-use: open dashboard with analysis open (link to index with param)
  function handleAnalyze(company) {
    // Redirect to dashboard with the company pre-selected via URL param
    window.location.href = `/?analyze=${company.id}`;
  }

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-[#080808] px-4 py-6 md:px-8 md:py-8 max-w-[1400px] mx-auto">

      {/* header */}
      <header className="mb-10 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold tracking-tight text-white">Saved Profile</h1>
            <span className="inline-flex items-center border border-neutral-700 rounded px-2 py-0.5 text-[10px] text-neutral-300 font-semibold tracking-widest uppercase">
              Richtech Robotics
            </span>
          </div>
          <p className="text-sm text-neutral-400">
            Your saved companies and target lists &mdash; {store.companies.length} saved
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/" className="inline-flex items-center border border-neutral-700 rounded px-3 py-1.5 text-xs text-neutral-400 hover:border-neutral-500 hover:text-neutral-200 transition-colors">
            ← dashboard
          </Link>
          <Link href="/admin" className="inline-flex items-center border border-emerald-900 rounded px-3 py-1.5 text-xs text-emerald-400 hover:border-emerald-700 transition-colors">
            ⚙ admin
          </Link>
        </div>
      </header>

      {/* ── Saved Companies ─────────────────────────────────────────── */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-neutral-100">Saved Companies</h2>
            <p className="text-xs text-neutral-600 mt-0.5">Companies flagged for follow-up on the dashboard</p>
          </div>
          {store.companies.length > 0 && (
            <span className="text-xs text-neutral-600">{store.companies.length} total</span>
          )}
        </div>

        {store.companies.length === 0 ? (
          <EmptyState text="No companies saved yet — use the ☆ Save button on any lead in the dashboard, or click AI Analysis and hit Save in the modal." />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {store.companies.map(company => (
              <div key={company.id} className="relative">
                <CompanyCard
                  company={company}
                  onRemove={() => removeCompany(company.id)}
                  onAnalyze={() => handleAnalyze(company)}
                />
                {/* Add to list dropdown */}
                <div className="mt-1">
                  {store.lists.length > 0 && (
                    <div className="relative">
                      <button
                        onClick={() => setAddToListId(addToListId === company.id ? null : company.id)}
                        className="w-full text-[10px] border border-neutral-800 text-neutral-600 rounded px-2 py-1 hover:border-neutral-700 transition-colors">
                        + add to list
                      </button>
                      {addToListId === company.id && (
                        <div className="absolute z-10 top-full left-0 mt-1 w-full bg-[#111] border border-neutral-700 rounded shadow-xl">
                          {store.lists.map(l => {
                            const alreadyIn = l.company_ids.includes(company.id);
                            return (
                              <button key={l.id}
                                onClick={() => alreadyIn ? null : addToList(l.id, company.id)}
                                className={`block w-full text-left px-3 py-2 text-xs ${
                                  alreadyIn ? 'text-neutral-700 cursor-default' : 'text-neutral-300 hover:bg-neutral-800'
                                } transition-colors`}>
                                {l.name} {alreadyIn ? '✓' : ''}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="border-t border-neutral-800 mb-10" />

      {/* ── Saved Lists ──────────────────────────────────────────────── */}
      <section>
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-base font-semibold text-neutral-100">Target Lists</h2>
            <p className="text-xs text-neutral-600 mt-0.5">Group companies into outreach lists for each campaign</p>
          </div>
        </div>

        {/* create new list */}
        <div className="flex gap-2 mb-6 max-w-sm">
          <input
            type="text"
            value={newListName}
            onChange={e => setNewListName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && createList()}
            placeholder="New list name (e.g. Q3 Hotel Targets)"
            className="flex-1 bg-transparent border border-neutral-700 rounded px-3 py-1.5 text-xs text-neutral-200 placeholder-neutral-700 focus:outline-none focus:border-neutral-500 transition-colors"
          />
          <button
            onClick={createList}
            disabled={!newListName.trim()}
            className="border border-emerald-900 text-emerald-400 hover:border-emerald-700 rounded px-3 py-1.5 text-xs disabled:opacity-30 transition-colors">
            + create
          </button>
        </div>

        {store.lists.length === 0 ? (
          <EmptyState text="No lists yet — create one above to organize your target companies into outreach campaigns." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {store.lists.map(l => (
              <div key={l.id} className="border border-neutral-800 rounded-lg">
                {/* list header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800">
                  <div>
                    <p className="text-sm font-medium text-neutral-200">{l.name}</p>
                    <p className="text-[10px] text-neutral-600 mt-0.5">
                      {l.company_ids.length} companies &middot; created {formatDate(l.created_at)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setActiveList(activeList === l.id ? null : l.id)}
                      className="text-[10px] border border-neutral-700 text-neutral-500 rounded px-2 py-1 hover:border-neutral-500 transition-colors">
                      {activeList === l.id ? 'collapse' : 'view'}
                    </button>
                    <button
                      onClick={() => deleteList(l.id)}
                      className="text-[10px] border border-neutral-800 text-neutral-700 rounded px-2 py-1 hover:border-red-900 hover:text-red-500 transition-colors">
                      delete
                    </button>
                  </div>
                </div>

                {/* list members (when expanded) */}
                {activeList === l.id && (
                  <div className="p-3">
                    {listCompanies.length === 0 ? (
                      <p className="text-xs text-neutral-700 px-1 py-2">
                        No companies in this list yet. Use &ldquo;+ add to list&rdquo; on any saved company above.
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {listCompanies.map(c => (
                          <div key={c.id} className="flex items-center justify-between border border-neutral-800 rounded px-3 py-2">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <TierBadge tier={c.tier} />
                              <span className="text-xs text-neutral-300 truncate">{c.name}</span>
                              {c.score != null && <ScoreNum value={c.score} />}
                            </div>
                            <div className="flex gap-2 shrink-0 ml-2">
                              <button
                                onClick={() => handleAnalyze(c)}
                                className="text-[10px] border border-emerald-900 text-emerald-500 rounded px-1.5 py-0.5 hover:border-emerald-700 transition-colors">
                                ▲
                              </button>
                              <button
                                onClick={() => removeFromList(l.id, c.id)}
                                className="text-[10px] border border-neutral-800 text-neutral-600 rounded px-1.5 py-0.5 hover:border-red-900 hover:text-red-500 transition-colors">
                                ✕
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* print/export (future) */}
                    <div className="mt-3 pt-3 border-t border-neutral-800 flex gap-2">
                      <button
                        onClick={() => {
                          const names = listCompanies.map(c => `${c.name} (${c.tier}, ${c.industry}, score: ${c.score ?? '—'})`).join('\n');
                          const blob = new Blob([`${l.name}\n${'─'.repeat(l.name.length)}\n\n${names}\n`], { type: 'text/plain' });
                          const a = document.createElement('a');
                          a.href = URL.createObjectURL(blob);
                          a.download = `${l.name.replace(/\s+/g, '_')}.txt`;
                          a.click();
                        }}
                        className="text-[10px] border border-neutral-800 text-neutral-600 rounded px-2 py-1 hover:border-neutral-600 hover:text-neutral-400 transition-colors">
                        ↓ export list
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Export all saved ─────────────────────────────────────────── */}
      {store.companies.length > 0 && (
        <div className="mt-10 pt-6 border-t border-neutral-800 flex gap-3">
          <button
            onClick={() => {
              const rows = store.companies.map(c =>
                [c.name, c.industry, c.tier, c.score ?? '', c.website ?? '', formatDate(c.saved_at)].join('\t')
              );
              const tsv = ['Company\tIndustry\tTier\tScore\tWebsite\tSaved', ...rows].join('\n');
              const blob = new Blob([tsv], { type: 'text/plain' });
              const a = document.createElement('a');
              a.href = URL.createObjectURL(blob);
              a.download = 'richtech_saved_companies.tsv';
              a.click();
            }}
            className="text-xs border border-neutral-700 text-neutral-500 rounded px-3 py-1.5 hover:border-neutral-500 hover:text-neutral-300 transition-colors">
            ↓ export all saved (TSV)
          </button>
          <button
            onClick={() => {
              if (!confirm('Clear ALL saved companies and lists? This cannot be undone.')) return;
              saveStore({ companies: [], lists: [] });
            }}
            className="text-xs border border-neutral-800 text-neutral-700 rounded px-3 py-1.5 hover:border-red-900 hover:text-red-500 transition-colors">
            clear all
          </button>
        </div>
      )}

      <footer className="mt-16 text-center text-[10px] text-neutral-700">
        ready for robots &middot; richtech robotics &middot; profile data stored locally
      </footer>
    </div>
  );
}
