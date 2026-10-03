"""
post_navaratri_song.py: assembles and uploads the first AI-generated
devotional SONG video -- "Swarnakavachadharini Kanakadurgamma", a
Dasara Navaratri Day 1 bhakti geetam. Built 2026-10-03 per explicit
request: original lyrics (content/ lives in the chat history, not this
repo -- this is a one-off piece, not a rotating series), the channel
owner's wife's own voice via Suno, landscape 16:9 visuals generated
with fal.ai (FLUX.1 stills animated with Kling 2.5 Turbo Pro).

PIPELINE:
  1. The song WAV already sits at data/<SONG_FILENAME> (fetched from
     Drive by a prior CI step -- see fetch_drive_asset.py).
  2. For each of the 6 unique SCENES below, fal.ai generates one still
     image (FLUX) then animates it into a short (~5s) slow-motion clip
     (Kling) -- see fal_scene_generator.py for why two steps.
  3. Each short clip is extended into a seamless ping-pong loop (clip +
     its own reverse, concatenated and looped) to fill that scene's
     actual share of the song's real duration -- scene durations are
     WEIGHTS of the real audio length (measured via ffprobe at runtime,
     not hardcoded), so this always matches whatever the final exported
     song's exact length turns out to be.
  4. All scene segments are concatenated in lyric order, the real song
     audio is laid under the whole thing, and a small corner watermark
     is burned in.
  5. Uploaded via the existing YouTubeShortsUploader (category Music,
     privacyStatus=private -- a draft the owner reviews and publishes
     themselves), then added to the Navaratri Songs playlist.

COST CONTROL: the Chorus appears twice in the lyrics with identical
text -- SCENE_SEQUENCE reuses the one "chorus" generation for both
occurrences instead of generating it twice, keeping this well within a
small fal.ai budget (see fal_scene_generator.py's module docstring).

Usage (from CI, via the "Post Navaratri Song" workflow):
    see .github/workflows/post-navaratri-song.yml
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mahanavi.config import get_settings
from mahanavi.content.navaratri_song_seo import build_navaratri_song_seo
from mahanavi.exceptions import MahanaviError, YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.fal_scene_generator import FalGenerationError, FalSceneGenerator, SceneSpec

SONG_FILENAME = "navaratri_durga_song_01.wav"
MUSIC_CATEGORY_ID = "10"

WORK_DIR = Path("data") / "navaratri_song"
OUTPUT_PATH = Path("data") / "generated" / "navaratri_durga_song_01.mp4"

# key -> (SceneSpec, weight). Weights sum to 1.0 and are multiplied by
# the REAL measured song duration at runtime -- see module docstring.
SCENES: dict[str, SceneSpec] = {
    "intro": SceneSpec(
        key="intro",
        image_prompt=(
            "Misty sunrise over Indrakeeladri hill temple silhouette in Vijayawada, "
            "golden light breaking over the Krishna river below, traditional South "
            "Indian temple gopuram, cinematic wide shot, devotional atmosphere, warm "
            "golden hour lighting, ultra-detailed, photorealistic"
        ),
        motion_prompt=(
            "slow gentle drift of mist over the river, soft golden light slowly "
            "brightening, extremely slow motion, cinematic, no camera shake"
        ),
    ),
    "verse1": SceneSpec(
        key="verse1",
        image_prompt=(
            "Majestic Hindu Goddess Durga temple idol at sanctum, holding trishul and "
            "chakra, seated gracefully beside a lion, golden ornaments, red silk saree, "
            "divine glow, intricately detailed deity idol, soft oil lamp lighting, "
            "respectful traditional South Indian iconography, photorealistic devotional art"
        ),
        motion_prompt=(
            "extremely slow, gentle camera dolly-in, subtle flicker of oil lamp light "
            "on the golden ornaments, slow motion, serene, reverent movement only"
        ),
    ),
    "chorus": SceneSpec(
        key="chorus",
        image_prompt=(
            "Close-up of a Goddess Durga idol's golden armor (swarna kavacham) at a "
            "South Indian temple, intricate gold craftsmanship, glowing ornaments, "
            "jasmine and marigold flower garlands, soft warm temple lighting, devotees' "
            "folded hands in soft focus foreground, grand devotional atmosphere, "
            "photorealistic"
        ),
        motion_prompt=(
            "slow motion rose and jasmine flower petals gently falling across frame, "
            "soft golden light shimmer on the armor, extremely slow, graceful, reverent"
        ),
    ),
    "verse2": SceneSpec(
        key="verse2",
        image_prompt=(
            "Grand Navaratri alankaram celebration at a South Indian temple, rows of "
            "lit oil lamps, marigold and jasmine flower decorations, golden temple "
            "interior, devotees in traditional attire with folded hands, warm festive "
            "glow, photorealistic devotional photography"
        ),
        motion_prompt=(
            "slow motion flicker of rows of oil lamp flames, gentle sway of flower "
            "garlands, soft incense smoke rising slowly, cinematic slow motion"
        ),
    ),
    "bridge": SceneSpec(
        key="bridge",
        image_prompt=(
            "Divine radiant golden light rays emanating softly around a clearly "
            "Hindu Goddess Durga idol silhouette -- EIGHT ARMS each holding a "
            "weapon (trishul, chakra, sword, bow), tall ornate crown (mukutam), "
            "seated astride her lion vehicle (simha vahanam), silhouette unmistakably "
            "female and multi-armed, cosmic devotional atmosphere, soft clouds and "
            "golden light particles, ethereal and powerful, respectful South Indian "
            "temple sacred art style, photorealistic with painterly divine glow. "
            "This is Goddess Durga, NOT a seated meditating monk or Buddha figure."
        ),
        motion_prompt=(
            "slow motion golden light particles drifting upward, gentle pulsing "
            "divine glow, extremely slow dreamlike motion, cinematic"
        ),
    ),
    "outro": SceneSpec(
        key="outro",
        image_prompt=(
            "Wide shot of a temple aarti ceremony at dusk, priest holding the long "
            "metal HANDLE of a traditional multi-wick brass aarti lamp (deepam) "
            "firmly in his fist, flames burning only from the lamp's wick tips well "
            "above his hand, waving the lamp before a Goddess idol, golden flame "
            "light illuminating the temple hall, devotees with folded hands, warm "
            "orange and gold tones, deeply devotional, photorealistic. The priest's "
            "hand holds the lamp's handle only -- no fire touches his skin anywhere."
        ),
        motion_prompt=(
            "slow motion circular sweep of the aarti lamp by its handle, gentle "
            "flicker of the lamp's flame, soft golden light, extremely slow and "
            "reverent camera movement, hand stays on the handle throughout"
        ),
    ),
}

# Lyric order -- "chorus" appears twice (reuses the same generated clip).
SCENE_SEQUENCE: list[tuple[str, float]] = [
    ("intro", 0.08),
    ("verse1", 0.16),
    ("chorus", 0.16),
    ("verse2", 0.16),
    ("chorus", 0.16),
    ("bridge", 0.16),
    ("outro", 0.12),
]

# Burned-in lyric caption for each section, shown centered near the
# bottom of frame for that whole section's screen time (added
# 2026-10-03 per explicit request -- "text according to singer singing
# lyrics at bottom"). One line per section, not word-by-word karaoke
# timing, since that's the granularity SCENE_SEQUENCE already gives us
# (each section IS one scene's screen time). "chorus" is sung
# identically both times it appears, so the same line is correct for
# both occurrences.
#
# *** PLACEHOLDER -- fill these in with the EXACT lines from the real
# Suno lyrics before the next run; leaving any of these empty just
# means that section plays with no caption, it will not break the
# pipeline. *** (see this script's module docstring: the actual lyric
# text lives in chat history, not committed to this repo, so it could
# not be filled in here without risking putting the wrong words under
# the real singing.)
LYRIC_LINES: dict[str, str] = {
    "intro": "",
    "verse1": "",
    "chorus": "",
    "verse2": "",
    "bridge": "",
    "outro": "",
}


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MahanaviError(f"Command failed: {' '.join(cmd)}\n{result.stderr[-3000:]}")


def _audio_duration_seconds(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise MahanaviError(f"ffprobe failed on {audio_path}: {result.stderr}")
    return float(result.stdout.strip())


def _escape_drawtext(text: str) -> str:
    """Escapes a string for safe use inside an ffmpeg drawtext filter's
    text='...' value -- drawtext treats :, ', \\, and % specially."""
    return (
        text.replace("\\", "\\\\\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def _make_pingpong_loop(clip_path: Path, target_seconds: float, out_path: Path, caption: str = "") -> None:
    """Extends a short clip into a seamless ping-pong loop (forward +
    reverse, concatenated, then looped) of exactly target_seconds.

    If `caption` is non-empty, burns it in centered near the bottom of
    frame for this entire segment -- one lyric line per scene/section,
    not word-by-word karaoke timing (see LYRIC_LINES' docstring)."""
    reversed_path = clip_path.with_name(clip_path.stem + "_rev.mp4")
    _run(["ffmpeg", "-y", "-i", str(clip_path), "-vf", "reverse", "-an", str(reversed_path)])

    unit_path = clip_path.with_name(clip_path.stem + "_unit.mp4")
    concat_list = clip_path.with_name(clip_path.stem + "_concat.txt")
    concat_list.write_text(f"file '{clip_path.resolve()}'\nfile '{reversed_path.resolve()}'\n")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-an", str(unit_path)])

    unit_duration = _audio_duration_seconds(unit_path)
    loops_needed = int(target_seconds // unit_duration) + 2  # generous over-shoot, trimmed below

    vf_parts = ["scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"]
    if caption.strip():
        font_path = get_settings().telugu_font_path
        escaped = _escape_drawtext(caption.strip())
        vf_parts.append(
            f"drawtext=fontfile='{font_path}':text='{escaped}':"
            "fontcolor=white:fontsize=52:x=(w-tw)/2:y=h-th-130:"
            "box=1:boxcolor=black@0.45:boxborderw=18:"
            "borderw=2:bordercolor=black@0.8"
        )
    _run([
        "ffmpeg", "-y", "-stream_loop", str(loops_needed), "-i", str(unit_path),
        "-t", f"{target_seconds:.3f}",
        "-vf", ",".join(vf_parts),
        "-an", "-r", "25", str(out_path),
    ])


def _assemble(song_path: Path, segment_paths: list[Path], watermark_text: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    concat_list = WORK_DIR / "final_concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in segment_paths))
    silent_video = WORK_DIR / "silent_full.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(silent_video)])

    settings = get_settings()
    font_path = settings.telugu_font_path
    drawtext = (
        f"drawtext=fontfile='{font_path}':text='{watermark_text}':"
        "fontcolor=white@0.55:fontsize=28:x=w-tw-30:y=h-th-30:"
        "box=1:boxcolor=black@0.25:boxborderw=8"
    )
    _run([
        "ffmpeg", "-y", "-i", str(silent_video), "-i", str(song_path),
        "-vf", drawtext,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(out_path),
    ])


def main() -> int:
    settings = get_settings()
    if not settings.fal_api_key:
        print("FAILED: MAHANAVI_FAL_API_KEY not set.", file=sys.stderr)
        return 1

    song_path = Path("data") / SONG_FILENAME
    if not song_path.exists():
        print(f"FAILED: song file not found at {song_path} -- did fetch_drive_asset.py run first?", file=sys.stderr)
        return 1

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    total_duration = _audio_duration_seconds(song_path)
    print(f"Song duration: {total_duration:.1f}s")

    generator = FalSceneGenerator(settings.fal_api_key, aspect_ratio="16:9")

    try:
        # Generate each UNIQUE scene once (chorus reused across both occurrences).
        clip_paths: dict[str, Path] = {}
        for key, scene in SCENES.items():
            still = generator.generate_still(scene, WORK_DIR)
            clip = generator.animate(scene, still, WORK_DIR, duration_seconds=5)
            clip_paths[key] = clip
            print(f"Generated scene '{key}': {clip}")

        # Build each sequence segment (looped to its share of total duration).
        segment_paths: list[Path] = []
        for i, (key, weight) in enumerate(SCENE_SEQUENCE):
            target_seconds = total_duration * weight
            seg_out = WORK_DIR / f"segment_{i:02d}_{key}.mp4"
            _make_pingpong_loop(clip_paths[key], target_seconds, seg_out, caption=LYRIC_LINES.get(key, ""))
            segment_paths.append(seg_out)
            print(f"Segment {i} ('{key}'): {target_seconds:.1f}s -> {seg_out}")

    except FalGenerationError as exc:
        print(f"FAILED (fal.ai): {exc}", file=sys.stderr)
        return 1

    _assemble(song_path, segment_paths, "Mahanavi Spirituals", OUTPUT_PATH)
    print(f"Assembled: {OUTPUT_PATH}")

    seo = build_navaratri_song_seo()
    uploader = YouTubeShortsUploader(settings, category_id=MUSIC_CATEGORY_ID)
    result = uploader.upload(OUTPUT_PATH, seo, privacy_status="private")
    if not result.success:
        print(f"FAILED to upload: {result.error_message}", file=sys.stderr)
        return 1
    print(f"Uploaded (private draft): {result.post_url}")

    if settings.playlist_id_navaratri_songs and result.video_id:
        if uploader.add_to_playlist(result.video_id, settings.playlist_id_navaratri_songs):
            print("Added to Navaratri Songs playlist.")
        else:
            print("Note: could not add to playlist (non-fatal).")
    else:
        print("Note: MAHANAVI_PLAYLIST_ID_NAVARATRI_SONGS not set -- skipped playlist add.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
