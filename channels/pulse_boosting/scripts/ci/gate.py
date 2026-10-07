"""Gate for Pulse Boosting: day-seeded target minute inside 12:00-12:40 IST (midday, so the
"last 6 hours" trending window has a fresh morning news cycle to pull from; late backup until
14:30 IST). Run via: python -m channels.pulse_boosting.scripts.ci.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(12, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(14, 30)

if __name__ == "__main__":
    sys.exit(gate.run("pulse_boosting", WINDOW_START, WINDOW_MINUTES, LATEST))
