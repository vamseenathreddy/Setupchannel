# Channel A — Devotional YouTube Shorts Automation

Automated content pipelines for the Telugu devotional YouTube channel
**Channel A** (@Channel ASpirituals). Everything ships as a
GitHub Actions workflow — nothing needs a laptop or server running 24/7.

> **Note:** this repo previously also ran a "Daily Community Post"
> pipeline (image + text, no video, 5 AM IST). It was fully removed —
> it got no engagement, and every module built for it (its own
> composition root, scheduler, DB tables, and Telegram/Facebook/
> Instagram publishers) was decommissioned along with it. If you're
> looking for that code, it's still in git history before this cleanup.

## What's actually running

### Alert Shorts — Rahu Kalam / Shubha Ghadiyalu (`daily-shorts.yml`)

Two YouTube Shorts every night, posted somewhere inside the real
**12:00–2:00 AM IST** window:

- **Rahu Kalam** (red card) — today's inauspicious period to avoid
  starting anything important. Attempted first, at the 12:00 AM tick.
- **Shubha Ghadiyalu** (green card) — today's auspicious moments.
  Attempted once Rahu Kalam is already posted, at the 1:00 AM tick.

Both are 10-second vertical Shorts: a rendered alert card
(`images/alert_card_renderer.py`) turned into an `.mp4`
(`video/assembler.py`) with background music baked in
(`assets/music/alert_bgm.mp3`), uploaded via the official YouTube Data
API v3 (`publishers/youtube_shorts_uploader.py`).

Entry point: `src/mahanavi/scripts/post_alert_shorts.py`.

**Timing design — hourly ticks + a gate, not a single precise-time cron:**
GitHub's `schedule:` event is best-effort and, confirmed across several
real nights, can simply not fire at all — not just late, but never.
Rather than depend on one cron fire succeeding, the workflow ticks
**every hour, all day** (`cron: '0 * * * *'`), and a cheap first step
(`scripts/ci/scheduler_gate.py`) decides on each tick whether to do
anything:

- **Never fires before 12:00 AM IST** — firing early would fetch and
  post *today's* Panchang under what's meant to be the next day's
  Short, i.e. show yesterday's timings.
- **Only fires inside 12:00 AM – 2:00 AM IST.** If both Shorts are
  still unposted when that window closes, that day's remaining
  Short(s) are skipped rather than posted late in the day — a very
  late post reads worse than a missed one for time-sensitive content.
- Because a dropped tick just means the *next* tick tries again (each
  Short has its own "posted today" marker), one missed schedule event
  no longer loses the whole night the way it used to with a single
  once-a-night cron.
- `workflow_dispatch` can pass `force_target` (`rahu_kalam` /
  `shubha_ghadiyalu` / `both`) to post immediately regardless of the
  window or today's marker — for manual testing or a deliberate re-post.

A `concurrency` group (`daily-shorts-post`) ensures two ticks can never
run the pipeline in parallel — a later tick queues behind one already
in progress and only starts once it's finished and pushed state.

**State persistence across runs** (GitHub Actions runners are ephemeral,
so nothing survives between runs on the runner itself): a Google Drive
folder holds `mahanavi.db`, `youtube_token.json`,
`last_run_date_rahu_kalam.txt`, and `last_run_date_shubha_ghadiyalu.txt`
— pulled at the start of each run and pushed back after a successful
post (`scripts/ci/drive_state_sync.py`), authenticated via a Google
service account. The two Shorts get separate marker files (not one
combined date) specifically so a delay on one never blocks or skips
the other.

### Purana video scripts (not yet automated)

`scripts/post_purana_video.py`, `post_kurma_purana_video.py`,
`post_panini_video.py`, `post_samudrika_video.py` — long-form landscape
(16:9) devotional story videos with Sarvam AI Telugu voiceover
(`audio/telugu_voiceover.py`) and/or fal.ai-generated scene visuals
(`images/fal_client.py`, `video/scene_visuals.py`). These exist in the
repo and have their own SEO/content modules
(`content/purana_video_seo.py`, `content/purana_selector.py`), but
**there is no GitHub Actions workflow wiring any of them up yet** — they
currently only run if you invoke them manually.

## Repository layout

```
src/mahanavi/
├── config.py                 # Settings — loaded from .env, validated at startup
├── logging_config.py         # Rotating file + console logging
├── exceptions.py              # Exception hierarchy used across the whole app
├── retry.py                   # Generic exponential-backoff decorator
├── text_utils.py               # Shared text-fitting helper
├── core/
│   ├── models.py                # Domain dataclasses (PanchangData, UploadResult, ...)
│   └── interfaces.py             # ABCs: PanchangProvider, ImageSelector
├── database/
│   ├── db.py                      # SQLite connection + schema (image_usage, purana_usage)
│   └── repositories.py             # ImageHistoryRepository, PuranaHistoryRepository
├── images/
│   ├── selector.py                  # RandomImageSelector — non-repeating rotation
│   ├── alert_card_renderer.py        # Renders the Rahu Kalam / Shubha Ghadiyalu cards
│   ├── purana_text_renderer.py        # Renders scrolling Puranam story text
│   ├── fonts.py                        # Telugu font loading (RAQM shaping)
│   ├── layout.py                       # Low-level Pillow drawing helpers
│   └── telugu_text.py                   # Telugu weekday/month/deity vocabulary
├── panchang/
│   ├── dummy_provider.py                 # Offline, deterministic — for dev/testing
│   ├── api_provider.py                    # Generic REST API client
│   ├── scraper_provider.py                 # BeautifulSoup scraper (config-driven selectors)
│   ├── prokerala_provider.py                # Prokerala Astrology API (forever-free tier)
│   ├── fallback_provider.py                  # Falls back to a 2nd Prokerala account on quota exhaustion
│   └── factory.py                             # Picks a provider based on Settings
├── content/
│   ├── data.py                                 # Deity-specific Telugu phrases/hashtags/keywords
│   ├── alert_seo.py                             # SEO for the Alert Shorts
│   ├── purana_video_seo.py                       # SEO for the Purana videos
│   └── purana_selector.py                        # Non-repeating Purana rotation
├── publishers/
│   ├── youtube_shorts_uploader.py                 # Official Data API v3 — Alert Shorts
│   └── youtube_selectors.py                        # (legacy) Studio UI selectors
├── audio/
│   ├── mixer.py                                     # Loops/fades background music under a voiceover
│   └── telugu_voiceover.py                           # Sarvam AI TTS
├── video/
│   ├── assembler.py                                  # Static image + audio -> .mp4 (Alert Shorts)
│   └── scroll_assembler.py                            # Scrolling text overlay (Purana videos)
└── scripts/
    ├── post_alert_shorts.py                           # Alert Shorts entry point (automated)
    ├── post_purana_video.py, post_kurma_purana_video.py,
    │   post_panini_video.py, post_samudrika_video.py      # Purana video entry points (manual only)
    ├── youtube_shorts_auth_setup.py                        # One-time OAuth setup for the Data API uploader
    └── check_festival_today.py                             # Ad-hoc festival lookup helper

.github/workflows/
├── daily-shorts.yml    # Ticks hourly all day; posts Alert Shorts within 12:00-2:00 AM IST
└── ci.yml               # Tests + mypy on every push/PR

scripts/ci/
├── drive_state_sync.py  # pull/mark-done <which>/push against the Google Drive state folder
└── scheduler_gate.py     # Decides per-tick whether/which Short to post (see README above)
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/vamseenathreddy/Setupchannel
cd Setupchannel
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`ffmpeg` must be on `PATH` (used by `video/assembler.py` and
`video/scroll_assembler.py`) — the GitHub Actions workflow installs it
via `apt-get`; install it locally too if you want to run things by hand.

### 2. Add your devotional images

Drop your actual images into the matching weekday folder:

```
Images/
├── Monday_Shiva/
├── Tuesday_Hanuman/
├── Wednesday_Ganesha/
├── Thursday_Sai/
├── Friday_Lakshmi/
├── Saturday_Venkateswara/
└── Sunday_Surya/
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` — see [Configuration reference](#configuration-reference)
below. **Leave a variable blank rather than setting it to a placeholder
string** — blank is treated as "not set."

### 4. Set up YouTube (official Data API v3)

```bash
python -m mahanavi.scripts.youtube_shorts_auth_setup
```

Opens a browser window for one-time OAuth consent; saves a refreshable
token to `MAHANAVI_YOUTUBE_TOKEN_FILE`. In CI, this token is stored in
the Google Drive state folder and restored at the start of each run
(see `scripts/ci/drive_state_sync.py`).

### 5. Set up real Panchang data

By default, `MAHANAVI_PANCHANG_PROVIDER=dummy` uses offline,
deterministic placeholder data — fine for testing, **not for real
posts**. For production, set `MAHANAVI_PANCHANG_PROVIDER=prokerala` and
`MAHANAVI_PROKERALA_CLIENT_ID`/`_SECRET` (get these from your Prokerala
dashboard, forever-free tier). A second client id/secret pair
(`_ID_2`/`_SECRET_2`) is optional and used as an automatic fallback if
the first account's daily quota is exhausted.

## Configuration reference

Every setting lives in `.env` (copy from `.env.example`), all prefixed
`MAHANAVI_`. Full list and defaults are in `src/mahanavi/config.py`.

| Variable | Purpose |
|---|---|
| `IMAGES_ROOT`, `ASSETS_DIR`, `OUTPUT_DIR`, `DATABASE_PATH`, `LOG_DIR` | Paths — defaults are fine for local dev |
| `TIMEZONE` | Used for "today" everywhere: Panchang, and the Alert Shorts posting windows |
| `PANCHANG_PROVIDER` | `dummy` / `api` / `scraper` / `prokerala` |
| `PROKERALA_CLIENT_ID`, `_SECRET`, `_ID_2`, `_SECRET_2` | Prokerala Astrology API, with optional 2nd-account fallback |
| `ALERT_SHORT_DURATION_SECONDS`, `ALERT_ICON_*_PATH`, `ALERT_SHORT_MUSIC_PATH` | Alert Shorts card/video content — all have real committed defaults |
| `SARVAM_API_KEY`, `SARVAM_VOICE`, `SARVAM_PACE`, `SARVAM_TEMPERATURE` | Telugu voiceover for Purana videos |
| `FAL_API_KEY` | AI-generated scene visuals for Purana videos |
| `YOUTUBE_CLIENT_SECRETS_FILE`, `YOUTUBE_TOKEN_FILE` | Official YouTube Data API v3 auth |
| `MAX_RETRIES`, `RETRY_BACKOFF_SECONDS` | Retry behavior for every network call |

## Running it

**Alert Shorts, manual test run:**

```bash
python -m mahanavi.scripts.post_alert_shorts --date 2026-09-16   # unlisted by default
python -m mahanavi.scripts.post_alert_shorts --public            # only once you're happy with the results
python -m mahanavi.scripts.post_alert_shorts --no-delay          # skip the wall-clock wait, for local testing
```

**In production**, this runs on GitHub's schedule via
`.github/workflows/daily-shorts.yml` — no manual invocation needed. You
can also trigger it on demand from the Actions tab
(`workflow_dispatch`).

## Testing

```bash
pip install pytest pytest-cov mypy
PYTHONPATH=src pytest                                       # full suite
PYTHONPATH=src pytest --cov=mahanavi --cov-report=term-missing
PYTHONPATH=src mypy src/mahanavi --ignore-missing-imports    # type checking
```

CI (`.github/workflows/ci.yml`) runs both automatically on every push/PR.

## Extending the system

- **New Panchang source**: implement `PanchangProvider` in `panchang/`,
  wire it into `panchang/factory.py`.
- **New deity/day**: add a folder under `Images/`, an entry to
  `WEEKDAY_FOLDER_MAP` in `config.py`, a `Deity` enum value in
  `core/models.py`, a Telugu name in `images/telugu_text.py`, and content
  in `content/data.py`.
- **Automate the Purana video scripts**: they currently have no
  scheduled workflow — add a new `.github/workflows/*.yml` following the
  pattern in `daily-shorts.yml` (Drive state pull/gate/push) once you're
  ready to run them unattended.

## Known limitations — read before relying on this daily

- **Dummy Panchang data is not astronomically accurate** — fine for
  testing the pipeline, not for real posts.
- **Prokerala's free tier has a daily quota** — the fallback second
  account buys headroom, but both can still be exhausted on a heavy day.
- **GitHub Actions scheduled triggers are best-effort** — GitHub's own
  docs say a `schedule:` event can simply not fire at all under load,
  confirmed on several real nights with the old once-a-night cron. The
  hourly-tick + gate design (see above) tolerates a dropped tick, but
  if the whole 12:00-2:00 AM IST window passes with no tick landing at
  all (not just one), that night's Short(s) are skipped, not posted
  late — use `workflow_dispatch` with `force_target` to post manually.
- **Purana video scripts have no scheduled trigger** — they're
  functional code, not yet wired into an automated daily run.
