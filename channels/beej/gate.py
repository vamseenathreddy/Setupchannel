"""Gate for the daily 6 AM beej mantra Short (three channels share beej_state.json, one POST_SLOT each).
Day-seeded target minute inside 06:00-06:40 IST; a late backup run may still post until 08:00 IST.

  BEEJ_CHANNEL=mahanavi|mantra_sangam|trance_beats POST_SLOT=<same> STATE_FILE=data/beej_state.json \\
      python -m channels.beej.gate
"""
import datetime as dt
import os
import sys

from channels.engine import gate

# Fixed start per channel (staggered 15 min: the three share one concurrency group).
START = {"mahanavi": dt.time(6, 0), "mantra_sangam": dt.time(6, 15), "trance_beats": dt.time(6, 30)}
WINDOW_MINUTES = 40
LATEST = dt.time(8, 0)

if __name__ == "__main__":
    sys.exit(gate.run(f"beej_{os.environ['BEEJ_CHANNEL']}", START[os.environ["BEEJ_CHANNEL"]], WINDOW_MINUTES, LATEST))
