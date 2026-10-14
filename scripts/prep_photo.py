"""
Prepare the portrait photo for clean ASCII conversion.

The source is a crop of a real photo (head + shoulders, 540 px square, from a
3840x5120 daylight photo with sky / trees / buildings behind), so the steps
are tuned for a photo, not a drawing:
  1. upscale, then remove the background (rembg) so the subject is isolated
  2. bilateral-smooth away JPEG noise while keeping edges
  3. stretch tones over the FACE only, so skin lands near white (sparse ascii)
     and sunglasses / beard / mouth stay dark (dense ascii)
  4. darken thin features (difference-of-gaussians ridges: eyes, brows, beard)
  5. below the chin, scale the black polo's ink down so it does not swamp the
     face, but keep its edges (collar, placket) via gradient magnitude, and
     fade it out toward the bottom
  6. add a soft silhouette rim so the outline reads, composite onto white

Output: scripts/source-prepped.png (grayscale), consumed by make_ascii_svg.py.

Usage (run locally; CI never runs the portrait pipeline):
    pip install pillow numpy opencv-python rembg
    python scripts/prep_photo.py [photo.png] [output.png]
    python scripts/make_ascii_svg.py          # -> assets/ascii-portrait.svg

FACE_BOX and CHIN_Y are in source-photo pixel coordinates; adjust them if the
source crop changes.

Adapted from AVIVASHISHTA29/AVIVASHISHTA29 (scripts/prep_photo.py).
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "source-prepped.png")

WORK_W = 900                  # working resolution (px) after upscaling
FACE_BOX = (142, 110, 402, 380)  # x0, y0, x1, y1 of the face in the source photo
CHIN_Y = 395                     # source y where the polo starts
FACE_PCT = (8, 55)               # face percentiles mapped to full ink / blank
GAMMA = 1.5                      # >1 thins mid tones so skin reads light
LINE_WEIGHT = 0.4                # how hard thin dark features are inked
SHIRT_SCALE = 0.30               # ink multiplier for the polo below the chin
EDGE_WEIGHT = 0.8                # ink for polo edges (collar, placket)
EDGE_DIV = 25.0                  # gradient magnitude that counts as a full edge
FADE = 0.18                      # bottom fraction of the image that fades out
RIM = 0.85                       # silhouette outline ink
RIM_PX = 11                      # outline thickness at working resolution

# 1. upscale + cut out the subject
im = Image.open(INP).convert("RGB")
sc = WORK_W / im.width
im = im.resize((WORK_W, round(im.height * sc)), Image.BICUBIC)
cut = remove(im.convert("RGBA"))
alpha = np.array(cut.split()[-1]).astype(np.float32) / 255.0   # 0 = background

# 2. smooth noise, keep edges
gray = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
gray = cv2.bilateralFilter(gray, 9, 25, 9).astype(np.float32)

# 3. tone stretch over the face, inverted into "ink" (1 = densest char)
fx0, fy0, fx1, fy1 = (round(v * sc) for v in FACE_BOX)
face = gray[fy0:fy1, fx0:fx1][alpha[fy0:fy1, fx0:fx1] > 0.5]
lo, hi = np.percentile(face, FACE_PCT)
ink = (1.0 - np.clip((gray - lo) / (hi - lo), 0, 1)) ** GAMMA

# 4. dark-on-light ridges -> more ink
fine = cv2.GaussianBlur(gray, (0, 0), 4)
coarse = cv2.GaussianBlur(gray, (0, 0), 14)
ink = np.clip(ink + LINE_WEIGHT * np.clip((coarse - fine) / 25.0, 0, 1), 0, 1)

# 5. tame the polo below the chin (keep its edges), fade out at the bottom
H = ink.shape[0]
ys = np.arange(H, dtype=np.float32)[:, None]
below = np.clip((ys - CHIN_Y * sc) / 30.0, 0, 1)
blurred = cv2.GaussianBlur(gray, (0, 0), 3)
grad = np.hypot(cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3),
                cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3))
edges = np.clip(grad / EDGE_DIV, 0, 1)
ink = ink * (1 - below) + np.maximum(ink * SHIRT_SCALE, edges * EDGE_WEIGHT) * below
fade = 1 - np.clip((ys - H * (1 - FADE)) / (H * FADE), 0, 1)
ink *= fade

# 6. silhouette rim, then mask to the subject (feathered to avoid a halo)
solid = (alpha > 0.5).astype(np.uint8)
rim = cv2.morphologyEx(solid, cv2.MORPH_GRADIENT, np.ones((RIM_PX, RIM_PX), np.uint8))
ink = np.maximum(ink, rim.astype(np.float32) * RIM * fade)
ink *= cv2.GaussianBlur(alpha, (0, 0), 1.5)

out = ((1.0 - ink) * 255).astype(np.uint8)   # make_ascii_svg: dark = dense
Image.fromarray(out, mode="L").save(OUT)
print("wrote", OUT, out.shape)
