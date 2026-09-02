import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.audio import AudioCuePlayer
from day_notifier.schedule import ScheduleEvent


class AudioCuePlayerTests(unittest.TestCase):
    def test_wake_up_event_opens_cue_then_morning_prayer_after_delay(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cue_path = root / "data" / "audio" / "rota-podem.mp3"
            prayer_path = root / "data" / "audio" / "morning-prays.mp3"
            cue_path.parent.mkdir(parents=True)
            cue_path.write_bytes(b"cue")
            prayer_path.write_bytes(b"prayer")
            calls = []
            player = AudioCuePlayer(
                root=root,
                opener=lambda path: calls.append(("open", path)),
                sleeper=lambda seconds: calls.append(("sleep", seconds)),
            )
            event = ScheduleEvent(
                event_id="wake-up",
                title="Подъем",
                message="Подъем",
                when=datetime(2026, 8, 31, 4, 0),
            )

            played = player.play_for_event(event)

        self.assertTrue(played)
        self.assertEqual(calls, [("open", cue_path), ("sleep", 2), ("open", prayer_path)])

    def test_wake_up_event_skips_morning_prayer_when_prayer_block_is_disabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cue_path = root / "data" / "audio" / "rota-podem.mp3"
            prayer_path = root / "data" / "audio" / "morning-prays.mp3"
            cue_path.parent.mkdir(parents=True)
            cue_path.write_bytes(b"cue")
            prayer_path.write_bytes(b"prayer")
            calls = []
            player = AudioCuePlayer(
                root=root,
                opener=lambda path: calls.append(("open", path)),
                sleeper=lambda seconds: calls.append(("sleep", seconds)),
                morning_prayer_enabled=lambda: False,
            )
            event = ScheduleEvent(
                event_id="wake-up",
                title="Подъем",
                message="Подъем",
                when=datetime(2026, 8, 31, 4, 0),
            )

            played = player.play_for_event(event)

        self.assertTrue(played)
        self.assertEqual(calls, [("open", cue_path)])

    def test_missing_wake_up_cue_still_opens_morning_prayer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prayer_path = root / "data" / "audio" / "morning-prays.mp3"
            prayer_path.parent.mkdir(parents=True)
            prayer_path.write_bytes(b"prayer")
            calls = []
            player = AudioCuePlayer(
                root=root,
                opener=lambda path: calls.append(("open", path)),
                sleeper=lambda seconds: calls.append(("sleep", seconds)),
            )
            event = ScheduleEvent(
                event_id="wake-up",
                title="Подъем",
                message="Подъем",
                when=datetime(2026, 8, 31, 4, 0),
            )

            with self.assertLogs(level="WARNING"):
                played = player.play_for_event(event)

        self.assertTrue(played)
        self.assertEqual(calls, [("open", prayer_path)])

    def test_non_wake_up_event_does_not_open_audio(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audio_path = root / "data" / "audio" / "morning-prays.mp3"
            audio_path.parent.mkdir(parents=True)
            audio_path.write_bytes(b"mp3")
            calls = []
            player = AudioCuePlayer(root=root, opener=calls.append)
            event = ScheduleEvent(
                event_id="morning-block",
                title="Утренний блок",
                message="МП",
                when=datetime(2026, 8, 31, 4, 1),
            )

            played = player.play_for_event(event)

        self.assertFalse(played)
        self.assertEqual(calls, [])

    def test_bedtime_event_opens_bedtime_audio(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bedtime_path = root / "data" / "audio" / "otboj.mp3"
            bedtime_path.parent.mkdir(parents=True)
            bedtime_path.write_bytes(b"bedtime")
            calls = []
            player = AudioCuePlayer(root=root, opener=lambda path: calls.append(("open", path)))
            event = ScheduleEvent(
                event_id="bedtime",
                title="Отбой",
                message="Сон",
                when=datetime(2026, 9, 1, 22, 0),
            )

            played = player.play_for_event(event)

        self.assertTrue(played)
        self.assertEqual(calls, [("open", bedtime_path)])

    def test_missing_wake_up_audio_does_not_raise(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            player = AudioCuePlayer(root=Path(temp_dir), opener=lambda path: None)
            event = ScheduleEvent(
                event_id="wake-up",
                title="Подъем",
                message="Подъем",
                when=datetime(2026, 8, 31, 4, 0),
            )

            with self.assertLogs(level="WARNING"):
                played = player.play_for_event(event)

        self.assertFalse(played)


if __name__ == "__main__":
    unittest.main()
