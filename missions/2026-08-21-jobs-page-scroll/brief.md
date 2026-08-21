# Jobs is a scrolling 3-step page, not a clipped box

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface  
**ICP:** OEM on `/` (Fourier N1 path and every Jobs submit)

## Goal

Jobs is a **wizard process on a normal page**. Chrome could not scroll below the fold because the workspace was a `100vh` + `overflow: hidden` two-pane box. Pinning Activate inside that box was a patch.

## Product decision (locked)

Site header + process bar (01 → 02 → 03) are page chrome. Content grows. The document scrolls. Two columns are layout, not a clipping box. Repeat the process bar at the bottom of the page.

## Acceptance

1. No `h-[calc(100vh…)]` / shell `overflow-hidden` on the Jobs workspace.
2. Process bar at the top (sticky under the site header) and at the bottom of the page.
3. Jobs list + Activate are in document flow; Chrome can scroll to them.
4. Vitest contract for the page shell.

## Out of scope

- Matcher / SIGNAL / Qualify
- Changing the 01 → 02 → 03 steps themselves
