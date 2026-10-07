"""Generic SEO metadata builder for Pattern-B (trending-headline) channels, shared by Pulse
Boosting, Tollywood News, and Live Hyderabad -- unlike Pattern A's per-channel metadata.py
(title/description text differs a lot channel to channel), these three only really differ in
channel name, hashtags, and keywords, so one parameterized builder covers all three.

Always attributes the real publisher by name AND links the original article in the
description -- see trending.py's module docstring for why (this surfaces real headlines, it
never invents or embellishes news/gossip content).
"""
import dataclasses
import os


@dataclasses.dataclass
class TrendingMetaConfig:
    channel_name: str
    core_tags: list        # first 3 shown above the title
    topic_tags: list        # channel-specific hashtags
    common_tags: list
    keywords: list
    intro: str               # one line describing the channel, used in every description
    comment_text: str        # seed comment (same every post -- content varies daily, comment doesn't need to)
    disclosure: str = ("This video surfaces a real headline from the publisher named below, linked in this "
                        "description. No claims beyond that headline are made by this channel.")
    tag_limit: int = 500
    hashtag_limit: int = 15


def _tag_cost(tag):
    return len(tag) + (2 if " " in tag else 0)


def _fit_tags(tags, limit):
    out, total, seen = [], 0, set()
    for tg in tags:
        k = tg.lower()
        if k in seen:
            continue
        cost = _tag_cost(tg) + (1 if out else 0)
        if total + cost > limit:
            continue
        seen.add(k)
        out.append(tg)
        total += cost
    return out


def hashtags(cfg: TrendingMetaConfig):
    tags = cfg.core_tags + cfg.topic_tags + cfg.common_tags
    seen, out = set(), []
    for h in tags:
        if h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[: cfg.hashtag_limit]


def title(row, cfg: TrendingMetaConfig):
    headline = row["text_primary"].strip()
    for cand in (f"{headline} | {cfg.channel_name}", headline):
        if len(cand) <= 100:
            return cand
    tail = f" | {cfg.channel_name}"
    cut = headline[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;")
    return f"{cut}…{tail}"


def description(row, cfg: TrendingMetaConfig, contact=None):
    contact = contact if contact is not None else os.environ.get("CONTACT_EMAIL", "")
    headline = row["text_primary"].strip()
    publisher = row.get("text_secondary", "").strip()
    link = row.get("source", "").strip()
    out = [headline, ""]
    out += [cfg.intro, ""]
    out += [cfg.disclosure, ""]
    if publisher:
        out += [f"Source: {publisher}" + (f" -- {link}" if link else "")]
        out += [""]
    out += [f"Like, share and subscribe to {cfg.channel_name}.", ""]
    out += [f"© {cfg.channel_name}. Headlines are the property of their original publishers; this channel "
            "surfaces and attributes them, it does not claim authorship."]
    if contact:
        out += [f"Contact: {contact}"]
    out += ["", " ".join(hashtags(cfg))]
    return "\n".join(out)


def tags(cfg: TrendingMetaConfig):
    return _fit_tags(cfg.keywords, cfg.tag_limit)


def srt(text, seconds=5):
    lines = "\n".join(s.strip() for s in text.split("|"))
    return f"1\n00:00:00,000 --> 00:00:{seconds:02d},000\n{lines}\n"


def make_bundle_fn(cfg: TrendingMetaConfig):
    """Returns a (row, special) -> dict bundle function matching every other channel's
    metadata.bundle shape, closed over this channel's TrendingMetaConfig."""
    def bundle(row, special=None):
        return {
            "title": title(row, cfg),
            "description": description(row, cfg),
            "tags": tags(cfg),
            "comment": cfg.comment_text,
        }
    return bundle


def make_captions_fn():
    def captions(row):
        return {"auto": srt(row["text_primary"])}
    return captions
