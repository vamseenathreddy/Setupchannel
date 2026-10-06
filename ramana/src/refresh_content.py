"""Monthly content refresh: ask the model (with web search) for ~31 new rows, drop duplicates, append.

Runs in GitHub Actions. Needs ANTHROPIC_API_KEY. Output is committed on a branch and opened as a
pull request so a human reviews every quote and its source before it can be published.
"""
import calendar
import datetime as dt
import json
import os
import re
import sys

import anthropic

from . import common

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
ROTATION = {0: "quote", 1: "qa", 2: "life", 3: "quote", 4: "qa", 5: "life", 6: "quote"}

PROMPT = """You are preparing content for a devotional YouTube Shorts channel about Sri Ramana Maharshi.
Each Short is 5 seconds, so every text must be very short.

Find {need} NEW items using web search, with these category counts: {counts}.
- quote: one teaching or saying. Telugu: 4 to 12 words. English: one short line.
- qa: a question and a one line answer, as in Talks or Who Am I?. Telugu and English both use the form
  "ప్ర: ...|జ: ..." and "Q: ...|A: ..." with a pipe between question and answer. Telugu max 16 words total.
- life: one single documented moment from his life. Telugu: max 14 words. English: one line.
Rules:
- Every item needs a real source: book title plus chapter, talk number or page when you can find it.
  Prefer public domain or the ashram's own texts (Who Am I?, Upadesa Saram, Forty Verses, Talks, Self-Realization).
  If you cannot name a real source for an item, do not include that item.
- Never invent or paraphrase loosely. If wording is a translation, keep it faithful.
- Do not include items that depend on a calendar date (birth, arrival, Mahasamadhi). Those are handled separately.
- Telugu must be natural, correct Telugu script. No transliteration.
- Avoid anything similar to these existing items (themes already used):
{existing}

Return ONLY a JSON array, no prose. Each element: {{"category":"quote|qa|life","telugu":"...","english":"...","source":"..."}}"""


def month_counts(year, month):
    days = calendar.monthrange(year, month)[1]
    c = {"quote": 0, "qa": 0, "life": 0}
    for d in range(1, days + 1):
        c[ROTATION[dt.date(year, month, d).weekday()]] += 1
    return c


def ask(need_counts, rows):
    existing = "\n".join(f"- {r['english'].replace('|', ' ')}" for r in rows[-120:])
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
        messages=[{"role": "user", "content": PROMPT.format(
            need=sum(need_counts.values()), counts=json.dumps(need_counts), existing=existing)}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        raise ValueError("Model returned no JSON array")
    return json.loads(m.group(0))


def valid(item):
    try:
        return (item["category"] in common.CATEGORIES and len(item["telugu"].strip()) > 3
                and len(item["english"].strip()) > 3 and len(item["source"].strip()) >= 8
                and re.search(r"[ఀ-౿]", item["telugu"])
                and (item["category"] != "qa" or ("|" in item["telugu"] and "|" in item["english"]))
                and len(item["telugu"].split()) <= 18)
    except (KeyError, AttributeError, TypeError):
        return False


def next_id(rows, cat):
    n = max([int(r["id"][1:]) for r in rows if r["category"] == cat and r["id"][1:].isdigit()] or [0]) + 1
    return f"{common.ID_PREFIX[cat]}{n:03d}"


def main():
    today = dt.date.today()
    y, m = (today.year + (today.month == 12), today.month % 12 + 1)  # next month
    want = month_counts(y, m)
    rows = common.load_rows()
    added, rejected = [], {"invalid": 0, "duplicate": 0}
    for attempt in range(3):
        need = {k: max(0, want[k] - sum(1 for a in added if a["category"] == k)) for k in want}
        if sum(need.values()) == 0:
            break
        try:
            items = ask(need, rows + added)
        except Exception as e:  # noqa: BLE001
            print(f"attempt {attempt + 1} failed: {e}")
            continue
        for it in items:
            if not valid(it):
                rejected["invalid"] += 1
                continue
            row = {"category": it["category"], "telugu": it["telugu"].strip(), "english": it["english"].strip(),
                   "source": it["source"].strip(), "verified": "no", "special": "", "used": "", "scheduled_for": ""}
            if common.is_duplicate(row, rows + added):
                rejected["duplicate"] += 1
                continue
            row["id"] = next_id(rows + added, row["category"])
            if sum(1 for a in added if a["category"] == row["category"]) < want[row["category"]]:
                added.append(row)

    if not added:
        print("::error::No valid new rows were produced.")
        return 1
    common.save_rows(rows + added)
    summary = (f"## Content refresh {y}-{m:02d}\nAdded {len(added)} rows (target {sum(want.values())}). "
               f"Rejected: {rejected}.\n\nReview every Telugu line and source before merging. "
               f"Set `verified` to `yes` once checked.\n")
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary)
    with open("refresh_summary.md", "w", encoding="utf-8") as f:
        f.write(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
