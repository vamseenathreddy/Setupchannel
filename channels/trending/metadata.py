"""Title, description, tags and comment for a trending Short. The source is always named and linked."""
from __future__ import annotations

from channels.trending import config as cfg
from channels.trending import regions
from channels.trending.sources import Story, trim

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
    "join": "తెలుగుదేశంతో కలిసి అడుగేయండి",
    "voice": "మీ నియోజకవర్గం, మీ గళం",
    "janasena": "కూటమి బలం: జనసేన, టీడీపీ, బీజేపీ",
}


def join_lines() -> list[str]:
    out = []
    if cfg.WHATSAPP_URL:
        out.append(f"WhatsApp గ్రూప్: {cfg.WHATSAPP_URL}")
    if cfg.TELEGRAM_URL:
        out.append(f"Telegram గ్రూప్: {cfg.TELEGRAM_URL}")
    return out


def hashtags(lang: str, niche: str, story: Story | None = None) -> list[str]:
    """YouTube shows the first three above the title: keep those the strongest. Then the district tags for this post."""
    tags = ["#TDP", "#AndhraPradesh", "#ChandrababuNaidu", "#PulseBoosting", "#Shorts", f"#{cfg.NICHE_TAG[niche]}",
            "#NaraLokesh", "#TeluguNews", "#TeluguDesam"]
    if niche == "janasena":
        tags[:3] = ["#Janasena", "#PawanKalyan", "#AndhraPradesh"]
        tags += ["#TDP"]
    if niche == "join":
        tags += ["#JoinTDP", "#TDPMembership"]
    if story is not None:
        for _te, en, region in regions.for_post(story.key, f"{story.headline} {story.summary}", 3):
            tags += ["#" + en.replace(" ", ""), "#" + region]
    seen, out = set(), []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:15]


def title(story: Story, lang: str, niche: str) -> str:
    tail = f" | {'Janasena' if niche == 'janasena' else 'TDP'} | {cfg.BRAND}"
    head = story.headline
    if len(head) + len(tail) <= 100:
        return head + tail
    cut = head[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;-")
    return f"{cut}…{tail}"


def tags(lang: str, niche: str, story: Story | None = None) -> list[str]:
    words = [cfg.BRAND, cfg.NICHE_EN[niche], cfg.niche_label(lang, niche), "TDP", "తెలుగుదేశం పార్టీ", "Telugu Desam Party",
             "Chandrababu Naidu", "చంద్రబాబు నాయుడు", "Nara Lokesh", "నారా లోకేశ్", "Andhra Pradesh", "ఆంధ్రప్రదేశ్",
             "Telugu news", "తెలుగు వార్తలు", "AP news", "AP politics", "AP assembly constituencies", "అన్ని నియోజకవర్గాలు", "shorts"]
    if niche == "janasena":
        words += ["Janasena", "జనసేన", "Pawan Kalyan", "పవన్ కళ్యాణ్", "Deputy CM Pawan Kalyan"]
    if story is not None:
        for te, en, region in regions.for_post(story.key, f"{story.headline} {story.summary}", 5):
            words += [en, te, f"{en} news"]
    out, total, seen = [], 0, set()
    for w in words:
        k = w.lower()
        cost = len(w) + (2 if " " in w else 0) + 1
        if k in seen or total + cost > 470:
            continue
        seen.add(k)
        out.append(w)
        total += cost
    return out


def source_line(story: Story) -> str:
    kind = "Source"
    return f"{kind}: {story.publisher}\nLink: {story.link}"


def area_lines(story: Story) -> list[str]:
    """Where this matters: districts the story names, then a rotation, across all three regions of Andhra Pradesh."""
    ds = regions.for_post(story.key, f"{story.headline} {story.summary}", 8)
    return [
        "ఈ వార్త ఆంధ్రప్రదేశ్‌లోని అన్ని జిల్లాలు, 175 నియోజకవర్గాల ప్రజల కోసం: " + ", ".join(d[0] for d in ds) + " మరియు ఉత్తరాంధ్ర, కోస్తాంధ్ర, రాయలసీమ ప్రాంతాలు.",
        "For people across Andhra Pradesh: " + ", ".join(d[1] for d in ds) + " and all 175 assembly constituencies.", ""]


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
        *area_lines(story),
        *join_lines(), *([""] if join_lines() else []),
        DISCLOSURE, "",
        f"{cfg.BRAND}: like, share and subscribe.", "",
        " ".join(hashtags(lang, niche, story)),
    ])


def bundle(story: Story, lang: str, niche: str) -> dict:
    return {
        "title": title(story, lang, niche),
        "description": description(story, lang, niche),
        "tags": tags(lang, niche, story),
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
            "text_primary": head, "text_summary": trim(story.summary, 190), "text_related": related,
            "text_secondary": f"{kind}: {story.publisher}"}
