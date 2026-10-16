"""Title, description, tags and comment for a trending Short. The source is always named and linked."""
from __future__ import annotations

from channels.trending import config as cfg
from channels.trending.sources import Story

DISCLOSURE = ("This Short surfaces a real headline from the source named above, linked in this description. "
              "It makes no claims beyond that headline. All rights belong to the original publisher.")


def hashtags(lang: str, niche: str) -> list[str]:
    tags = ["#PulseBoosting", "#Shorts", f"#{cfg.NICHE_TAG[niche]}", f"#{cfg.LANG_TAG[lang]}", "#Trending",
            "#IndiaNews", "#LatestNews", "#TrendingNow", "#NewsShorts"]
    nat = cfg.niche_label(lang, niche).replace(" ", "")
    if lang != "en":
        tags.append("#" + nat)
    seen, out = set(), []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:15]


def title(story: Story, lang: str, niche: str) -> str:
    tail = f" | {cfg.NICHE_EN[niche]} | {cfg.BRAND}" if lang != "en" else f" | {cfg.BRAND}"
    head = story.headline
    if len(head) + len(tail) <= 100:
        return head + tail
    cut = head[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;-")
    return f"{cut}…{tail}"


def tags(lang: str, niche: str) -> list[str]:
    words = [cfg.BRAND, "Pulse Boosting news", cfg.NICHE_EN[niche], cfg.niche_label(lang, niche), cfg.LANG_EN[lang],
             f"{cfg.LANG_EN[lang]} news", f"{cfg.NICHE_EN[niche]} news", "trending news", "news today", "India news",
             "latest news", "news shorts", "breaking news", "trending now", "shorts"]
    out, total, seen = [], 0, set()
    for w in words:
        k = w.lower()
        cost = len(w) + (2 if " " in w else 0) + 1
        if k in seen or total + cost > 480:
            continue
        seen.add(k)
        out.append(w)
        total += cost
    return out


def source_line(story: Story) -> str:
    kind = "YouTube trending, creator" if story.kind == "yt" else "Source"
    return f"{kind}: {story.publisher}\nLink: {story.link}"


def description(story: Story, lang: str, niche: str) -> str:
    return "\n".join([
        story.headline, "",
        source_line(story), "",
        cfg.INTRO[lang],
        cfg.INTRO["en"] if lang != "en" else "", "",
        DISCLOSURE, "",
        f"{cfg.BRAND} brings trending news in Telugu, Hindi, English, Tamil, Kannada and Malayalam. "
        "Like, share and subscribe.", "",
        " ".join(hashtags(lang, niche)),
    ])


def bundle(story: Story, lang: str, niche: str) -> dict:
    return {
        "title": title(story, lang, niche),
        "description": description(story, lang, niche),
        "tags": tags(lang, niche),
        "comment": f"{source_line(story)}\n{cfg.CTA[lang][1]}",
        "language": lang,
    }


def row_for(story: Story, lang: str, niche: str) -> dict:
    """The card: label, headline (trimmed to a readable length), and the source."""
    head = story.headline
    if len(head) > 110:
        head = head[:110].rsplit(" ", 1)[0].rstrip(",.:;-") + "…"
    src = f"{'YouTube' if story.kind == 'yt' else 'Source'}: {story.publisher}"
    return {"id": story.key, "category": niche, "special": "",
            "label": ("TRENDING • " + cfg.NICHE_EN[niche].upper()) if lang == "en"
            else f"{cfg.niche_label(lang, niche)} • {cfg.NICHE_EN[niche]}",
            "text_primary": head, "text_secondary": src}
