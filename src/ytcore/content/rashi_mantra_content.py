"""
Static content for the "Rashi Mantra of the Month" Shorts series.

WHY THIS EXISTS: competitor research (2026-10-01) into channels YouTube's
own "audience also watches" panel surfaces for this channel found that
rashi/zodiac-prediction Shorts (e.g. Kenisha Channel, a 20k-subscriber
Telugu channel) pull dramatically more views than their subscriber count
would suggest -- one example hit 71k views on a 20k-subscriber channel.
Same production style as this channel already uses (static Telugu text
card, no voiceover), different content pillar from the daily Panchang
alert Shorts. See /areas/... channel strategy notes for the fuller
analysis; this module is the first implementation step.

NOT PROKERALA: per explicit product decision, this series does NOT call
the Prokerala API (that's for daily, date-specific Panchang timings --
tithi/nakshatra/rahu kalam etc. -- which change every day). A rashi's
ruling planet and that planet's traditional chanting mantra are FIXED,
ancient associations from classical Vedic astrology (Jyotisha) -- they
don't change day to day, so there's nothing to fetch. This data is typed
in directly below.

COPYRIGHT: every mantra here is a single-line Sanskrit "bija" (seed)
salutation to a Navagraha (the nine classical planets) -- e.g. "ఓం
సూర్యాయ నమః" (Om, salutations to Surya). These are centuries-old
liturgical formulas repeated verbatim across thousands of public temple
plaques, printed panchangams, and devotional publications; they are
traditional/religious material in the public domain, not any single
author's copyrighted work -- consistent with the user's own read that
devotional content is "mostly not copyrighted". No modern commentary,
translation, or third-party description is reproduced here; only the
mantra line itself and a short original benefit description written for
this channel.

"Mantra of the month": the series name, not a monthly-changing mantra --
each rashi's ruling-planet mantra is a fixed, evergreen association in
Jyotisha. The series rotates through all 12 rashis (one per post), and
a rashi can be re-featured in a later month as a recurring reminder.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RashiMantraContent:
    name_te: str  # Telugu rashi name, e.g. "మేషం"
    name_en: str  # English/transliterated name, e.g. "Mesha (Aries)"
    symbol_te: str  # short symbol description, e.g. "పొట్టేలు" (ram)
    ruling_planet_te: str  # e.g. "కుజుడు (అంగారకుడు)"
    ruling_planet_en: str  # e.g. "Mars (Kuja)"
    mantra_te: str  # the chanting mantra itself, Telugu script
    mantra_transliteration: str  # Roman-script transliteration, for the video description
    benefit_te: str  # one short line on what chanting this mantra is traditionally said to support
    chant_count_te: str  # traditional recommended repetition count, e.g. "108 సార్లు"


# Order follows the standard Jyotisha rashi sequence (Mesha first).
RASHI_MANTRAS: list[RashiMantraContent] = [
    RashiMantraContent(
        name_te="మేషం",
        name_en="Mesha (Aries)",
        symbol_te="పొట్టేలు రాశి",
        ruling_planet_te="కుజుడు",
        ruling_planet_en="Mars (Kuja)",
        mantra_te="ఓం అంగారకాయ నమః",
        mantra_transliteration="Om Angarakaya Namah",
        benefit_te="ధైర్యం, ఆత్మవిశ్వాసం, శక్తి కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="వృషభం",
        name_en="Vrishabha (Taurus)",
        symbol_te="ఎద్దు రాశి",
        ruling_planet_te="శుక్రుడు",
        ruling_planet_en="Venus (Shukra)",
        mantra_te="ఓం శుక్రాయ నమః",
        mantra_transliteration="Om Shukraya Namah",
        benefit_te="సంపద, సౌందర్యం, సంతోషం కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="మిథునం",
        name_en="Mithuna (Gemini)",
        symbol_te="మిథున రాశి",
        ruling_planet_te="బుధుడు",
        ruling_planet_en="Mercury (Budha)",
        mantra_te="ఓం బుధాయ నమః",
        mantra_transliteration="Om Budhaya Namah",
        benefit_te="బుద్ధి వికాసం, వాక్చాతుర్యం కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="కర్కాటకం",
        name_en="Karkataka (Cancer)",
        symbol_te="కర్కాటక రాశి",
        ruling_planet_te="చంద్రుడు",
        ruling_planet_en="Moon (Chandra)",
        mantra_te="ఓం చంద్రాయ నమః",
        mantra_transliteration="Om Chandraya Namah",
        benefit_te="మనశ్శాంతి, కుటుంబ సౌఖ్యం కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="సింహం",
        name_en="Simha (Leo)",
        symbol_te="సింహ రాశి",
        ruling_planet_te="సూర్యుడు",
        ruling_planet_en="Sun (Surya)",
        mantra_te="ఓం సూర్యాయ నమః",
        mantra_transliteration="Om Suryaya Namah",
        benefit_te="ఆరోగ్యం, నాయకత్వ లక్షణాల కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="కన్య",
        name_en="Kanya (Virgo)",
        symbol_te="కన్యా రాశి",
        ruling_planet_te="బుధుడు",
        ruling_planet_en="Mercury (Budha)",
        mantra_te="ఓం బుధాయ నమః",
        mantra_transliteration="Om Budhaya Namah",
        benefit_te="విద్య, ఏకాగ్రత, విశ్లేషణ శక్తి కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="తుల",
        name_en="Tula (Libra)",
        symbol_te="తులా రాశి",
        ruling_planet_te="శుక్రుడు",
        ruling_planet_en="Venus (Shukra)",
        mantra_te="ఓం శుక్రాయ నమః",
        mantra_transliteration="Om Shukraya Namah",
        benefit_te="సమతుల్యత, సత్సంబంధాల కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="వృశ్చికం",
        name_en="Vrishchika (Scorpio)",
        symbol_te="వృశ్చిక రాశి",
        ruling_planet_te="కుజుడు",
        ruling_planet_en="Mars (Kuja)",
        mantra_te="ఓం అంగారకాయ నమః",
        mantra_transliteration="Om Angarakaya Namah",
        benefit_te="అంతర్గత శక్తి, రక్షణ కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="ధనుస్సు",
        name_en="Dhanussu (Sagittarius)",
        symbol_te="ధనుస్సు రాశి",
        ruling_planet_te="గురుడు (బృహస్పతి)",
        ruling_planet_en="Jupiter (Guru)",
        mantra_te="ఓం బృహస్పతయే నమః",
        mantra_transliteration="Om Brihaspataye Namah",
        benefit_te="జ్ఞానం, అదృష్టం, శుభ ఫలితాల కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="మకరం",
        name_en="Makara (Capricorn)",
        symbol_te="మకర రాశి",
        ruling_planet_te="శని",
        ruling_planet_en="Saturn (Shani)",
        mantra_te="ఓం శనయే నమః",
        mantra_transliteration="Om Shanaye Namah",
        benefit_te="క్రమశిక్షణ, ఓర్పు, స్థిరత్వం కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="కుంభం",
        name_en="Kumbha (Aquarius)",
        symbol_te="కుంభ రాశి",
        ruling_planet_te="శని",
        ruling_planet_en="Saturn (Shani)",
        mantra_te="ఓం శనయే నమః",
        mantra_transliteration="Om Shanaye Namah",
        benefit_te="అడ్డంకుల నివారణ, న్యాయమైన ఫలితాల కోసం",
        chant_count_te="108 సార్లు",
    ),
    RashiMantraContent(
        name_te="మీనం",
        name_en="Meena (Pisces)",
        symbol_te="మీన రాశి",
        ruling_planet_te="గురుడు (బృహస్పతి)",
        ruling_planet_en="Jupiter (Guru)",
        mantra_te="ఓం బృహస్పతయే నమః",
        mantra_transliteration="Om Brihaspataye Namah",
        benefit_te="ఆధ్యాత్మిక వికాసం, కరుణ కోసం",
        chant_count_te="108 సార్లు",
    ),
]
