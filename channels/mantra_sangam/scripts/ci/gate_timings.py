"""Gates for the three daily Hindi timing Shorts (Divine Mantra Sangam). TIMING_KIND env: rahu | shubh | durm.

  shubh  04:00-04:40 IST (before the Brahma Muhurat it names ends), latest 07:00
  rahu   05:30-06:10 IST, latest 08:30
  durm   07:00-07:40 IST, latest 10:00
Run via: TIMING_KIND=rahu python -m channels.mantra_sangam.scripts.ci.gate_timings
"""
import datetime as dt
import os
import sys

from channels.engine import gate

SLOTS = {
    "shubh": ("mantra_shubh", dt.time(4, 0), 40, dt.time(7, 0)),
    "rahu": ("mantra_rahu", dt.time(5, 30), 40, dt.time(8, 30)),
    "durm": ("mantra_durm", dt.time(7, 0), 40, dt.time(10, 0)),
}

if __name__ == "__main__":
    key, start, minutes, latest = SLOTS[os.environ["TIMING_KIND"]]
    sys.exit(gate.run(key, start, minutes, latest))
