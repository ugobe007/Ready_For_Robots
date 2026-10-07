# Robot Job Ontology

> A Robot Job is a bounded piece of physical work evidenced at a real
> company/worksite and represented independently of a particular robot
> until matching.

## Object

`robot_job_id`, `job_number`, company, worksite, workflow, work
description, route/handoff, evidence, existence confidence, definition
completeness, requirements, unknowns, commercial state.

## Admission test

Answer: 1. What physical work exists? 2. Where? 3. What
object/material/environment? 4. What evidence supports existence? 5.
What must a robot do? 6. What remains unknown?

If worksite is unresolved, retain a pattern/claim rather than
fabricating a facility pursuit.

## Requirements

Each requirement has capability, importance
(`REQUIRED|PREFERRED|OPTIONAL`), constraint, and robot state
(`MATCHED|UNMET|UNKNOWN|LIKELY`).

Example palletizing: manipulate case; acquire from conveyor; place to
pattern; payload ≥ case weight; adequate reach; compatible grasp;
adequate cycle time.

## Match outcomes

`STRONG_MATCH | POSSIBLE_MATCH | NOT_A_MATCH | INSUFFICIENT_ROBOT_EVIDENCE | CORPUS_GAP`

`UNKNOWN` never silently becomes `MATCHED`. A hard `UNMET` required
capability may block.

`INSUFFICIENT_ROBOT_EVIDENCE` is not `CORPUS_GAP`.

## Commercial progression

`DISCOVERED → DESK QUALIFIED → CONTACT QUALIFIED → READY FOR PURSUIT → PLACED later`

Attribution seed: `Company + Worksite + Work`.

> Principle: describe work first; match robots afterward.
