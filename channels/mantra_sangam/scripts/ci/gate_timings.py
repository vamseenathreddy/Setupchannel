"""Gates for the Hindi Shorts (Divine Mantra Sangam), on the same IST windows as Mahanavi Spirituals.
TIMING_KIND env: rahu | shubh | durm | rashi | purana.

  rahu 00:05-00:30, shubh 01:05-01:30, durm 02:05-02:30 (panchang for the new day), rashi 08:00-08:50, purana 17:00-17:50
Run via: TIMING_KIND=rahu python -m channels.mantra_sangam.scripts.ci.gate_timings
"""
import datetime as dt
import os
import sys

from channels.engine import gate

SLOTS = {  # same windows as Mahanavi Spirituals (IST); the day's target minute falls inside the window
    "rahu": ("mantra_rahu", dt.time(0, 5), 25, dt.time(1, 0)),
    "shubh": ("mantra_shubh", dt.time(1, 5), 25, dt.time(2, 0)),
    "durm": ("mantra_durm", dt.time(2, 5), 25, dt.time(3, 0)),
    "rashi": ("mantra_rashi", dt.time(8, 0), 50, dt.time(9, 0)),
    "purana": ("mantra_purana", dt.time(17, 0), 50, dt.time(18, 0)),
}

if __name__ == "__main__":
    key, start, minutes, latest = SLOTS[os.environ["TIMING_KIND"]]
    sys.exit(gate.run(key, start, minutes, latest))
