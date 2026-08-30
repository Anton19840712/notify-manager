import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.app import select_due_events
from day_notifier.config import load_settings
from day_notifier.schedule import ScheduleEvent
from day_notifier.state import JsonStateStore


class ConfigStateAppTests(unittest.TestCase):
    def test_load_settings_allows_missing_local_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = load_settings(Path(temp_dir) / "missing.json")

        self.assertFalse(settings.telegram_enabled)
        self.assertIsNone(settings.bot_token)
        self.assertIsNone(settings.chat_id)

    def test_load_settings_reads_telegram_credentials(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text(
                '{"bot_token": "123:abc", "chat_id": "456", "telegram_poll_seconds": 2}',
                encoding="utf-8",
            )

            settings = load_settings(path)

        self.assertTrue(settings.telegram_enabled)
        self.assertEqual(settings.bot_token, "123:abc")
        self.assertEqual(settings.chat_id, "456")
        self.assertEqual(settings.telegram_poll_seconds, 2)

    def test_state_persists_seen_event_and_last_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            event = ScheduleEvent(
                event_id="water-1",
                title="1 пв",
                message="Выпей воду",
                when=datetime(2026, 8, 30, 7, 0),
            )

            state = JsonStateStore(path)
            state.mark_notified(event)
            reloaded = JsonStateStore(path)

        self.assertTrue(reloaded.has_seen(event))
        self.assertEqual(reloaded.last_event.event_id, "water-1")

    def test_state_adds_snoozed_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            event = ScheduleEvent(
                event_id="water-1",
                title="1 пв",
                message="Выпей воду",
                when=datetime(2026, 8, 30, 7, 0),
            )
            state = JsonStateStore(path)

            snoozed = state.add_snooze(event, 10)
            due = state.due_snoozes(datetime(2026, 8, 30, 7, 10))

        self.assertEqual(snoozed.when.strftime("%H:%M"), "07:10")
        self.assertEqual(due[0].event_id, "water-1-snooze")

    def test_select_due_events_skips_old_events_and_keeps_fresh_due_events(self):
        now = datetime(2026, 8, 30, 7, 10)
        old_event = ScheduleEvent("old", "Старое", "Старое", now - timedelta(minutes=20))
        fresh_event = ScheduleEvent("fresh", "Свежее", "Свежее", now - timedelta(minutes=3))
        future_event = ScheduleEvent("future", "Будущее", "Будущее", now + timedelta(minutes=1))

        with tempfile.TemporaryDirectory() as temp_dir:
            state = JsonStateStore(Path(temp_dir) / "state.json")
            due = select_due_events([old_event, fresh_event, future_event], state, now, grace_minutes=5)

        self.assertEqual([event.event_id for event in due], ["fresh"])
        self.assertTrue(state.has_seen(old_event))
        self.assertFalse(state.has_seen(future_event))


if __name__ == "__main__":
    unittest.main()

