# Home FIND tape has no height after page-scroll

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface

## Goal

Live Robot Jobs on `/` (FIND) must show 12 classified rows. After unlocking document scroll, the tape still sized itself with `h-full` of a parent pane. Rows are `position: absolute`, so a parent without an explicit height clips the list to zero.

## Acceptance

1. Tape list viewport height is `12 × 58px`, not `h-full` / `flex-1`.
2. Home FIND shows Live Robot Jobs without a `100vh` workspace.
3. Vitest contract green.

## Out of scope

- Changing the 01→02→03 page architecture
- Matcher / SIGNAL
