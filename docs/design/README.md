# ReadyForRobots design reference

## New_Ready mockups (`new-ready-mockups/`)

PNG exports from the Manus redesign pass (June 2026). Use these as the visual source of truth for:

- **Dark navy hero** (`#0b0f17` → `#111827`) with emerald mesh
- **Operator pages** — Pipeline, Signals, Robots with dark toolbars and data tables
- **Marketing** — Home hero, live pipeline widget, testimonials, HEIR blocks
- **Typography** — Space Grotesk display, JetBrains Mono for scores/stats

### File index

| File | Page / section |
|------|----------------|
| `New_Ready.png` | Robots table footer + HEIR CTA + newsletter |
| `New_Ready1.png` | Humanoid index table |
| `NEW_READY2.png` | HEIF engineering maturity matrix |
| `NEW_READY3.png` | Robots hero + leader cards |
| `NEW_READY4–5.png` | Signals library + live strength |
| `NEW_READY6.png` | Footer + newsletter band |
| `NEW_READY7–8.png` | Live pipeline rows + page hero |
| `NEW_READY9.png` | Automation Imperative report banner |
| `NEW_READY10–15.png` | Homepage sections (HEIR, testimonials, how it works) |
| `NEW_READY16.png` | Homepage hero + live pipeline widget |

Implementation lives in `readyforrobots-new/client/src/index.css` (`page-hero-dark`, `page-dark-shell`, `pipeline-workspace`) and `components/layout/PageHeroDark.tsx`.
