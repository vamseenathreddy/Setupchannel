"""
post_navaratri_day2_song.py: assembles and uploads the Dasara Navaratri
Day 2 devotional SONG video -- "Sri Bala Tripurasundari Devi". Built
2026-10-04, following the same pipeline shape as Day 1's
post_navaratri_song.py (see that module's docstring for the full
rationale), with ONE deliberate difference per explicit request:
visuals are channel-owner-SUPPLIED stills committed to this repo under
assets/images/navaratri_day2/ (NOT fal.ai-generated) -- this script
animates each still locally with a Ken Burns-style slow zoom/pan
(ffmpeg zoompan), instead of calling fal.ai's FLUX+Kling pipeline. No
MAHANAVI_FAL_API_KEY dependency here at all.

PIPELINE:
  1. The song WAV already sits at data/<SONG_FILENAME> (fetched from
     Drive by a prior CI step -- see fetch_drive_asset.py).
  2. For each of the 6 unique SCENES below, a short (~5s) Ken Burns clip
     is rendered locally from the committed still image -- no network
     call, no generation cost.
  3. Each short clip is extended into a seamless ping-pong loop (clip +
     its own reverse, concatenated and looped) to fill that scene's
     actual share of the song's real duration -- scene durations are
     WEIGHTS of the real audio length (measured via ffprobe at
     runtime), exactly as in post_navaratri_song.py.
  4. All scene segments are concatenated in lyric order, the real song
     audio is laid under the whole thing, and a small corner watermark
     is burned in.
  5. SEO (title/description/tags) is built AFTER the real duration is
     known, so chapter timestamps in the description are always
     correct for this exact export -- no manual follow-up edit needed
     (unlike Day 1, where chapters were added in a later pass).
  6. Uploaded via the existing YouTubeShortsUploader (category Music,
     privacyStatus=private -- a draft the owner reviews and publishes
     themselves), then added to the Navaratri Songs playlist.

Usage (from CI, via the "Post Navaratri Day 2 Song" workflow):
    see .github/workflows/post-navaratri-day2-song.yml
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from mahanavi.config import get_settings
from mahanavi.content.navaratri_day2_song_seo import build_navaratri_day2_song_seo
from mahanavi.exceptions import MahanaviError
from mahanavi.images.fonts import FontManager
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

SONG_FILENAME = "navaratri_balatripurasundari_song_02.wav"
MUSIC_CATEGORY_ID = "10"

WORK_DIR = Path("data") / "navaratri_day2_song"
OUTPUT_PATH = Path("data") / "generated" / "navaratri_balatripurasundari_song_02.mp4"

IMAGES_DIR = Path("assets") / "images" / "navaratri_day2"

# scene key -> (still image path, Ken Burns motion style). Images are
# channel-owner-supplied (see this module's docstring), committed to
# the repo -- chosen/ordered to match the lyric flow: an establishing
# temple shot, the main deity portrait, the Sri Chakra close-up (the
# devotional "centerpiece" moment, standing in for Day 1's golden-armor
# close-up), a devotee/celebration shot, a radiant close-up for the
# bridge, and a grand closing shot on her swan (hamsa) vehicle.
SCENES: dict[str, tuple[Path, str]] = {
    "intro": (IMAGES_DIR / "scene_intro.jpg", "pan_left_to_right"),
    "verse1": (IMAGES_DIR / "scene_verse1.jpg", "zoom_in"),
    "chorus": (IMAGES_DIR / "scene_chorus.jpg", "zoom_in"),
    "verse2": (IMAGES_DIR / "scene_verse2.jpg", "pan_right_to_left"),
    "bridge": (IMAGES_DIR / "scene_bridge.jpg", "zoom_in"),
    "outro": (IMAGES_DIR / "scene_outro.jpg", "pan_left_to_right"),
}

# Lyric order -- "chorus" appears twice (reuses the same rendered clip),
# identical weights to Day 1's SCENE_SEQUENCE.
SCENE_SEQUENCE: list[tuple[str, float]] = [
    ("intro", 0.08),
    ("verse1", 0.16),
    ("chorus", 0.16),
    ("verse2", 0.16),
    ("chorus", 0.16),
    ("bridge", 0.16),
    ("outro", 0.12),
]

# Burned-in lyric caption for each section -- same mechanism as Day 1
# (see post_navaratri_song.py's LYRIC_LINES docstring).
LYRIC_LINES: dict[str, list[str]] = {
    "intro": [
        "ఓం ఐం హ్రీం శ్రీం బాలా త్రిపురసుందరీ",
        "శ్రీవిద్యా రూపిణి జగదంబా",
        "బాల రూపమున వెలిగే తల్లి",
    ],
    "verse1": [
        "శ్రీచక్ర మధ్యమున కొలువైన తల్లి",
        "కామేశ్వరీ రూపున వెలిగే జ్యోతి",
        "పుస్తకం అక్షమాల చేతపట్టి",
        "జ్ఞాన సిద్ధి నొసగు బాలా దేవి",
    ],
    "chorus": [
        "బాలా త్రిపురసుందరీ శ్రీమాతా",
        "శరణు శరణు అంటూ మొక్కేము తల్లీ",
        "కరుణతో మమ్ము కాపాడవమ్మా",
        "విద్యాబుద్ధులు నొసగు జగదంబా",
    ],
    "verse2": [
        "నవరాత్రి రెండవ రోజు పూజలలో",
        "బాల రూపమున అలంకారం నీదే",
        "పంచదశీ మంత్ర స్వరూపిణివి",
        "షోడశీ కళలతో శోభిల్లు తల్లి",
    ],
    "bridge": [
        "లలితా సహస్రనామముల తల్లి",
        "త్రిపుర సుందరివి నీవే అమ్మా",
        "బాలికా రూపమున భక్తుల కాచే",
        "శ్రీవిద్యా దేవత నీకిదే వందనం",
    ],
    "outro": [
        "జయ జయ బాలా త్రిపురసుందరీ",
        "శ్రీవిద్యా రూపిణి జగదంబా",
        "ఓం ఐం హ్రీం శ్రీం నమః",
        "ఓం ఐం హ్రీం శ్రీం నమః",
    ],
}

_CANVAS_W, _CANVAS_H = 1920, 1080


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MahanaviError(f"Command failed: {' '.join(cmd)}\n{result.stderr[-3000:]}")


def _audio_duration_seconds(media_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(media_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise MahanaviError(f"ffprobe failed on {media_path}: {result.stderr}")
    return float(result.stdout.strip())


def _render_kenburns_clip(
    image_path: Path, out_path: Path, motion: str, duration_seconds: float = 5.0, fps: int = 25,
) -> None:
    """Renders a slow Ken Burns zoom/pan clip from a single still image
    -- the standard ffmpeg zoompan recipe (pre-scale the image well
    above target resolution first so zoompan doesn't jitter, then
    zoompan+crop to the final canvas size).

    motion:
      "zoom_in"            -- slow centered zoom from 1.0x to ~1.15x.
      "pan_left_to_right"  -- fixed 1.08x zoom, pans left to right.
      "pan_right_to_left"  -- fixed 1.08x zoom, pans right to left.
    """
    if not image_path.exists():
        raise MahanaviError(f"Scene image not found: {image_path}")

    frames = int(duration_seconds * fps)
    if motion == "zoom_in":
        zoompan = (
            f"zoompan=z='min(zoom+0.0015,1.15)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={_CANVAS_W}x{_CANVAS_H}:fps={fps}"
        )
    elif motion == "pan_left_to_right":
        zoompan = (
            f"zoompan=z='1.08':"
            f"x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={_CANVAS_W}x{_CANVAS_H}:fps={fps}"
        )
    elif motion == "pan_right_to_left":
        zoompan = (
            f"zoompan=z='1.08':"
            f"x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={_CANVAS_W}x{_CANVAS_H}:fps={fps}"
        )
    else:
        raise MahanaviError(f"Unknown Ken Burns motion: {motion!r}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
        "-vf", f"scale=3840:-2,{zoompan}",
        "-t", f"{duration_seconds:.3f}", "-r", str(fps),
        "-pix_fmt", "yuv420p", str(out_path),
    ])


def _render_caption_png(text: str, out_path: Path) -> None:
    """Identical approach to post_navaratri_song.py's _render_caption_png
    -- PIL + the project's FontManager (RAQM/HarfBuzz) for correct
    Telugu complex-script shaping, not ffmpeg's drawtext."""
    settings = get_settings()
    fonts = FontManager(settings.telugu_font_path)
    font = fonts.get_font(size=50, weight="Bold")

    canvas = Image.new("RGBA", (_CANVAS_W, _CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 36, 18
    box_w, box_h = text_w + 2 * pad_x, text_h + 2 * pad_y
    box_x0 = (_CANVAS_W - box_w) / 2
    box_y0 = _CANVAS_H - 160 - box_h
    draw.rounded_rectangle(
        [box_x0, box_y0, box_x0 + box_w, box_y0 + box_h], radius=14, fill=(0, 0, 0, 130),
    )
    text_x = box_x0 + pad_x - bbox[0]
    text_y = box_y0 + pad_y - bbox[1]
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        draw.text((text_x + ox, text_y + oy), text, font=font, fill=(0, 0, 0, 220))
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def _make_pingpong_loop(
    clip_path: Path, target_seconds: float, out_path: Path, caption_lines: list[str] | None = None,
) -> None:
    """Identical to post_navaratri_song.py's _make_pingpong_loop -- see
    that module for the full explanation of the ping-pong-loop +
    per-line caption overlay approach."""
    reversed_path = clip_path.with_name(clip_path.stem + "_rev.mp4")
    _run(["ffmpeg", "-y", "-i", str(clip_path), "-vf", "reverse", "-an", str(reversed_path)])

    unit_path = clip_path.with_name(clip_path.stem + "_unit.mp4")
    concat_list = clip_path.with_name(clip_path.stem + "_concat.txt")
    concat_list.write_text(f"file '{clip_path.resolve()}'\nfile '{reversed_path.resolve()}'\n")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-an", str(unit_path)])

    unit_duration = _audio_duration_seconds(unit_path)
    loops_needed = int(target_seconds // unit_duration) + 2

    lines = [line.strip() for line in (caption_lines or []) if line.strip()]
    if not lines:
        _run([
            "ffmpeg", "-y", "-stream_loop", str(loops_needed), "-i", str(unit_path),
            "-t", f"{target_seconds:.3f}",
            "-vf", f"scale={_CANVAS_W}:{_CANVAS_H}:force_original_aspect_ratio=decrease,"
                   f"pad={_CANVAS_W}:{_CANVAS_H}:(ow-iw)/2:(oh-ih)/2",
            "-an", "-r", "25", str(out_path),
        ])
        return

    caption_paths: list[Path] = []
    for i, line in enumerate(lines):
        cap_path = clip_path.with_name(clip_path.stem + f"_cap{i}.png")
        _render_caption_png(line, cap_path)
        caption_paths.append(cap_path)

    slice_seconds = target_seconds / len(lines)
    cmd = ["ffmpeg", "-y", "-stream_loop", str(loops_needed), "-i", str(unit_path)]
    for cap_path in caption_paths:
        cmd += ["-loop", "1", "-i", str(cap_path)]

    filter_parts = [
        f"[0:v]scale={_CANVAS_W}:{_CANVAS_H}:force_original_aspect_ratio=decrease,"
        f"pad={_CANVAS_W}:{_CANVAS_H}:(ow-iw)/2:(oh-ih)/2[base]"
    ]
    prev_label = "base"
    for i in range(len(lines)):
        start = i * slice_seconds
        end = target_seconds if i == len(lines) - 1 else (i + 1) * slice_seconds
        out_label = f"v{i}"
        filter_parts.append(
            f"[{prev_label}][{i + 1}:v]overlay=0:0:"
            f"enable='between(t\\,{start:.3f}\\,{end:.3f})'[{out_label}]"
        )
        prev_label = out_label

    cmd += [
        "-filter_complex", ";".join(filter_parts),
        "-map", f"[{prev_label}]",
        "-t", f"{target_seconds:.3f}",
        "-an", "-r", "25", str(out_path),
    ]
    _run(cmd)


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

    song_path = Path("data") / SONG_FILENAME
    if not song_path.exists():
        print(f"FAILED: song file not found at {song_path} -- did fetch_drive_asset.py run first?", file=sys.stderr)
        return 1

    for key, (image_path, _motion) in SCENES.items():
        if not image_path.exists():
            print(f"FAILED: scene image for '{key}' not found at {image_path}", file=sys.stderr)
            return 1

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    total_duration = _audio_duration_seconds(song_path)
    print(f"Song duration: {total_duration:.1f}s")

    # Render each UNIQUE scene's base Ken Burns clip once (chorus reused
    # across both occurrences in SCENE_SEQUENCE).
    clip_paths: dict[str, Path] = {}
    for key, (image_path, motion) in SCENES.items():
        clip_out = WORK_DIR / f"base_{key}.mp4"
        _render_kenburns_clip(image_path, clip_out, motion)
        clip_paths[key] = clip_out
        print(f"Rendered scene '{key}' ({motion}): {clip_out}")

    # Build each sequence segment (looped to its share of total duration).
    segment_paths: list[Path] = []
    for i, (key, weight) in enumerate(SCENE_SEQUENCE):
        target_seconds = total_duration * weight
        seg_out = WORK_DIR / f"segment_{i:02d}_{key}.mp4"
        _make_pingpong_loop(clip_paths[key], target_seconds, seg_out, caption_lines=LYRIC_LINES.get(key))
        segment_paths.append(seg_out)
        print(f"Segment {i} ('{key}'): {target_seconds:.1f}s -> {seg_out}")

    _assemble(song_path, segment_paths, "Mahanavi Spirituals", OUTPUT_PATH)
    print(f"Assembled: {OUTPUT_PATH}")

    seo = build_navaratri_day2_song_seo(total_duration)
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
