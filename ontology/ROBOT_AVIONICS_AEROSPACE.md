# Avionics vs aerospace

**Purpose:** keep flying-vehicle robots distinct from space robots. Both are
FIND classes and operating-environment verticals. Neither is a SIGNAL industry
tag. Jobs still match from grounded capabilities and task models — never
`company → category → jobs`.

## Avionics

**In class:** drones (UAV), eVTOL (“flying cars”), airplane-like robots
(autonomous / optionally piloted aircraft).

**Work families:** drone inspection, drone delivery, eVTOL passenger/cargo
flight, autonomous flight. Hangar or airside *inspection of an airframe* is
avionics work a drone can do — it is not the definition of the class.

**Not avionics:** satellites, rockets, orbital debris, space exploration.

**Capability:** `avionics_task` (from `claims_avionics` or product class
`avionics` / `aviation_robot` / `drone` / `evtol`). Empty specs stay `UNKNOWN`.

**Configuration (R28):** do not dump every avionics job onto every flying
SKU. `evtol` grounds `evtol_flight` (passenger/cargo air taxi). `drone`/`uav`
grounds `drone_task` (aerial inspect or delivery). Hangar or airside *walking*
around parked aircraft is inspect work for a quadruped (`inspect_route`) or
an inspect drone (`drone_task`). It is **not** work an eVTOL flying car
performs — the flying car is the aircraft sitting on the ramp.

## Aerospace

**In class:** satellites, rockets, robots for space exploration and
development. Hot work: a robot **attached to a satellite** that captures or
clears **orbital debris**.

**Work families:** satellite servicing, orbital debris removal, launch / rocket
ground support (when the robot is the ground or on-orbit agent).

**Not aerospace:** drones, eVTOL, autonomous airplanes.

**Capability:** `aerospace_task` (from `claims_aerospace` or product class
`aerospace` / `aerospace_robot`). Empty specs stay `UNKNOWN`.

## Rule

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → …
```

A company that sells both a drone and a satellite bus does not dump every job
onto either SKU. Configuration matters: a debris-capture arm on a servicing
satellite is a **configuration** of that satellite product, not an “aerospace
class” shortcut to jobs.
