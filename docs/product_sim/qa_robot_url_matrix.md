# QA — robot URL integrity matrix (pre-traffic)

**Date:** 2026-08-15  
**Rule:** Never invent a match. False Origin/Neo jobs for the wrong physics = do not send traffic.

## Before integrity gate

Silent fallback mapped **8/10** non-AMR/non-scrub URLs onto `locus_origin` (warehouse tote jobs). **FAIL.**

## After integrity gate (`mapUrlToEnvelope`)

| Kind | URL | Result |
|------|-----|--------|
| AMR | locusrobotics.com/products/origin/ | `locus_origin` PASS |
| Floor cleaning | avidbots.com/neo | `avidbots_neo` PASS |
| Inspection | bostondynamics.com/products/spot/ | unsupported PASS |
| Cobot | universal-robots.com/products/ur10e/ | unsupported PASS |
| Palletizer | …/robotic-palletizer | unsupported PASS |
| Humanoid | agilityrobotics.com/robots/digit | unsupported PASS |
| Agriculture | advanced.farm/strawberry-harvester | unsupported PASS |
| Delivery | starship.xyz/robot | unsupported PASS |
| Construction | builtrobotics.com/excavator | unsupported PASS |
| Food service | misorobotics.com/flippy | unsupported PASS |

**Verdict: PASS — safe for Cohort 1 traffic** (honest refuse + offer Origin/Neo demos).

Unsupported UX copy: “We don't have jobs for this robot yet” + try AMR / scrub.

Event: `rdd_unsupported_robot` (guessed_family when known).
