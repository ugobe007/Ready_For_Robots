# Dexory FIND no longer dumps a class onto DexoryView

**Date:** 2026-09-01
**Type:** build
**Branch:** `cursor/dexory-find-no-dump-009b` from `origin/main` @ `3abc2b6e`

This is the review. `brief.md` is the contract.

## What I saw on live FIND

Paste `https://www.dexory.com/` on production.

The listing overlay already named DexoryView and left it unclassified. That is what the last OEM review promised.

Fly FIND did not agree. It returned DexoryView as `robot_class=service_robot`, zero jobs, then the class picker. The profile note said catalog skip, so it never crawled. Impact was not in the product list on that path.

The homepage still has Forrester's Total Economic Impact™ line. Chrome labels already treat Impact as nav. The dump class was the live integrity break.

Tennant still lists X6 ROVR / T7AMR. Dexmate still returns named Job Cards. Cal desk is 401 without a token, not a 500. I did not SSH Alembic. I did not re-dispatch the cancelled Fly push.

## Cause

Two restores of a class the listing already dropped.

`compile_vendor_seed` wrote `service_robot` whenever `primary_class` was missing. The mixed catalog also stored DexoryView as `service_robot`, so the seed shipped a `product_class` fact: "DexoryView indexed class service_robot."

FIND then did `prefer_work_language_class(...) or claimed`. Prefer returned none. `or claimed` put `service_robot` back.

## What I changed

DexoryView is unclassified in the mixed catalog, the vendor seed, and the frontend lineup cache. No invented scanner name.

Seed compile leaves a missing class empty. FIND display_class uses `keep_claimed_display_class`, which will not restore generic `service_robot`.

Impact / Total Economic Impact / `/impact` stay chrome. Critic chrome names include them.

## Tests

`tests/test_dexory_find.py`: seed, listing, catalog profile (no crawl, no dump class, no Impact), critic corpus.

Related pytest 110 passed. Vitest `knownOemLineups.test.ts` passed.

`PYTHONPATH=/workspace python3 scripts/pstack_release.py --local` is next on this branch.

## Do not

Fly-deploy unless you want production FIND to match listing. This is a dump-class fix. Draft PR.

Do not merge #195. Leftover #202 is superseded by #205.
