"""Gate for Live Hyderabad: day-seeded target minute inside 14:00-14:40 IST (afternoon, between
Tollywood News and Gita Sloka's 15:00 slot; late backup until 16:30 IST). Run via:
python -m channels.live_hyderabad.scripts.ci.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(14, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(16, 30)

if __name__ == "__main__":
    sys.exit(gate.run("live_hyderabad", WINDOW_START, WINDOW_MINUTES, LATEST))
