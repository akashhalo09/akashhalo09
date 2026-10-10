"""Prep a photo for the ASCII portrait. Run once per photo, locally.

    python scripts/prep_photo.py source-photo.png [--crop x0,y0,x1,y1]

Removes the background, boosts local contrast and puts the subject on pure white
(white maps to the blank end of the character ramp). Writes source-prepped.png.
Crop to a square around the face for a close-up; then run scripts/make_ascii_svg.py.
"""
import argparse

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

MIN_SIDE = 720  # small crops are upscaled so the cutout and contrast steps have pixels to work with

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

cutout = remove(img, session=new_session(args.model))
alpha = np.array(cutout)[:, :, 3]

white = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
white.alpha_composite(cutout)
gray = cv2.cvtColor(np.array(white.convert("RGB")), cv2.COLOR_RGB2GRAY)

# Flat lighting turns a face into one dark blob; CLAHE brings the features back.
gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
gray[alpha < 128] = 255  # CLAHE can tint the background; force it back to blank

Image.fromarray(gray).save(args.out)
print(f"wrote {args.out} ({gray.shape[1]}x{gray.shape[0]})")
