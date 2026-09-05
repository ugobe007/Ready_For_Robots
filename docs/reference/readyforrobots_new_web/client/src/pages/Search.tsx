import SiteShell from "@/components/SiteShell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LEADS_PUBLIC_FETCH_LIMIT } from "@/lib/leadsApiConstants";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { cn } from "@/lib/utils";
import { ArrowRight, Search as SearchIcon, Sparkles } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "wouter";

type SearchHit = {
  id: number;
  company_name?: string;
  industry?: string;
  overall_score?: number;
  priority_tier?: string;
  matched_signals?: { signal_type?: string; signal_text?: string; strength?: number }[];
};

type SearchResponse = {
  results: SearchHit[];
  total: number;
  query: string | null;
  category: string | null;
  category_label?: string | null;
};

/** Preset theme keys — aligned with the search API category aliases. */
const CATEGORIES: { key: string; label: string }[] = [
  { key: "funding", label: "Automation investment" },
  { key: "ma", label: "M&A" },
  { key: "labor", label: "Labor / staffing" },
  { key: "expansion", label: "Expansion / CapEx" },
  { key: "exec", label: "Executive hire" },
  { key: "warehouse_logistics", label: "Warehouse logistics" },
  { key: "robot_automation", label: "Robot automation" },
  { key: "cleaning_robots", label: "Cleaning robots" },
];

function readUrlParams() {
  const sp = new URLSearchParams(typeof window !== "undefined" ? window.location.search : "");
  return { q: sp.get("q") || "", category: sp.get("category") };
}

function tierBadgeVariant(_tier: string | undefined): "default" | "secondary" | "outline" | "destructive" {
  return "outline";
}

function tierBadgeClass(tier: string | undefined): string {
  if (tier === "HOT") return "border-orange-400 text-orange-950 bg-orange-50 font-semibold";
  if (tier === "WARM") return "border-sky-300 text-sky-900 bg-transparent font-semibold";
  return "border-gray-300 text-gray-800 bg-transparent font-semibold";
}

export default function Search() {
  const [, setLoc] = useLocation();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const run = useCallback(async (q: string, cat: string | null) => {
    const API = getApiBase();
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set("q", q.trim());
      if (cat) params.set("category", cat);
      params.set("limit", LEADS_PUBLIC_FETCH_LIMIT);
      const r = await fetch(`${API}/api/search?${params}`, liveFetchInit());
      if (!r.ok) {
        setError(await r.text().catch(() => r.statusText));
        setData(null);
        return;
      }
      const raw = await r.text();
      if (raw.trimStart().startsWith("<")) {
        setError("API returned HTML instead of JSON.");
        setData(null);
        return;
      }
      setData(JSON.parse(raw) as SearchResponse);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadHot = useCallback(async () => {
    const API = getApiBase();
    setLoading(true);
    setError(null);
    try {
      const base = new URLSearchParams({
        limit: LEADS_PUBLIC_FETCH_LIMIT,
        exclude_junk: "true",
        sort: "score",
      });
      const hotParams = new URLSearchParams(base);
      hotParams.set("tier", "HOT");
      let r = await fetch(`${API}/api/leads?${hotParams}`, liveFetchInit());
      if (!r.ok) {
        setError(await r.text().catch(() => r.statusText));
        setData(null);
        return;
      }
      let leads = JSON.parse(await r.text()) as Record<string, unknown>[];
      let label = "HOT leads";
      if (!leads.length) {
        r = await fetch(`${API}/api/leads?${base}`, liveFetchInit());
        if (r.ok) {
          const raw = await r.text();
          if (!raw.trimStart().startsWith("<")) {
            try {
              leads = JSON.parse(raw) as Record<string, unknown>[];
              label = "Top scored leads";
            } catch {
              /* keep empty */
            }
          }
        }
      }
      const results: SearchHit[] = leads.map((row) => ({
        id: row.id as number,
        company_name: row.company_name as string,
        industry: row.industry as string,
        overall_score: (row.score as { overall_score?: number } | undefined)?.overall_score,
        priority_tier: row.priority_tier as string,
        matched_signals: (row.signals as SearchHit["matched_signals"]) || [],
      }));
      setData({
        results,
        total: results.length,
        query: null,
        category: null,
        category_label: results.length ? `${label} (browse)` : null,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const { q, category: c } = readUrlParams();
    setQuery(q);
    setCategory(c);
    if (q || c) void run(q, c);
    else void loadHot();
  }, [run, loadHot]);

  function syncUrl(qv: string, cat: string | null) {
    const p = new URLSearchParams();
    if (qv.trim()) p.set("q", qv.trim());
    if (cat) p.set("category", cat);
    const qs = p.toString();
    setLoc(qs ? `/search?${qs}` : "/search");
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    syncUrl(query, category);
    void run(query, category);
  }

  return (
    <SiteShell>
      <div className="pb-16">
        <section
          className="relative overflow-hidden border-b border-emerald-100/70"
          style={{
            background: "linear-gradient(135deg, #ffffff 0%, #ecfdf5 42%, #eff6ff 100%)",
          }}
        >
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.35]"
            style={{
              backgroundImage:
                "radial-gradient(circle at 20% 20%, oklch(0.85 0.08 162.5) 0%, transparent 45%), radial-gradient(circle at 80% 10%, oklch(0.9 0.06 250) 0%, transparent 40%)",
            }}
          />
          <div className="container relative py-10 md:py-14">
            <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/80 bg-white/70 px-3 py-1 text-xs font-semibold text-emerald-800 shadow-sm backdrop-blur-sm">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-600" aria-hidden />
                  Intent search
                </div>
                <h1
                  className="mt-4 text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight leading-[1.08]"
                  style={{ fontFamily: "'Bricolage Grotesque', sans-serif", letterSpacing: "-0.03em" }}
                >
                  Find buyers by{" "}
                  <span style={{ color: "oklch(0.527 0.154 162.5)" }}>signal</span>, not guesswork
                </h1>
                <p className="mt-4 text-base md:text-lg text-gray-600 leading-relaxed max-w-xl">
                  Search live signal text and company names. Try a category shortcut, or leave the box empty to browse
                  what&apos;s trending now.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 lg:justify-end">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-transparent px-4 py-2.5 text-sm font-semibold text-gray-900 hover:border-gray-400 transition-colors"
                >
                  Dashboard
                  <ArrowRight className="h-4 w-4 opacity-60" aria-hidden />
                </Link>
                <Link
                  href="/pipeline"
                  className="inline-flex items-center gap-1.5 rounded-md border bg-transparent px-4 py-2.5 text-sm font-semibold hover:opacity-90 transition-opacity"
                  style={{ borderColor: "oklch(0.527 0.154 162.5)", color: "oklch(0.527 0.154 162.5)" }}
                >
                  Full pipeline
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </Link>
              </div>
            </div>
          </div>
        </section>

        <div className="container -mt-6 md:-mt-8 relative z-[1] space-y-8 pt-2 md:pt-0">
          <Card className="border-emerald-100/90 shadow-xl shadow-emerald-900/[0.06] overflow-hidden rounded-2xl bg-white/95 backdrop-blur-sm">
            <CardHeader className="pb-2 border-b border-gray-100/80 bg-gradient-to-r from-white to-emerald-50/30">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-md border border-emerald-600/80 text-emerald-800 bg-transparent">
                  <SearchIcon className="h-4 w-4" aria-hidden />
                </div>
                <div>
                  <CardTitle className="text-lg">Search & filters</CardTitle>
                  <CardDescription className="text-sm">Categories jump straight to common buying themes.</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-5 p-5 md:p-6">
              <form onSubmit={onSubmit} className="flex flex-col md:flex-row gap-3">
                <Input
                  placeholder="Company, keyword, signal snippet…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="md:flex-1 h-11 text-base border-gray-200 shadow-inner bg-white"
                />
                <Button
                  type="submit"
                  variant="outline"
                  className="shrink-0 h-11 px-6 font-semibold border-emerald-600 text-emerald-800 bg-transparent hover:bg-transparent hover:text-emerald-950"
                >
                  Run search
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="h-11 border-gray-200"
                  onClick={() => {
                    setQuery("");
                    setCategory(null);
                    setLoc("/search");
                    void loadHot();
                  }}
                >
                  Clear
                </Button>
              </form>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Quick themes</p>
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map((c) => (
                    <button
                      key={c.key}
                      type="button"
                      onClick={() => {
                        const next = category === c.key ? null : c.key;
                        setCategory(next);
                        syncUrl(query, next);
                        void run(query, next);
                      }}
                      className={cn(
                        "rounded-md border px-3.5 py-1.5 text-sm font-medium transition-all bg-transparent",
                        category === c.key
                          ? "border-emerald-600 text-emerald-900"
                          : "border-gray-300 text-gray-700 hover:border-gray-400 hover:text-gray-900"
                      )}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {error ? (
            <Card className="border-red-200 bg-red-50/80 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-red-900 text-base">Search failed</CardTitle>
                <CardDescription className="text-red-900/90 whitespace-pre-wrap">{error}</CardDescription>
              </CardHeader>
            </Card>
          ) : null}

          <Card className="border-gray-200/80 shadow-md overflow-hidden rounded-2xl">
            <CardHeader className="border-b border-gray-100 bg-gray-50/80">
              <CardTitle className="text-lg">Results</CardTitle>
              <CardDescription className="text-sm">
                {loading
                  ? "Scanning…"
                  : data
                    ? `${data.total} ${data.total === 1 ? "match" : "matches"}${data.category_label ? ` · ${data.category_label}` : ""}`
                    : "—"}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-10 flex flex-col items-center justify-center gap-3 text-gray-500">
                  <div className="h-9 w-9 rounded-full border-2 border-emerald-200 border-t-emerald-600 animate-spin" />
                  <p className="text-sm font-medium">Pulling the latest rows…</p>
                </div>
              ) : !data?.results?.length ? (
                <div className="p-10 text-center">
                  <p className="text-gray-700 font-medium">No matches yet</p>
                  <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">
                    Try another keyword, pick a theme above, or clear the form to browse the live list.
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-gray-100">
                      <TableHead className="font-semibold">Company</TableHead>
                      <TableHead className="w-[100px] font-semibold">Tier</TableHead>
                      <TableHead className="w-[88px] text-right font-semibold">Score</TableHead>
                      <TableHead className="font-semibold">Industry</TableHead>
                      <TableHead className="font-semibold min-w-[200px]">Signal / match</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.results.map((row, idx) => (
                      <TableRow
                        key={row.id}
                        className={cn(
                          "border-gray-100 transition-colors",
                          idx % 2 === 1 ? "bg-gray-50/40" : "bg-white",
                          "hover:bg-emerald-50/30"
                        )}
                      >
                        <TableCell className="font-semibold text-gray-900">{row.company_name || "—"}</TableCell>
                        <TableCell>
                          <Badge variant={tierBadgeVariant(row.priority_tier)} className={tierBadgeClass(row.priority_tier)}>
                            {row.priority_tier || "—"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm tabular-nums text-emerald-900/90">
                          {row.overall_score != null ? Math.round(row.overall_score) : "—"}
                        </TableCell>
                        <TableCell className="text-gray-600 text-sm max-w-[220px]">{row.industry || "—"}</TableCell>
                        <TableCell className="text-xs text-gray-600 leading-snug max-w-lg">
                          {(row.matched_signals && row.matched_signals[0]?.signal_text) || "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </SiteShell>
  );
}
