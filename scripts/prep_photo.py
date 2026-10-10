"""Prep a photo for the ASCII portrait. Run once per photo, locally.

    python scripts/prep_photo.py source-photo.png [--crop x0,y0,x1,y1]

Cuts the subject out of the background, boosts local contrast and sharpens. Writes
source-prepped.png: grayscale, with the cutout mask as alpha so the next step can
leave the background empty while still drawing dark hair.
Crop to a square around the face for a close-up; then run scripts/make_ascii_svg.py.
"""
import argparse

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

MIN_SIDE = 840  # small crops are upscaled so the cutout and contrast steps have pixels to work with

parser = argparse.ArgumentParser()
parser.add_argument("src")
parser.add_argument("--crop", help="x0,y0,x1,y1 in source pixels, applied before anything else")
parser.add_argument("--out", default="source-prepped.png")
# u2net is a ~176 MB one-time download; rembg's newer default (bria-rmbg) is ~1 GB.
parser.add_argument("--model", default="u2net")
args = parser.parse_args()

img = Image.open(args.src).convert("RGBA")
if args.crop:
    img = img.crop(tuple(int(v) for v in args.crop.split(",")))
if min(img.size) < MIN_SIDE:
    scale = MIN_SIDE / min(img.size)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)

cutout = np.array(remove(img, session=new_session(args.model)))
alpha = cutout[:, :, 3]
gray = cv2.cvtColor(cutout[:, :, :3], cv2.COLOR_RGB2GRAY)

# Flat lighting turns a face into one blob; CLAHE brings the features back. The backdrop
# is filled with the subject's median first so it doesn't skew the contrast statistics.
subject = alpha >= 128
gray[~subject] = int(np.median(gray[subject]))
gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)

# Unsharp mask: keeps edges (glasses, jawline, curls) alive through the heavy downsample.
blurred = cv2.GaussianBlur(gray, (0, 0), 3)
gray = cv2.addWeighted(gray, 1.8, blurred, -0.8, 0)

Image.fromarray(np.dstack([gray, alpha]), "LA").save(args.out)
print(f"wrote {args.out} ({gray.shape[1]}x{gray.shape[0]})")
