"""Channel display names, loaded from the private CHANNEL_BRANDS secret instead of living in source.

CHANNEL_BRANDS is a JSON object (GitHub Actions secret, or a local env var / .env):
    {"a_name": "...", "a_short": "...", "a_handle": "...",
     "b_name": "...", "b_short": "...", "c_name": "...", "c_short": "...", "d_name": "..."}
  *_name   = full channel name shown in titles, descriptions, tags
  a_te / b_hi / d_te = the same name written in Telugu / Hindi script; *_handle = "@handle" (also used in URLs)
  *_short  = the short form that must appear in the channel title (upload safety check)
  a_handle = watermark handle

Inside GitHub Actions the secret is REQUIRED (a missing secret stops the run instead of posting with
placeholder names). Anywhere else (unit tests, local development) neutral placeholders are used.
"""
from __future__ import annotations

import json
import os
import sys

_KEYS = ("a_name", "a_short", "a_handle", "a_te", "b_name", "b_short", "b_handle", "b_hi",
         "c_name", "c_short", "c_handle", "d_name", "d_handle", "d_te")
_PLACEHOLDER = {
    "a_name": "Channel A", "a_short": "Channel A", "a_handle": "@ChannelA", "a_te": "Channel A",
    "b_name": "Channel B", "b_short": "Channel B", "b_handle": "@ChannelB", "b_hi": "Channel B",
    "c_name": "Channel C", "c_short": "Channel C", "c_handle": "@ChannelC",
    "d_name": "Channel D", "d_handle": "@ChannelD", "d_te": "Channel D",
}


def _load() -> dict[str, str]:
    raw = os.environ.get("CHANNEL_BRANDS", "").strip()
    if not raw:
        if os.environ.get("GITHUB_ACTIONS") == "true" and "pytest" not in sys.modules:
            raise RuntimeError("CHANNEL_BRANDS secret is not set (Settings > Secrets and variables > Actions)")
        return dict(_PLACEHOLDER)
    data = json.loads(raw)
    missing = [k for k in _KEYS if not data.get(k)]
    if missing:
        raise RuntimeError(f"CHANNEL_BRANDS is missing keys: {', '.join(missing)}")
    return {k: str(data[k]) for k in _KEYS}


_B = _load()
A_NAME, A_SHORT, A_HANDLE, A_TE = _B["a_name"], _B["a_short"], _B["a_handle"], _B["a_te"]
B_NAME, B_SHORT, B_HANDLE, B_HI = _B["b_name"], _B["b_short"], _B["b_handle"], _B["b_hi"]
C_NAME, C_SHORT, C_HANDLE = _B["c_name"], _B["c_short"], _B["c_handle"]
D_NAME, D_HANDLE, D_TE = _B["d_name"], _B["d_handle"], _B["d_te"]
