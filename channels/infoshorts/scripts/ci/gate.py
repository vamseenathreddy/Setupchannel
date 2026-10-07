"""Gate for InfoShorts Telugu: day-seeded target minute inside 07:00-07:40 IST (late backup
until 09:00 IST). Run via: python -m channels.infoshorts.scripts.ci.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(7, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(9, 0)

if __name__ == "__main__":
    sys.exit(gate.run("infoshorts", WINDOW_START, WINDOW_MINUTES, LATEST))
