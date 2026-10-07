"""bhagavatam series. python -m channels.trance_beats.scripts.post_bhagavatam [--dry-run] [--public] [--row ID]"""
import sys

from channels.trance_beats.scripts._series import main

if __name__ == "__main__":
    sys.exit(main("bhagavatam"))
