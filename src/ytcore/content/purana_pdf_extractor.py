"""
purana_pdf_extractor.py: extracts Telugu text from a page range in the
source Puranam PDF via OCR (Tesseract), NOT via the PDF's own internal
text layer.

WHY OCR, NOT pdftotext: confirmed via direct testing that this specific
PDF (Astadasa_Puranalu.pdf) uses a legacy custom font encoding where
each glyph's character code does NOT map to standard Unicode Telugu --
pdftotext extraction produces garbled, unusable output even though the
PAGES THEMSELVES render correctly (the embedded font displays properly
when rasterized; only the underlying text-extraction mapping is
broken). OCR reads the actual rendered glyph shapes instead of trusting
that broken mapping, so it works regardless of the font encoding issue.

ACCURACY: a direct comparison against a manually-proofread page (the
Manasadevi episode's page 1300) showed OCR output was highly accurate,
including several spots where an earlier MANUAL visual transcription
had actually introduced errors that OCR got right. Not perfect --
occasional single-character glitches remain (a stray symbol, a dropped
vowel-length mark) -- so treat this as a strong first draft that still
deserves a quick proofread before going into a real video, not as a
guaranteed-correct final source.

WHAT THIS DOES NOT AUTOMATE: finding WHICH page range holds a good,
self-contained story (with a natural beginning/end, ideally closing in
its own mantra/stotram) still needs a human decision -- that's a
judgment call about content and story structure, not a text-extraction
problem. This tool removes the slow "manually type out what I see in
the image" bottleneck once you already know which pages to pull from.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from ytcore.exceptions import AppError

logger = logging.getLogger(__name__)

RASTER_DPI = 200  # higher than the 150 used for visual spot-checks earlier -- more DPI generally helps OCR accuracy

# Systematic, high-confidence OCR mistakes observed repeatedly across
# real extractions -- NOT a general spell-checker, just specific known
# confusions Tesseract's Telugu model makes consistently (e.g. the
# "త్క"/"త్మ" conjunct forms look similar to it). Confirmed via a real
# extraction: "జరత్మారు" (wrong) appeared 10 times vs "జరత్కారు"
# (correct) only 2 times for the same word, same page range. Extend
# this dict only when you've directly confirmed a pattern is both
# systematic (not a one-off) and safe to blanket-replace.
_KNOWN_OCR_CORRECTIONS: dict[str, str] = {
    "జరత్మారు": "జరత్కారు",
}


def _apply_known_corrections(text: str) -> str:
    for wrong, right in _KNOWN_OCR_CORRECTIONS.items():
        text = text.replace(wrong, right)
    return text


def extract_pages_as_paragraphs(pdf_path: Path, first_page: int, last_page: int) -> list[str]:
    """OCR every page in [first_page, last_page] (1-indexed, inclusive,
    matching pdftoppm's own numbering) and return the result as a list
    of paragraphs (split on blank lines within and across pages).

    Strips the running page header (this book repeats the current
    Purana's name at the top of every page) and a lone page-number
    footer, based on the consistent single-column layout confirmed via
    direct inspection of this book -- if a different Purana section
    uses a different layout, spot-check the output before trusting it.
    """
    if shutil.which("pdftoppm") is None:
        raise AppError("pdftoppm not found. Install poppler-utils (apt install poppler-utils).")
    if shutil.which("tesseract") is None:
        raise AppError("tesseract not found. Install it (apt install tesseract-ocr tesseract-ocr-tel).")
    if not pdf_path.exists():
        raise AppError(f"PDF does not exist: {pdf_path}")

    all_lines: list[str] = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raster_prefix = tmp_path / "page"

        raster_cmd = [
            "pdftoppm", "-jpeg", "-r", str(RASTER_DPI),
            "-f", str(first_page), "-l", str(last_page),
            str(pdf_path), str(raster_prefix),
        ]
        result = subprocess.run(raster_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AppError(f"pdftoppm failed: {result.stderr}")

        page_images = sorted(tmp_path.glob("page-*.jpg"))
        if not page_images:
            raise AppError(f"No pages rendered for range {first_page}-{last_page}.")

        for image_path in page_images:
            ocr_cmd = ["tesseract", str(image_path), "stdout", "-l", "tel"]
            ocr_result = subprocess.run(ocr_cmd, capture_output=True, text=True)
            if ocr_result.returncode != 0:
                raise AppError(f"tesseract failed on {image_path}: {ocr_result.stderr}")

            page_lines = [line.strip() for line in ocr_result.stdout.splitlines()]
            page_lines = _strip_header_and_footer(page_lines)
            all_lines.extend(page_lines)
            logger.info("OCR'd %s (%d lines after header/footer strip).", image_path.name, len(page_lines))

    return _lines_to_paragraphs(all_lines)


def _strip_header_and_footer(lines: list[str]) -> list[str]:
    """Drop leading blank lines, the running header (first non-blank
    line), and a trailing lone page-number footer -- confirmed layout
    pattern from direct inspection of this book's pages."""
    lines = list(lines)
    while lines and not lines[0]:
        lines.pop(0)
    if lines:
        lines.pop(0)  # running header line
    while lines and not lines[-1]:
        lines.pop()
    if lines and lines[-1].strip().isdigit():
        lines.pop()  # page number footer
        while lines and not lines[-1]:  # a blank line can be exposed above the footer
            lines.pop()
    return lines


def _lines_to_paragraphs(lines: list[str]) -> list[str]:
    """Join lines into paragraphs, splitting on blank lines (Tesseract
    preserves the source's paragraph spacing as blank OCR'd lines)."""
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            paragraphs.append(_apply_known_corrections(" ".join(current)))
            current = []
    if current:
        paragraphs.append(_apply_known_corrections(" ".join(current)))
    return paragraphs
