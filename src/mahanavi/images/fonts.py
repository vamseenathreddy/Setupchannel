"""
FontManager: loads a single variable Telugu font file and hands out
cached ImageFont instances at whichever (weight, size) is requested.

Why RAQM matters: Telugu (like other Indic scripts) uses vowel signs and
conjunct consonants that must be *shaped* — reordered and combined by a
text-shaping engine — to render correctly. Pillow's default layout engine
draws each codepoint's glyph independently, which garbles Telugu. Passing
`layout_engine=ImageFont.Layout.RAQM` (backed by HarfBuzz) fixes this, and
is why the project depends on Pillow being built with libraqm support
(true for the standard `Pillow` wheels from PyPI on Linux/macOS/Windows).
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import ImageDraw, ImageFont
from fontTools.ttLib import TTFont

from mahanavi.exceptions import ImageRenderError

logger = logging.getLogger(__name__)

_VALID_WEIGHTS = {
    "Thin", "ExtraLight", "Light", "Regular", "Medium",
    "SemiBold", "Bold", "ExtraBold", "Black",
}


class FontManager:
    """Loads and caches Telugu font instances at requested weight/size."""

    def __init__(self, font_path: Path, fallback_path: Path | None = None) -> None:
        if not font_path.exists():
            raise ImageRenderError(
                f"Telugu font not found at {font_path}. "
                "Download a Telugu-supporting font (e.g. Noto Sans Telugu) "
                "and set MAHANAVI_TELUGU_FONT_PATH, or place it at the default path."
            )
        self._font_path = font_path
        # Ponnala (the channel's Telugu face, per explicit request
        # 2026-10-07: "use ponnala bold for every telugu text") ships only
        # a Regular weight and has NO Latin letters. So when it is the
        # primary font: (1) bold is synthesized with a thin stroke, and
        # (2) everything outside the Telugu block (Latin, digits, punctuation) is drawn with
        # Noto Sans Telugu Bold -- see the ImageDraw patch at the bottom.
        self._synthetic = "ponnala" in font_path.name.lower()
        self._fallback_path = None
        self._cmap: frozenset[int] = frozenset()
        if self._synthetic:
            fb = fallback_path or font_path.parent / "NotoSansTelugu-Variable.ttf"
            self._fallback_path = fb if fb.exists() else None
            self._cmap = frozenset(TTFont(str(font_path)).getBestCmap().keys())
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
        self._raqm_available = self._check_raqm()

    def get_font(self, size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
        if weight not in _VALID_WEIGHTS:
            raise ImageRenderError(
                f"Unknown font weight '{weight}'. Expected one of: {sorted(_VALID_WEIGHTS)}"
            )
        cache_key = (weight, size)
        if cache_key in self._cache:
            return self._cache[cache_key]

        layout_engine = ImageFont.Layout.RAQM if self._raqm_available else ImageFont.Layout.BASIC
        font = ImageFont.truetype(str(self._font_path), size, layout_engine=layout_engine)

        if self._synthetic:
            font._mv_stroke = 0  # plain Ponnala Regular, NO synthetic bold (owner, 2026-10-07: "only ponnala not ponnala bold")
            font._mv_cmap = self._cmap
            font._mv_fallback = None
            if self._fallback_path is not None:
                fb = ImageFont.truetype(str(self._fallback_path), size, layout_engine=layout_engine)
                font._mv_fallback = fb  # Latin/digits/punctuation in Noto at its default (regular) weight
            self._cache[cache_key] = font
            return font

        try:
            font.set_variation_by_name(weight)
        except OSError:
            # Not a variable font, or this weight isn't a named instance —
            # fall back to whatever the file's default weight is.
            logger.warning(
                "Font %s has no named instance '%s'; using default weight.",
                self._font_path.name, weight,
            )

        self._cache[cache_key] = font
        return font

    @staticmethod
    def _check_raqm() -> bool:
        try:
            from PIL import features
            available = bool(features.check("raqm"))
        except Exception:  # pragma: no cover - defensive, feature check itself failing
            available = False

        if not available:
            logger.warning(
                "Pillow was built without libraqm support — Telugu text will "
                "NOT shape correctly (conjuncts/vowel signs may render broken). "
                "Install a Pillow build with raqm support to fix this."
            )
        return available


# ---------------------------------------------------------------------------
# Synthetic-bold + Latin-fallback support for Ponnala (see FontManager).
# Patches ImageDraw so every renderer in the project picks it up with no
# call-site changes. Fonts that FontManager did not tag (_mv_cmap) are
# passed straight through to Pillow unchanged.
# ---------------------------------------------------------------------------
_KEEP_WITH_RUN = " \u200c\u200d"


def _runs(text: str, font) -> list[tuple[str, object, int]]:
    """Split text into (chunk, font, stroke) runs: Ponnala-covered Telugu in plain Ponnala,
    everything else in the Noto fallback."""
    cmap = font._mv_cmap
    fb = font._mv_fallback
    runs: list[list] = []
    for ch in text:
        covered = fb is None or (0x0C00 <= ord(ch) <= 0x0C7F and ord(ch) in cmap)
        if ch in _KEEP_WITH_RUN and runs:
            runs[-1][0] += ch
            continue
        f, st = (font, font._mv_stroke) if covered else (fb, 0)
        if runs and runs[-1][1] is f:
            runs[-1][0] += ch
        else:
            runs.append([ch, f, st])
    return [(r[0], r[1], r[2]) for r in runs]


_orig_text = ImageDraw.ImageDraw.text
_orig_textbbox = ImageDraw.ImageDraw.textbbox
_orig_textlength = ImageDraw.ImageDraw.textlength


def _text(self, xy, text, fill=None, font=None, *args, **kwargs):
    if font is None or not hasattr(font, "_mv_cmap") or "\n" in str(text) or args:
        return _orig_text(self, xy, text, fill, font, *args, **kwargs)
    x, y = xy
    for chunk, f, stroke in _runs(str(text), font):
        _orig_text(self, (x, y), chunk, fill, f, stroke_width=stroke, stroke_fill=fill)
        x += _orig_textlength(self, chunk, f) + 2 * stroke
    return None


def _textbbox(self, xy, text, font=None, *args, **kwargs):
    if font is None or not hasattr(font, "_mv_cmap") or "\n" in str(text) or args:
        return _orig_textbbox(self, xy, text, font, *args, **kwargs)
    x, y = xy
    box = None
    for chunk, f, stroke in _runs(str(text), font):
        b = _orig_textbbox(self, (x, y), chunk, f, stroke_width=stroke)
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        x += _orig_textlength(self, chunk, f) + 2 * stroke
    return box if box is not None else _orig_textbbox(self, xy, text, font, *args, **kwargs)


def _textlength(self, text, font=None, *args, **kwargs):
    if font is None or not hasattr(font, "_mv_cmap") or "\n" in str(text) or args:
        return _orig_textlength(self, text, font, *args, **kwargs)
    return sum(_orig_textlength(self, c, f) + 2 * st for c, f, st in _runs(str(text), font))


ImageDraw.ImageDraw.text = _text
ImageDraw.ImageDraw.textbbox = _textbbox
ImageDraw.ImageDraw.textlength = _textlength
