"""Captures every string a card renderer draws, so the description and the pinned comment can carry the full
card text (explicit request 2026-10-14: the card content must also be in the comment, with hashtags).

Works for every channel without touching each renderer: PIL's ImageDraw.text is wrapped to record strings, and
Image.save() snapshots the recorded strings (only when it saw real text, so watermark-only saves are ignored).
"""
from __future__ import annotations

import re
from typing import Any

from PIL import Image, ImageDraw

_buffer: list[tuple[float, float, str]] = []
LAST: list[str] = []
_installed = False


def _clean(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s).strip()


def _useful(s: str) -> bool:
    return len(s) >= 2 and not s.startswith("@") and any(c.isalnum() for c in s)


def _snapshot() -> None:
    """Group drawn strings into reading-order rows (same y = same row, left to right)."""
    items = sorted(_buffer, key=lambda t: (t[0], t[1]))
    _buffer.clear()
    rows: list[list[tuple[float, str]]] = []
    last_y: float | None = None
    for y, x, raw in items:
        s = _clean(raw)
        if not _useful(s) and not (s and last_y is not None):
            continue
        if last_y is None or abs(y - last_y) > 14:
            rows.append([])
            last_y = y
        if all(s != t for _, t in rows[-1]):
            rows[-1].append((x, s))
    seen: set[str] = set()
    out: list[str] = []
    for row in rows:
        line = " ".join(t for _, t in row).strip()
        if _useful(line) and line not in seen:
            seen.add(line)
            out.append(line)
    if out:
        LAST[:] = out


def _xy(xy: Any) -> tuple[float, float]:
    try:
        return float(xy[1]), float(xy[0])
    except (TypeError, IndexError, ValueError):
        return 0.0, 0.0


def install() -> None:
    global _installed
    if _installed:
        return
    _installed = True
    orig_text = ImageDraw.ImageDraw.text
    orig_multi = ImageDraw.ImageDraw.multiline_text
    orig_save = Image.Image.save

    def text(self: Any, xy: Any, text: Any, *a: Any, **k: Any) -> Any:
        if isinstance(text, str):
            y, x = _xy(xy)
            _buffer.append((y, x, text))
        return orig_text(self, xy, text, *a, **k)

    def multiline_text(self: Any, xy: Any, text: Any, *a: Any, **k: Any) -> Any:
        if isinstance(text, str):
            y, x = _xy(xy)
            _buffer.append((y, x, text))
        return orig_multi(self, xy, text, *a, **k)

    def save(self: Any, *a: Any, **k: Any) -> Any:
        _snapshot()
        return orig_save(self, *a, **k)

    ImageDraw.ImageDraw.text = text  # type: ignore[method-assign]
    ImageDraw.ImageDraw.multiline_text = multiline_text  # type: ignore[method-assign]
    Image.Image.save = save  # type: ignore[method-assign]


def lines() -> list[str]:
    return list(LAST)


def block(exclude: str = "") -> str:
    """Card text, one item per line, minus lines already present in `exclude`."""
    return "\n".join(s for s in LAST if s not in exclude)


def hashtag_line(*groups: list[str] | tuple[str, ...], limit: int = 15) -> str:
    out: list[str] = []
    low: set[str] = set()
    for g in groups:
        for t in g:
            t = t.strip()
            if not t:
                continue
            t = t if t.startswith("#") else "#" + re.sub(r"\s+", "", t)
            if t.lower() not in low and len(t) > 1:
                low.add(t.lower())
                out.append(t)
    return " ".join(out[:limit])


CHANNEL_TAGS: dict[str, list[str]] = {
    "mahanavi": ["#MahanaviSpirituals", "#Mahanavi", "#TeluguDevotional", "#SanatanaDharma", "#Shorts"],
    "mantra_sangam": ["#DivineMantraSangam", "#HindiDevotional", "#SanatanaDharma", "#Shorts"],
    "trance_beats": ["#DevotionalTranceBeats", "#HindiDevotional", "#Krishna", "#Shorts"],
    "ramana": ["#RamanaMaharshiTV", "#RamanaMaharshi", "#Advaita", "#Shorts"],
    "jesus": ["#JesusWorshipWaves", "#Jesus", "#ChristianShorts", "#Shorts"],
}


def related_from_tags(tags: list[str], limit: int = 8) -> list[str]:
    """Plain YouTube tags -> hashtag candidates (single tokens only, no spaces, short)."""
    return [t for t in tags if t and " " not in t.strip() and len(t) <= 30][:limit]


def comment(base: str, channel: str, related: list[str]) -> str:
    """Pinned comment: the card text, the existing line (if any), then channel + related hashtags."""
    parts = []
    body = block(exclude=base)
    if body:
        parts.append(body)
    if base:
        parts.append(base)
    tags = hashtag_line(CHANNEL_TAGS.get(channel, []), related, limit=15)
    if tags:
        parts.append(tags)
    return "\n\n".join(parts)[:9000]


def description(desc: str, max_len: int = 4900) -> str:
    """Description with the card text inserted before the trailing hashtag line (if there is one)."""
    body = block(exclude=desc)
    if not body:
        return desc
    head, sep, tail = desc.rstrip().rpartition("\n")
    if sep and tail.count("#") >= 2:
        base_head, base_tail = head, tail
    else:
        base_head, base_tail = desc.rstrip(), ""
    room = max_len - len(base_head) - len(base_tail) - 40
    if room < 80:
        return desc
    if len(body) > room:
        body = body[:room].rsplit("\n", 1)[0]
    out = f"{base_head}\n\n{body}"
    return f"{out}\n\n{base_tail}" if base_tail else out
