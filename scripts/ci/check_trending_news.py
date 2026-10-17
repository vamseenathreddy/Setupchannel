"""Report, per niche, how many latest-news stories the Pulse Boosting filters let through right now (no posting)."""
from channels.trending import sources
from channels.trending.sources import POLITICAL_QUERY

for n in POLITICAL_QUERY:
    try:
        st = sources.political_stories(n)
        top = "; ".join(f"{s.publisher}: {s.headline[:60]}" for s in st[:2])
        print(f"::notice::{n}: {len(st)} stories pass. {top}")
    except Exception as exc:  # noqa: BLE001
        print(f"::error::{n}: {type(exc).__name__}: {str(exc)[:150]}")
