"""
Selectors/locators for automating YouTube's Community Post composer.

*** READ THIS BEFORE RELYING ON THIS MODULE IN PRODUCTION ***

This has already been corrected twice against real evidence from actual
runs (not just guessed and left alone):
  1. Studio's "Create" button and its "Create post" quick-action button
     both matched a substring search on "Create" — fixed with exact=True.
  2. Clicking "Create post" doesn't open a dialog inside Studio at all —
     it opens a NEW TAB at the public youtube.com channel's /posts page,
     with the composer embedded inline there. So automation now navigates
     directly to that URL (see channel_posts_url) instead of automating
     Studio's dropdown and tracking a newly-opened tab.

Still UNCONFIRMED as of this writing — flagged individually below —
because I don't have a live DOM inspection of the composer's actual
caption input or post-confirmation state:
    1. Run the pipeline (`--run-now`) and check the failure screenshot at
       data/generated/youtube_post_*.png plus the full error in
       data/logs/ytcore.log if a step fails.
    2. For anything flagged UNCONFIRMED, right-click the real element in
       your browser -> Inspect -> Copy -> Copy outerHTML, so the actual
       DOM structure (not another guess) drives the selector.
    3. Update the values below to match. Nothing else in the codebase
       needs to change — youtube_playwright_uploader.py only references
       these constants.

Preferring Playwright's role/text-based locators (get_by_role, get_by_text)
over raw CSS selectors is deliberate: class names are machine-generated and
change often, while visible button labels and ARIA roles change far less
frequently. But role/text matches are substring matches by default, not
exact — use exact=True wherever a label could be a substring of another
visible label on the same page (this bit us once already, see above).
"""

from __future__ import annotations

STUDIO_BASE_URL = "https://studio.youtube.com"


def channel_posts_url(channel_id: str) -> str:
    """Confirmed via a real run (2026-09-14): clicking Studio's 'Create post'
    menu item just opens this public youtube.com URL in a new tab, with the
    composer embedded inline. Navigating straight here is far more robust
    than automating Studio's Create-button dropdown and then tracking a
    newly-opened tab."""
    return f"https://www.youtube.com/channel/{channel_id}/posts"


# Text/role locators — verify against the live UI (see module docstring).
#
# POST_ACTIVATE_PLACEHOLDER_SELECTOR: THE actual fix for the "verification
# passes but the real post ends up with no caption" bug (2026-09-14) — the
# earlier JS-only page.evaluate(...).focus() approach put text into the
# raw DOM (so our read-back check reported success), but never triggered
# whatever real click handler the framework uses to sync its OWN internal
# text model, which is what actually gets submitted on Post. Confirmed via
# a real strict-mode-violation log: the activate placeholder has a STABLE
# id, "commentbox-placeholder" — unlike its rotating aria-label text (five
# different variants seen across runs), the id never changes. A genuine
# Playwright .click() here (not JS .focus()) fires real events, so the
# framework's model updates the way it would for an actual user.
POST_ACTIVATE_PLACEHOLDER_SELECTOR = "#commentbox-placeholder"
#
# CANCEL_BUTTON_ROLE: sits next to "Post" once the composer is expanded.
# Because the browser profile is PERSISTENT across runs, a previous run's
# leftover draft can leave the composer already expanded on page load —
# in which case POST_ACTIVATE_PLACEHOLDER_SELECTOR genuinely doesn't
# exist (it only shows in the collapsed state). Clicking Cancel first (if
# present) discards any such leftover draft and resets to the collapsed
# state before every run.
CANCEL_BUTTON_ROLE = ("button", "Cancel")
#
# POST_TEXTBOX_SELECTOR: THE key discovery, after five different rotating
# prompt variants were observed across real runs on 2026-09-14 alone
# ("Share an image to start a caption contest", "What do you want to
# share with members today?", "Share a sneak peek of your...", "What's on
# your mind?", "Try showing members a sneak peek of your next video") —
# matching on ANY visible/accessible text for this element was never going
# to be reliable, no matter how the pattern was refined. What IS stable
# across every single one of those runs is the underlying element's ID:
# <div id="contenteditable-root" contenteditable="true" ...>. Used both as
# the readback target (to verify typed text really landed) and as a real
# click target on verification-retry.
POST_TEXTBOX_SELECTOR = "#contenteditable-root"
#
# ADD_PHOTO_BUTTON_ROLE: corrected via a real strict-mode violation
# (2026-09-14) — the visible label is "Image" but its actual accessible
# name is "Add an image". A non-exact match on "Image" ambiguously
# matched THREE elements: this real button, an "Add an image poll"
# button (which also contains "image" as a substring), and a leftover
# placeholder element from before the composer was focused. exact=True
# is required when clicking this — "Add an image" is itself a substring
# of "Add an image poll", so even the corrected name still needs an
# exact match to disambiguate the two.
ADD_PHOTO_BUTTON_ROLE = ("button", "Add an image")
# FILE_INPUT_SELECTOR: corrected via a real strict-mode violation
# (2026-09-14) — a generic input[type='file'] search ambiguously matched
# THREE hidden file inputs on the page (one for the search box, one for a
# general drag-and-drop zone, one for the Image button). This one is
# scoped to the container tied to the "Add an image" button we just
# clicked, matching its own ID.
FILE_INPUT_SELECTOR = "#add-image-button-container input[name='Filedata']"
# POST_SUBMIT_BUTTON_ROLE: needs exact=True when clicked — confirmed via
# a real strict-mode violation (2026-09-14) listing DOZENS of matches for
# a non-exact "Post" search, because every already-published post visible
# further down the same page has Like/Dislike buttons whose aria-labels
# also contain the word "post" (e.g. "Like this post along with 68 other
# people"). The real button's exact aria-label is just "Post".
POST_SUBMIT_BUTTON_ROLE = ("button", "Post")
POST_CONFIRMATION_TEXT = "Post published"  # UNCONFIRMED — pending a real successful post to verify

# Timeouts (milliseconds) — Studio can be slow to load; generous by default.
NAVIGATION_TIMEOUT_MS = 45_000
ACTION_TIMEOUT_MS = 20_000
UPLOAD_PROCESSING_TIMEOUT_MS = 30_000
