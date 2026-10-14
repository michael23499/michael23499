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
  7. beard: fill a hand-traced beard + mustache shape with a dense, coherent
     ink mass (clean jaw edge), cutting the mouth out so the smile stays open
  8. optional hacker hood (HOOD=1): zoom the portrait out a little and draw a
     procedural hood over the head -- rounded peak, sides draping into the
     shoulders, soft folds, a light rim around the face opening and a shadow
     falling on the forehead under it

Output: scripts/source-prepped.png (grayscale), consumed by make_ascii_svg.py.

Usage (run locally; CI never runs the portrait pipeline):
    pip install pillow numpy opencv-python rembg
    python scripts/prep_photo.py [photo.png] [output.png]
    python scripts/make_ascii_svg.py          # -> assets/ascii-portrait.svg

FACE_BOX and CHIN_Y are in source-photo pixel coordinates; the beard / mouth
polygons and hood geometry are in working (WORK_W) pixels. Adjust them if the
source crop changes. Every HOOD_* / BEARD* knob can be overridden from the
environment, e.g.  HOOD=0 python scripts/prep_photo.py  for the plain version.

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


def knob(name, default):
    """Constant with an optional environment override (same type)."""
    return type(default)(os.environ.get(name, default))


BEARD = knob("BEARD", 1)              # 0 = keep the raw photo beard
BEARD_INK = knob("BEARD_INK", 0.66)    # base ink of the beard mass
BEARD_TEXTURE = knob("BEARD_TEXTURE", 0.30)  # extra ink where the photo is darker
MOUTH_LIGHT = knob("MOUTH_LIGHT", 0.05)  # ink multiplier inside the mouth (smile gap)
MOUTH_GROW = knob("MOUTH_GROW", 1.45)     # vertical scale of the mouth cut-out (readability)
# working-px outline: cheek tops -> mustache -> cheek tops -> along the jaw
BEARD_POLY = [(266, 462), (350, 452), (385, 430), (450, 422), (520, 427), (566, 450),
              (626, 458), (620, 490), (606, 522), (572, 578), (522, 622), (460, 642),
              (400, 642), (338, 622), (294, 572), (270, 512)]
MOUTH_POLY = [(352, 466), (382, 451), (450, 443), (520, 449), (561, 463),
              (530, 491), (450, 503), (385, 493)]   # lips + teeth (smile gap)

HOOD = knob("HOOD", 1)                # 0 = plain portrait, no hood
HOOD_ZOOM = knob("HOOD_ZOOM", 0.82)    # portrait scale inside the canvas
HOOD_W = knob("HOOD_W", 285)          # half-width of the hood at the temples
HOOD_PEAK = knob("HOOD_PEAK", 95)      # how far the peak rises above the head
HOOD_OPEN_W = knob("HOOD_OPEN_W", 205)  # face opening half-width
HOOD_OPEN_TOP = knob("HOOD_OPEN_TOP", 150)  # face opening top (working y)
HOOD_OPEN_BOT = knob("HOOD_OPEN_BOT", 700)  # face opening bottom (working y)
HOOD_INK = knob("HOOD_INK", 0.55)      # base fabric ink
HOOD_FOLDS = knob("HOOD_FOLDS", 0.22)  # fold shading amplitude
HOOD_SHADOW = knob("HOOD_SHADOW", 0.55)  # forehead shadow under the rim
HEAD_TOP_Y, HEAD_CX = 70, 450          # working px: top of the head, face centre

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

# 7. beard: one dense mass with a clean edge, mouth cut out
if BEARD:
    beard = np.zeros_like(ink, np.uint8)
    cv2.fillPoly(beard, [np.array(BEARD_POLY, np.int32)], 1)
    mouth = np.zeros_like(ink, np.uint8)
    mp = np.array(MOUTH_POLY, np.float32)
    mp[:, 1] = mp[:, 1].mean() + (mp[:, 1] - mp[:, 1].mean()) * MOUTH_GROW
    cv2.fillPoly(mouth, [mp.astype(np.int32)], 1)
    beard &= 1 - mouth
    soft = cv2.GaussianBlur(beard.astype(np.float32), (0, 0), 2.5)
    darker = np.clip((hi - cv2.GaussianBlur(gray, (0, 0), 4)) / (hi - lo), 0, 1)
    beard_ink = np.clip(BEARD_INK + BEARD_TEXTURE * darker, 0, 1)
    ink = ink * (1 - soft) + beard_ink * soft
    msoft = cv2.GaussianBlur(mouth.astype(np.float32), (0, 0), 2.0)
    ink *= 1 - (1 - MOUTH_LIGHT) * msoft             # keep the smile open

# 8. hacker hood
if HOOD:
    S = ink.shape[0]
    small = cv2.resize(ink, None, fx=HOOD_ZOOM, fy=HOOD_ZOOM, interpolation=cv2.INTER_AREA)
    ox, oy = (S - small.shape[1]) // 2, S - small.shape[0]     # bottom-aligned
    canvas = np.zeros_like(ink)
    canvas[oy:oy + small.shape[0], ox:ox + small.shape[1]] = small
    ink = canvas

    def T(x, y):                       # working px -> zoomed canvas px
        return ox + HOOD_ZOOM * x, oy + HOOD_ZOOM * y

    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    z = HOOD_ZOOM
    cx, _ = T(HEAD_CX, 0)
    # outer silhouette: dome over the head, straight sides, flaring into the shoulders
    top = T(0, HEAD_TOP_Y - HOOD_PEAK)[1]
    _, mid = T(0, 330)
    w = HOOD_W * z
    dome = ((xx - cx) / w) ** 2 + ((yy - mid) / (mid - top)) ** 2 <= 1
    _, drop = T(0, 560)
    t = np.clip((yy - drop) / (S - drop), 0, 1)
    half = w + (S * 0.62 - w) * t ** 1.6                  # sides widen into shoulders
    body = (yy >= mid) & (np.abs(xx - cx) <= half)
    outer = (dome | body).astype(np.float32)
    # face opening
    _, otop = T(0, HOOD_OPEN_TOP)
    _, obot = T(0, HOOD_OPEN_BOT)
    ocy, ory, orx = (otop + obot) / 2, (obot - otop) / 2, HOOD_OPEN_W * z
    r = np.sqrt(((xx - cx) / orx) ** 2 + ((yy - ocy) / ory) ** 2)   # <1 inside
    opening = (r < 1).astype(np.float32)
    fabric = outer * (1 - opening)
    fabric = cv2.GaussianBlur(fabric, (0, 0), 1.5)
    fabric *= 1 - np.clip((yy - S * (1 - FADE)) / (S * FADE), 0, 1)   # same bottom fade
    # shading: distance from the opening edge drives folds + an inner shadow
    d = (r - 1) * min(orx, ory)                          # px outside the opening
    folds = HOOD_FOLDS * np.sin(d / 16.0 + 0.6 * np.sin((xx - cx) / 45.0))
    deep = 0.12 * np.exp(-np.maximum(d - 18, 0) / 40.0)     # darker just past the rim
    cloth = np.clip(HOOD_INK + folds + deep, 0, 1)
    rim_band = np.exp(-(d / 7.0) ** 2) * (d > -2)          # light edge of the hood
    cloth = cloth * (1 - 0.55 * rim_band)
    # the polo below merges into the hoodie body
    ink = ink * (1 - fabric) + np.maximum(cloth, ink) * fabric
    # forehead shadow under the rim (strongest at the top of the opening)
    inside = np.clip(-d, 0, None)
    topw = np.clip((ocy - yy) / ory, 0, 1) ** 0.7
    shade = HOOD_SHADOW * np.exp(-inside / 45.0) * topw * opening
    ink = np.maximum(ink, shade)

out = ((1.0 - ink) * 255).astype(np.uint8)   # make_ascii_svg: dark = dense
Image.fromarray(out, mode="L").save(OUT)
print("wrote", OUT, out.shape)
