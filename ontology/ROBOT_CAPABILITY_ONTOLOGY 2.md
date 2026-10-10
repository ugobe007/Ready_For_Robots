# Robot Capability Ontology

Capabilities are **verbs**, not robot categories.

Each capability carries:
`state=EXPLICIT|DERIVED|LIKELY|UNKNOWN|CONFLICTED`, confidence, subject,
supporting facts, sources, constraints.

## Mobility

move, navigate, localize, map, avoid obstacles, follow route, climb
stairs, use ramp/elevator, dock, reposition, balance.

## Transport

carry, tow, push/pull cart, move tote/rack/pallet, lift pallet, convey,
deliver, retrieve, replenish, recirculate container.

Mobility alone never proves transport.

## Manipulation

**Atomic:** manipulate, reach, grasp, release, pick, place, hold,
carry-in-hand. **Motion/force:** push, pull, lift, lower, rotate,
orient, slide, insert, remove, press, turn, twist, open, close.
**Higher-order:** dual-arm, bimanual, dexterous, in-hand, whole-body
manipulation, handoff, tool use/change, fixture load/unload.

Manipulation is not one binary bit.

## Handling

detect/locate object, pick/place object, sort, singulate, pack/unpack,
load/unload, induct, palletize/depalletize, case/tote/parcel/part
handling, bin pick.

## Machine interaction

machine load/unload, fixture part, operate button/handle/door, tend
cycle, feed material. Arm presence alone does not prove machine tending.

## Cleaning

scrub, sweep, vacuum, mop, disinfect, wipe, collect debris, clean route.

## Inspection

follow inspection route, capture image/thermal, read gauge/display,
detect anomaly/leak/gas, measure temperature, inspect asset, scan
inventory.

A camera alone does not prove `read_gauge`.

## Human/environment interaction

accept/handoff item, follow/guide person, voice interaction, operate in
human space, open door, operate elevator, use workstation, access shelf.

## Autonomy

teleoperated, supervised autonomy, autonomous navigation, autonomous
task execution/recovery, fleet coordinated.

> Principle: infer the smallest defensible physical ability first;
> compose workflows later.
