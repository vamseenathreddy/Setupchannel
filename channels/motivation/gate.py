"""Gate for the daily 9 PM "Purana motivation word" Short (Mahanavi). Day-seeded target minute inside
21:00-21:40 IST; a late backup run may still post until 23:00 IST. Uses POST_SLOT in beej_state.json.

  POST_SLOT=motivation STATE_FILE=data/beej_state.json python -m channels.motivation.gate
"""
import datetime as dt
import sys

from channels.engine import gate

WINDOW_START = dt.time(21, 0)
WINDOW_MINUTES = 40
LATEST = dt.time(23, 0)

if __name__ == "__main__":
    sys.exit(gate.run("motivation_mahanavi", WINDOW_START, WINDOW_MINUTES, LATEST))
