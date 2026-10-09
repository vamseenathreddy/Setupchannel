from mahanavi.content.branding import BRAND_NAME, brand_tags, brand_title


def test_brand_title_appends_name_and_fits():
    t = brand_title("రాహుకాలం ఈరోజు")
    assert t.endswith(f" | {BRAND_NAME}") and len(t) <= 100
    long = brand_title("x" * 120)
    assert long.endswith(BRAND_NAME) and len(long) <= 100 and "\u2026" in long


def test_brand_title_idempotent():
    t = brand_title("Purana Kathalu by Mahanavi Spirituals")
    assert t == "Purana Kathalu by Mahanavi Spirituals" and brand_title(t) == t


def test_brand_tags_added_once():
    tags = brand_tags(["Shorts", "mahanavi spirituals"])
    assert tags.count("mahanavi spirituals") == 1 and "mahanavispirituals" in tags
