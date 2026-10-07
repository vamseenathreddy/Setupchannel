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
from mahanavi.video.watermark import build_watermark_layers, overlay_filter

logger = logging.getLogger(__name__)


def _watermark_inputs(output_path: Path, positions_y: tuple[int, ...] | None = None) -> list[Path]:
    """Generate the channel-handle watermark layers next to the output file."""
    from mahanavi.config import get_settings

    kwargs = {} if positions_y is None else {"positions_y": positions_y}
    return build_watermark_layers(output_path.parent / ".watermark", get_settings().telugu_font_path, **kwargs)

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
    watermark: bool = True,
    watermark_positions_y: tuple[int, ...] | None = None,
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

    if watermark:
        wm_paths = _watermark_inputs(output_path, watermark_positions_y)
        for wm in wm_paths:
            cmd += ["-framerate", str(fps), "-loop", "1", "-i", str(wm)]
        # inputs: 0 image, 1 audio, 2.. watermark layers
        filter_complex = (
            f"[0:v]{video_filter}[base];"
            + overlay_filter("base", 2, len(wm_paths), "wmout")
            + ";[wmout]format=yuv420p[vout]"
        )
        cmd += ["-t", str(duration_seconds), "-filter_complex", filter_complex, "-map", "[vout]", "-map", "1:a"]
    else:
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


# How many turns the Sri Chakra makes across one loop of the Short.
# Halved AGAIN per explicit request (2026-10-02: "i suggest decrease
# speed to 50% from current", following up on "user should not feel"
# the Short end/loop) -- from 1.0 (first version) to 0.5 (first
# slowdown) to 0.25 (this one) of a full turn per loop. Any of these
# values stays seamless ONLY because images/sri_chakra.py's motif
# (CHAKRA_POINTS=12 points, 30-degree rotational symmetry period) was
# specifically built so every multiple of 1/12 of a revolution lands on
# a pixel-identical frame at the loop point -- 0.25 = 3/12, still a
# clean multiple. Slowing further is still possible down to 1/12
# (~0.083) without a redesign; going below that, or to a value that
# isn't a multiple of 1/12, would put a visible jump at the loop point.
CHAKRA_REVOLUTIONS_PER_LOOP = 0.25


def assemble_purana_short_with_rotating_chakra(
    background_path: Path,
    chakra_path: Path,
    text_path: Path,
    output_path: Path,
    duration_seconds: float,
    chakra_x: int,
    chakra_y: int,
    audio_path: Path | None = None,
    fps: int = DEFAULT_FPS,
    revolutions_per_loop: float = CHAKRA_REVOLUTIONS_PER_LOOP,
    watermark: bool = True,
) -> Path:
    """Assembles the Purana Story Short's three separate layers
    (PuranaShortCardRenderer.render_layers()) into one .mp4 with the Sri
    Chakra background motif continuously rotating IN PLACE (same center,
    turning like a wheel), instead of a single flat still image -- per
    explicit request (2026-10-02: "i want slowly rotating sri chakram in
    background... to bring live feel instead of static", then
    2026-10-02: "its rotating front back but it should rotate at
    samplace circle" -- an earlier version used a back-and-forth sway
    instead of a continuous spin, which read as swinging rather than
    rotating; replaced with a real continuous rotation per this
    correction, then 2026-10-02 again: "it looks funny. center dot is
    center point to rotate" -- that earlier version also rotated the
    chakra_path image as-is, which was full-card-sized with the motif
    drawn off-center within it, so ffmpeg's rotate filter (which always
    spins an image around ITS OWN center) was actually spinning the
    whole card-sized canvas around the CARD's center, not around the
    chakra's own bindu -- the motif visibly orbited instead of spinning
    in place. Fixed by having PuranaShortCardRenderer build chakra_path
    as its own small, tightly-sized image centered on its bindu
    (_build_chakra_layer), so rotating that image IS rotating around the
    bindu; `chakra_x`/`chakra_y` is where that (fixed-size) rotated image
    gets overlaid on the background so its center lands in the right
    spot on the full card).

    WHY revolutions_per_loop MUST MATCH THE MOTIF'S OWN SYMMETRY: this
    Short is intentionally short (duration_seconds, loop-friendly, no
    fade -- see module docstring) and relies on YouTube auto-looping it
    seamlessly so repeated loops read as one continuous, stable view
    rather than a video restarting. The chakra's rotation angle follows
    `2*pi*revolutions_per_loop*t/duration`, so the angle swept over one
    loop is `revolutions_per_loop` full turns. That only lands back on a
    visually identical frame at t=duration if revolutions_per_loop is a
    multiple of the motif's own rotational symmetry period. A whole
    number (1.0, 2.0, ...) always works for any shape, since a full
    360-degree turn returns ANY image to its starting orientation; a
    fractional value (0.5, 0.25, ... used here per the "slow this
    rotation" / "decrease speed to 50% from current" requests) only
    works because images/sri_chakra.py's motif was deliberately built
    with CHAKRA_POINTS-fold (12-fold, 30-degree) rotational symmetry --
    every multiple of 1/12 of a revolution lands back on an identical
    frame. Changing revolutions_per_loop to a value that ISN'T a
    multiple of 1/12 would put a visible jump at the loop point.
    Verified here by comparing extracted frames: the chakra spins
    continuously in place, always around the same fixed center, and the
    frame at t=duration is pixel-identical to t=0 -- and because the
    motion is periodic with period=duration, consecutive loops flow as
    one unbroken spin rather than restarting.

    The three layers are composited in this order (back to front):
    background (opaque) -> chakra (rotating, transparent, overlaid at
    chakra_x/chakra_y) -> text (fixed, transparent) -- so the chakra
    always sits behind the text, visible only through the gaps between
    letters/lines, exactly like the static watermark design it replaces.
    """
    if shutil.which("ffmpeg") is None:
        raise VideoAssemblyError(
            "ffmpeg was not found on PATH. Install it (e.g. `winget install Gyan.FFmpeg` "
            "on Windows) and restart your terminal so PATH picks it up."
        )
    for label, path in (("background", background_path), ("chakra", chakra_path), ("text", text_path)):
        if not path.exists():
            raise VideoAssemblyError(f"Purana short {label} layer does not exist: {path}")
    if audio_path is not None and not audio_path.exists():
        raise VideoAssemblyError(f"Audio file does not exist: {audio_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        "ffmpeg", "-y",
        "-framerate", str(fps), "-loop", "1", "-i", str(background_path),
        "-framerate", str(fps), "-loop", "1", "-i", str(chakra_path),
        "-framerate", str(fps), "-loop", "1", "-i", str(text_path),
    ]

    if audio_path is not None:
        cmd += ["-stream_loop", "-1", "-i", str(audio_path)]
        audio_map = ["-map", "3:a"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        audio_map = ["-map", "3:a"]

    angle_expr = f"2*PI*{revolutions_per_loop}*t/{duration_seconds}"
    if watermark:
        wm_paths = _watermark_inputs(output_path)
        for wm in wm_paths:  # inputs 4.. (after bg, chakra, text, audio)
            cmd += ["-framerate", str(fps), "-loop", "1", "-i", str(wm)]
        tail = (
            f"[bg_chakra][2:v]overlay=0:0:format=auto,fps={fps}[card];"
            + overlay_filter("card", 4, len(wm_paths), "wmout")
            + ";[wmout]format=yuv420p[vout]"
        )
    else:
        tail = f"[bg_chakra][2:v]overlay=0:0:format=auto,fps={fps},format=yuv420p[vout]"
    filter_complex = (
        f"[1:v]format=rgba,rotate=a='{angle_expr}':c=none:ow=iw:oh=ih[chakra_rot];"
        f"[0:v][chakra_rot]overlay={chakra_x}:{chakra_y}:format=auto[bg_chakra];"
        + tail
    )

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        *audio_map,
        "-t", str(duration_seconds),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]

    logger.info("Assembling rotating-chakra video: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise VideoAssemblyError(
            f"ffmpeg failed (exit code {result.returncode}) assembling {output_path}. "
            f"stderr:\n{result.stderr[-2000:]}"
        )

    logger.info("Assembled rotating-chakra video: %s", output_path)
    return output_path
