# Mission: Accept international robot URLs (.com.cn)

**Date:** 2026-08-21
**Type:** build
**Agents:** LeadQuality / ProductSurface
**Status:** in progress

## Goal

`https://en.engineai.com.cn/` researches instead of "Research failed." International / compound ccTLD hosts resolve even when Fly's system DNS cannot.

## Why

Production returned `Could not resolve host: en.engineai.com.cn` (400) in ~1s. The host is valid; it CNAMEs through a `.cn` CDN. Unicode hosts also need IDNA.

## Acceptance

- [x] `registrable_domain("en.engineai.com.cn") == "engineai.com.cn"`
- [x] IDNA punycode for international labels
- [x] DNS-over-HTTPS fallback when getaddrinfo fails
- [x] SSRF still rejects loopback / private
- [x] Tests pass
