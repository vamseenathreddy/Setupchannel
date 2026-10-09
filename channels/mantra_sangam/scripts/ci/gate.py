"""RETIRED gate for the old single daily Divine Mantra Sangam post (09:00 IST). Mantra Sangam now posts
only through the five series workflows (rahu, shubh, durm, rashi, purana). This gate never posts, so a
leftover cron-job.org ping to post-divine-mantra-sangam.yml is a harmless no-op."""
import os
import sys


def main() -> int:
    print("Old single-post Divine Mantra Sangam workflow is retired -- nothing posted.")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write("post=false\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
