# Robot Hardware Ontology

Hardware describes what physically exists before capability inference.

## Mobility

Wheeled, tracked, biped, quadruped, aerial, fixed/gantry/rail.
Interfaces may include forks, lift mast, tow hitch, conveyor top,
cart/rack interface, dock.

`mobile=true` does not imply transport.

## Manipulation

**Arms:** count, DoF, reach/workspace, payload, repeatability,
force/torque sensing.

**Hands:** count, fingers, DoF, tactile sensing, force control;
dexterous, anthropomorphic, parallel-jaw, underactuated.

**End effectors:** gripper, suction, clamp, magnetic, fork, hook, tool
holder, screwdriver, welder, dispenser, custom EOAT.

**Whole-body support:** torso/waist articulation, mobile-base
coordination, balance, whole-body force control.

## Perception

RGB/stereo/RGB-D/thermal cameras; 2D/3D LiDAR; radar; ultrasonic;
wrist/joint force; tactile/contact; inspection payloads.

Sensor hardware does not prove a workflow-level sensing capability.

## Payload scope

Always distinguish whole-robot carry, arm, hand, tray/shelf, fork/lift,
tow, and attachment payload. Never convert per-tray capacity into robot
payload.

## Energy/environment

Runtime, duty cycle, charging; indoor/outdoor, warehouse, factory,
hospital, hospitality, home, construction; IP rating, stairs, doors,
elevators, floor type, human proximity.

## Morphology

Non-exclusive: `humanoid`, `mobile_manipulator`, `AMR`, `AGV`, `cobot`,
`industrial_arm`, `quadruped`, `cleaning_robot`, `inspection_robot`,
`service_robot`, `drone`, `construction_robot`.

An AMR may also be a mobile manipulator. A humanoid may also be a
service robot.

> Principle: morphology describes the machine; hardware grounds what it
> may be able to do.
