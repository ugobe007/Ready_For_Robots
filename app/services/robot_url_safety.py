"""URL normalization and SSRF-safe fetch helpers for V1 robot analysis."""
from __future__ import annotations

import ipaddress
import re
import socket
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


class UrlSafetyError(ValueError):
    """Raised when a URL is unsafe or unsupported for crawling."""


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
    # Drop fragments; keep query for product deep links.
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def assert_public_http_url(url: str) -> str:
    """Normalize and reject private / link-local / metadata targets (SSRF)."""
    normalized = normalize_product_url(url)
    if not normalized:
        raise UrlSafetyError("URL is required")
    parsed = urlparse(normalized)
    host = parsed.hostname or ""
    if not host:
        raise UrlSafetyError("URL must include a host")
    if host.lower() in {"localhost", "metadata.google.internal"}:
        raise UrlSafetyError("Private or metadata hosts are not allowed")
    _assert_host_public(host)
    return normalized


def _assert_host_public(host: str) -> None:
    # Literal IP
    try:
        ip = ipaddress.ip_address(host)
        _reject_private_ip(ip)
        return
    except ValueError:
        pass

    # RFC 2606 / 6761 reserved names — used in tests and docs; skip DNS.
    lowered = host.lower().rstrip(".")
    if lowered.endswith((".example", ".test", ".invalid")) or lowered in {"example", "test", "invalid"}:
        return

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UrlSafetyError(f"Could not resolve host: {host}") from exc
    if not infos:
        raise UrlSafetyError(f"Could not resolve host: {host}")
    for info in infos:
        sockaddr = info[4]
        ip = ipaddress.ip_address(sockaddr[0])
        _reject_private_ip(ip)


def _reject_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if any(ip in net for net in _PRIVATE_NETWORKS):
        raise UrlSafetyError("Private network targets are not allowed")
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        raise UrlSafetyError("Non-public network targets are not allowed")
