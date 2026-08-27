# Agriculture / marine / avionics / construction robot classes

**Date:** 2026-08-27
**Type:** build
**Agents:** ProductSurface + LeadQuality (ontology)
**Status:** done

## Goal

FIND step 02 **NAME THE ROBOT CLASS** was missing work-domain / platform classes. LaserWeeder (carbonrobotics.com) is an agriculture robot that removes weeds from crops, not a warehouse AMR or cobot. Add **agriculture, marine, avionics, construction** to the same picker, and teach the ontology to infer LaserWeeder / Carbon Robotics as agricultural weeding so FIND can skip the picker when evidence is enough.

## Acceptance

1. Picker keeps the original six tiles and adds four work-domain tiles (label + one-line work hint). Tests: all 10 classes render.
2. Ontology + inference: LaserWeeder / carbonrobotics.com → agriculture class + weeding task model. Marine / avionics / construction have real task models (not empty category→jobs). UNKNOWN specs stay UNKNOWN.
3. FIND: Carbon Robotics LaserWeeder prefers agriculture / weeding / crop / field jobs, not humanoid warehouse primitives. If class is UNKNOWN, picker includes agriculture.
4. pytest + vitest for picker + LaserWeeder identity/class. CRM KEEP 0 / Yes, keep them from #158 is unchanged.

## Out of scope

SIGNAL hop. Invented rental $. Deleting the original six classes. Treating agriculture as a SIGNAL industry tag.
