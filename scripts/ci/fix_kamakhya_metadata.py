#!/usr/bin/env python3
"""fix_kamakhya_metadata.py: cleans the metadata of the channel's existing
Kamakhya videos (explicitly authorised by the owner, 2026-10-07). Titles
are NOT changed. What changes:
  * tags that do not describe the video are removed
  * the keyword-stuffed "SEO Tags" block is cut from descriptions, and
    hashtag-only lines are replaced by 4 relevant hashtags (YouTube ignores
    all hashtags when a description has more than 15)
  * a "more Kamakhya Devi stotrams" line with the playlist link is added
    at the top of the description
  * a Kamakhya playlist is created (apply mode) and the videos added

Usage: python scripts/ci/fix_kamakhya_metadata.py dry-run|apply
"""
from __future__ import annotations

import re
import sys

from mahanavi.config import get_settings
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

VIDEOS = ["at-SA1XoOL8", "3pQ29TSbhow", "hyScHvnkLmI", "mpsvfMT0guo", "cqld4FfKIrM", "Tu7tuH9PBI0"]
PLAYLIST_TITLE = "శ్రీ కామాఖ్యా దేవి స్తోత్రాలు | Sri Kamakhya Devi Stotrams and Mantras"
PLAYLIST_DESC = (
    "శ్రీ కామాఖ్యా దేవి స్తోత్రాలు, బీజ మంత్రం మరియు అష్టకం, తెలుగు భక్తి ఛానల్ మహానవి స్పిరిచువల్స్ నుండి.\n\n"
    "Sri Kamakhya Devi stotram, beej mantra chant and ashtakam from Mahanavi Spirituals, "
    "a Telugu devotional channel.\n\n"
    "ప్రతి శుక్రవారం కొత్త స్తోత్రం కోసం సబ్‌స్క్రైబ్ చేయండి."
)
BAD_TAG_PARTS = (
    "ranveer", "podcast", "t-series", "yoni", "vashikaran", "curse", "secret", "rahasya", "mystery",
)
HASHTAGS = "#KamakhyaDevi #TeluguDevotional #Stotram #ShaktiPeetha"
TOP_LINE = "🪔 మరిన్ని కామాఖ్యా దేవి స్తోత్రాలు / More Kamakhya Devi stotrams: {url}"


def clean_tags(tags: list[str]) -> list[str]:
    out = []
    for t in tags:
        if any(p in t.lower() for p in BAD_TAG_PARTS):
            continue
        if t not in out:
            out.append(t)
    return out


def clean_description(desc: str, playlist_url: str) -> str:
    idx = re.search(r"^.*SEO Tags.*$", desc, flags=re.M)
    if idx:
        desc = desc[: idx.start()]
    lines = [ln for ln in desc.splitlines() if not re.fullmatch(r"(\s*#\S+)+\s*", ln)]
    deduped: list[str] = []
    for ln in lines:
        if ln.strip() and deduped and ln.strip() == deduped[-1].strip():
            continue
        deduped.append(ln)
    body = "\n".join(deduped).rstrip()
    head = TOP_LINE.format(url=playlist_url) + "\n\n" if playlist_url else ""
    return (head + body + "\n\n" + HASHTAGS)[:4900]


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "dry-run"
    apply = mode == "apply"
    yt = YouTubeShortsUploader(get_settings())._build_service()  # noqa: SLF001
    print("CHANNEL:", yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"])

    playlist_id = ""
    if apply:
        pl = yt.playlists().insert(
            part="snippet,status",
            body={"snippet": {"title": PLAYLIST_TITLE, "description": PLAYLIST_DESC, "defaultLanguage": "te"},
                  "status": {"privacyStatus": "public"}},
        ).execute()
        playlist_id = pl["id"]
        print("PLAYLIST_ID:", playlist_id)
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}" if playlist_id else "<playlist-url>"

    items = yt.videos().list(part="snippet", id=",".join(VIDEOS)).execute()["items"]
    for v in items:
        s = v["snippet"]
        new_tags = clean_tags(s.get("tags", []))
        removed = [t for t in s.get("tags", []) if t not in new_tags]
        new_desc = clean_description(s["description"], playlist_url)
        print("=" * 60)
        print(f"{v['id']} | {s['title']}")
        print(f"  tags {len(s.get('tags', []))} -> {len(new_tags)}; removed: {removed}")
        print(f"  description {len(s['description'])} -> {len(new_desc)} chars")
        print("  new description head:", new_desc[:260].replace("\n", " / "))
        print("  new description tail:", new_desc[-160:].replace("\n", " / "))
        if apply:
            snippet = {"title": s["title"], "description": new_desc, "tags": new_tags, "categoryId": s["categoryId"]}
            if s.get("defaultLanguage"):
                snippet["defaultLanguage"] = s["defaultLanguage"]
            yt.videos().update(part="snippet", body={"id": v["id"], "snippet": snippet}).execute()
            print("  UPDATED")
            yt.playlistItems().insert(
                part="snippet",
                body={"snippet": {"playlistId": playlist_id,
                                  "resourceId": {"kind": "youtube#video", "videoId": v["id"]}}},
            ).execute()
            print("  added to playlist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
