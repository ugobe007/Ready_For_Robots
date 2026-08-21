# Mission: Make Jobs Place a working buyer step

**Date:** 2026-08-21
**Type:** build
**Agents:** ProductSurface
**Status:** in progress

## Goal

Place (step 3) is a real commercial exit: click a live buyer, read pitch + outreach on `/`, and open that buyer in pipeline **without** treating the robot OEM URL as a scanned company.

## Why

`See buyers →` currently goes to `/pipeline?url=ROBOT_OEM&src=place`. Pipeline treats `url=` as a buyer-company scan (`match-url`), so EngineAI lands as a weak "Service Robot" profile instead of customer opportunities. Place on `/` lists names but does not prove pitch or draft.

## Acceptance

- [ ] Place buyers are clickable; selected row shows pitch + outreach draft on `/`
- [ ] `jobsPlaceHref` does **not** pass the robot OEM as `url=`
- [ ] Pipeline `src=place` ignores `url=` and does not recover a stored scan URL
- [ ] Pipeline hop deep-links `?lead=` for the selected buyer
- [ ] No Qualify panel, no Next on the job card, `src=place` is not a Jobs bounce
