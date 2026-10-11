"""
scroll_assembler.py: assembles a long-form Puranam video from a
background deity image + a tall scrolling Telugu text image (rendered
by images/purana_text_renderer.py) + background music -- the
"end-credits" scroll technique confirmed via a real test render: the
text image is overlaid on the (darkened, for readability) background
and animated upward via ffmpeg's overlay filter with a time-varying
y-expression, entering from below the frame and exiting above it.

Separate module from video/assembler.py (the Shorts assembler) because
the two are genuinely different techniques -- Shorts are one static
frame the whole duration; this is continuous motion over the full
runtime, with a landscape 16:9 canvas instead of vertical 9:16.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from ytcore.exceptions import VideoAssemblyError
from ytcore.images.purana_text_renderer import VIDEO_HEIGHT, VIDEO_WIDTH

logger = logging.getLogger(__name__)

# How much to darken the background image (0 = unchanged, more negative
# = darker) -- confirmed via a real render to give good text contrast
# while the background image stays recognizable, not blacked out.
# Darkened further from the original -0.35 (per explicit request) for
# better contrast with the regular white text -- the gold emphasis
# color still reads clearly against this darker background too.
BACKGROUND_BRIGHTNESS = -0.55
AUDIO_FADE_OUT_SECONDS = 2.0


def assemble_scroll_video(
    background_image_path: Path,
    text_image_path: Path,
    text_image_height: int,
    output_path: Path,
    duration_seconds: float,
    audio_path: Path | None = None,
    audio_volume: float = 0.5,
    video_width: int = VIDEO_WIDTH,
    video_height: int = VIDEO_HEIGHT,
) -> Path:
    """Assemble the scrolling Puranam video.

    text_image_height is the actual pixel height of text_image_path
    (returned by PuranaTextRenderer.render) -- needed to compute how
    far the overlay must travel so the text fully enters and exits the
    frame, not just an assumed/guessed distance.

    video_width/video_height default to the landscape long-form canvas
    (VIDEO_WIDTH/VIDEO_HEIGHT, 1920x1080) -- pass 1080x1920 (matching
    alert_card_renderer.py's ALERT_CARD_WIDTH/HEIGHT, the channel's
    existing Shorts canvas) for a vertical Shorts-format scroll video
    instead.
    """
    if shutil.which("ffmpeg") is None:
        raise VideoAssemblyError(
            "ffmpeg was not found on PATH. Install it and restart your terminal so PATH picks it up."
        )
    if not background_image_path.exists():
        raise VideoAssemblyError(f"Background image does not exist: {background_image_path}")
    if not text_image_path.exists():
        raise VideoAssemblyError(f"Text image does not exist: {text_image_path}")
    if audio_path is not None and not audio_path.exists():
        raise VideoAssemblyError(f"Audio file does not exist: {audio_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Starts with the text ALREADY VISIBLE at mid-frame (not fully below
    # the frame) and scrolls up from there to fully exit above -- a real
    # render with the old "start fully off-screen below" approach showed
    # 12-13 seconds of empty screen at the start, since the entrance
    # travel got stretched across the same slow, deliberate pace as the
    # rest of the scroll. Starting already on-screen removes that dead
    # time entirely.
    scroll_distance = (video_height / 2) + text_image_height
    y_expr = f"({video_height}/2)-(t/{duration_seconds})*{scroll_distance}"

    filter_complex = (
        f"[0:v]scale={video_width}:{video_height}:force_original_aspect_ratio=increase,"
        f"crop={video_width}:{video_height},eq=brightness={BACKGROUND_BRIGHTNESS}[bg];"
        f"[1:v]format=rgba[txt];"
        f"[bg][txt]overlay=x=(W-w)/2:y='{y_expr}':shortest=1[v]"
    )

    cmd: list[str] = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(background_image_path),
        "-loop", "1", "-i", str(text_image_path),
    ]

    if audio_path is not None:
        cmd += ["-stream_loop", "-1", "-i", str(audio_path)]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

    fade_start = max(duration_seconds - AUDIO_FADE_OUT_SECONDS, 0)
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-t", str(duration_seconds),
        "-af", f"volume={audio_volume},afade=t=out:st={fade_start}:d={AUDIO_FADE_OUT_SECONDS}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(output_path),
    ]

    logger.info("Assembling scroll video: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise VideoAssemblyError(
            f"ffmpeg failed (exit code {result.returncode}) assembling {output_path}. "
            f"stderr:\n{result.stderr[-2000:]}"
        )

    logger.info("Assembled scroll video: %s", output_path)
    return output_path
