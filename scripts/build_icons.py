#!/usr/bin/env python3
"""Rasterize design/mark.svg into the extension's PNG icon sizes.

The extension directory is deliberately buildless, so these PNGs are generated
here by a human-run script and committed. Nothing rasterizes at load time.

This machine has no rsvg-convert, inkscape, ImageMagick, cairosvg or Pillow, and
the extension tree must stay free of npm dependencies. It does have a Chrome
binary cached by puppeteer, so Chrome's headless --screenshot flag does the
rasterizing and the rest is pure standard library.

Two things learned the hard way, both encoded below:

  * Chrome will not honour a --window-size below its minimum. Asking for a
    16x16 screenshot makes it hang indefinitely rather than fail. So we render
    ONCE at a comfortable size and downsample.
  * Headless Chrome runs against a virtual screen that defaults to 800x600. A
    window taller than that ALSO hangs -- 768x768 silently never returns. The
    render size must stay inside the screen, so we set the screen explicitly
    and keep the render well under it.
  * A cold Chrome start with a fresh profile costs ~20s. Three sizes meant three
    launches. One launch is the whole difference between fast and painful.

384 is chosen because it divides evenly by 3, 8 and 24 -> 128, 48 and 16, so
every downsample is an exact integer box filter with no resampling artefacts,
and because it sits safely inside the virtual screen.

Usage:
    python3 scripts/build_icons.py            # write extension/icons/*.png
    python3 scripts/build_icons.py --check    # verify existing icons, write nothing
"""

from __future__ import annotations

import argparse
import glob
import os
import struct
import subprocess
import sys
import tempfile
import zlib

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK_SVG = os.path.join(REPO_ROOT, "design", "mark.svg")
ICON_DIR = os.path.join(REPO_ROOT, "extension", "icons")

RENDER_SIZE = 384
# Headless Chrome's virtual screen defaults to 800x600; a window larger than the
# screen hangs instead of failing. Set it explicitly so RENDER_SIZE has headroom.
SCREEN_SIZE = 1200
SIZES = (16, 48, 128)

# A near-blank PNG of these sizes is what we are replacing (428/175/95 bytes).
# Real gradient artwork lands far above this; the floor catches a silent
# regression back to blank output.
MIN_BYTES = {16: 200, 48: 500, 128: 1500}

CHROME_GLOBS = [
    os.path.expanduser("~/.cache/puppeteer/chrome/*/chrome-linux64/chrome"),
    os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome"),
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_chrome() -> str:
    for pattern in CHROME_GLOBS:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]
    sys.exit(
        "No Chrome binary found. Looked in:\n  "
        + "\n  ".join(CHROME_GLOBS)
        + "\nInstall Chrome, or run `npx puppeteer browsers install chrome`."
    )


# --------------------------------------------------------------------------
# Minimal PNG codec (8-bit RGBA, non-interlaced -- what Chrome emits)
# --------------------------------------------------------------------------

def png_read_rgba(path: str) -> tuple[int, int, bytearray]:
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")

    width = height = 0
    idat = bytearray()
    pos = 8
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", body[:10])
            if depth != 8 or color != 6:
                raise ValueError(
                    f"{path}: expected 8-bit RGBA, got depth={depth} colour={color}"
                )
            if body[12] != 0:
                raise ValueError(f"{path}: interlaced PNGs are not supported")
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length

    raw = zlib.decompress(bytes(idat))
    stride = width * 4
    out = bytearray(height * stride)

    pos = 0
    for y in range(height):
        ftype = raw[pos]
        pos += 1
        row = bytearray(raw[pos:pos + stride])
        pos += stride
        base = y * stride
        prior = out[base - stride:base] if y else bytes(stride)

        if ftype == 0:
            pass
        elif ftype == 1:
            for i in range(4, stride):
                row[i] = (row[i] + row[i - 4]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                row[i] = (row[i] + prior[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = row[i - 4] if i >= 4 else 0
                row[i] = (row[i] + ((left + prior[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                a = row[i - 4] if i >= 4 else 0
                b = prior[i]
                c = prior[i - 4] if i >= 4 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pred) & 0xFF
        else:
            raise ValueError(f"{path}: unknown filter type {ftype}")

        out[base:base + stride] = row

    return width, height, out


def png_write_rgba(path: str, width: int, height: int, pixels: bytes) -> None:
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)  # filter: None
        raw += pixels[y * stride:(y + 1) * stride]

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(png)


def box_downsample(src_w: int, src: bytes, factor: int) -> tuple[int, bytes]:
    """Exact integer box filter, averaging in premultiplied alpha.

    Averaging straight RGBA darkens edge pixels wherever alpha varies, because
    transparent pixels contribute their (meaningless) colour. Premultiplying
    first and dividing back out afterwards keeps the rounded corners clean.
    """
    dst_w = src_w // factor
    out = bytearray(dst_w * dst_w * 4)
    area = factor * factor

    for y in range(dst_w):
        for x in range(dst_w):
            r = g = b = a = 0
            for sy in range(y * factor, (y + 1) * factor):
                row = sy * src_w * 4
                for sx in range(x * factor, (x + 1) * factor):
                    i = row + sx * 4
                    alpha = src[i + 3]
                    r += src[i] * alpha
                    g += src[i + 1] * alpha
                    b += src[i + 2] * alpha
                    a += alpha
            o = (y * dst_w + x) * 4
            if a:
                out[o] = min(255, r // a)
                out[o + 1] = min(255, g // a)
                out[o + 2] = min(255, b // a)
            out[o + 3] = a // area

    return dst_w, bytes(out)


# --------------------------------------------------------------------------

def render_master(chrome: str, out_path: str) -> None:
    with open(MARK_SVG, "r", encoding="utf-8") as handle:
        svg = handle.read()

    # Inlined rather than <img src=> so Chrome cannot treat it as a
    # cross-origin resource, and so this works from any cwd.
    html = (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        "html,body{margin:0;padding:0;background:transparent;overflow:hidden}"
        f"svg{{display:block;width:{RENDER_SIZE}px;height:{RENDER_SIZE}px}}"
        "</style></head><body>" + svg + "</body></html>"
    )

    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "page.html")
        with open(page, "w", encoding="utf-8") as handle:
            handle.write(html)

        result = subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                # Without this the output comes back scaled by the device pixel
                # ratio and the icon is silently the wrong size.
                "--force-device-scale-factor=1",
                # Preserves transparency outside the mark's rounded corners.
                "--default-background-color=00000000",
                f"--screenshot={out_path}",
                f"--window-size={RENDER_SIZE},{RENDER_SIZE}",
                f"--ozone-override-screen-size={SCREEN_SIZE},{SCREEN_SIZE}",
                # Deliberately NOT passing --user-data-dir. Pointing it at a
                # fresh temp profile makes this invocation hang forever instead
                # of rendering (verified: exit 124 with, clean render without).
                page,
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

    # Chrome under WSL prints dbus connection errors to stderr on every run and
    # still writes a correct file. Judge the artifact, never the chatter.
    if not os.path.exists(out_path):
        sys.exit(
            f"Chrome produced no screenshot.\n"
            f"exit={result.returncode}\nstderr:\n{result.stderr}"
        )


def validate(size: int, path: str) -> list[str]:
    if not os.path.exists(path):
        return [f"{path} is missing"]

    problems = []
    with open(path, "rb") as handle:
        header = handle.read(24)
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (size, size):
        problems.append(f"{path} decodes at {width}x{height}, expected {size}x{size}")

    actual = os.path.getsize(path)
    if actual < MIN_BYTES[size]:
        problems.append(
            f"{path} is {actual} bytes, under the {MIN_BYTES[size]} floor "
            "-- this is what a blank icon looks like"
        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the committed icons without regenerating them",
    )
    args = parser.parse_args()

    if not args.check:
        if not os.path.exists(MARK_SVG):
            sys.exit(f"Missing {MARK_SVG}")
        chrome = find_chrome()
        os.makedirs(ICON_DIR, exist_ok=True)
        print(f"Chrome:  {chrome}")

        with tempfile.TemporaryDirectory() as tmp:
            master = os.path.join(tmp, "master.png")
            render_master(chrome, master)
            width, height, pixels = png_read_rgba(master)
            print(f"Master:  {width}x{height} ({os.path.getsize(master)} bytes)")

            for size in SIZES:
                factor = width // size
                if width % size:
                    sys.exit(f"{width} is not an integer multiple of {size}")
                dst_w, dst = box_downsample(width, pixels, factor)
                out_path = os.path.join(ICON_DIR, f"{size}.png")
                png_write_rgba(out_path, dst_w, dst_w, dst)
                print(f"  wrote {out_path} ({os.path.getsize(out_path)} bytes)")

    problems = []
    for size in SIZES:
        problems.extend(validate(size, os.path.join(ICON_DIR, f"{size}.png")))

    if problems:
        print("\nIcon validation FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("Icons OK: " + ", ".join(f"{s}x{s}" for s in SIZES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
