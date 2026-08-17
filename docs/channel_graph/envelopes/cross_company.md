# Cross Company — capability envelope (solution integrator)

**Partner:** Cross Company · Southeast US  
**Kind:** solution_integrator  
**Need:** Find automation work my company can solve.  
**Not:** Find jobs for one OEM SKU.

## Represented platforms (from channel graph)

| OEM | Role evidence | Families |
|-----|---------------|----------|
| Doosan Robotics | Distributor + certified integrator + service center (C3) | cobot · palletizing · machine tending |
| Universal Robots | Certified system integrator (C2) | cobot · palletizing · machine tending |
| FANUC | Systems integrator (C2) | industrial manip · palletizing · packaging · machine tending |

## Combined capability envelope

- Collaborative and industrial arm work  
- End-of-line **palletizing** (cases/cartons → pallet)  
- **Machine tending** (load/unload CNC, press, molding)  
- Case packing / related cell work  
- Integration · deployment · field service · training  

## Territory (Doosan representation)

NC · SC · VA · TN · GA · FL · MS · KY · AL  
(National project work possible; SE is the hard footprint for routing.)

## Product modes (same engine)

| Mode | Prompt |
|------|--------|
| OEM | Find jobs for your robot |
| Distributor | Find jobs for the robots you sell |
| Integrator | Find automation jobs your company can solve |

Manipulation Open-World 25 exists to feed **this** envelope — not to invent ontology.

## After Manipulation 25

| | Before | After |
|--|--------|-------|
| Compatible RFR jobs | **0** | **~19** |
| Palletizing | 0 | ~11 |
| Machine tending | 0 | ~8 |
| SE routable candidates | 0 | ~9–11 |

**Product line (fixture only):**  
> We found ~19 automation jobs your company can solve.  
> Matched to Doosan / Universal Robots / FANUC.

See [`../../product_sim/worksite/manipulation_open_world_25_results.md`](../../product_sim/worksite/manipulation_open_world_25_results.md) · [`../integrator_demo_fixture.json`](../integrator_demo_fixture.json)

Routable Job still needs per-job Channel Match (capability × territory × sell/integrate/deploy/service). Do not build UI yet.
