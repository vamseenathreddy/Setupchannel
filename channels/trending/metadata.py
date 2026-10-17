"""Title, description, tags and comment for a trending Short. The source is always named and linked."""
from __future__ import annotations

from channels.trending import config as cfg
from channels.trending.sources import Story

DISCLOSURE = ("ఈ ఛానెల్ తెలుగుదేశం పార్టీ అనుకూల దృక్పథంతో నడుస్తుంది. ఇందులోని విశ్లేషణ మా అభిప్రాయం; వార్తలు పేర్కొన్న "
              "మూలాల నుంచి తీసుకున్నవి. హక్కులు ఆయా ప్రచురణకర్తలవి.\n"
              "This channel is run from a pro-TDP point of view. The analysis is our opinion; the facts come from the "
              "sources named above. All rights belong to the original publishers.")

ANGLE = {  # one positive-angle line per niche, shown on the card and in the description (opinion, labelled as such)
    "chandrababu": "దూరదృష్టితో కూడిన పాలనకు ఇది మరో ఉదాహరణ",
    "lokesh": "యువతకు అవకాశాలు పెంచే దిశగా ఒక అడుగు",
    "tdp": "ప్రజాసేవలో పార్టీ చూపుతున్న నిబద్ధత",
    "nda": "డబుల్ ఇంజిన్ సహకారంతో రాష్ట్రానికి లాభం",
    "development": "రాష్ట్ర అభివృద్ధికి, ఉపాధికి ఊతం",
    "innovations": "సాంకేతికతతో పాలనలో కొత్త ఒరవడి",
}


def join_lines() -> list[str]:
    out = []
    if cfg.WHATSAPP_URL:
        out.append(f"WhatsApp గ్రూప్: {cfg.WHATSAPP_URL}")
    if cfg.TELEGRAM_URL:
        out.append(f"Telegram గ్రూప్: {cfg.TELEGRAM_URL}")
    return out


def hashtags(lang: str, niche: str) -> list[str]:
    tags = ["#PulseBoosting", "#Shorts", f"#{cfg.NICHE_TAG[niche]}", f"#{cfg.LANG_TAG[lang]}", "#Trending",
            "#TDP", "#TeluguDesam", "#ChandrababuNaidu", "#NaraLokesh", "#AndhraPradesh", "#TeluguNews"]
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
    tail = f" | TDP | {cfg.BRAND}"
    head = story.headline
    if len(head) + len(tail) <= 100:
        return head + tail
    cut = head[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;-")
    return f"{cut}…{tail}"


def tags(lang: str, niche: str) -> list[str]:
    words = [cfg.BRAND, "Pulse Boosting news", cfg.NICHE_EN[niche], cfg.niche_label(lang, niche), cfg.LANG_EN[lang],
             f"{cfg.LANG_EN[lang]} news", f"{cfg.NICHE_EN[niche]} news", "trending news", "TDP", "Telugu Desam Party",
             "Chandrababu Naidu", "Nara Lokesh", "Andhra Pradesh", "Telugu news", "AP news", "shorts"]
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
    kind = "Source"
    return f"{kind}: {story.publisher}\nLink: {story.link}"


def description(story: Story, lang: str, niche: str) -> str:
    more = [ANGLE[niche], ""]
    more += [story.summary, ""] if story.summary else []
    if story.related:
        more += ["Also reported:"] + [f"- {h} ({p})" for h, p in story.related] + [""]
    return "\n".join([
        story.headline, "",
        *more,
        source_line(story), "",
        cfg.INTRO[lang],
        cfg.INTRO["en"], "",
        *join_lines(), *([""] if join_lines() else []),
        DISCLOSURE, "",
        f"{cfg.BRAND}: like, share and subscribe.", "",
        " ".join(hashtags(lang, niche)),
    ])


def bundle(story: Story, lang: str, niche: str) -> dict:
    return {
        "title": title(story, lang, niche),
        "description": description(story, lang, niche),
        "tags": tags(lang, niche),
        "comment": f"{source_line(story)}\n{cfg.CTA[lang][2]}",
        "language": lang,
    }


def row_for(story: Story, lang: str, niche: str) -> dict:
    """The card: headline, the publisher's summary, related headlines, and a small source line."""
    head = story.headline
    if len(head) > 110:
        head = head[:110].rsplit(" ", 1)[0].rstrip(",.:;-") + "…"
    kind = "Source"
    related = "\n".join([ANGLE[niche]] + [f"• {h}" for h, _ in story.related[:2]])
    return {"id": story.key, "category": niche, "special": "",
            "text_primary": head, "text_summary": story.summary, "text_related": related,
            "text_secondary": f"{kind}: {story.publisher}"}
