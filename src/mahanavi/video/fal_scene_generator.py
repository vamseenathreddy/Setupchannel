"""
fal_scene_generator.py: generates a short, slow-motion devotional video
clip for one "scene" using fal.ai -- FLUX.1 [dev] text-to-image for a
still frame, then Kling 2.5 Turbo Pro image-to-video to animate it with
gentle, cinematic motion. Built 2026-10-03 for the first AI-generated
devotional SONG video (Navaratri Day 1, "Swarnakavachadharini
Kanakadurgamma" -- see scripts/post_navaratri_song.py), using the
fal_api_key field that was already reserved in config.py but unused
until now.

WHY TWO STEPS (image then video) INSTEAD OF DIRECT TEXT-TO-VIDEO:
image-to-video models like Kling give far more control over exactly
what's in frame (the still image IS the first frame) than text-to-video,
which matters a lot for devotional imagery where getting the deity's
form, ornaments and posture right is the whole point -- a bad first
frame can be regenerated cheaply before spending the (much more
expensive) video generation budget on it.

COST: this is NOT called per-second of final video. One short clip
(FLUX still + one Kling animation, a few seconds each) is generated per
scene/lyric-section, then looped/extended locally with ffmpeg to fill
that section's actual duration in the final song -- real fal.ai spend
stays to a handful of generations, not one per second of a ~4-minute
song. See post_navaratri_song.py for the loop-to-fill step.

API: fal.ai's queue-based REST API (https://fal.run and
https://queue.fal.run), authenticated with `Authorization: Key
<fal_api_key>`. No official Python SDK dependency added here --
httpx is already a transitive dependency (requests-mock pulls requests;
google-api-python-client pulls httplib2) but we use requests directly
since every other network call in this codebase already does.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from mahanavi.exceptions import MahanaviError

logger = logging.getLogger(__name__)

FLUX_MODEL = "fal-ai/flux/dev"
KLING_MODEL = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"

_POLL_INTERVAL_SECONDS = 4
_POLL_TIMEOUT_SECONDS = 600  # Kling animation can genuinely take a few minutes


class FalGenerationError(MahanaviError):
    """Raised when a fal.ai image or video generation call fails or
    times out -- caller decides whether to retry a different scene or
    abort the whole run."""


@dataclass(frozen=True, slots=True)
class SceneSpec:
    """One lyric-section's worth of visual direction.

    key: short identifier, also used for the generated file names.
    image_prompt: what FLUX.1 should paint as the first frame.
    motion_prompt: what Kling should animate from that still --
        deliberately gentle/slow ("slow motion", "subtle") since this is
        devotional content meant to be watched, not an action clip.
    """
    key: str
    image_prompt: str
    motion_prompt: str
    negative_prompt: str = (
        "text, watermark, logo, extra limbs, distorted hands, blurry, "
        "low quality, modern clothing, sunglasses, western dress, "
        "disrespectful depiction"
    )


class FalSceneGenerator:
    def __init__(self, fal_api_key: str, aspect_ratio: str = "16:9") -> None:
        if not fal_api_key:
            raise FalGenerationError("fal.ai API key is empty -- set MAHANAVI_FAL_API_KEY.")
        self._key = fal_api_key
        self._aspect_ratio = aspect_ratio
        self._headers = {"Authorization": f"Key {fal_api_key}", "Content-Type": "application/json"}

    def _submit(self, model: str, payload: dict) -> tuple[str, str, str]:
        """Submits a job and returns (request_id, status_url, response_url).

        IMPORTANT: the status/result URLs are NOT simply
        f"https://queue.fal.run/{model}/requests/{id}[/status]" for a
        model id with more than two path segments (owner/alias), e.g.
        "fal-ai/flux/dev" or "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"
        -- fal.ai's own queue routing only uses the owner/alias prefix
        for the requests/<id> path; anything past that (the "/dev" or
        "/v2.5-turbo/pro/image-to-video" part) belongs to the SUBMIT
        path only. Confirmed by reading fal.ai's official fal-client
        Python package source (AppId.from_endpoint_id + Queued/submit
        building status_url as f"{owner}/{alias}/requests/{id}/status"
        -- never including app_id.path). Reconstructing the URL with
        the full model string (as an earlier version of this method
        did) hits a route that 405s. The fix: use the status_url and
        response_url the submit response ITSELF returns, exactly like
        fal-client does, instead of reconstructing anything.
        """
        resp = requests.post(f"https://queue.fal.run/{model}", headers=self._headers, json=payload, timeout=60)
        if resp.status_code >= 400:
            raise FalGenerationError(f"fal.ai submit failed for {model}: {resp.status_code} {resp.text[:500]}")
        data = resp.json()
        request_id = data.get("request_id")
        status_url = data.get("status_url")
        response_url = data.get("response_url")
        if not request_id or not status_url or not response_url:
            raise FalGenerationError(f"fal.ai submit for {model} returned an unexpected shape: {data}")
        return str(request_id), str(status_url), str(response_url)

    def _poll(self, model: str, status_url: str, response_url: str, request_id: str) -> dict:
        deadline = time.monotonic() + _POLL_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            resp = requests.get(status_url, headers=self._headers, timeout=30)
            if resp.status_code >= 400:
                raise FalGenerationError(f"fal.ai status check failed: {resp.status_code} {resp.text[:500]}")
            status = resp.json().get("status")
            if status == "COMPLETED":
                result = requests.get(response_url, headers=self._headers, timeout=30)
                if result.status_code >= 400:
                    raise FalGenerationError(f"fal.ai result fetch failed: {result.status_code} {result.text[:500]}")
                return dict(result.json())
            if status in ("ERROR", "FAILED"):
                raise FalGenerationError(f"fal.ai generation failed for {model} ({request_id}): {resp.text[:500]}")
            time.sleep(_POLL_INTERVAL_SECONDS)
        raise FalGenerationError(f"fal.ai generation timed out for {model} ({request_id}) after {_POLL_TIMEOUT_SECONDS}s")

    def _download(self, url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, timeout=120)
        if resp.status_code >= 400:
            raise FalGenerationError(f"Failed to download fal.ai output from {url}: {resp.status_code}")
        dest.write_bytes(resp.content)
        return dest

    def generate_still(self, scene: SceneSpec, out_dir: Path) -> Path:
        """FLUX.1 [dev] text-to-image -- one still frame for this scene."""
        logger.info("fal.ai: generating still for scene '%s'", scene.key)
        request_id, status_url, response_url = self._submit(FLUX_MODEL, {
            "prompt": scene.image_prompt,
            "negative_prompt": scene.negative_prompt,
            "image_size": "landscape_16_9" if self._aspect_ratio == "16:9" else "portrait_16_9",
            "num_images": 1,
        })
        result = self._poll(FLUX_MODEL, status_url, response_url, request_id)
        images = result.get("images") or []
        if not images:
            raise FalGenerationError(f"FLUX returned no images for scene '{scene.key}': {result}")
        return self._download(images[0]["url"], out_dir / f"{scene.key}_still.png")

    def animate(self, scene: SceneSpec, still_path: Path, out_dir: Path, duration_seconds: int = 5) -> Path:
        """Kling 2.5 Turbo Pro image-to-video -- animates the still with
        gentle, slow motion matching scene.motion_prompt."""
        logger.info("fal.ai: animating scene '%s' (%ds)", scene.key, duration_seconds)
        image_url = self._upload(still_path)
        request_id, status_url, response_url = self._submit(KLING_MODEL, {
            "prompt": scene.motion_prompt,
            "image_url": image_url,
            "duration": str(duration_seconds),
            "negative_prompt": scene.negative_prompt,
        })
        result = self._poll(KLING_MODEL, status_url, response_url, request_id)
        video = result.get("video") or {}
        video_url = video.get("url")
        if not video_url:
            raise FalGenerationError(f"Kling returned no video for scene '{scene.key}': {result}")
        return self._download(video_url, out_dir / f"{scene.key}_clip.mp4")

    def _upload(self, path: Path) -> str:
        """Uploads a local file to fal.ai's storage and returns its
        access URL -- Kling needs a URL, not raw bytes, so the
        locally-downloaded FLUX still gets re-uploaded here first.

        The single-POST "https://fal.run/storage/upload" endpoint this
        used to hit no longer exists (404 "Application 'upload' not
        found" on a real run, 2026-10-03). Replaced with the
        two-step "storage/upload/initiate" flow fal.ai's own fal-client
        package uses for its simpler (non-CDN-token) upload repository:
        POST rest.fal.ai/storage/upload/initiate with the same
        "Authorization: Key ..." header already used everywhere else
        in this class to get a one-time signed PUT url + the final
        access url, then PUT the raw bytes there directly.
        """
        init_resp = requests.post(
            "https://rest.fal.ai/storage/upload/initiate?storage_type=gcs",
            headers={"Authorization": f"Key {self._key}", "Content-Type": "application/json"},
            json={"file_name": path.name, "content_type": "image/png"},
            timeout=60,
        )
        if init_resp.status_code >= 400:
            raise FalGenerationError(f"fal.ai upload-initiate failed: {init_resp.status_code} {init_resp.text[:500]}")
        init_data = init_resp.json()
        upload_url = init_data.get("upload_url")
        file_url = init_data.get("file_url")
        if not upload_url or not file_url:
            raise FalGenerationError(f"fal.ai upload-initiate returned an unexpected shape: {init_data}")

        put_resp = requests.put(
            upload_url,
            headers={"Content-Type": "image/png"},
            data=path.read_bytes(),
            timeout=120,
        )
        if put_resp.status_code >= 400:
            raise FalGenerationError(f"fal.ai file upload (PUT) failed: {put_resp.status_code} {put_resp.text[:500]}")
        return str(file_url)
