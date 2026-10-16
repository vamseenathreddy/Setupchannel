"""Gate for the trending channel: POST_SLOT (t1..t4) picks the slot; a day-seeded random minute inside its window."""
import datetime as dt
import os
import sys

from channels.engine import gate
from channels.trending import config as cfg

if __name__ == "__main__":
    slot = os.environ["POST_SLOT"]
    hour = dict((s, h) for h, s in cfg.SLOTS)[slot]
    # latest = window start + 2 hours, so a late ping can still post but never into the next slot
    sys.exit(gate.run(f"trending_{slot}", dt.time(hour, 0), cfg.WINDOW_MINUTES, dt.time(min(hour + 2, 23), 59)))
