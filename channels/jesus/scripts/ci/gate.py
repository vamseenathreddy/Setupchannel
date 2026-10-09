"""Gate for Jesus Worship Waves: day-seeded target minute inside 00:00-00:40 IST (a late
backup run may still post until 02:00 IST). Run via:

  python -m channels.jesus.scripts.ci.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(0, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(2, 0)

if __name__ == "__main__":
    sys.exit(gate.run("jesus", WINDOW_START, WINDOW_MINUTES, LATEST))
