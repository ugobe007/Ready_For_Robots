/**
 * Client mirror of app/services/industry_search_lexicon.py
 * Source of truth: app/data/industry_sector_ontology.json
 */
import ontology from "@ontology";

type SubOntology = { label?: string; terms?: string[] };
type Sector = {
  id: string;
  label?: string;
  canonical_industries?: string[];
  root_aliases?: string[];
  sub_ontologies?: Record<string, SubOntology>;
};

const QUERY_ALIASES: Record<string, string> = {
  manufacting: "manufacturing",
  "package handing": "package handling",
  "intra logistic": "intra logistics",
  "micro logistic": "micro logistics",
  "light logistic": "light logistics",
  "warehouse logistic": "warehouse logistics",
  janitorial: "janitorial automation",
  housekeeping: "housekeeping automation",
  hotel: "hotel automation",
};

type TermRef = { sectorId: string; subId: string; raw: string };

function normalizeTerm(text: string): string {
  return (text || "").trim().toLowerCase().replace(/\s+/g, " ");
}

function buildTermIndex(): Map<string, TermRef[]> {
  const index = new Map<string, TermRef[]>();
  const add = (term: string, sectorId: string, subId: string) => {
    const key = normalizeTerm(term);
    if (!key) return;
    const row = index.get(key) ?? [];
    row.push({ sectorId, subId, raw: term });
    index.set(key, row);
  };

  for (const sector of (ontology.sectors ?? []) as Sector[]) {
    add(sector.label ?? "", sector.id, "__sector__");
    for (const alias of sector.root_aliases ?? []) add(alias, sector.id, "__root__");
    for (const canonical of sector.canonical_industries ?? []) add(canonical, sector.id, "__canonical__");
    for (const [subId, sub] of Object.entries(sector.sub_ontologies ?? {})) {
      add(sub.label ?? "", sector.id, subId);
      for (const term of sub.terms ?? []) add(term, sector.id, subId);
    }
  }
  return index;
}

const TERM_INDEX = buildTermIndex();

function termMatchesQuery(term: string, query: string): boolean {
  if (!term || !query) return false;
  if (term === query) return true;
  if (query.length >= 4 && term.includes(query)) return true;
  if (term.length >= 4 && query.includes(term)) return true;
  return false;
}

function dedupe(items: string[]): string[] {
  const seen = new Set<string>();
  return items.filter((raw) => {
    const t = normalizeTerm(raw);
    if (!t || seen.has(t)) return false;
    seen.add(t);
    return true;
  });
}

function resolveQuery(query: string): string {
  const q = normalizeTerm(query);
  return QUERY_ALIASES[q] ?? q;
}

interface OntologyMatch {
  canonicalIndustries: string[];
  expansionTerms: string[];
}

function matchOntologyQuery(query: string): OntologyMatch {
  const q = resolveQuery(query);
  if (!q) return { canonicalIndustries: [], expansionTerms: [] };

  const matchedSectorSubs = new Map<string, Set<string>>();
  const sectorFullMatch = new Set<string>();
  const directTerms = [q];

  for (const [termKey, refs] of TERM_INDEX.entries()) {
    if (!termMatchesQuery(termKey, q)) continue;
    directTerms.push(termKey);
    for (const { sectorId, subId, raw } of refs) {
      directTerms.push(raw);
      if (subId === "__root__" || subId === "__sector__" || subId === "__canonical__") {
        sectorFullMatch.add(sectorId);
      } else {
        const subs = matchedSectorSubs.get(sectorId) ?? new Set<string>();
        subs.add(subId);
        matchedSectorSubs.set(sectorId, subs);
      }
    }
  }

  for (const sectorId of sectorFullMatch) {
    if (!matchedSectorSubs.has(sectorId)) matchedSectorSubs.set(sectorId, new Set());
  }

  if (matchedSectorSubs.size === 0) {
    return { canonicalIndustries: [], expansionTerms: dedupe(directTerms) };
  }

  const canonicalIndustries: string[] = [];
  const expansionTerms: string[] = [...directTerms];

  for (const sector of (ontology.sectors ?? []) as Sector[]) {
    if (!matchedSectorSubs.has(sector.id)) continue;
    canonicalIndustries.push(...(sector.canonical_industries ?? []));
    expansionTerms.push(sector.label ?? "", ...(sector.root_aliases ?? []));
    for (const sub of Object.values(sector.sub_ontologies ?? {})) {
      expansionTerms.push(sub.label ?? "", ...(sub.terms ?? []));
    }
  }

  return {
    canonicalIndustries: dedupe(canonicalIndustries),
    expansionTerms: dedupe(expansionTerms),
  };
}

export function normalizeSearchQuery(query: string): string {
  return normalizeTerm(query);
}

export function expandSearchTerms(query: string): string[] {
  const q = resolveQuery(query);
  if (!q) return [];
  const match = matchOntologyQuery(q);
  const terms = [q];
  if (normalizeTerm(query) !== q) terms.push(normalizeTerm(query));
  terms.push(...match.expansionTerms, ...match.canonicalIndustries.map((ind) => ind.toLowerCase()));
  return dedupe(terms);
}

export function textMatchesIndustrySearch(text: string, query: string): boolean {
  const q = resolveQuery(query);
  if (!q) return true;
  const hay = (text || "").toLowerCase();
  if (hay.includes(q)) return true;
  return expandSearchTerms(q).some((term) => hay.includes(term));
}

export function dealMatchesIndustrySearch(
  parts: { industry?: string; company?: string; signal?: string; location?: string },
  query: string,
): boolean {
  const q = resolveQuery(query);
  if (!q || q === "all") return true;
  const hay = [parts.industry, parts.company, parts.signal, parts.location]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return textMatchesIndustrySearch(hay, q);
}
