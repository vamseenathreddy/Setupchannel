"""One-off: cut the people out of their photos (GrabCut seeded by a face-centred rectangle) into transparent PNGs."""
import sys
import cv2
import numpy as np
from PIL import Image

U = "/root/.claude/uploads/61aeb768-bbd6-5eed-831c-fcae51d72ca4/"
JOBS = {  # name: (file, rect as fractions x0,y0,x1,y1 of the subject, max side)
    "cbn": ("5b583899-image.jpg", (0.05, 0.02, 0.97, 1.0)),
    "lokesh": ("caebb933-image.webp", (0.05, 0.02, 0.95, 1.0)),
    "ntr": ("8b9c2919-image.jpg", (0.52, 0.0, 1.0, 1.0)),
    "me": ("cc2fb980-image.jpg", (0.12, 0.12, 0.98, 1.0)),
}
OUT = "channels/trending/assets/people/"


def cut(name, f, r):
    im = Image.open(U + f).convert("RGB")
    if name == "ntr":  # right half only = the turban portrait
        w, h = im.size
        im = im.crop((int(w * 0.5) + 4, 4, w - 2, h - 4))
        r = (0.04, 0.02, 0.96, 1.0)
    if name == "lokesh":  # head and shoulders only: leaves out the flags and the mic
        w, h = im.size
        im = im.crop((int(w * 0.22), 0, int(w * 0.76), h))
        r = (0.02, 0.02, 0.98, 1.0)
    im.thumbnail((900, 900))
    a = np.array(im)[:, :, ::-1].copy()
    h, w = a.shape[:2]
    rect = (int(w * r[0]), int(h * r[1]), int(w * (r[2] - r[0])), int(h * (r[3] - r[1])))
    mask = np.zeros(a.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(a, mask, rect, bg, fg, 8, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        m = np.where(lab == 1 + np.argmax(stats[1:, 4]), 255, 0).astype(np.uint8)
    m = cv2.GaussianBlur(m, (5, 5), 0)
    rgba = np.dstack([a[:, :, ::-1], m])
    img = Image.fromarray(rgba, "RGBA")
    img = img.crop(img.getbbox())
    img.save(OUT + name + ".png")
    print(name, img.size)


for k in (sys.argv[1:] or JOBS):
    cut(k, *JOBS[k])
