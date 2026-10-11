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
from ytcore.brandcfg import A_NAME  # noqa: E402

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from ytcore.config import get_settings
from ytcore.content.navaratri_song_seo import build_navaratri_song_seo
from ytcore.exceptions import AppError, YouTubeUploadError
from ytcore.images.fonts import FontManager
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.fal_scene_generator import FalGenerationError, FalSceneGenerator, SceneSpec

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
# bottom of frame (added 2026-10-03 per explicit request -- "text
# according to singer singing lyrics at bottom"). Each section's lines
# are shown ONE AT A TIME, evenly timed across that section's actual
# screen duration (see _make_pingpong_loop's caption_lines handling) --
# not all 4 lines at once, and not full word-level karaoke, but still
# roughly tracking where the singer is in each section. "chorus" is
# sung identically both times it appears in SCENE_SEQUENCE, so the
# same lines are correct both times.
#
# Exact lyrics as given by the channel owner (sourced from the real
# Suno lyrics box, 2026-10-03) -- see post_navaratri_song.py's module
# docstring for why this couldn't be filled in from this repo alone.
LYRIC_LINES: dict[str, list[str]] = {
    "intro": [
        "ఓం ఐం హ్రీం క్లీం చాముండాయై విచ్చే",
        "జయ జయ దుర్గమ్మా జగదంబా",
        "ఇంద్రకీలాద్రి వాసా కనకదుర్గమ్మా",
    ],
    "verse1": [
        "కృష్ణా నదీ తీరాన కొలువైన తల్లీ",
        "ఇంద్రకీలాద్రి శిఖరాన వెలిగే జ్యోతి",
        "త్రిశూలం ధరియించి రాక్షస సంహారీ",
        "సింహవాహినివై నడయాడే శక్తి",
    ],
    "chorus": [
        "స్వర్ణకవచధారిణి కనకదుర్గమ్మా",
        "శరణు శరణు అంటూ మొక్కేము తల్లీ",
        "చల్లని చూపులతో కాపాడవమ్మా",
        "వరములు కురిపించు కనకదుర్గమ్మా",
    ],
    "verse2": [
        "నవరాత్రి వేళలో అలంకారం నీదే",
        "బంగారు కవచాన శోభిల్లే రూపం",
        "భక్తుల గుండెల్లో భక్తి దీపం వెలిగించి",
        "చీకటిని పారద్రోలే వెలుగై నిలుచుంటివి",
    ],
    "bridge": [
        "అష్టాదశ శక్తి పీఠాలలో వెలసిన తల్లి",
        "ఆది శక్తి రూపానివి నీవే అమ్మా",
        "దుష్ట శిక్షణ శిష్ట రక్షణ చేసే తల్లి",
        "జగన్మాత నీకిదె మా వందనం",
    ],
    "outro": [
        "జయ జయ కనకదుర్గా జగజ్జననీ",
        "స్వర్ణకవచధారిణి కనకదుర్గమ్మా",
        "ఓం శ్రీ దుర్గాదేవ్యై నమః",
        "ఓం శ్రీ దుర్గాదేవ్యై నమః",
    ],
}


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AppError(f"Command failed: {' '.join(cmd)}\n{result.stderr[-3000:]}")


def _audio_duration_seconds(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise AppError(f"ffprobe failed on {audio_path}: {result.stderr}")
    return float(result.stdout.strip())


_CANVAS_W, _CANVAS_H = 1920, 1080


def _render_caption_png(text: str, out_path: Path) -> None:
    """Renders ONE lyric line onto a full-frame (1920x1080) transparent
    PNG, text centered near the bottom in a semi-transparent box --
    meant to be overlaid onto a video frame via ffmpeg's `overlay`
    filter at (0,0).

    Uses PIL + the project's own FontManager (RAQM/HarfBuzz layout),
    NOT ffmpeg's drawtext -- drawtext has no complex-script shaping
    (see images/fonts.py's module docstring) and visibly garbles
    Telugu conjuncts/vowel signs. Every other Telugu text image in
    this project already goes through PIL+RAQM for the same reason;
    this keeps lyric captions consistent with that, instead of
    reintroducing the same bug fresh via ffmpeg.
    """
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
    # Thin dark outline (drawn as 4 offset copies) so the white text
    # stays readable over bright parts of the background video too.
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        draw.text((text_x + ox, text_y + oy), text, font=font, fill=(0, 0, 0, 220))
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def _make_pingpong_loop(
    clip_path: Path, target_seconds: float, out_path: Path, caption_lines: list[str] | None = None,
) -> None:
    """Extends a short clip into a seamless ping-pong loop (forward +
    reverse, concatenated, then looped) of exactly target_seconds.

    If `caption_lines` is given, that section's lyric lines are shown
    ONE AT A TIME, each for an even share of target_seconds (e.g. 4
    lines over a 36s segment -> 9s each), composited in via chained
    `overlay` filters with an `enable` time window -- not all 4 lines
    at once, and not full word-level karaoke, but still roughly
    tracking the singer's position within the section (see
    LYRIC_LINES' docstring)."""
    reversed_path = clip_path.with_name(clip_path.stem + "_rev.mp4")
    _run(["ffmpeg", "-y", "-i", str(clip_path), "-vf", "reverse", "-an", str(reversed_path)])

    unit_path = clip_path.with_name(clip_path.stem + "_unit.mp4")
    concat_list = clip_path.with_name(clip_path.stem + "_concat.txt")
    concat_list.write_text(f"file '{clip_path.resolve()}'\nfile '{reversed_path.resolve()}'\n")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-an", str(unit_path)])

    unit_duration = _audio_duration_seconds(unit_path)
    loops_needed = int(target_seconds // unit_duration) + 2  # generous over-shoot, trimmed below

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
            _make_pingpong_loop(clip_paths[key], target_seconds, seg_out, caption_lines=LYRIC_LINES.get(key))
            segment_paths.append(seg_out)
            print(f"Segment {i} ('{key}'): {target_seconds:.1f}s -> {seg_out}")

    except FalGenerationError as exc:
        print(f"FAILED (fal.ai): {exc}", file=sys.stderr)
        return 1

    _assemble(song_path, segment_paths, f"{A_NAME}", OUTPUT_PATH)
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
