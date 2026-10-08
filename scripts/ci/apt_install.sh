#!/usr/bin/env bash
# Retrying apt install for CI. A single hung "apt-get update" once stalled a Daily Shorts run for 90
# minutes (2026-10-07), which held the concurrency lock and made the night's last Short miss its window.
# Each attempt is time-boxed, so a hang costs minutes, not the whole run.
set -u
for attempt in 1 2 3; do
  if sudo timeout 150 apt-get update -y -o Acquire::Retries=3 -o Acquire::http::Timeout=20 \
     && sudo timeout 300 apt-get install -y --no-install-recommends "$@"; then
    exit 0
  fi
  echo "apt attempt $attempt failed or timed out; retrying" >&2
  sleep 10
done
exit 1
