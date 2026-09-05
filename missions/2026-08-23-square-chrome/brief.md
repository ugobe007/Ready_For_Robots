# Square chrome + 1970s control-panel motif

**Date:** 2026-08-23  
**Type:** build  
**Agents:** ProductSurface

## Goal

Users should feel a familiar terminal, not a SaaS pill factory. Panels, buttons, cards, and inputs are **rectangles** (no rounded corners). Add a few 1970s control-panel cues (bevel, inset fields, CRT scan, square LEDs) so Jobs feels powerful and addictive without becoming costume.

## Acceptance

1. Theme `--radius` is `0`. Global CSS forces `border-radius: 0` on UI chrome (decorative glow orbs may stay elliptical).
2. Buttons, inputs, cards, badges, checkboxes are square. Native job-card checkboxes are square LEDs.
3. Jobs CTAs use a hard bevel; URL field is inset; Jobs shell has a faint scanline.
4. Vitest covers the chrome contract. Production FIND still has no Pipeline in the header.

## Out of scope

SIGNAL ranking, matcher, inventing jobs, restyling every leftover marketing metaphor beyond the global radius flatten.
