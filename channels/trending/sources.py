"""Where the stories come from. Two free, real-world sources only; nothing is written or embellished here.

1. Google News topic feeds, one per language edition (te, hi, ta, kn, ml, en). Native-language headlines come
   straight from the publisher, so no translation is involved. Needs no key.
2. YouTube "most popular in India" (videos.list chart=mostPopular, 1 quota unit), filtered to the language and
   category. Used as a source for Cinema and Viral, and as a fallback for the other niches.

Every story carries its publisher (or YouTube channel) and a link, which go on the card and in the description.
parse_rss, clean_title, matches_language and fresh_enough are pure functions so tests need no network."""
from __future__ import annotations

import email.utils
import hashlib
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

USER_AGENT = "Mozilla/5.0 (compatible; trending-shorts-bot/1.0)"

# language -> (hl, gl, ceid, unicode block start, end) ; en uses Latin.
EDITIONS = {
    "te": ("te", "IN", "IN:te"),
    "hi": ("hi", "IN", "IN:hi"),
    "ta": ("ta", "IN", "IN:ta"),
    "kn": ("kn", "IN", "IN:kn"),
    "ml": ("ml", "IN", "IN:ml"),
    "en": ("en-IN", "IN", "IN:en"),
}
SCRIPT_RANGE = {"te": (0x0C00, 0x0C7F), "hi": (0x0900, 0x097F), "ta": (0x0B80, 0x0BFF),
                "kn": (0x0C80, 0x0CFF), "ml": (0x0D00, 0x0D7F)}

# niche -> Google News topic, and YouTube category (None = overall chart)
NEWS_TOPIC = {"breaking": "NATION", "sports": "SPORTS", "cinema": "ENTERTAINMENT", "technology": "TECHNOLOGY",
              "business": "BUSINESS", "health": "HEALTH", "viral": "NATION"}
YT_CATEGORY = {"breaking": "25", "sports": "17", "cinema": "24", "technology": "28", "viral": None}
TOP_N = 10
# order of sources to try per niche
SOURCE_ORDER = {"innovations": ("bank", "news"), "development": ("news", "bank"), "join": ("bank",), "voice": ("bank",),
                "janasena": ("news", "bank")}
DEFAULT_ORDER = ("news", "bank")

# TDP-supportive channel (2026-10-17): Telugu political search feeds, keyword-filtered.
POLITICAL_QUERY = {
    "chandrababu": ["చంద్రబాబు నాయుడు", "సీఎం చంద్రబాబు"], "lokesh": ["నారా లోకేశ్", "మంత్రి లోకేశ్"],
    "tdp": ["తెలుగుదేశం పార్టీ", "టీడీపీ"],
    "nda": ["కూటమి ప్రభుత్వం", "కూటమి ప్రభుత్వం ఆంధ్రప్రదేశ్ అభివృద్ధి", "ఎన్డీఏ ఆంధ్రప్రదేశ్"],
    "janasena": ["జనసేన పవన్ కళ్యాణ్", "డిప్యూటీ సీఎం పవన్ కళ్యాణ్"],
    "development": "ఆంధ్రప్రదేశ్ అభివృద్ధి పెట్టుబడులు", "innovations": "ఆంధ్రప్రదేశ్ ప్రభుత్వం కొత్త పథకం సాంకేతికత",
}
# Headlines that are about the opposition or about trouble are skipped: the channel only carries positive stories.
EXCLUDE = ("వైఎస్ఆర్సీపీ", "వైసీపీ", "జగన్", "YSRCP", "YCP", "Jagan", "అరెస్ట్", "హత్య", "మృతి", "ప్రమాదం", "దాడి",
           "అత్యాచారం", "విమర్శ", "ఆరోపణ", "కుంభకోణం", "వివాదం", "మరణ", "ఆత్మహత్య", "కేసు", "దుర్ఘటన", "నిరసన", "సమాధి", "గల్లంతు", "విషాదం", "దుర్మరణం", "బలి", "హతం", "అగ్నిప్రమాదం",
           "వరద", "భూకంపం", "సినిమా", "చిత్రం", "నటన", "హీరో", "మూవీ", "ట్రైలర్", "బాక్సాఫీస్", "ఓజీ")
SUBJECT = {  # the headline must actually be about the niche's subject
    "chandrababu": ("చంద్రబాబు", "సీఎం", "బాబు"), "lokesh": ("లోకేశ్", "లోకేష్"), "tdp": ("టీడీపీ", "తెలుగుదేశం", "తెదేపా"),
    "nda": ("కూటమి", "ఎన్డీఏ", "జనసేన", "బీజేపీ"), "janasena": ("జనసేన", "పవన్"),
    "development": ("ఆంధ్రప్రదేశ్", "ఏపీ", "అమరావతి", "రాష్ట్ర", "విశాఖ"),
}
POSITIVE = ("అభివృద్ధి", "పెట్టుబడ", "ఉద్యోగ", "ప్రారంభ", "శంకుస్థాపన", "ఒప్పందం", "పథకం", "నిధులు", "ప్రశంస",
            "హర్షం", "శుభవార్త", "అమరావతి", "ఐటీ", "డేటా సెంటర్", "ఏఐ", "పరిశ్రమ", "రైతు", "మహిళ", "విద్య",
            "అవార్డు", "కృషి", "ఆవిష్కరణ", "సాంకేతిక", "మంజూరు", "పెంపు", "భరోసా", "సంక్షేమ", "లక్ష")
# Outlets preferred first (Eenadu, Andhra Jyothy, then other mainstream Telugu outlets).
PREFERRED = ("ఈనాడు", "Eenadu", "ఆంధ్రజ్యోతి", "Andhra Jyothy", "Andhrajyothy", "సాక్షి_x", "Sakshi_x")
BLOCKED_PUBLISHERS = ("సాక్షి", "Sakshi")  # the opposition-run outlet; not used as a source


def is_positive(headline: str, summary: str = "") -> bool:
    text = f"{headline} {summary}"
    if any(x.casefold() in text.casefold() for x in EXCLUDE):
        return False
    return any(x in text for x in POSITIVE)


def political_stories(niche: str, lang: str = "te") -> list[Story]:
    """Telugu Google News search for the niche's subject: positive, non-opposition headlines, preferred outlets first."""
    import urllib.parse

    queries = POLITICAL_QUERY[niche]
    queries = [queries] if isinstance(queries, str) else queries
    found, seen = [], set()
    for text in queries:  # several searches per niche = a wider pool of the latest stories
        q = urllib.parse.quote(f"{text} when:2d")
        url = f"https://news.google.com/rss/search?q={q}&hl=te&gl=IN&ceid=IN:te"
        try:
            batch = parse_rss(_get(url))
        except Exception as exc:  # noqa: BLE001 - one failing query must not lose the others
            print(f"::warning::news query '{text}' failed: {type(exc).__name__}")
            continue
        for x in batch:
            if x.link not in seen:
                seen.add(x.link)
                found.append(x)
    out = [s for s in found if is_informative(s) and matches_language(s.headline, "te")
           and not any(b in s.publisher for b in BLOCKED_PUBLISHERS)
           and is_positive(s.headline)
           and (niche not in SUBJECT or any(w in s.headline for w in SUBJECT[niche]))]
    from channels.trending.regions import mentioned

    out.sort(key=lambda x: (0 if mentioned(x.headline) else 1, 0 if any(p in x.publisher for p in PREFERRED) else 1, x.rank))
    for i, x in enumerate(out, start=1):
        x.rank = i
    return out


@dataclass
class Story:
    headline: str
    publisher: str
    link: str
    published: datetime | None = None
    kind: str = "news"  # "news" | "yt"
    summary: str = ""   # the publisher's own one or two line summary (meta description), when available
    related: tuple = ()  # (headline, publisher) pairs from the same story cluster
    rank: int = 0        # position in the source's own trending order (1 = top); 0 = unknown

    @property
    def key(self) -> str:
        norm = re.sub(r"[\W_]+", " ", self.headline.casefold()).strip()[:90]
        return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def clean_title(title: str, publisher: str = "") -> str:
    """Drop the trailing ' - Publisher', hashtags, emoji-heavy tails and extra spaces."""
    t = _strip_html(title)
    if publisher and t.endswith(f" - {publisher}"):
        t = t[: -(len(publisher) + 3)]
    t = re.sub(r"#\S+", "", t)
    t = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️]", "", t)
    t = re.sub(r"\s+", " ", t).strip(" -|:")
    return t


def parse_rss(xml_text: str) -> list[Story]:
    root = ET.fromstring(xml_text)
    out = []
    for position, item in enumerate(root.findall("./channel/item"), start=1):
        src = item.find("source")
        publisher = _strip_html(src.text) if src is not None and src.text else ""
        title = clean_title(item.findtext("title") or "", publisher)
        link = (item.findtext("link") or "").strip()
        when = None
        raw = (item.findtext("pubDate") or "").strip()
        if raw:
            try:
                when = email.utils.parsedate_to_datetime(raw)
            except (TypeError, ValueError):
                when = None
        if title and link:
            out.append(Story(title, publisher or "Google News", link, when, "news",
                             related=_related(item.findtext("description") or "", title), rank=position))
    return out


def _related(description_html: str, main_title: str) -> tuple:
    """Google News lists the other outlets' headlines for the same story in <description>. Real headlines only."""
    out = []
    for href_text, pub in re.findall(r"<a [^>]*>(.*?)</a>(?:&nbsp;|\s)*<font[^>]*>(.*?)</font>", description_html, re.S):
        head = clean_title(href_text, _strip_html(pub))
        pub = _strip_html(pub)
        if head and head.casefold() != main_title.casefold() and len(head) >= 18:
            out.append((head, pub))
    return tuple(out)


def is_informative(s: Story, min_chars: int = 18, min_words: int = 3) -> bool:
    h = s.headline.strip()
    if len(h) < min_chars or len(h.split()) < min_words or len(h) > 160:
        return False
    return h.casefold().rstrip(". ") != s.publisher.casefold().rstrip(". ")


def matches_language(text: str, lang: str) -> bool:
    """Native-script languages: at least a third of the letters are in that script. English: mostly ASCII letters."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    if lang == "en":
        return sum(c.isascii() for c in letters) / len(letters) > 0.9
    lo, hi = SCRIPT_RANGE[lang]
    return sum(lo <= ord(c) <= hi for c in letters) / len(letters) >= 0.33


def fresh_enough(s: Story, now: datetime, hours: int) -> bool:
    return s.published is None or now - s.published <= timedelta(hours=hours)


def _get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def news_stories(niche: str, lang: str) -> list[Story]:
    if niche in POLITICAL_QUERY:
        return political_stories(niche, lang)
    hl, gl, ceid = EDITIONS[lang]
    url = (f"https://news.google.com/rss/headlines/section/topic/{NEWS_TOPIC[niche]}"
           f"?hl={hl}&gl={gl}&ceid={ceid}")
    # Google sometimes serves another language's outlet in an edition (a Hindi story in the kn feed): drop those,
    # otherwise the card shows glyphs the language's font lacks (boxes).
    return [s for s in parse_rss(_get(url)) if is_informative(s) and matches_language(s.headline, lang)]


def youtube_stories(yt, niche: str, lang: str) -> list[Story]:
    """Most popular videos in India right now, in this language. Surfaces the title and the creator's channel as the
    source; no footage is ever reused."""
    kw = dict(part="snippet", chart="mostPopular", regionCode="IN", maxResults=50)
    cat = YT_CATEGORY.get(niche)
    if cat:
        kw["videoCategoryId"] = cat
    items = yt.videos().list(**kw).execute().get("items", [])
    out = []
    for v in items:
        sn = v["snippet"]
        title = clean_title(sn.get("title", ""))
        if not matches_language(title, lang):
            continue
        when = None
        try:
            when = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            pass
        s = Story(title, sn.get("channelTitle", "YouTube"), f"https://www.youtube.com/watch?v={v['id']}", when, "yt")
        if is_informative(s):
            s.rank = len(out) + 1  # position among the language's trending videos
            out.append(s)
    return out


def _meta_description(page_html: str) -> str:
    for pat in (r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
                r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:description["\']',
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']'):
        m = re.search(pat, page_html, re.S | re.I)
        if m:
            return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
    return ""


def trim(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.:;-") + "…"


def article_summary(link: str, lang: str, headline: str, timeout: int = 15) -> str:
    """The publisher's own summary line (its meta description) for the story, or ''. Resolves Google News' encoded
    link first. Never copies article body text. Any failure returns ''."""
    try:
        from googlenewsdecoder import gnewsdecoder

        res = gnewsdecoder(link, interval=1)
        ok = res.get("status", res.get("success"))  # the decoder library reports it as "success" in newer versions
        url = res.get("decoded_url") if ok else ""
        if not url:
            print(f"::notice::no summary (link not decoded: {str(res)[:120]})")
            return ""
        page = _get(url, timeout)[:400_000]
        text = _meta_description(page)
        if not text or not matches_language(text, lang) or text.casefold().startswith(headline.casefold()[:40]):
            print(f"::notice::no summary (page meta unusable: {text[:60]!r})")
            return ""
        return trim(text, 260)
    except Exception as exc:  # noqa: BLE001
        print(f"::notice::no summary ({type(exc).__name__}: {exc})")
        return ""


def enrich(story: Story, lang: str) -> Story:
    """Add reading matter: the publisher's summary and up to four related headlines in the same language."""
    if story.kind == "news":
        story.summary = article_summary(story.link, lang, story.headline)
    story.related = tuple((trim(h, 90), p) for h, p in story.related if matches_language(h, lang))[:4]
    return story


def pick_story(niche: str, lang: str, used: set[str], yt=None, now: datetime | None = None,
               fetch_news=news_stories, fetch_yt=youtube_stories, fetch_bank=None) -> Story | None:
    """First unused, informative, recent story for this niche and language. Tries the niche's sources in order, then
    widens the freshness window from 8 to 30 hours. Returns None when nothing qualifies."""
    now = now or datetime.now(timezone.utc)
    pools: list[list[Story]] = []
    if fetch_bank is None:
        from channels.trending.bank import bank_stories as fetch_bank
    for src in SOURCE_ORDER.get(niche, DEFAULT_ORDER):
        try:
            if src == "bank":
                pools.append(fetch_bank(niche))
            elif src == "news":
                pools.append(fetch_news(niche, lang))
            elif yt is not None:
                pools.append(fetch_yt(yt, niche, lang))
        except Exception as exc:  # noqa: BLE001 - one failing source must not stop the slot
            print(f"::warning::{src} source failed for {niche}/{lang}: {type(exc).__name__}: {exc}")
    for hours in (8, 30):
        for pool in pools:
            # Only the source's top 10. Widest coverage first (most outlets carrying the story = most reach), then
            # shorter headlines (they read better on a 5 second card), then the source's own order.
            top = [x for x in pool if 0 < x.rank <= TOP_N or x.rank == 0]
            for s in sorted(top, key=lambda x: (-len(x.related), len(x.headline) > 85, x.rank)):
                if s.key not in used and fresh_enough(s, now, hours):
                    return s
    return None
