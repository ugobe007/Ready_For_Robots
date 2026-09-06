# Robot Workflow Ontology

A workflow is a repeatable composition of capabilities. It is not yet a
Robot Job.

## Core workflows

**Tote/cart return:** locate → acquire/interface → navigate → deliver →
release → return.

**Cart delivery/exchange:** acquire → navigate → deliver →
exchange/release → return.

**POU replenishment:** collect material → transport → stage → return.

**Kit-to-line:** receive kit → acquire/carry/tow → navigate → stage at
line.

**Palletizing:** detect case → acquire → lift → orient → place to pallet
pattern → repeat. Wrapping/skid movement are separate extensions.

**Depalletizing:** perceive stack → select → grasp → remove → orient →
place to conveyor/bin.

**Machine tending:** retrieve part → approach/access machine → load
fixture → await/trigger cycle → unload → place output.
Programming/setup/QA remain separate unless evidenced.

**Pick/pack:** identify → locate → grasp → pick → move → place → verify
if supported.

**Floor scrub:** navigate → dispense → scrub → recover fluid → cover
route → dock/refill/charge. Vacuum/sweep are distinct.

**Inspection route:** navigate to asset → position sensor → capture/read
→ evaluate/transmit → next asset.

**Trailer unloading:** access trailer → perceive cases → acquire →
remove → transfer → repeat.

**Human-environment/service:** object retrieval, shelf organization,
dish/laundry handling, wiping, door interaction, cart pushing, room
delivery. These can share primitives with industrial work.

Each workflow declares required/optional capabilities,
quantitative/environment constraints, autonomy needs, and human-owned
steps.

> Principle: workflows are composed from capabilities, never inferred
> from category alone.
