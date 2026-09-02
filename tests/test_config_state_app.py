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
from day_notifier.telegram_client import DeleteSummary, TelegramCommand


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

    def test_state_tracks_telegram_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            state = JsonStateStore(path)

            state.track_telegram_message(10, "incoming", datetime(2026, 8, 31, 21, 0))
            state.track_telegram_message(11, "outgoing", datetime(2026, 8, 31, 21, 1))
            reloaded = JsonStateStore(path)

        self.assertEqual(
            reloaded.telegram_messages,
            [
                {"message_id": 10, "direction": "incoming", "at": "2026-08-31T21:00:00"},
                {"message_id": 11, "direction": "outgoing", "at": "2026-08-31T21:01:00"},
            ],
        )

    def test_state_clears_tracked_telegram_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            state = JsonStateStore(path)
            state.track_telegram_message(10, "incoming", datetime(2026, 8, 31, 21, 0))

            state.clear_telegram_messages()
            reloaded = JsonStateStore(path)

        self.assertEqual(reloaded.telegram_messages, [])

    def test_state_caps_tracked_telegram_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            state = JsonStateStore(path)

            for message_id in range(502):
                state.track_telegram_message(message_id, "outgoing", datetime(2026, 8, 31, 21, 0))
            reloaded = JsonStateStore(path)

        self.assertEqual(len(reloaded.telegram_messages), 500)
        self.assertEqual(reloaded.telegram_message_ids()[0], 2)
        self.assertEqual(reloaded.telegram_message_ids()[-1], 501)

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

        self.assertNotIn("notify-manager запущен", text)
        self.assertTrue(text.startswith("Сегодня осталось:"))
        self.assertIn("22:00 Отбой", text)

    def test_format_startup_summary_adds_countdowns_for_meals_bedtime_and_batch_cooking(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "meal-4", "time": "21:00", "title": "4 пп", "message": "Контейнер"},
                    {
                        "id": "batch-cooking",
                        "time": "21:30",
                        "title": "Batch-cooking: 12 приемов на 3 дня",
                        "message": "Готовка",
                    },
                    {"id": "bedtime", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [],
            }
        )

        text = format_startup_summary(schedule, datetime(2026, 8, 30, 20, 45))

        self.assertIn("21:00 4 пп (до приема пищи: 15 мин)", text)
        self.assertIn(
            "21:30 Batch-cooking: 12 приемов на 3 дня (до batch-cooking: 45 мин)",
            text,
        )
        self.assertIn("22:00 Отбой (до сна: 1 ч 15 мин)", text)

    def test_format_startup_summary_hides_pre_meal_reminders(self):
        schedule = Schedule.from_dict(
            {
                "events": [],
                "cycles": [
                    {
                        "id": "food-cycle",
                        "start_time": "07:00",
                        "period_minutes": 145,
                        "count": 1,
                        "items": [
                            {
                                "offset_minutes": 15,
                                "id_template": "meal-{n}",
                                "title_template": "{n} пп",
                                "message_template": "{n} прием пищи",
                            }
                        ],
                    }
                ],
            }
        )

        text = format_startup_summary(schedule, datetime(2026, 8, 30, 7, 1))

        self.assertIn("07:15 1 пп", text)
        self.assertNotIn("10 минут до", text)

    def test_test_notification_sends_telegram_before_blocking_desktop_box(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            calls = []
            app = NotifierApp.__new__(NotifierApp)
            app.telegram = RecordingTelegram(calls)
            app.desktop = RecordingDesktop(calls)
            app.state = JsonStateStore(Path(temp_dir) / "state.json")

            app.send_test_notification()

        self.assertEqual(calls[0][0], "telegram")
        self.assertEqual(calls[1][0], "desktop")
        self.assertEqual(calls[1][1], "notify-manager")
        self.assertTrue(calls[1][3])

    def test_scheduled_notification_sends_telegram_before_desktop_box(self):
        calls = []
        app = NotifierApp.__new__(NotifierApp)
        app.telegram = RecordingTelegram(calls)
        app.desktop = RecordingDesktop(calls)
        app.audio = NoopAudio()
        app.state = RecordingState(calls)
        event = ScheduleEvent(
            event_id="water-1",
            title="1 пв",
            message="Выпей воду",
            when=datetime(2026, 8, 30, 7, 0),
        )

        app.notify(event, now=datetime(2026, 8, 30, 7, 0))

        self.assertEqual(calls[0][0], "telegram")
        self.assertEqual(calls[1][0], "telegram-state")
        self.assertEqual(calls[2][0], "desktop")
        self.assertEqual(calls[2][1], "1 пв")
        self.assertIn("Сейчас: 07:00", calls[2][2])
        self.assertFalse(calls[2][3])
        self.assertEqual(calls[3], ("state", "water-1"))

    def test_wake_up_notification_starts_audio_before_marking_notified(self):
        calls = []
        app = NotifierApp.__new__(NotifierApp)
        app.telegram = RecordingTelegram(calls)
        app.desktop = RecordingDesktop(calls)
        app.audio = RecordingAudio(calls)
        app.state = RecordingState(calls)
        event = ScheduleEvent(
            event_id="wake-up",
            title="Подъем",
            message="Подъем",
            when=datetime(2026, 8, 31, 4, 0),
        )

        app.notify(event)

        self.assertEqual(calls[0], ("audio", "wake-up"))
        self.assertEqual(calls[-1], ("state", "wake-up"))

    def test_scheduled_notification_records_outgoing_telegram_message_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            calls = []
            app = NotifierApp.__new__(NotifierApp)
            app.telegram = RecordingTelegram(calls)
            app.desktop = RecordingDesktop(calls)
            app.audio = NoopAudio()
            app.state = JsonStateStore(Path(temp_dir) / "state.json")
            event = ScheduleEvent(
                event_id="water-1",
                title="1 пв",
                message="Выпей воду",
                when=datetime(2026, 8, 30, 7, 0),
            )

            app.notify(event)

        self.assertEqual(app.state.telegram_messages[0]["direction"], "outgoing")

    def test_process_telegram_records_incoming_and_reply_message_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            app = NotifierApp(root)
            app.telegram = RecordingTelegram(
                [],
                commands=[TelegramCommand(update_id=10, text="/next", message_id=77)],
            )

            app.process_telegram_commands()

        self.assertEqual([item["direction"] for item in app.state.telegram_messages], ["incoming", "outgoing"])

    def test_cleanup_telegram_chat_deletes_tracked_messages_and_returns_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            calls = []
            app = NotifierApp.__new__(NotifierApp)
            app.telegram = RecordingTelegram(calls)
            app.state = JsonStateStore(Path(temp_dir) / "state.json")
            app.state.track_telegram_message(10, "incoming", datetime(2026, 8, 31, 21, 0))
            app.state.track_telegram_message(11, "outgoing", datetime(2026, 8, 31, 21, 1))

            result = app.cleanup_telegram_chat()

        self.assertIn("Отбой. Чат очищен", result)
        self.assertIn(("delete_messages", [10, 11]), calls)
        self.assertEqual(app.state.telegram_messages, [])

    def test_process_telegram_shift_command_writes_day_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            app = NotifierApp(root)
            calls = []
            app.telegram = RecordingTelegram(
                calls,
                commands=[TelegramCommand(update_id=10, text="/sd 10:00")],
            )

            app.process_telegram_commands()

            override_files = list((root / "data" / "day_overrides").glob("*.json"))
            self.assertEqual(len(override_files), 1)
            override_text = override_files[0].read_text(encoding="utf-8")

        self.assertIn("Перенес день на 10:00", calls[-1][1])
        self.assertIn('"suppress_events"', override_text)
        self.assertNotIn("пв", override_text)

    def test_process_telegram_stop_bot_command_requests_shutdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            app = NotifierApp(root)
            calls = []
            app.telegram = RecordingTelegram(
                calls,
                commands=[TelegramCommand(update_id=10, text="/stop_bot")],
            )

            app.process_telegram_commands()

        self.assertTrue(app.stop_requested)
        self.assertIn("Останавливаю notify-manager", calls[-1][1])

    def test_process_telegram_block_on_command_writes_block_state_and_reloads_schedule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            add_optional_prayer_block(root)
            app = NotifierApp(root)
            calls = []
            app.telegram = RecordingTelegram(
                calls,
                commands=[TelegramCommand(update_id=10, text="/block_on chrysostom-prayers")],
            )

            app.process_telegram_commands()

            block_state = json.loads((root / "data" / "block_state.json").read_text(encoding="utf-8"))
            events = app.schedule.events_for_date(datetime(2026, 8, 30).date())

        self.assertTrue(block_state["blocks"]["chrysostom-prayers"]["enabled"])
        self.assertIn("Блок включен", calls[-1][1])
        self.assertIn("chrysostom-prayers", calls[-1][1])
        self.assertIn("chrysostom-prayer-01", [event.event_id for event in events])

    def test_block_status_reports_effective_block_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            add_optional_prayer_block(root)
            app = NotifierApp(root)

            result = app.block_status()

        self.assertIn("chrysostom-prayers", result)
        self.assertIn("выключен", result)

    def test_morning_prayer_audio_uses_runtime_prayer_block_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            schedule_path = root / "config" / "schedule.json"
            data = json.loads(schedule_path.read_text(encoding="utf-8"))
            data["blocks"] = {
                "prayers": {
                    "title": "Молитвы / духовный блок",
                    "enabled": True,
                }
            }
            schedule_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            (root / "data" / "block_state.json").write_text(
                json.dumps({"blocks": {"prayers": {"enabled": False}}}, ensure_ascii=False),
                encoding="utf-8",
            )
            app = NotifierApp(root)

            enabled = app.is_morning_prayer_enabled()

        self.assertFalse(enabled)

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

    def test_sync_bot_commands_sends_menu_to_telegram(self):
        calls = []
        app = NotifierApp.__new__(NotifierApp)
        app.telegram = RecordingTelegram(calls)

        result = app.sync_bot_commands()

        self.assertIn("Синхронизировал команды Telegram-меню", result)
        self.assertEqual([call[0] for call in calls], ["set_my_commands", "set_my_commands"])
        self.assertIsNone(calls[0][2])
        self.assertEqual(calls[1][2], {"type": "all_private_chats"})
        self.assertIn({"command": "mi1", "description": "съел 1 прием пищи"}, calls[0][1])
        self.assertIn({"command": "mi1", "description": "съел 1 прием пищи"}, calls[1][1])


class RecordingTelegram:
    def __init__(self, calls, commands=None):
        self.calls = calls
        self.commands = commands or []

    def send_message(self, text):
        self.calls.append(("telegram", text))
        return 101 + len(self.calls)

    def get_commands(self, offset=None):
        self.calls.append(("get_commands", offset))
        return self.commands

    def delete_messages(self, message_ids):
        self.calls.append(("delete_messages", list(message_ids)))
        return DeleteSummary(deleted=len(message_ids), failed=0)

    def set_my_commands(self, commands, scope=None, language_code=None):
        self.calls.append(("set_my_commands", commands, scope, language_code))
        return True


class RecordingDesktop:
    def __init__(self, calls):
        self.calls = calls

    def show(self, title, message, blocking=False):
        self.calls.append(("desktop", title, message, blocking))
        return True


class NoopAudio:
    def play_for_event(self, event):
        return False


class RecordingAudio:
    def __init__(self, calls):
        self.calls = calls

    def play_for_event(self, event):
        self.calls.append(("audio", event.event_id))
        return True


class RecordingState:
    def __init__(self, calls):
        self.calls = calls
        self.last_event = None

    def track_telegram_message(self, message_id, direction, when=None):
        self.calls.append(("telegram-state", message_id, direction))

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


def add_optional_prayer_block(root: Path) -> None:
    schedule_path = root / "config" / "schedule.json"
    data = json.loads(schedule_path.read_text(encoding="utf-8"))
    data["blocks"] = {
        "chrysostom-prayers": {
            "title": "Молитвы Иоанна Златоуста",
            "enabled": False,
        }
    }
    data["events"].append(
        {
            "id": "chrysostom-prayer-01",
            "block": "chrysostom-prayers",
            "time": "05:00",
            "title": "Молитва Иоанна Златоуста 1/16",
            "message": "Господи, не лиши мене небесных Твоих благ.",
        }
    )
    schedule_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
