from ytcore.video.watermark import GITA_POSITIONS_Y, POSITIONS_Y, overlay_filter


def test_overlay_filter_cycles_each_layer_in_its_own_slot():
    f = overlay_filter("base", 2, 2, "out")
    assert "[base][2:v]" in f and "[wm0][3:v]" in f and f.endswith("[out]")
    assert "mod(t,8)" in f  # 2 positions x 4 s


def test_positions_stay_inside_card_and_above_youtube_caption_zone():
    for ys in (POSITIONS_Y, GITA_POSITIONS_Y):
        assert all(60 <= y <= 1650 for y in ys)
