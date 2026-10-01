"""
VideoAssembler: turns a static AlertCard image into an actual .mp4 Short
by shelling out to ffmpeg — looping the provided audio track (or silence,
if none given) to fill the target duration. By default there's a short
video fade-in and audio fade-out so playback doesn't start/end abruptly;
both can be set to 0 for a Short meant to be watched on loop, where any
fade would be a visible/audible seam on every repeat (see
LOOP-FRIENDLY SHORTS below).

V1 deliberately does NOT include a Ken Burns zoom/pan effect on the
image. ffmpeg's zoompan filter is notoriously finicky (version-dependent
behavior, easy to get subtly wrong) -- better to ship a simple, reliably
correct static-image-plus-audio version first and confirm the whole
pipeline (render -> assemble -> upload) actually works end to end,
THEN add a zoom effect as a refinement once the baseline is proven, not
before.

LOOP-FRIENDLY SHORTS (added per explicit request, 2026-10-01): a static
text card that takes longer to read than the video is long will make
YouTube Shorts auto-loop it -- each completed loop counts as a fresh
view, and rewatches are a real retention/satisfaction signal to the
recommendation system, so shortening a text-heavy card deliberately
(so a viewer naturally loops 2-3x to finish reading) is a legitimate
growth tactic, not a gimmick. The point of the loop is for the viewer to
NOT notice it's repeating -- it should read as one continuous, stable
view they're simply still reading, not as a video restarting. That
rules out any visible/audible seam at the loop point: both the video
fade-in and the audio fade-out are skipped entirely (0 seconds, not
just shortened) for a loop-style Short -- `fade_in_seconds=0` and
`fade_out_seconds=0` (LOOP_FRIENDLY_FADE_IN_SECONDS /
LOOP_FRIENDLY_FADE_OUT_SECONDS, both 0.0). A longer, one-shot Short
where looping isn't the design keeps the normal fades (the 0.6s/1.0s
defaults) since those aren't meant to be watched on repeat. There is no
single "right" duration for every card -- it should be a bit SHORTER
than a comfortable first full read, not an arbitrary small number, so
callers pass their own duration rather than relying on a shared
default.

Requires ffmpeg on PATH -- this module shells out to the real `ffmpeg`
binary via subprocess rather than a Python video library, since ffmpeg
is the actual, battle-tested tool for this and Python wrappers around it
just add an extra layer that can go wrong.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from mahanavi.exceptions import VideoAssemblyError

logger = logging.getLogger(__name__)

DEFAULT_DURATION_SECONDS = 10.0
DEFAULT_FPS = 30
AUDIO_FADE_OUT_SECONDS = 1.0
VIDEO_FADE_IN_SECONDS = 0.6
# No fade at all for loop-style Shorts -- per explicit request, the loop
# point must be invisible/inaudible so a viewer reads it as one stable,
# continuous view rather than noticing a restart. Any fade, however
# short, is a seam that repeats on every loop.
LOOP_FRIENDLY_FADE_IN_SECONDS = 0.0
LOOP_FRIENDLY_FADE_OUT_SECONDS = 0.0


def assemble_short(
    image_path: Path,
    output_path: Path,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    audio_path: Path | None = None,
    fps: int = DEFAULT_FPS,
    fade_in_seconds: float = VIDEO_FADE_IN_SECONDS,
    fade_out_seconds: float = AUDIO_FADE_OUT_SECONDS,
) -> Path:
    """Assemble a static image (+ optional looped audio) into a .mp4.

    If audio_path is None, the output has a silent audio track (still a
    valid, playable video -- some platforms expect SOME audio stream
    even if silent, rather than none at all).

    `fade_in_seconds` / `fade_out_seconds`: pass the LOOP_FRIENDLY_*
    constants (both 0.0) for a Short whose duration is intentionally
    shorter than its reading time, so there is no visible/audible seam
    at the loop point -- it should look like one continuous, stable
    view, not a video restarting. Keep the defaults for a longer,
    one-shot Short where looping isn't the design (see module docstring).
    """
    if shutil.which("ffmpeg") is None:
        raise VideoAssemblyError(
            "ffmpeg was not found on PATH. Install it (e.g. `winget install Gyan.FFmpeg` "
            "on Windows) and restart your terminal so PATH picks it up."
        )
    if not image_path.exists():
        raise VideoAssemblyError(f"Image file does not exist: {image_path}")
    if audio_path is not None and not audio_path.exists():
        raise VideoAssemblyError(f"Audio file does not exist: {audio_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = ["ffmpeg", "-y", "-loop", "1", "-i", str(image_path)]

    if audio_path is not None:
        # -stream_loop -1 loops the audio input indefinitely; the global
        # -t below caps the actual output length regardless.
        cmd += ["-stream_loop", "-1", "-i", str(audio_path)]
    else:
        # Silent audio track via ffmpeg's own lavfi source, so the output
        # always has an audio stream (some platforms expect one).
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

    video_filter = f"fps={fps},format=yuv420p"
    if fade_in_seconds > 0:
        video_filter += f",fade=t=in:st=0:d={fade_in_seconds}"

    cmd += ["-t", str(duration_seconds), "-vf", video_filter]

    if fade_out_seconds > 0:
        fade_start = max(duration_seconds - fade_out_seconds, 0)
        cmd += ["-af", f"afade=t=out:st={fade_start}:d={fade_out_seconds}"]

    cmd += [
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]

    logger.info("Assembling video: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise VideoAssemblyError(
            f"ffmpeg failed (exit code {result.returncode}) assembling {output_path}. "
            f"stderr:\n{result.stderr[-2000:]}"  # last 2000 chars -- ffmpeg's own errors are usually near the end
        )

    logger.info("Assembled video: %s", output_path)
    return output_path
