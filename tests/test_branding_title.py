from ytcore.brandcfg import A_HANDLE, A_NAME  # noqa: E402
from ytcore.content.branding import BRAND_NAME, brand_tags, brand_title


def test_brand_title_appends_name_and_fits():
    t = brand_title("రాహుకాలం ఈరోజు")
    assert t.endswith(f" | {BRAND_NAME}") and len(t) <= 100
    long = brand_title("x" * 120)
    assert long.endswith(BRAND_NAME) and len(long) <= 100 and "\u2026" in long


def test_brand_title_idempotent():
    t = brand_title(f"Purana Kathalu by {A_NAME}")
    assert t == f"Purana Kathalu by {A_NAME}" and brand_title(t) == t


def test_brand_tags_added_once():
    tags = brand_tags(["Shorts", f"{A_NAME.lower()}"])
    assert tags.count(f"{A_NAME.lower()}") == 1 and f"{A_HANDLE.lstrip("@").lower()}" in tags
