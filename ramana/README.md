# Channel D: daily Shorts pipeline

One 5 second bilingual Short (Telugu in Ponnala bold, English below) posted every day before 6 AM IST with your own Om music. Each content row is used once and never repeats. Built on the same gate pattern as your other channels.

## How it works

| Piece | Job |
|---|---|
| `scripts/ci/ramana_gate.py` | Gate. Day-seeded target minute inside 05:00 to 05:40 IST. Prints `DECISION: post ...` or `DECISION: skip ...` |
| `scripts/ci/drive_state.py` | Pulls and pushes `ramana_state.json` to a Google Drive folder (service account) |
| `scripts/post_ramana.py` | Pipeline: choose row, render, upload, captions (te, en), playlist, seed comment, mark state |
| `.github/workflows/post_ramana.yml` | pull state, gate, then every later step conditioned on the gate, push state, artifact, Telegram on failure |
| `src/pick.py` | Deterministic choice (seeded by date). Mon, Thu, Sun quote. Tue, Fri Q&A. Wed, Sat life. First 14 Shorts skip death related rows |
| `src/metadata.py` | SEO title, description, hashtags, tags (exact 500 character budget), Telugu localization, captions, seed comment |
| `src/render.py` | Pillow + ffmpeg, 1080x1920, 5.0 s, completely still picture and text, photo rotates by date |
| `src/refresh_content.py` + `monthly-refresh.yml` | 25th of every month: new rows via web search, duplicates removed, opened as a pull request for your review |
| `data/content.csv`, `data/special_days.csv` | Content bank and key dates (birth, arrival, Mahasamadhi and so on) |

**Gate and pinger.** GitHub's own schedule can be 15 to 90 minutes late, so it is only a backup. The real trigger is an external pinger (cron-job.org) that dispatches the workflow every 5 minutes from 05:00 to 05:55 IST. Each ping first checks state: already posted today means a 30 second no-op. The first ping after the target minute posts. A late backup run may still post until 08:00 IST, after that the day is skipped. The workflow uses one concurrency group, so two runs can never post together.

**State.** `ramana_state.json` in your Drive folder holds `posted` (date to row and video id) and `used_ids`. State is saved right after the upload succeeds, before captions, playlist and comment, so a failure in those extras never causes a second post.

## One time setup

### 1. Assets (already in the repo)
`assets/om_01.mp3` to `om_06.mp3`, `assets/backgrounds/photo_01.jpg` to `photo_10.jpg`, fonts in `assets/fonts/`. Add more photos any time. A new captioned collage can be cut with `python -m src.split_collage collage.png --gold-grid --keep-top 418` and upscaled with `python -m src.upscale_photos assets/backgrounds --model EDSR_x4.pb`.

### 2. YouTube API: reuse your audited Google Cloud project
The "uploads are forced to private" lock applies per Google Cloud project, not per channel. Use the same project and OAuth client you already use for your other channel, so the audit already covers it.
1. Run once on your computer: `pip install google-auth-oauthlib` then `python src/get_refresh_token.py client_secret.json`.
2. At the Google consent screen choose the **Channel D** channel. Allow upload, captions and comments.
3. Copy the three printed values.

### 3. Drive folder for the state file
1. In Drive create a folder, for example `Channel D Automation`.
2. Inside it create a file named exactly `ramana_state.json` from your own account. Content for a fresh start: `{"posted": {}, "used_ids": []}`.
   If you post the first Short by hand (for example `q001` on 7 Oct 2026), use this content so the automation does not repeat it:
   `{"posted": {"2026-10-07": {"row": "q001", "video_id": "manual"}}, "used_ids": ["q001"]}`
3. Google Cloud console > IAM and Admin > Service accounts > Create (or reuse your existing one) > Keys > Add key > JSON.
4. Share the Drive folder with the service account email as **Editor**.
5. A service account has no storage of its own, which is why the file must be created by you first. The script only updates it.

### 4. GitHub repository (private)
Secrets (Settings > Secrets and variables > Actions):
`YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `GDRIVE_SA_JSON` (whole key file), `GDRIVE_STATE_FOLDER_ID` (the folder id from its URL), `ANTHROPIC_API_KEY` (monthly refresh), optional `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, optional `GH_DISPATCH_TOKEN` (starts the refresh early when stock is low).
Variables (same page, Variables tab), all optional: `PLAYLIST_ID`, `PLAYLIST_URL`, `CONTACT_EMAIL`.
Settings > Actions > General > Workflow permissions: read and write, and tick "Allow GitHub Actions to create and approve pull requests" (needed by the monthly refresh).

### 5. External pinger (cron-job.org)
Create a GitHub fine-grained token for this repository only with **Actions: Read and write**. In cron-job.org create a job:
- URL: `https://api.github.com/repos/OWNER/REPO/actions/workflows/post_ramana.yml/dispatches`
- Method: POST. Body: `{"ref":"main"}`
- Headers: `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`
- Schedule: time zone Asia/Kolkata, hour 5, minutes 0,5,10,15,20,25,30,35,40,45,50,55 (12 pings, about 6 Actions minutes a day).

### 6. First run
Actions > Channel D | Quote Short (12 AM IST) > Run workflow with **force** and **dry_run** ticked. Download the artifact and watch the video. Then run it once with only **force** ticked to post for real.

## Verifying a post is real (do not trust a green run)
A green run only means the workflow finished. Most pings are legitimate no-ops.
- Open the run's step list. The step **Run pipeline** must show success (skipped means the gate said skip). The gate step log shows the decision line.
- A real post takes about 60 to 110 seconds (ffmpeg install, render, upload). A no-op takes about 25 to 35 seconds.
- Only one run per day may execute the pipeline step. Check this on the first few days.
- The artifact `ramana-<run id>` holds the video, `meta.json`, captions and the state file.

## SEO and compliance built in
- Title (max 100 characters) starts with the text on the Short, then `Ramana Maharshi Teachings/Satsang/Life`, then the Telugu. A Telugu title and description are added as a localization.
- Description: text, intro, originality and artwork disclosure, source, call to action, playlist link, credits, copyright line, contact, 13 hashtags (never more than 15). No chapters: a 5 second Short has none.
- Tags are deduplicated and fit the 500 character limit exactly (tags with spaces count their quotes).
- Language is set explicitly (`defaultLanguage: en`) and real caption tracks (Telugu and English) are uploaded, timed to the burned-in text.
- A bilingual seed comment is posted on every video.
- `containsSyntheticMedia` is set to true because the backgrounds are AI generated artwork of a real person, which YouTube requires you to disclose.

## Monthly content refresh
On the 25th a pull request adds about 31 new rows. Check every Telugu line and its source, set `verified` to `yes`, then merge before the 1st. Moving dates (Jayanti by star, Aradhana by tithi) must be added by hand each year to `data/special_days.csv` with a full date after checking the ashram calendar, plus a matching row in `content.csv` with the same date in the `special` column.

## Tests
`pip install pytest fonttools` then `python -m pytest -q` before every commit. They check the gate (including that force can never double post), deterministic picking with no repeats over 31 days, every title, tag and description limit, text fit for every row and layout, and that every Telugu character exists in the font.

## Local preview
`python -m src.run --date 2026-12-30` renders what would post that day into `out/preview` without uploading anything.
