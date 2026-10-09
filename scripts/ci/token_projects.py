"""Prints, for every saved YouTube token in data/, which Google Cloud project (OAuth client id prefix)
it belongs to. YouTube Data API quota (10,000 units/day by default) is per PROJECT, so tokens sharing a
project share one quota. Secrets are never printed."""
import glob
import json
import os
from collections import defaultdict

by_project = defaultdict(list)
for f in sorted(glob.glob("data/*token*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"{os.path.basename(f)}: unreadable ({exc})")
        continue
    cid = str(d.get("client_id", "")).split("-")[0] or "?"
    by_project[cid].append(os.path.basename(f))
for cid, files in by_project.items():
    print(f"PROJECT {cid} ({len(files)} token files share this quota):")
    for n in files:
        print(f"   {n}")
