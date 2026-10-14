"""Prepare a portrait photo for ASCII conversion.

Steps: remove the background (rembg), boost local contrast (CLAHE on the
L channel), then composite the subject onto a white background so the
background maps to blank characters in the ASCII ramp.

Usage:
    python scripts/prep_photo.py path/to/photo.jpg [output.png]

Requires the portrait-only deps listed in scripts/requirements.txt.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "scripts" / "source-prepped.png"


def remove_background(img: Image.Image) -> Image.Image:
    return remove(img.convert("RGBA"))


def apply_clahe(rgb: np.ndarray, clip: float = 2.0, grid: int = 8) -> np.ndarray:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid))
    merged = cv2.merge((clahe.apply(l_chan), a_chan, b_chan))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)


def composite_on_white(rgba: np.ndarray) -> np.ndarray:
    alpha = rgba[..., 3:4].astype(np.float32) / 255.0
    rgb = rgba[..., :3].astype(np.float32)
    white = np.full_like(rgb, 255.0)
    return (rgb * alpha + white * (1.0 - alpha)).clip(0, 255).astype(np.uint8)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    cutout = np.array(remove_background(Image.open(src)))
    rgb = apply_clahe(np.ascontiguousarray(cutout[..., :3]))
    rgba = np.dstack([rgb, cutout[..., 3]])
    result = composite_on_white(rgba)

    # Trim to the subject's bounding box so the portrait fills the frame.
    ys, xs = np.nonzero(cutout[..., 3] > 16)
    if len(xs) and len(ys):
        result = result[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(result).save(dst)
    print(f"wrote {dst} ({result.shape[1]}x{result.shape[0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
