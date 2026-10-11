"""
mixer.py: mixes narrated voiceover audio with ducked background music
into one combined track, and measures audio duration.

Used by the long-form Puranam video pipeline now that real voiceover
narration exists: the video's scroll speed/duration is now driven by
the ACTUAL spoken length of the narration (measured here), replacing
the earlier rough words-per-minute estimate used before voiceover
existed.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from ytcore.exceptions import AppError

logger = logging.getLogger(__name__)

# Music sits well under the voiceover, not competing with it -- this is
# deliberately much lower than the 0.5 used for the Shorts (which have
# no voiceover at all, so the music itself is the only audio).
DEFAULT_MUSIC_DUCK_VOLUME = 0.12


def get_audio_duration_seconds(audio_path: Path) -> float:
    """Returns an audio file's duration in seconds via ffprobe."""
    if shutil.which("ffprobe") is None:
        raise AppError("ffprobe not found (part of ffmpeg). Install ffmpeg.")
    if not audio_path.exists():
        raise AppError(f"Audio file does not exist: {audio_path}")

    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AppError(f"ffprobe failed on {audio_path}: {result.stderr}")

    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def mix_voiceover_with_music(
    voiceover_path: Path,
    music_path: Path | None,
    output_path: Path,
    music_volume: float = DEFAULT_MUSIC_DUCK_VOLUME,
) -> Path:
    """Mixes voiceover (full volume) with looped, ducked background
    music into one combined audio track, trimmed to the voiceover's own
    length. If music_path is None, just passes the voiceover through
    unchanged (re-encoded, not just copied, so the output format is
    always consistent regardless of which path was taken)."""
    if shutil.which("ffmpeg") is None:
        raise AppError("ffmpeg not found on PATH.")
    if not voiceover_path.exists():
        raise AppError(f"Voiceover file does not exist: {voiceover_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if music_path is None:
        cmd = ["ffmpeg", "-y", "-i", str(voiceover_path), str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AppError(f"ffmpeg failed re-encoding voiceover: {result.stderr[-2000:]}")
        return output_path

    if not music_path.exists():
        raise AppError(f"Music file does not exist: {music_path}")

    voiceover_duration = get_audio_duration_seconds(voiceover_path)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(voiceover_path),
        "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex",
        f"[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-t", str(voiceover_duration),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AppError(f"ffmpeg failed mixing voiceover with music: {result.stderr[-2000:]}")

    logger.info("Mixed voiceover + music: %s (%.1fs)", output_path, voiceover_duration)
    return output_path
