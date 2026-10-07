"""Gate for Divine Mantra Sangam: day-seeded target minute inside 09:00-09:40 IST (morning
prayer time; late backup until 11:00 IST). Run via: python -m channels.mantra_sangam.scripts.ci.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(9, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(11, 0)

if __name__ == "__main__":
    sys.exit(gate.run("mantra_sangam", WINDOW_START, WINDOW_MINUTES, LATEST))
