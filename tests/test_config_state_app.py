import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.app import NotifierApp, format_startup_summary, select_due_events
from day_notifier.config import load_settings, set_desktop_enabled
from day_notifier.schedule import Schedule, ScheduleEvent
from day_notifier.state import JsonStateStore
from day_notifier.telegram_client import TelegramCommand


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

    def test_set_desktop_enabled_preserves_existing_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text(
                '{"bot_token": "123:abc", "chat_id": "456", "desktop_enabled": true}',
                encoding="utf-8",
            )

            settings = set_desktop_enabled(path, False)

            reloaded = load_settings(path)

        self.assertFalse(settings.desktop_enabled)
        self.assertFalse(reloaded.desktop_enabled)
        self.assertEqual(reloaded.bot_token, "123:abc")
        self.assertEqual(reloaded.chat_id, "456")

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

    def test_format_startup_summary_lists_remaining_today_events(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "sleep", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [],
            }
        )

        text = format_startup_summary(schedule, datetime(2026, 8, 30, 21, 0))

        self.assertIn("notify-manager запущен", text)
        self.assertIn("Сегодня осталось", text)
        self.assertIn("22:00 Отбой", text)

    def test_test_notification_sends_telegram_before_blocking_desktop_box(self):
        calls = []
        app = NotifierApp.__new__(NotifierApp)
        app.telegram = RecordingTelegram(calls)
        app.desktop = RecordingDesktop(calls)

        app.send_test_notification()

        self.assertEqual(calls[0][0], "telegram")
        self.assertEqual(calls[1], ("desktop", "notify-manager", True))

    def test_scheduled_notification_sends_telegram_before_desktop_box(self):
        calls = []
        app = NotifierApp.__new__(NotifierApp)
        app.telegram = RecordingTelegram(calls)
        app.desktop = RecordingDesktop(calls)
        app.state = RecordingState(calls)
        event = ScheduleEvent(
            event_id="water-1",
            title="1 пв",
            message="Выпей воду",
            when=datetime(2026, 8, 30, 7, 0),
        )

        app.notify(event)

        self.assertEqual(calls[0][0], "telegram")
        self.assertEqual(calls[1], ("desktop", "1 пв", False))
        self.assertEqual(calls[2], ("state", "water-1"))

    def test_process_telegram_shift_command_writes_day_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            app = NotifierApp(root)
            calls = []
            app.telegram = RecordingTelegram(
                calls,
                commands=[TelegramCommand(update_id=10, text="/shift day 10:00")],
            )

            app.process_telegram_commands()

            override_files = list((root / "data" / "day_overrides").glob("*.json"))
            self.assertEqual(len(override_files), 1)
            override_text = override_files[0].read_text(encoding="utf-8")

        self.assertIn("Перенес день на 10:00", calls[-1][1])
        self.assertIn('"suppress_events"', override_text)
        self.assertNotIn("пв", override_text)

    def test_shift_day_writes_override_and_returns_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            app = NotifierApp(root)

            result = app.shift_day("10:00", now=datetime(2026, 8, 31, 9, 0))

            override_text = (root / "data" / "day_overrides" / "2026-08-31.json").read_text(
                encoding="utf-8"
            )

        self.assertIn("Перенес день на 10:00", result)
        self.assertIn("12:25 2 пп", result)
        self.assertIn('"suppress_events"', override_text)


class RecordingTelegram:
    def __init__(self, calls, commands=None):
        self.calls = calls
        self.commands = commands or []

    def send_message(self, text):
        self.calls.append(("telegram", text))

    def get_commands(self, offset=None):
        self.calls.append(("get_commands", offset))
        return self.commands


class RecordingDesktop:
    def __init__(self, calls):
        self.calls = calls

    def show(self, title, message, blocking=False):
        self.calls.append(("desktop", title, blocking))
        return True


class RecordingState:
    def __init__(self, calls):
        self.calls = calls
        self.last_event = None

    def mark_notified(self, event):
        self.calls.append(("state", event.event_id))


def write_project_files(root: Path) -> None:
    (root / "config").mkdir(parents=True)
    (root / "data").mkdir(parents=True)
    (root / "config" / "schedule.json").write_text(
        json.dumps(
            {
                "events": [
                    {"id": "wake-up", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {
                        "id": "morning-block",
                        "time": "04:01",
                        "title": "Утренний блок: МП + кардио",
                        "message": "МП",
                    },
                    {"id": "bedtime", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [
                    {
                        "id": "water-food-cycle",
                        "start_time": "07:00",
                        "period_minutes": 145,
                        "count": 4,
                        "items": [
                            {
                                "offset_minutes": 0,
                                "id_template": "water-{n}",
                                "title_template": "{n} пв",
                                "message_template": "{n} прием воды",
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
