# Robot Inference Rules

## Reasoning order

`SOURCE → SUBJECT-SCOPED FACT → HARDWARE → ATOMIC CAPABILITY → COMPOSED CAPABILITY → WORKFLOW → JOB REQUIREMENT MATCH`

Never jump from company/category directly to jobs.

## Evidence states

`EXPLICIT`: directly supported. `DERIVED`: follows from grounded
facts/rule. `LIKELY`: strong incomplete support. `UNKNOWN`:
insufficient. `CONFLICTED`: credible scoped evidence disagrees.

## Subject rules

Facts bind to company/product/generation/configuration/module/component.
Selected-product inference cannot consume sibling products or unselected
modules.

## Manipulation

-   ≥1 grounded arm + grounded hand/end-effector may derive
    `manipulate`.
-   Arm alone does not prove every manipulation primitive.
-   `arm_count>=2` grounds dual-arm hardware; coordinated dual-arm
    manipulation needs task evidence.
-   Dexterous hands + grounded grasp/object/tool behavior may derive
    dexterous manipulation.
-   Grounded mobility + grounded manipulation derives
    `mobile_manipulation`, regardless of whether morphology is humanoid,
    AMR, or service robot.
-   Never infer palletizing/machine tending/packing merely from
    manipulation.

## Mobility/transport

Grounded locomotion derives `move`. Navigation needs navigation
evidence. `move` alone never unlocks transport. Transport needs a
payload/material interface or explicit carry/tow/push/delivery evidence.

## Perception

Camera may support image capture; it does not automatically support
gauge reading, inspection, or object recognition.

## Autonomy

Keep locomotion, navigation, and task autonomy separate. Autonomous
navigation does not prove autonomous manipulation. Teleoperation changes
autonomy, not physical hardware capability.

## Payload

Normalize scope before comparison. Arm payload, hand payload, tray
payload, whole-robot carry, tow, and lift capacity are different
predicates.

## Configuration

AMR + optional arm: base AMR does not inherit arm capability; selected
arm configuration may. Alternate hands/tools on humanoids remain
configuration-specific.

## Match examples

**Palletizing:** requires manipulation + acquisition + placement.
Payload/reach/grasp/cycle may remain UNKNOWN; absence of manipulation
blocks.

**Tote return:** requires navigation + grounded
carry/tow/push/interface. Mobility alone is insufficient.

**Scrub:** requires scrub capability; navigation alone is insufficient.

**Inspection:** requires route mobility/navigation plus relevant
sensing/inspection capability.

## Zero states

`INSUFFICIENT_ROBOT_EVIDENCE`: too little grounded robot capability to
evaluate. `NOT_A_MATCH`: profile is adequate; hard requirements fail.
`CORPUS_GAP`: robot is adequately understood, but relevant work domain
is materially absent from the corpus.

## Anti-rules

Never add `if OEM == X`. Never infer capabilities because a company is
famous for them. Never use morphology as a substitute for hardware.
Never create fake differentiation. Never hide unknowns.

> Core rule: inference may add meaning, but never detach meaning from
> evidence.
