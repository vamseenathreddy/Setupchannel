"""Upscale small photos 4x with the EDSR super-resolution model (run locally once, not in GitHub Actions).

  pip install opencv-contrib-python-headless
  # download EDSR_x4.pb from https://github.com/Saafke/EDSR_Tensorflow/tree/master/models
  python -m src.upscale_photos assets/backgrounds --model EDSR_x4.pb

Files are replaced in place. Photos already 1000 px wide or more are skipped.
"""
import argparse
from pathlib import Path

import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--model", required=True)
    ap.add_argument("--min-width", type=int, default=1000)
    args = ap.parse_args()

    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(args.model)
    sr.setModel("edsr", 4)
    for p in sorted(Path(args.folder).glob("*.jpg")):
        img = cv2.imread(str(p))
        if img.shape[1] >= args.min_width:
            print("skip", p.name)
            continue
        out = sr.upsample(img)
        cv2.imwrite(str(p), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print("upscaled", p.name, img.shape[1::-1], "->", out.shape[1::-1])


if __name__ == "__main__":
    main()
