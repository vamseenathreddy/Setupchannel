"""Gate for the Jesus Worship Waves EVENING Bible Quiz Short: day-seeded target minute inside
18:00-18:40 IST (a late backup run may still post until 20:00 IST). Run via:

  python -m channels.jesus.scripts.ci.gate_quiz
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(18, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(20, 0)

if __name__ == "__main__":
    sys.exit(gate.run("jesus_quiz", WINDOW_START, WINDOW_MINUTES, LATEST))
