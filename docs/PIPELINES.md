# Pipelines map (IST). One row per daily Short. Workflow display names follow "<Channel> | <Short> (<time>)".

All 9 channel tokens share ONE Google Cloud project (client 199121460691) = ONE YouTube API quota. Avoid test uploads.
Reliable trigger = cron-job.org (GitHub `schedule:` pings are best-effort and sometimes arrive hours late).

| Channel | Short | Workflow file | Window (IST) | Token file |
|---|---|---|---|---|
| Mahanavi | Rahu / Shubh / Durm | daily-shorts.yml | 12-1 / 1-2 / 2-3 AM (one hour each) | youtube_token.json |
| Mahanavi | Rashi Mantra | post-rashi-mantra.yml | 8:00-8:50 AM | youtube_token.json |
| Mahanavi | Purana Concept | post-concept-short.yml | 11:00-12:50 | youtube_token.json |
| Mahanavi | Gita Sloka | post-gita-sloka.yml | 3:00-3:50 PM | youtube_token.json |
| Mahanavi | Purana Story | post-purana-short.yml | 5:00-5:50 PM | youtube_token.json |
| Mantra Sangam | Rahu / Shubh / Durm | post-mantra-sangam-rahu / -shubh / -durm.yml | 12:05 / 1:05 / 2:05 AM (from 10 Oct 2026) | youtube_token_mantra_sangam.json |
| Mantra Sangam | Rashi Mantra | post-mantra-sangam-rashi.yml | 8:00-8:50 AM | same |
| Mantra Sangam | Purana Story | post-mantra-sangam-purana.yml | 5:00-5:50 PM | same |
| Ramana TV | Quote / Q&A / Life | post-ramana-short / -qa / -life.yml | 12 AM / 10 AM / 5 PM | youtube_token_ramana.json |
| Jesus | Bible Quote / Bible Quiz | post-jesus-worship-waves.yml / post-jesus-bible-quiz.yml | 6 AM / 6 PM | youtube_token_jesus.json |
| Trance Beats | Bhagavatam / Mantra / Gita | post-trance-bhagavatam / -mantra / post-devotional-trance-beats.yml | 7 AM / 1 PM / 7 PM | youtube_token_trance_beats.json |
| InfoShorts | Telugu Short | post-infoshorts-telugu.yml | 7 AM | youtube_token_infoshorts.json |
| Pulse | Boosting Short | post-pulse-boosting.yml | 12 PM | youtube_token_pulse_boosting.json |
| Tollywood News | Short | post-tollywood-news.yml | 1 PM | youtube_token_tollywood_news.json |
| Live Hyderabad | Short | post-live-hyderabad.yml | 2 PM | youtube_token_live_hyderabad.json |

Retired: post-divine-mantra-sangam.yml (old single 9 AM post, deleted; its cron-job.org job 8595443 is disabled).
Name prefixes: `Tools |` one-off utilities, `Setup |` one-time setup/token uploads, `System |` scheduled housekeeping.
