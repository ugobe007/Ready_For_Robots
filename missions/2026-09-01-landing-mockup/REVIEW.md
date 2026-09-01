# Landing mockup: robots need jobs

**Date:** 2026-09-01  
**Type:** build  
**Branch:** `cursor/landing-fork-copy-009b` (draft #209)  
**Mockup:** https://rfr70sui-wipjpxme.manus.space  
**Did not** merge #195. **Did not** Fly-deploy. Cal stays off `/`.

## What the mockup said

Source: Manus page `Home.tsx` in the published bundle, plus desktop and mobile screenshots.

**Chrome.** ReadyForRobots wordmark. Nav Jobs / About / CRM / outlined Sign In. Dark page `#0A0F1E`, mint `#2EE6A8`, body `#E8EEF7`, muted `#8B98B0`. Display type Space Grotesk, body Archivo, labels Space Mono.

**Hero.** Eyebrow `ReadyForRobots · Robot Employment`. Headline A (default, selected): **Robots need jobs. We find the work.** Last sentence mint. Subhead: jobs for a robot you already have, or robots for work you need done. Paste a product URL, match to real jobs, keep them in CRM.

**Designer chrome we did not ship.** Headline picker A–E under the subhead:

| | Headline |
|---|---|
| A (shipped) | Robots need jobs. We find the work. |
| B | Find the work your robot was built to do. |
| C | The job board for robots. |
| D | Put your robot to work. |
| E | Real jobs, matched to real machines. |

**Two doors.** Robot owner: Look for robot jobs. Employer: Look for robot candidates. Same CTA labels as #208. Copy from the mockup, not the #209 rewrite.

**Below the fold.** How Jobs works / Three steps. No buyer pipeline. (01 Show us your robot, 02 Available jobs, 03 CRM). Jobs brief this week with Amazon OPEN, Benchmark CONDITIONAL, Whitsons CONDITIONAL. Vocabulary: Employer. Workplace. Work. Robot Job. Close: Start free workspace + Download the 2026 briefing. Footer Pricing / FAQ / Privacy / support@.

The mockup is one marketing page. Clicking doors did not change route in the mockup. We keep product routing.

## Live vs fork vs mockup

Production `https://readyforrobots.com` still shows **Who is this visit?** (Vercel has not shipped #209). The fork on this branch had **Jobs for robots. Robots for jobs.** in a boxed two-card shell. The mockup is a full marketing landing with mint CTAs, process strip, sample Job Cards, and vocabulary.

## What we changed

`/` and `/?new=1` render the mockup landing. Doors still go to `/?visit=jobs` (FIND step 1) and `/?visit=candidates` (employer step 1). FIND and employer interiors are unchanged Jobs chrome.

- Headline A, mockup subhead and door copy
- How it works, jobs brief (named employers, robot classes, not invented SKUs), vocabulary, close CTA, slim footer
- Landing fonts Space Grotesk / Archivo / Space Mono
- Sign In outlined mint on Jobs header
- No A–E picker. No Cal. No third product.

## Verify

`pnpm exec vitest run client/src/lib/jobsLanding.test.ts`: 5 passed.  
`PYTHONPATH=. python3 scripts/pstack_release.py --local`: How / Act / Critic ok. FIND drive skipped.  
Local Vite `http://127.0.0.1:3000/`:

- H1 is Robots need jobs. We find the work. Old Who is this visit? is gone. No Headline options.
- Look for robot jobs → FIND step 1 (URL + I know the robot).
- Look for robot candidates → employer step 1 (What is the work).
- Cal is not on the landing.

Stay draft. No Fly.

## Gaps

- Header still uses the product Kare pixel face and Jobs nav on mobile. The mockup hid nav under `md` and used a simple SVG head.
- FIND / employer keep the existing Jobs shell, scanline, process bar. The mockup never designed those screens.
- Jobs brief cards are the mockup’s Amazon / Benchmark / Whitsons examples, not a live FIND payload.
- Footer links on the mockup were `#`. Ours go to Pricing, FAQ, Privacy, and mail.
- A–E picker is designer-only. We shipped A.
