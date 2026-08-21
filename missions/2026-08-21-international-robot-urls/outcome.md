# Outcome: Accept international robot URLs

**Date:** 2026-08-21
**Type:** build
**Status:** on branch

## What changed

Production `POST /api/robot-profile` for `https://en.engineai.com.cn/` returned 400 `Could not resolve host` (Fly system DNS misses that `.com.cn` CDN chain; it can also succeed intermittently). The UI mapped any 400 to "Research failed."

Also `en.engineai.com.cn` was stored as the company domain instead of `engineai.com.cn`.

- IDNA / punycode for international host labels
- Compound ccTLD registrable domain (`en.engineai.com.cn` → `engineai.com.cn`)
- DNS-over-HTTPS fallback (Cloudflare, then Google) when getaddrinfo fails
- Thread-local IP override so fetch uses those public A records (SNI still the hostname)
- SSRF still rejects loopback / private, including DoH answers
- Jobs UI surfaces the API detail instead of a generic Research failed

## Tests

`venv/bin/python -m pytest tests/test_robot_url_safety.py tests/test_robot_analysis_slice1.py` — 20 passed

Local profile build (system DNS stubbed empty, DoH + fetch): company `ENGINEAI`, domain `engineai.com.cn`, HTTP 200, 13 facts.

Production `POST /api/robot-profile` at check time returned **200** (cached `2026-08-21T03:02:02Z`) with `primary_domain: en.engineai.com.cn` — the DNS 400 is intermittent; the compound-ccTLD domain bug is still live until deploy.

## Follow-up

Fly deploy of `app/services/robot_url_safety.py` is required for production. This VM has no Fly token. Profile cache TTL is 6h, so a successful cached EngineAI profile may keep the old domain until expiry.
