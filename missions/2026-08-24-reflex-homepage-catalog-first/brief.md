# Indexed OEM homepages skip live fetch (Reflex)

**Date:** 2026-08-24
**Type:** build
**Agents:** ProductSurface, Deploy

## Goal

Pasting `https://www.reflexrobotics.com/` on FIND must open the SKU picker (Reflex Gen2 / Reflex Humanoid) instead of aborting at 22s with “paste a product URL.”

## Why

The vendor index already lists Reflex. FIND still fetched the live homepage first. A slow/challenged OEM host burned the client timeout and blamed the user for pasting a hub.

## Acceptance

1. Indexed vendor URLs (homepage or SKU) do not call `fetch_page`.
2. Reflex homepage returns `needs_product_choice` with Gen2 and Humanoid in under 1s in tests.
3. Unknown OEMs still fetch live pages (no Wayback).
4. Timeout copy no longer tells indexed-homepage users they pasted the wrong kind of URL.

## Out of scope

SIGNAL. Inventing SKU pages Reflex does not publish. Fly deploy of this branch (PR first).
