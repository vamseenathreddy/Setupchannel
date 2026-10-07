"""Pattern-B content source: one real, currently-trending headline per day, fetched from
Google News RSS -- free, no API key, no account, no billing (satisfies "reduce very less
amount of usage"). Used by Pulse Boosting (general news), Tollywood News (Telugu film
industry), and Live Hyderabad (city-specific), each with their own query (see each channel's
channel_config.py).

Deliberately does NOT write or embellish the headline, and does not generate commentary,
rumor, or unverified claims of its own -- it only ever surfaces a REAL headline a real outlet
already published, with that outlet named and linked as the source in both the video
description and the on-screen text. This keeps the "gossip"/"news" channels factual
(aggregation + attribution) rather than putting Claude in the position of authoring or
inventing news/gossip content, which would be a real accuracy/liability risk. A human should
still spot-check posts periodically -- see each channel's README.

Google News RSS's own `when:Nh` search qualifier does the "last N hours" filtering server-side
(one HTTP GET, nothing else), so "popular content of last 6 hours" is satisfied directly by
the query string rather than by fetching lots of candidates and filtering locally.

Uses only the Python standard library (urllib + xml.etree) -- no extra pip dependency, and the
XML-parsing logic (parse_rss) is a pure function so it can be unit tested against a static
sample feed without a network call.
"""
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

USER_AGENT = "Mozilla/5.0 (compatible; mahanavi-spirituals-channel-bot/1.0)"


@dataclass
class Story:
    headline: str          # with the trailing " - Publisher" suffix stripped
    publisher: str
    link: str
    pub_date: str


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def parse_rss(xml_text: str) -> list[Story]:
    """Pure function: parse a Google News RSS feed's XML text into Story objects, in feed
    order (Google News already ranks by relevance for a search query)."""
    root = ET.fromstring(xml_text)
    out = []
    for item in root.findall("./channel/item"):
        title = _strip_html(item.findtext("title") or "")
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        publisher = _strip_html(source_el.text) if source_el is not None and source_el.text else ""
        # Google News titles are "Headline - Publisher Name" -- strip the trailing publisher
        # if it matches the <source> element, so the on-screen text is just the headline.
        if publisher and title.endswith(f" - {publisher}"):
            title = title[: -(len(publisher) + 3)].strip()
        if title and link:
            out.append(Story(headline=title, publisher=publisher or "Google News", link=link, pub_date=pub_date))
    return out


def is_informative(story: "Story", min_words: int = 5, min_chars: int = 25) -> bool:
    """A usable on-screen headline: long enough to carry information (not a bare brand/page title like
    just "NASA") and not merely the publisher's name repeated."""
    h = story.headline.strip()
    if len(h) < min_chars or len(h.split()) < min_words:
        return False
    return h.lower().rstrip(". ") != story.publisher.lower().rstrip(". ")


def fetch_top_story(query: str, hl: str = "en-IN", gl: str = "IN", ceid: str = "IN:en",
                     hours: int = 6, exclude_links: frozenset[str] = frozenset(), timeout: int = 20) -> Story | None:
    """Fetch the top (most relevant) story for `query` published in the last `hours` hours,
    skipping any link already in exclude_links (recent used_ids, to avoid an exact repeat).
    Returns None if nothing fresh is found (the pipeline then skips posting for today rather
    than forcing a stale or fabricated story)."""
    q = f"{query} when:{hours}h"
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": hl, "gl": gl, "ceid": ceid})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        xml_text = resp.read().decode("utf-8", errors="replace")
    for story in parse_rss(xml_text):
        if story.link not in exclude_links and is_informative(story):
            return story
    return None
