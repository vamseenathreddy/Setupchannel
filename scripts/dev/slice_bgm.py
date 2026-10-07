"""Cut an uploaded song into BGM clips for the Jesus Worship Waves Shorts, and approve the
ones the owner likes.

  python scripts/dev/slice_bgm.py slice SONG.mp3 [SONG2.mp3 ...]   # -> assets/music/candidates/
  python scripts/dev/slice_bgm.py approve clip_name [clip_name ...] # candidates/ -> approved/
  python scripts/dev/slice_bgm.py list

Clips are CLIP_SECONDS long (one Short), cut back to back, with a short fade in/out and
loudness-normalised. Only files in assets/music/approved/ are ever used by the pipeline
(one clip per Short, rotating -- same idea as Ramana Maharshi TV's rotating Om clips), so the
owner listens to the candidates first and approves only the good ones.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

MUSIC = Path(__file__).resolve().parents[2] / "channels/jesus/assets/music"
CANDIDATES, APPROVED = MUSIC / "candidates", MUSIC / "approved"
CLIP_SECONDS = 15
FADE = 0.4


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def slice_song(song: Path) -> list[Path]:
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    total, made = duration(song), []
    n = int(total // CLIP_SECONDS)
    # Numbered 001, 002, ... (continuing after any existing candidates) so the owner can approve by number.
    next_no = max([int(p.stem) for p in CANDIDATES.glob("[0-9][0-9][0-9].mp3")] + [0]) + 1
    for i in range(n):
        start = i * CLIP_SECONDS
        out = CANDIDATES / f"{next_no + i:03d}.mp3"
        (CANDIDATES / "index.txt").open("a").write(f"{out.stem}\t{song.name}\t{start // 60}:{start % 60:02d}\n")
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(CLIP_SECONDS), "-i", str(song),
            "-af", f"afade=t=in:d={FADE},afade=t=out:st={CLIP_SECONDS - FADE}:d={FADE},loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "44100", "-b:a", "192k", str(out)], check=True)
        made.append(out)
    return made


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("slice"); s.add_argument("songs", nargs="+", type=Path)
    a = sub.add_parser("approve"); a.add_argument("clips", nargs="+")
    sub.add_parser("list")
    args = ap.parse_args()
    if args.cmd == "slice":
        for song in args.songs:
            clips = slice_song(song)
            print(f"{song.name}: {len(clips)} clips -> {CANDIDATES}")
    elif args.cmd == "approve":
        APPROVED.mkdir(parents=True, exist_ok=True)
        for name in args.clips:
            src = CANDIDATES / (name if name.endswith(".mp3") else name + ".mp3")
            if not src.exists():
                print(f"missing: {src.name}", file=sys.stderr); return 1
            shutil.copy2(src, APPROVED / src.name)
            print(f"approved: {src.name}")
    else:
        print("candidates:", len(list(CANDIDATES.glob('*.mp3'))), "| approved:", len(list(APPROVED.glob('*.mp3'))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
