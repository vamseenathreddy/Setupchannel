import wave

from mahanavi.config import get_settings


def test_alert_loop_audio_matches_video_length_exactly():
    s = get_settings()
    with wave.open(str(s.alert_loop_music_path)) as w:
        audio = w.getnframes() / w.getframerate()
    # whole number of 30 fps frames, so the video and the audio loop at the same instant (no seam)
    assert abs(audio - s.alert_short_duration_seconds) < 0.001
    assert abs(s.alert_short_duration_seconds * 30 - round(s.alert_short_duration_seconds * 30)) < 0.01
    assert s.alert_short_duration_seconds < 5
