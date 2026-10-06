"""Local preview tool: render a Short and its metadata without uploading anything or touching state.

  python -m src.run --date 2026-12-30             # what would post on that day
  python -m src.run --row q001 --out out/first    # preview one specific row

The real pipeline is scripts/post_ramana.py (behind the gate scripts/ci/ramana_gate.py).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from . import common, metadata, pick, render


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD, default today")
    ap.add_argument("--row", help="content row id to force")
    ap.add_argument("--out", default="out/preview")
    args = ap.parse_args()
    date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    rows = common.load_rows()
    special = common.special_for(date)
    if args.row:
        row, reason = next(r for r in rows if r["id"] == args.row), "forced"
    else:
        row, reason = pick.choose_row(rows, date, [])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    info = render.render(row, str(out / "short.mp4"), date.isoformat(), special, workdir=str(out))
    meta = metadata.bundle(row, special)
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{date} | {row['id']} | {reason} | {info}\n{meta['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
