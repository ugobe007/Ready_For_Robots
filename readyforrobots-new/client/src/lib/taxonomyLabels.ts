/**
 * Plain words for taxonomy slugs. Keys come from tests/fixtures/taxonomy.v1.json.
 * A slug with no label is omitted. Already-plain text (a city, a sentence) is kept.
 */
import taxonomy from "../../../../tests/fixtures/taxonomy.v1.json";

type TaxonomyDoc = {
  functions?: Record<string, string>;
  industries?: Record<string, string>;
  form?: Record<string, string>;
  primary_class?: Record<string, string>;
};

const TOKEN: Record<string, string> = {
  beverage: "drink",
  "3pl": "3PL",
  qsr: "quick-service",
  k12: "K-12",
};

/** Catalog ids that name a taxonomy slug. food_prep is the old class for food_beverage_prep. */
const ALIAS: Record<string, string> = {
  food_prep: "food_beverage_prep",
};

/** Humanized slug would be an acronym or a doubled word. Phrase comes from the taxonomy meaning. */
const PREFER: Record<string, string> = {
  amr_logistics: "Warehouse and logistics",
  amr_mobile_robot: "Mobile robot",
  robotic_arm_cobot: "Robotic arm",
  factory_industrial: "Factory",
  food_robotics: "Food and drink",
};

function humanize(slug: string): string {
  if (PREFER[slug]) return PREFER[slug];
  const words = slug
    .split("_")
    .filter(Boolean)
    .map((word) => TOKEN[word] || word);
  const phrase = words.join(" ").replace(/\bfood drink\b/g, "food and drink");
  if (!phrase) return "";
  return phrase.charAt(0).toUpperCase() + phrase.slice(1);
}

export function taxonomySlugs(doc: TaxonomyDoc = taxonomy): string[] {
  const slugs: string[] = [];
  for (const group of [doc.functions, doc.industries, doc.form, doc.primary_class]) {
    for (const key of Object.keys(group || {})) {
      if (!key.startsWith("_")) slugs.push(key);
    }
  }
  return slugs;
}

export function buildTaxonomyLabels(doc: TaxonomyDoc = taxonomy): Record<string, string> {
  const labels: Record<string, string> = {};
  for (const slug of taxonomySlugs(doc)) {
    const label = humanize(slug);
    if (label) labels[slug] = label;
  }
  for (const [alias, slug] of Object.entries(ALIAS)) {
    if (labels[slug]) labels[alias] = labels[slug];
  }
  return labels;
}

export const TAXONOMY_LABELS = buildTaxonomyLabels();

const SLUG = /^[a-z0-9]+(?:_[a-z0-9]+)*$/;

/** Label for a taxonomy slug. Empty when the slug has no label. Plain sentences pass through. */
export function taxonomyLabel(value: string | null | undefined): string {
  const raw = (value || "").trim();
  if (!raw) return "";
  const key = raw.toLowerCase().replace(/ /g, "_");
  if (TAXONOMY_LABELS[key]) return TAXONOMY_LABELS[key];
  if (SLUG.test(raw)) return "";
  return raw;
}

export type LabeledSearch = {
  capabilities?: { key?: string; label?: string }[];
  jobs?: { industry?: string | null; locality?: string | null; title?: string | null; company_name?: string | null }[];
  products?: {
    name?: string;
    display_class?: string | null;
    form?: string | null;
    description?: string | null;
  }[];
};

/** Every taxonomy-derived string the results page and the picker show. */
export function labeledSearchText(payload: LabeledSearch): string {
  const lines: string[] = [];
  const cap = (payload.capabilities || []).find((item) => (item.key || item.label || "").trim());
  const work = taxonomyLabel(cap?.key || cap?.label);
  if (work) lines.push(work);
  for (const job of payload.jobs || []) {
    const industry = taxonomyLabel(job.industry);
    if (industry) lines.push(industry);
    if (job.locality) lines.push(job.locality);
    if (job.title) lines.push(job.title);
    if (job.company_name) lines.push(job.company_name);
  }
  for (const product of payload.products || []) {
    if (product.name) lines.push(product.name);
    const klass = taxonomyLabel(product.form || product.display_class);
    if (klass) lines.push(klass);
    const about = taxonomyLabel(product.description);
    if (about) lines.push(about);
  }
  return lines.join("\n");
}
