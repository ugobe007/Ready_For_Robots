#!/usr/bin/env python3
"""Build Cal GIF assets — email sting (small) + shareable POV Monday meme."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETING = ROOT / "readyforrobots-new" / "client" / "public" / "marketing"


@dataclass(frozen=True)
class GifSpec:
    name: str
    html: Path
    out: Path
    width: int
    height: int
    frame_count: int
    frame_duration_ms: int

    @property
    def input_fps(self) -> float:
        return 1000.0 / self.frame_duration_ms


SPECS = (
    GifSpec(
        name="email-sting",
        html=ROOT / "scripts" / "assets" / "cal_sting_frames.html",
        out=MARKETING / "cal-pipeline-demo.gif",
        width=320,
        height=108,
        frame_count=3,
        frame_duration_ms=2000,
    ),
    GifSpec(
        name="pov-monday-meme",
        html=ROOT / "scripts" / "assets" / "cal_meme_frames.html",
        out=MARKETING / "cal-meme-monday.gif",
        width=280,
        height=160,
        frame_count=4,
        frame_duration_ms=2000,
    ),
)


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _capture_frames(spec: GifSpec, tmp: Path) -> list[Path]:
    from playwright.sync_api import sync_playwright

    paths: list[Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": spec.width, "height": spec.height})
        page.goto(spec.html.as_uri())
        page.wait_for_timeout(250)
        for i in range(spec.frame_count):
            page.evaluate(f"window.showFrame({i})")
            page.wait_for_timeout(350)
            out = tmp / f"{spec.name}_frame_{i:02d}.png"
            page.screenshot(path=str(out), type="png")
            paths.append(out)
        browser.close()
    return paths


def _assemble_gif_ffmpeg(spec: GifSpec, frames: list[Path], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    # Rename to sequential pattern for ffmpeg
    for i, src in enumerate(frames):
        dest = src.parent / f"frame_{i:02d}.png"
        if src != dest:
            src.rename(dest)
    pattern = frames[0].parent / "frame_%02d.png"
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(spec.input_fps),
        "-i",
        str(pattern),
        "-vf",
        (
            f"scale={spec.width}:{spec.height}:flags=lanczos,"
            "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        ),
        "-loop",
        "0",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _assemble_gif_pillow(spec: GifSpec, frames: list[Path], out: Path) -> None:
    from PIL import Image

    images = [Image.open(p).convert("P", palette=Image.ADAPTIVE, colors=128) for p in frames]
    out.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=spec.frame_duration_ms,
        loop=0,
        optimize=True,
    )


def build_one(spec: GifSpec) -> int:
    if not spec.html.is_file():
        print(f"Missing {spec.html}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix=f"cal-gif-{spec.name}-") as td:
        tmp = Path(td)
        try:
            frames = _capture_frames(spec, tmp)
        except Exception as exc:
            print(f"[{spec.name}] Playwright capture failed: {exc}", file=sys.stderr)
            return 1

        try:
            if _ffmpeg_available():
                _assemble_gif_ffmpeg(spec, frames, spec.out)
            else:
                _assemble_gif_pillow(spec, frames, spec.out)
        except Exception as exc:
            print(f"[{spec.name}] GIF assembly failed: {exc}", file=sys.stderr)
            return 1

    size_kb = spec.out.stat().st_size // 1024
    total_sec = spec.frame_count * spec.frame_duration_ms / 1000
    print(
        f"Wrote {spec.out.name} ({spec.width}x{spec.height}, "
        f"{spec.frame_count} frames, ~{total_sec:.0f}s, {size_kb} KB)"
    )
    return 0


def main() -> int:
    rc = 0
    for spec in SPECS:
        if build_one(spec) != 0:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
