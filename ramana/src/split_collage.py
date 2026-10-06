"""Cut a collage image into separate photos.

  python -m src.split_collage collage.jpg                 # auto detect (photos separated by a plain background or gaps)
  python -m src.split_collage collage.jpg --grid 2x5      # fallback: equal grid, rows x columns
  python -m src.split_collage collage.jpg --out assets/backgrounds --prefix photo

Auto mode finds the plain border or gap colour, treats everything else as photos, and cuts each
connected block. Results are saved as photo_01.jpg, photo_02.jpg ... in reading order.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def _bg_colour(arr):
    edge = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    vals, counts = np.unique(edge.reshape(-1, 3) // 8, axis=0, return_counts=True)
    return vals[counts.argmax()] * 8 + 4


def auto_boxes(img, expected=None, min_area=0.01):
    arr = np.asarray(img.convert("RGB")).astype(np.int16)
    bg = _bg_colour(arr)
    for thr in (40, 28, 55, 20, 70):
        mask = np.abs(arr - bg).sum(axis=2) > thr
        mask = ndi.binary_closing(mask, structure=np.ones((9, 9)))
        mask = ndi.binary_fill_holes(mask)
        mask = ndi.binary_opening(mask, structure=np.ones((5, 5)))
        lab, n = ndi.label(mask)
        boxes = []
        for i, sl in enumerate(ndi.find_objects(lab), 1):
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            if h * w >= min_area * arr.shape[0] * arr.shape[1] and (lab[sl] == i).mean() > 0.6:
                boxes.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
        if expected is None and boxes or len(boxes) == expected:
            return boxes
    return boxes


def _clusters(idx, max_width=10):
    out, cur = [], []
    for i in idx:
        if cur and i - cur[-1] > 2:
            out.append(cur); cur = []
        cur.append(int(i))
    if cur:
        out.append(cur)
    return [(c[0] + c[-1]) // 2 for c in out if len(c) <= max_width]


def gold_grid_boxes(img, keep_top=None, pad=4, thresh=0.5):
    """Cards separated by thin gold lines (as in captioned collages).
    keep_top: pixels of each card to keep from its top edge (cuts off the caption bar under the photo)."""
    a = np.asarray(img.convert("RGB")).astype(int)
    gold = (a[..., 0] > 150) & (a[..., 1] > 110) & (a[..., 2] < 110) & (a[..., 0] - a[..., 2] > 80)
    h, w = gold.shape
    xs = [0] + _clusters(np.where(gold.mean(axis=0) > thresh)[0]) + [w]
    ys = [0] + _clusters(np.where(gold.mean(axis=1) > thresh)[0]) + [h]
    xs = sorted(set(x for x in xs if x <= 2 or x >= w - 3 or True))
    xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 40]
    ys = [y for i, y in enumerate(sorted(set(ys))) if i == 0 or y - sorted(set(ys))[i - 1] > 40]
    if xs[-1] < w - 40:
        xs.append(w)
    if ys[-1] < h - 40:
        ys.append(h)
    boxes = []
    for r in range(len(ys) - 1):
        for c in range(len(xs) - 1):
            x0 = xs[c] + pad; x1 = xs[c + 1] - pad
            y0 = ys[r] + pad; y1 = (ys[r] + keep_top) if keep_top else ys[r + 1] - pad
            boxes.append((x0, y0, min(x1, w), min(y1, ys[r + 1] - pad)))
    return boxes


def grid_boxes(img, rows, cols):
    w, h = img.size
    return [(c * w // cols, r * h // rows, (c + 1) * w // cols, (r + 1) * h // rows)
            for r in range(rows) for c in range(cols)]


def reading_order(boxes):
    if not boxes:
        return boxes
    med_h = np.median([b[3] - b[1] for b in boxes])
    return sorted(boxes, key=lambda b: (round((b[1] + b[3]) / 2 / (med_h * 0.8)), b[0]))


def trim_edges(img, pad=3):
    """Shave a few pixels so no gap colour or border line leaks into the cut photo."""
    w, h = img.size
    return img.crop((pad, pad, w - pad, h - pad)) if min(w, h) > 40 else img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--grid", help="ROWSxCOLS, e.g. 2x5")
    ap.add_argument("--gold-grid", action="store_true", help="cards separated by thin gold lines")
    ap.add_argument("--keep-top", type=int, help="with --gold-grid: pixels to keep from the top of each card (removes captions)")
    ap.add_argument("--expected", type=int, help="number of photos you expect (helps auto detection)")
    ap.add_argument("--out", default="assets/backgrounds")
    ap.add_argument("--prefix", default="photo")
    args = ap.parse_args()

    img = Image.open(args.image).convert("RGB")
    if args.gold_grid:
        boxes = gold_grid_boxes(img, args.keep_top)
    elif args.grid:
        r, c = (int(x) for x in args.grid.lower().split("x"))
        boxes = grid_boxes(img, r, c)
    else:
        boxes = auto_boxes(img, args.expected)
    boxes = reading_order(boxes)
    if not boxes:
        raise SystemExit("No photos detected. Try --grid ROWSxCOLS.")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for i, b in enumerate(boxes, 1):
        crop = img.crop(b) if args.gold_grid else trim_edges(img.crop(b))
        crop.save(out / f"{args.prefix}_{i:02d}.jpg", quality=95)
        print(f"{args.prefix}_{i:02d}.jpg  box={b}  size={crop.size}")
    print(f"Saved {len(boxes)} photos to {out}")


if __name__ == "__main__":
    main()
