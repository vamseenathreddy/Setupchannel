"""Andhra Pradesh regions and districts, so every post can carry local search keywords (SEO) and local stories can be
preferred. (telugu, english, region). Names are the common ones people search for."""
from __future__ import annotations

import hashlib

DISTRICTS = [
    ("శ్రీకాకుళం", "Srikakulam", "ఉత్తరాంధ్ర"), ("విజయనగరం", "Vizianagaram", "ఉత్తరాంధ్ర"),
    ("పార్వతీపురం మన్యం", "Parvathipuram Manyam", "ఉత్తరాంధ్ర"), ("అల్లూరి సీతారామరాజు", "Alluri Sitarama Raju", "ఉత్తరాంధ్ర"),
    ("విశాఖపట్నం", "Visakhapatnam", "ఉత్తరాంధ్ర"), ("అనకాపల్లి", "Anakapalli", "ఉత్తరాంధ్ర"),
    ("కాకినాడ", "Kakinada", "కోస్తాంధ్ర"), ("తూర్పుగోదావరి", "East Godavari", "కోస్తాంధ్ర"),
    ("కోనసీమ", "Konaseema", "కోస్తాంధ్ర"), ("పశ్చిమగోదావరి", "West Godavari", "కోస్తాంధ్ర"),
    ("ఏలూరు", "Eluru", "కోస్తాంధ్ర"), ("విజయవాడ", "Vijayawada", "కోస్తాంధ్ర"),
    ("కృష్ణా జిల్లా", "Krishna", "కోస్తాంధ్ర"), ("గుంటూరు", "Guntur", "కోస్తాంధ్ర"),
    ("పల్నాడు", "Palnadu", "కోస్తాంధ్ర"), ("బాపట్ల", "Bapatla", "కోస్తాంధ్ర"),
    ("ప్రకాశం", "Prakasam", "కోస్తాంధ్ర"), ("నెల్లూరు", "Nellore", "కోస్తాంధ్ర"),
    ("కర్నూలు", "Kurnool", "రాయలసీమ"), ("నంద్యాల", "Nandyal", "రాయలసీమ"),
    ("అనంతపురం", "Anantapur", "రాయలసీమ"), ("శ్రీ సత్యసాయి", "Sri Sathya Sai", "రాయలసీమ"),
    ("కడప", "Kadapa", "రాయలసీమ"), ("అన్నమయ్య", "Annamayya", "రాయలసీమ"),
    ("చిత్తూరు", "Chittoor", "రాయలసీమ"), ("తిరుపతి", "Tirupati", "రాయలసీమ"),
]
REGIONS = {"ఉత్తరాంధ్ర": "Uttarandhra", "కోస్తాంధ్ర": "CoastalAndhra", "రాయలసీమ": "Rayalaseema"}


def mentioned(text: str) -> list[tuple]:
    """Districts named in the text (Telugu or English)."""
    low = text.casefold()
    return [d for d in DISTRICTS if d[0].split()[0] in text or d[1].casefold() in low]


def for_post(key: str, text: str = "", n: int = 6) -> list[tuple]:
    """The districts to tag on this post: the ones the story names first, then a rotation seeded by the story key so
    that, across a day's 12 posts, every region and most districts get covered."""
    out = mentioned(text)[:3]
    start = int(hashlib.sha1(key.encode()).hexdigest(), 16) % len(DISTRICTS)
    i = 0
    while len(out) < n and i < len(DISTRICTS):
        d = DISTRICTS[(start + i * 4) % len(DISTRICTS)]  # stride 4 spreads picks across the three regions
        if d not in out:
            out.append(d)
        i += 1
    return out
