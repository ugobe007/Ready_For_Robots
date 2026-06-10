/**
 * Client mirror of app/services/industry_search_lexicon.py
 * Source of truth: app/data/industry_sector_ontology.json
 */
import ontology from "@ontology";

type SubOntology = {
  label?: string;
  subject?: string;
  modifiers?: string[];
  terms?: string[];
};
type Sector = {
  id: string;
  label?: string;
  canonical_industries?: string[];
  root_aliases?: string[];
  sub_ontologies?: Record<string, SubOntology>;
};

type SubjectRef = {
  sectorId: string;
  subId: string;
  subject: string;
  modifiers: string[];
  terms: string[];
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
  "out patient": "outpatient",
  er: "emergency room",
  ed: "emergency room",
  datacenter: "data center",
  qsr: "quick serve",
  carwash: "car wash",
  truckstop: "truck stop",
};

const INFERENCE_ANCHORS: string[] = (
  (ontology as { inference_anchors?: string[] }).inference_anchors ?? [
    "automation", "automated", "robot", "robotics", "autonomous", "amr", "agv", "cobot",
    "deployment", "deploys", "deployed", "pilot", "pilots",
  ]
).map((a) => normalizeTerm(a));

type TermRef = { sectorId: string; subId: string; raw: string };

function normalizeTerm(text: string): string {
  return (text || "").trim().toLowerCase().replace(/\s+/g, " ");
}

function buildSubjectRefs(): SubjectRef[] {
  const refs: SubjectRef[] = [];
  for (const sector of (ontology.sectors ?? []) as Sector[]) {
    for (const [subId, sub] of Object.entries(sector.sub_ontologies ?? {})) {
      const subject = normalizeTerm(sub.subject ?? "");
      if (!subject) continue;
      refs.push({
        sectorId: sector.id,
        subId,
        subject,
        modifiers: (sub.modifiers ?? []).map((m) => normalizeTerm(m)).filter(Boolean),
        terms: (sub.terms ?? []).map((t) => normalizeTerm(t)).filter(Boolean),
      });
    }
  }
  return refs.sort((a, b) => b.subject.length - a.subject.length);
}

const SUBJECT_REFS = buildSubjectRefs();

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
      if (sub.subject) add(sub.subject, sector.id, subId);
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

function stripInferenceSuffix(query: string): string {
  let q = normalizeTerm(query);
  for (const anchor of INFERENCE_ANCHORS) {
    const suffix = ` ${anchor}`;
    if (q.endsWith(suffix) && q.length > suffix.length) {
      q = q.slice(0, -suffix.length).trim();
    }
  }
  return q;
}

function resolveSubjectRefs(query: string): SubjectRef[] {
  const q = stripInferenceSuffix(resolveQuery(query));
  if (!q) return [];
  return SUBJECT_REFS.filter(
    (ref) => termMatchesQuery(ref.subject, q) || termMatchesQuery(q, ref.subject),
  );
}

function subjectInText(subject: string, hay: string): boolean {
  if (!subject || !hay) return false;
  if (subject.includes(" ")) return hay.includes(subject);
  if (subject.length <= 4) {
    return new RegExp(`\\b${subject.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`).test(hay);
  }
  return hay.includes(subject);
}

function hasInferenceAnchor(hay: string): boolean {
  return INFERENCE_ANCHORS.some((anchor) => hay.includes(anchor));
}

function textMatchesSubjectInference(text: string, query: string): boolean {
  const hay = normalizeTerm(text);
  if (!hay || !hasInferenceAnchor(hay)) return false;
  const refs = resolveSubjectRefs(query);
  if (!refs.length) return false;
  return refs.some((ref) => {
    if (!subjectInText(ref.subject, hay)) return false;
    if (ref.modifiers.some((mod) => hay.includes(mod))) return true;
    if (ref.terms.some((term) => hay.includes(term))) return true;
    return subjectInText(ref.subject, hay);
  });
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

  for (const ref of resolveSubjectRefs(q)) {
    const subs = matchedSectorSubs.get(ref.sectorId) ?? new Set<string>();
    subs.add(ref.subId);
    matchedSectorSubs.set(ref.sectorId, subs);
    directTerms.push(ref.subject, ...ref.modifiers, ...ref.terms);
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
      expansionTerms.push(sub.label ?? "", ...(sub.subject ? [sub.subject] : []), ...(sub.modifiers ?? []), ...(sub.terms ?? []));
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
  if (expandSearchTerms(q).some((term) => hay.includes(term))) return true;
  return textMatchesSubjectInference(hay, q);
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
