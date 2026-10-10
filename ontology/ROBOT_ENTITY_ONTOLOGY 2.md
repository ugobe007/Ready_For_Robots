# Robot Entity Ontology

## Chain

`Company → Product Family → Product/SKU → Generation → Configuration → Module → Component`

Capabilities belong to the selected **product/configuration**, not
automatically to a company.

## Core objects

**Company:** canonical name, brands, domain,
manufacturer/brand/distributor/integrator role, identity confidence,
evidence.

**Product:** company, family, name/model, generation, commercial status,
non-exclusive categories, evidence.

**Configuration:** product plus installed options/modules that
materially change capability. Examples: base AMR; AMR+conveyor;
AMR+arm+gripper; cobot+vacuum EOAT; quadruped+inspection payload.

**Module:** optional/removable hardware. Never promote module capability
to the base robot unless that configuration includes it.

## Subject scoping

Every fact must carry `subject_type`, `subject_id`, `predicate`,
`value`, `source_id`.

Selected-product inference may not consume sibling SKU facts, unrelated
products, unselected accessories, partner/customer robots, or generic
company marketing.

## Multi-product URL

Never arbitrarily select one robot. Return `products_found[]`; allow
one, several, or all. Portfolio mode preserves independent profiles.

Identity states: `CONFIRMED | PROBABLE | WEAK | UNRESOLVED`.

> Invariant: evidence about one machine must not silently become truth
> about another machine.
