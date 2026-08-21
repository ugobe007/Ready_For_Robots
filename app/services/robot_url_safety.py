"""URL normalization and SSRF-safe fetch helpers for V1 robot analysis."""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import threading
import urllib.error
import urllib.request
from urllib.parse import urlparse, urlunparse

_PRIVATE_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)

# Compound public suffixes used by OEM sites (China, JP, UK, …). Not a full PSL.
_MULTI_PART_SUFFIXES = frozenset(
    {
        "com.cn",
        "net.cn",
        "org.cn",
        "gov.cn",
        "ac.cn",
        "edu.cn",
        "co.uk",
        "org.uk",
        "ac.uk",
        "gov.uk",
        "co.jp",
        "or.jp",
        "ne.jp",
        "ac.jp",
        "com.au",
        "net.au",
        "org.au",
        "co.kr",
        "co.in",
        "com.tw",
        "com.hk",
        "com.br",
        "co.za",
        "com.sg",
        "co.nz",
        "com.mx",
        "co.id",
        "com.my",
        "com.vn",
        "com.tr",
        "co.th",
        "com.ar",
        "com.ua",
        "co.il",
    }
)

_DOH_URLS = (
    "https://cloudflare-dns.com/dns-query?name={host}&type=A",
    "https://dns.google/resolve?name={host}&type=A",
)

_TLS = threading.local()
_real_getaddrinfo = socket.getaddrinfo
_HOOK_INSTALLED = False


class UrlSafetyError(ValueError):
    """Raised when a URL is unsafe or unsupported for crawling."""


def idna_hostname(host: str) -> str:
    """ASCII / punycode hostname. International labels must not stay as Unicode."""
    text = (host or "").strip().rstrip(".").lower()
    if not text:
        return text
    try:
        return text.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        return text


def registrable_domain(host: str) -> str:
    """eTLD+1, including compound ccTLDs like engineai.com.cn."""
    host = idna_hostname(host).removeprefix("www.")
    labels = [p for p in host.split(".") if p]
    if len(labels) >= 3 and ".".join(labels[-2:]) in _MULTI_PART_SUFFIXES:
        return ".".join(labels[-3:])
    if len(labels) >= 2:
        return ".".join(labels[-2:])
    return host


def normalize_product_url(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    if not re.match(r"^https?://", text, re.I):
        text = f"https://{text}"
    parsed = urlparse(text)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise UrlSafetyError("Only http and https URLs are supported")
    if not parsed.netloc:
        raise UrlSafetyError("URL must include a host")
    hostname = parsed.hostname or ""
    ascii_host = idna_hostname(hostname)
    if ascii_host and ascii_host != hostname:
        parsed = _replace_hostname(parsed, ascii_host)
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def assert_public_http_url(url: str) -> str:
    """Normalize and reject private / link-local / metadata targets (SSRF)."""
    _install_getaddrinfo_hook()
    normalized = normalize_product_url(url)
    if not normalized:
        raise UrlSafetyError("URL is required")
    parsed = urlparse(normalized)
    host = idna_hostname(parsed.hostname or "")
    if not host:
        raise UrlSafetyError("URL must include a host")
    if host in {"localhost", "metadata.google.internal"}:
        raise UrlSafetyError("Private or metadata hosts are not allowed")
    _assert_host_public(host)
    return normalized


def _replace_hostname(parsed, new_host: str):
    auth = ""
    netloc = parsed.netloc
    if "@" in netloc:
        auth = netloc.rsplit("@", 1)[0] + "@"
    port = parsed.port
    if ":" in new_host and "." not in new_host and not new_host.startswith("["):
        host_part = f"[{new_host}]"
    else:
        host_part = new_host
    port_part = f":{port}" if port else ""
    return parsed._replace(netloc=f"{auth}{host_part}{port_part}")


def _assert_host_public(host: str) -> None:
    try:
        ip = ipaddress.ip_address(host)
        _reject_private_ip(ip)
        return
    except ValueError:
        pass

    lowered = host.lower().rstrip(".")
    if lowered.endswith((".example", ".test", ".invalid")) or lowered in {
        "example",
        "test",
        "invalid",
    }:
        return

    ips = _resolve_public_ips(host)
    if not ips:
        raise UrlSafetyError(f"Could not resolve host: {host}")
    for ip in ips:
        _reject_private_ip(ip)
    _remember_host_ips(host, [str(ip) for ip in ips])


def _resolve_public_ips(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    raw = _system_resolve_ips(host)
    if not raw:
        raw = _doh_resolve_ips(host)
    ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    seen: set[str] = set()
    for item in raw:
        try:
            ip = ipaddress.ip_address(item)
        except ValueError:
            continue
        key = str(ip)
        if key in seen:
            continue
        seen.add(key)
        ips.append(ip)
    return ips


def _system_resolve_ips(host: str) -> list[str]:
    found: list[str] = []
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            infos = _real_getaddrinfo(host, None, family)
        except socket.gaierror:
            continue
        for info in infos:
            found.append(info[4][0])
    return found


def _doh_resolve_ips(host: str) -> list[str]:
    """Public DNS-over-HTTPS when the platform resolver cannot see ccTLD / CDN hosts."""
    quoted = host
    for template in _DOH_URLS:
        url = template.format(host=quoted)
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/dns-json", "User-Agent": "ReadyForRobots/1.0"},
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                payload = json.loads(resp.read().decode("utf-8") or "{}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            continue
        ips: list[str] = []
        for ans in payload.get("Answer") or []:
            if int(ans.get("type") or 0) != 1:
                continue
            data = str(ans.get("data") or "").strip()
            if data:
                ips.append(data)
        if ips:
            return ips
    return []


def _remember_host_ips(host: str, ips: list[str]) -> None:
    mapping = getattr(_TLS, "host_ips", None)
    if mapping is None:
        mapping = {}
        _TLS.host_ips = mapping
    mapping[host] = ips


def _hooked_getaddrinfo(host, port, *args, **kwargs):
    key = idna_hostname(host or "")
    ips = getattr(_TLS, "host_ips", {}) or {}
    mapped = ips.get(key)
    if mapped:
        family = kwargs.get("family", args[0] if args else 0) or 0
        socktype = kwargs.get("type", args[1] if len(args) > 1 else 0) or socket.SOCK_STREAM
        proto = kwargs.get("proto", args[2] if len(args) > 2 else 0) or 0
        port_n = int(port or 0)
        out = []
        for ip in mapped:
            af = socket.AF_INET6 if ":" in ip else socket.AF_INET
            if family not in (0, socket.AF_UNSPEC, af):
                continue
            sockaddr = (ip, port_n, 0, 0) if af == socket.AF_INET6 else (ip, port_n)
            out.append((af, socktype, proto, "", sockaddr))
        if out:
            return out
    return _real_getaddrinfo(host, port, *args, **kwargs)


def _install_getaddrinfo_hook() -> None:
    global _HOOK_INSTALLED
    if _HOOK_INSTALLED:
        return
    socket.getaddrinfo = _hooked_getaddrinfo
    _HOOK_INSTALLED = True


def _reject_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if any(ip in net for net in _PRIVATE_NETWORKS):
        raise UrlSafetyError("Private network targets are not allowed")
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        raise UrlSafetyError("Non-public network targets are not allowed")
