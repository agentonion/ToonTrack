#!/usr/bin/env python3
"""Build ToonTrack.icns from the menu bar eye emoji."""

import shutil
import subprocess
import sys
from pathlib import Path

from AppKit import (
    NSBezierPath,
    NSBitmapImageRep,
    NSColor,
    NSDeviceRGBColorSpace,
    NSFont,
    NSFontAttributeName,
    NSGraphicsContext,
    NSImage,
    NSMakeRect,
)
from Foundation import NSMakeSize, NSString

ROOT = Path(__file__).resolve().parent
ICONSET = ROOT / "ToonTrack.iconset"
ICNS = ROOT / "ToonTrack.icns"
EMOJI = "👀"

SIZES = {
    "icon_16x16.png": 16,
    "icon_16x16@2x.png": 32,
    "icon_32x32.png": 32,
    "icon_32x32@2x.png": 64,
    "icon_128x128.png": 128,
    "icon_128x128@2x.png": 256,
    "icon_256x256.png": 256,
    "icon_256x256@2x.png": 512,
    "icon_512x512.png": 512,
    "icon_512x512@2x.png": 1024,
}


def render_png(path: Path, size: int) -> None:
    rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, size, size, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 32
    )
    image = NSImage.alloc().initWithSize_(NSMakeSize(size, size))
    image.addRepresentation_(rep)
    image.lockFocusOnRepresentation_(rep)

    NSColor.clearColor().set()
    NSBezierPath.fillRect_(NSMakeRect(0, 0, size, size))

    font = NSFont.systemFontOfSize_(size * 0.72)
    attrs = {NSFontAttributeName: font}
    text = NSString.stringWithString_(EMOJI)
    text_size = text.sizeWithAttributes_(attrs)
    point = ((size - text_size.width) / 2, (size - text_size.height) / 2)
    text.drawAtPoint_withAttributes_(point, attrs)
    image.unlockFocus()

    png = rep.representationUsingType_properties_(4, None)
    if png is None:
        raise RuntimeError(f"Failed to render icon at {size}px")
    png.writeToFile_atomically_(str(path), True)


def main() -> int:
    if ICONSET.exists():
        shutil.rmtree(ICONSET)
    ICONSET.mkdir()

    for name, size in SIZES.items():
        render_png(ICONSET / name, size)

    if ICNS.exists():
        ICNS.unlink()

    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)],
        check=True,
    )
    print(f"Wrote {ICNS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
