"""
telugu_voiceover.py: generates Telugu voiceover narration via Sarvam
AI's Text-to-Speech API, for narrating Puranam story text aloud
alongside the scrolling text in the long-form video pipeline.

API parameter names verified directly against the INSTALLED SDK version
via inspect.signature (not just docs, since the docs snippet used a
slightly different/older parameter name and voice roster than what
ships in sarvamai 0.1.34):
    from sarvamai import SarvamAI
    client = SarvamAI(api_subscription_key=...)
    response = client.text_to_speech.convert(
        text=..., language_code="te-IN", model="bulbul:v3", speaker="priya",
        output_audio_codec="wav",
    )
    # response.audios is a list of base64-encoded audio strings (one per input)

CHARACTER LIMIT: confirmed 2,500 characters per request. Our episode
scripts run well beyond that (3,000-4,500+ characters), so text is
split into chunks at PARAGRAPH boundaries (never mid-sentence) and the
resulting audio clips are concatenated via ffmpeg into one file.
"""

from __future__ import annotations

import base64
import logging
import subprocess
import tempfile
from pathlib import Path

from ytcore.config import Settings
from ytcore.exceptions import AppError
from ytcore.images.purana_text_renderer import TextSegment

logger = logging.getLogger(__name__)

MAX_CHARS_PER_REQUEST = 2500
DEFAULT_MODEL = "bulbul:v3"
TARGET_LANGUAGE_CODE = "te-IN"


def chunk_paragraphs(paragraphs: list[str], max_chars: int = MAX_CHARS_PER_REQUEST) -> list[str]:
    """Groups paragraphs into chunks under max_chars each, never
    splitting a paragraph mid-sentence. A single paragraph longer than
    max_chars (possible for a big shloka block) is kept whole anyway --
    sent as its own oversized chunk. Sarvam's API will reject it with a
    clear error in that rare case, which is easier to diagnose and fix
    than risking a silently garbled mid-word split."""
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def generate_voiceover(paragraphs: list[str | TextSegment], output_path: Path, settings: Settings) -> Path:
    """Generates one concatenated Telugu voiceover audio file narrating
    all the given paragraphs, via Sarvam AI's TTS API. Accepts the same
    paragraph type the text renderer uses (plain str or TextSegment) so
    the same list can drive both the on-screen text and the narration
    -- TextSegment's emphasized flag only affects on-screen styling and
    is ignored here, since narration has no equivalent "emphasis"."""
    if not settings.sarvam_api_key:
        raise AppError(
            "MAHANAVI_SARVAM_API_KEY is not set. Get a key at sarvam.ai/try/tts-api "
            "and set it in your .env file."
        )

    try:
        from sarvamai import SarvamAI
    except ImportError as exc:
        raise AppError("Missing package. Run: pip install sarvamai") from exc

    client = SarvamAI(api_subscription_key=settings.sarvam_api_key)
    plain_text_paragraphs = [p.text if isinstance(p, TextSegment) else p for p in paragraphs]
    chunks = chunk_paragraphs(plain_text_paragraphs)
    logger.info("Generating voiceover in %d chunk(s)...", len(chunks))

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        chunk_paths: list[Path] = []

        for i, chunk in enumerate(chunks):
            try:
                response = client.text_to_speech.convert(
                    text=chunk,
                    language_code=TARGET_LANGUAGE_CODE,
                    model=DEFAULT_MODEL,
                    speaker=settings.sarvam_voice,
                    output_audio_codec="wav",
                )
            except Exception as exc:
                raise AppError(
                    f"Sarvam AI TTS request failed on chunk {i + 1}/{len(chunks)}: {exc}"
                ) from exc

            chunk_path = tmp_path / f"chunk_{i:03d}.wav"
            chunk_path.write_bytes(base64.b64decode(response.audios[0]))
            chunk_paths.append(chunk_path)
            logger.info("Generated voiceover chunk %d/%d (%d chars)", i + 1, len(chunks), len(chunk))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        _concatenate_audio(chunk_paths, output_path)

    logger.info("Voiceover generated: %s", output_path)
    return output_path


def _concatenate_audio(chunk_paths: list[Path], output_path: Path) -> None:
    """Concatenates multiple audio files into one, via ffmpeg's concat demuxer."""
    if len(chunk_paths) == 1:
        cmd = ["ffmpeg", "-y", "-i", str(chunk_paths[0]), str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AppError(f"ffmpeg failed re-encoding voiceover: {result.stderr[-2000:]}")
        return

    list_file_fd = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    try:
        for p in chunk_paths:
            list_file_fd.write(f"file '{p}'\n")
        list_file_fd.close()
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_fd.name, str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AppError(f"ffmpeg failed concatenating voiceover chunks: {result.stderr[-2000:]}")
    finally:
        Path(list_file_fd.name).unlink(missing_ok=True)
