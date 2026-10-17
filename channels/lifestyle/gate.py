"""Gate for the weekly Sunday lifestyle video: posts only on Sunday (IST), inside a day-seeded minute of the
08:00-08:40 window, and at most once per day per channel (POST_SLOT). FORCE_POST=true bypasses everything.

  LIFESTYLE_LANG=te|hi POST_SLOT=<same> STATE_FILE=data/lifestyle_state_te.json python -m channels.lifestyle.gate
"""
import datetime as dt
import os
import sys

from channels.engine import gate

WINDOW_START = dt.time(8, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(11, 0)

if __name__ == "__main__":
    now = dt.datetime.now(gate.IST)
    if now.weekday() != 6 and os.environ.get("FORCE_POST") != "true" and "--force" not in sys.argv:
        print(f"DECISION: skip, not Sunday ({now:%A})")
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a") as f:
                f.write(f"post=false\ndate={now.date().isoformat()}\n")
        sys.exit(0)
    sys.exit(gate.run(f"lifestyle_{os.environ['LIFESTYLE_LANG']}", WINDOW_START, WINDOW_MINUTES, LATEST))
