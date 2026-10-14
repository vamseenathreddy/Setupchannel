from PIL import Image, ImageDraw

from mahanavi.content import card_text


def test_card_text_captured_grouped_and_in_comment_and_description():
    img = Image.new("RGB", (400, 300))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "14", fill=1)
    d.text((60, 10), "October", fill=1)       # same row -> one line
    d.text((10, 80), "Rahu Kalam", fill=1)
    d.text((10, 80), "Rahu Kalam", fill=1)    # shadow duplicate
    d.text((10, 150), "@Watermark", fill=1)   # handle ignored
    img.save("/tmp/_ct_test.png")
    assert card_text.lines() == ["14 October", "Rahu Kalam"]
    c = card_text.comment("#base", "jesus", ["#Faith"])
    assert c.startswith("14 October\nRahu Kalam") and "#JesusWorshipWaves" in c and "#Faith" in c
    desc = card_text.description("Intro\n\n#Shorts #Tag")
    assert "14 October" in desc and desc.rstrip().endswith("#Shorts #Tag")


def test_watermark_only_save_keeps_previous_card_text():
    img = Image.new("RGB", (50, 50))
    ImageDraw.Draw(img).text((1, 1), "Real text", fill=1)
    img.save("/tmp/_ct_test.png")
    ImageDraw.Draw(img).text((1, 1), "@handle", fill=1)
    img.save("/tmp/_ct_test.png")
    assert card_text.lines() == ["Real text"]
