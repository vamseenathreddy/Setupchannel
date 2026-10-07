"""Gate for Tollywood News: day-seeded target minute inside 13:00-13:40 IST (lunchtime, after
the morning entertainment-desk stories have published; late backup until 15:30 IST). Run via:
python -m channels.tollywood_news.scripts.ci.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(13, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(15, 30)

if __name__ == "__main__":
    sys.exit(gate.run("tollywood_news", WINDOW_START, WINDOW_MINUTES, LATEST))
