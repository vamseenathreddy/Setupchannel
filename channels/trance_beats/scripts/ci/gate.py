"""Gate for Channel C: day-seeded target minute inside 19:00-19:40 IST (evening
aarti time, distinct from Channel B's morning slot; late backup until 21:00 IST).
Run via: python -m channels.trance_beats.scripts.ci.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(19, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(21, 0)

if __name__ == "__main__":
    sys.exit(gate.run("trance_beats", WINDOW_START, WINDOW_MINUTES, LATEST))
