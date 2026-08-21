# Outcome: Accept international robot URLs

**Date:** 2026-08-21
**Type:** build
**Status:** on branch

## What changed

Production `POST /api/robot-profile` for `https://en.engineai.com.cn/` returned 400 `Could not resolve host` — Fly's system DNS misses that `.com.cn` CDN chain.

- IDNA / punycode for international host labels
- Compound ccTLD registrable domain (`en.engineai.com.cn` → `engineai.com.cn`)
- DNS-over-HTTPS fallback (Cloudflare, then Google) when getaddrinfo fails
- Thread-local IP override so fetch uses those public A records (SNI still the hostname)
- SSRF still rejects loopback / private, including DoH answers
- Jobs UI surfaces the API detail instead of a generic Research failed

## Tests

`venv/bin/python -m pytest tests/test_robot_url_safety.py tests/test_robot_analysis_slice1.py` — 20 passed

Local profile build (system DNS stubbed empty, DoH + fetch): company `ENGINEAI`, domain `engineai.com.cn`, HTTP 200.

## Follow-up

Fly deploy of `app/services/robot_url_safety.py` is required for production. This VM has no Fly token.
