/**
 * Example cards name the kind of organization. Keep these phrases aligned with
 * example_employer_label in app/services/job_card_provenance.py.
 */
const EXAMPLE_EMPLOYER_RULES: Array<[RegExp, string]> = [
  [/memory care|assisted living|senior living|skilled nursing/i, "Senior living operator"],
  [/surgery/i, "Surgery center"],
  [/hospital|healthcare|\bhealth\b/i, "Hospital system"],
  [/\bmall\b/i, "Regional mall operator"],
  [/restroom|facilities|facility services/i, "Facilities services company"],
  [/airport|aviation|avionics|terminal floor/i, "Airport operator"],
  [/university|college|\bcampus\b/i, "University"],
  [/cafe|coffee|espresso/i, "Cafe operator"],
  [/hotel|marriott|hilton|hyatt|room-service|room service|guest rooms?/i, "Hotel operator"],
  [/\bbar\b|cocktail|nightclub/i, "Bar operator"],
  [/restaurant|dining|grill|quick-service|fast-casual|\bkitchen\b/i, "Restaurant operator"],
  [/pharma|pharmacy/i, "Pharmacy distribution operator"],
  [/grocery/i, "Grocery operator"],
  [/warehouse|\bdc\b|fulfillment|distribution|\b3pl\b|logistics|parcel|apparel|auto parts/i, "Warehouse or logistics operator"],
  [/factory|manufactur|machine shop|\bplant\b|industrial/i, "Manufacturer"],
  [/farm|agricultur|orchard|grower|\bgrain\b/i, "Farm operator"],
  [/mining/i, "Mining operator"],
  [/construction|builder|home improvement|home center/i, "Construction company"],
  [/marine|\bport\b|drydock/i, "Port or marine operator"],
  [/aerospace|\bnasa\b/i, "Aerospace operator"],
  [/utilities|utility/i, "Utility operator"],
  [/retail/i, "Retail operator"],
  [/\bcnc\b|med device/i, "Manufacturer"],
  [/pallet|cases|returns/i, "Warehouse or logistics operator"],
];

/** Parts are tried in order, so pass organization fields before work text. */
export function exampleEmployerLabel(...parts: Array<string | null | undefined>): string {
  for (const part of parts) {
    if (!part) continue;
    for (const [pattern, label] of EXAMPLE_EMPLOYER_RULES) {
      if (pattern.test(part)) return label;
    }
  }
  return "Example employer";
}

/** "Harris Health — LBJ Hospital · Houston" -> "Hospital system · Houston". */
export function exampleTapeIndustry(industry: string, title = "", path = ""): string {
  const parts = industry.split("·").map(part => part.trim()).filter(Boolean);
  const place = parts.slice(1).join(" · ");
  const label = exampleEmployerLabel(parts[0], title, path);
  return place ? `${label} · ${place}` : label;
}
