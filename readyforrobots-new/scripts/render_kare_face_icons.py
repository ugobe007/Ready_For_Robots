#!/usr/bin/env python3
"""Render the Kare face bitmap into favicon / touch / Open Graph assets.

Source of truth: client/src/lib/kareIcons.ts → KARE_FACE (15×15).
Run from repo:  python3 readyforrobots-new/scripts/render_kare_face_icons.py
"""

from __future__ import annotations

import argparse
import re
import struct
import zlib
from pathlib import Path

NAVY = (8, 17, 38)  # #081126 — Jobs terminal
EMERALD = (62, 207, 142)  # #3ecf8e — FACE_EMERALD
NAVY_HEX = "#081126"
EMERALD_HEX = "#3ecf8e"

ROOT = Path(__file__).resolve().parents[1]
TS_PATH = ROOT / "client" / "src" / "lib" / "kareIcons.ts"
PUBLIC = ROOT / "client" / "public"
BRANDING = PUBLIC / "branding"


def parse_kare_face(ts_text: str) -> list[list[int]]:
    match = re.search(
        r"export const KARE_FACE(?::[^=]+)? = \[([\s\S]*?)\n\];",
        ts_text,
    )
    if not match:
        raise SystemExit("KARE_FACE array not found in kareIcons.ts")
    rows = re.findall(r"\[([01](?:,\s*[01]){14})\]", match.group(1))
    if len(rows) != 15:
        raise SystemExit(f"expected 15 face rows, got {len(rows)}")
    grid = [[int(n) for n in row.split(",")] for row in rows]
    if any(len(r) != 15 for r in grid):
        raise SystemExit("face rows must be 15 wide")
    return grid


def load_face() -> list[list[int]]:
    return parse_kare_face(TS_PATH.read_text())


def png_rgba(rows: list[list[tuple[int, int, int]]]) -> bytes:
    height = len(rows)
    width = len(rows[0])
    raw = b"".join(
        b"\x00" + b"".join(bytes((*px, 255)) for px in row) for row in rows
    )
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", ihdr),
            chunk(b"IDAT", zlib.compress(raw, 9)),
            chunk(b"IEND", b""),
        ]
    )


def paint_face(
    face: list[list[int]],
    *,
    canvas: int,
    scale: int,
    pad: int,
    fill: tuple[int, int, int] = EMERALD,
    bg: tuple[int, int, int] = NAVY,
) -> list[list[tuple[int, int, int]]]:
    rows = [[bg for _ in range(canvas)] for _ in range(canvas)]
    for y, row in enumerate(face):
        for x, bit in enumerate(row):
            if not bit:
                continue
            color = fill
            for dy in range(scale):
                for dx in range(scale):
                    rows[pad + y * scale + dy][pad + x * scale + dx] = color
    return rows


def paint_og(face: list[list[int]], width: int = 1200, height: int = 630) -> list[list[tuple[int, int, int]]]:
    scale = 28  # 15 * 28 = 420
    face_px = 15 * scale
    ox = (width - face_px) // 2
    oy = (height - face_px) // 2
    rows = [[NAVY for _ in range(width)] for _ in range(height)]
    for y, row in enumerate(face):
        for x, bit in enumerate(row):
            if not bit:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    rows[oy + y * scale + dy][ox + x * scale + dx] = EMERALD
    return rows


def svg_face(face: list[list[int]]) -> str:
    rects = []
    for y, row in enumerate(face):
        for x, bit in enumerate(row):
            if bit:
                rects.append(f'<rect x="{x}" y="{y}" width="1" height="1"/>')
    inner = "\n    ".join(rects)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 15 15" '
        f'shape-rendering="crispEdges">\n'
        f'  <rect width="15" height="15" fill="{NAVY_HEX}"/>\n'
        f'  <g fill="{EMERALD_HEX}">\n    {inner}\n  </g>\n'
        f"</svg>\n"
    )


def write_png(path: Path, rows: list[list[tuple[int, int, int]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png_rgba(rows))


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path.name} is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def check_assets(face: list[list[int]]) -> None:
    svg = PUBLIC / "favicon.svg"
    if NAVY_HEX not in svg.read_text() or EMERALD_HEX not in svg.read_text():
        raise SystemExit("favicon.svg missing brand colors")
    expected_bits = sum(sum(row) for row in face)
    if svg.read_text().count("<rect x=") != expected_bits:
        raise SystemExit("favicon.svg pixel rect count does not match KARE_FACE")
    expected_sizes = {
        PUBLIC / "favicon-16x16.png": (16, 16),
        PUBLIC / "favicon-32x32.png": (32, 32),
        PUBLIC / "apple-touch-icon.png": (180, 180),
        BRANDING / "icon-192.png": (192, 192),
        BRANDING / "icon-512.png": (512, 512),
        BRANDING / "og-face.png": (1200, 630),
    }
    for path, size in expected_sizes.items():
        if png_size(path) != size:
            raise SystemExit(f"{path.name} is {png_size(path)}, expected {size}")
    if face[0][0] != 1:
        raise SystemExit("face stroke origin missing")
    rows32 = paint_face(face, canvas=32, scale=2, pad=1)
    if rows32[0][0] != NAVY or rows32[1][1] != EMERALD or rows32[1][0] != NAVY:
        raise SystemExit("32×32 face padding/stroke pixels are wrong")
    ico = PUBLIC / "favicon.ico"
    if ico.read_bytes()[6:10] != b"\x20\x20\x00\x00":
        raise SystemExit("favicon.ico is not a 32×32 ICO")
    print("check ok")


def render_all(face: list[list[int]]) -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    BRANDING.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "favicon.svg").write_text(svg_face(face))
    # 16×16: 15×15 face + 1px navy on right and bottom.
    rows16 = paint_face(face, canvas=16, scale=1, pad=0)
    write_png(PUBLIC / "favicon-16x16.png", rows16)
    write_png(PUBLIC / "favicon-32x32.png", paint_face(face, canvas=32, scale=2, pad=1))
    write_png(PUBLIC / "apple-touch-icon.png", paint_face(face, canvas=180, scale=10, pad=15))
    ico_png = (PUBLIC / "favicon-32x32.png").read_bytes()
    # ICO wrapping a PNG (Vista+). Offset 22 = ICONDIR (6) + one ICONDIRENTRY (16).
    (PUBLIC / "favicon.ico").write_bytes(
        struct.pack("<HHH", 0, 1, 1)
        + struct.pack("<BBBBHHII", 32, 32, 0, 0, 1, 32, len(ico_png), 22)
        + ico_png
    )
    write_png(BRANDING / "icon-192.png", paint_face(face, canvas=192, scale=12, pad=6))
    write_png(BRANDING / "icon-512.png", paint_face(face, canvas=512, scale=32, pad=16))
    write_png(BRANDING / "og-face.png", paint_og(face))
    (PUBLIC / "site.webmanifest").write_text(
        """{
  "name": "ReadyForRobots",
  "short_name": "ReadyForRobots",
  "icons": [
    { "src": "/favicon-32x32.png", "sizes": "32x32", "type": "image/png" },
    { "src": "/branding/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/branding/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "theme_color": "#081126",
  "background_color": "#081126",
  "display": "standalone"
}
"""
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    face = load_face()
    if args.check:
        check_assets(face)
        return
    render_all(face)
    check_assets(face)
    print(f"wrote face icons under {PUBLIC}")


if __name__ == "__main__":
    main()
