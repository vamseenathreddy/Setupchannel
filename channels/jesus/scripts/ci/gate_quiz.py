"""Gate for the Jesus Worship Waves Bible Quiz Short: day-seeded target minute inside
09:00-09:40 IST (a late backup run may still post until 11:00 IST). Run via:

  python -m channels.jesus.scripts.ci.gate_quiz
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(9, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(11, 0)

if __name__ == "__main__":
    sys.exit(gate.run("jesus_quiz", WINDOW_START, WINDOW_MINUTES, LATEST))
