import json
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.commands import CommandContext, handle_command
from day_notifier.schedule import Schedule, ScheduleEvent


@dataclass
class MemoryState:
    snoozed: list[ScheduleEvent] = field(default_factory=list)
    done: list[str] = field(default_factory=list)
    last_event: ScheduleEvent | None = None

    def add_snooze(self, event, minutes):
        snoozed = ScheduleEvent(
            event_id=f"{event.event_id}-snooze",
            title=f"{event.title} +{minutes} мин",
            message=event.message,
            when=event.when + timedelta(minutes=minutes),
        )
        self.snoozed.append(snoozed)
        return snoozed

    def mark_done(self, event, when):
        self.done.append(event.event_id)


class CommandTests(unittest.TestCase):
    def make_context(self, inbox_path):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "water-1", "time": "07:00", "title": "1 пв", "message": "Выпей воду"},
                ],
                "cycles": [],
            }
        )
        return CommandContext(
            schedule=schedule,
            state=MemoryState(),
            inbox_path=inbox_path,
            now=lambda: datetime(2026, 8, 30, 6, 30),
        )

    def make_food_schedule(self):
        return Schedule.from_dict(
            {
                "events": [],
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
                            },
                            {
                                "offset_minutes": 15,
                                "id_template": "meal-{n}",
                                "title_template": "{n} пп",
                                "message_template": "{n} прием пищи",
                            },
                        ],
                    }
                ],
            }
        )

    def test_next_command_returns_next_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")

            result = handle_command("/next", context)

        self.assertIn("07:00", result.reply)
        self.assertIn("1 пв", result.reply)

    def test_inbox_command_appends_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            inbox_path = Path(temp_dir) / "inbox.md"
            context = self.make_context(inbox_path)

            result = handle_command("/inbox переслать зеленку видео", context)

            self.assertIn("Добавил", result.reply)
            self.assertIn("переслать зеленку видео", inbox_path.read_text(encoding="utf-8"))

    def test_snooze_command_delays_next_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")

            result = handle_command("/snooze 10", context)

        self.assertIn("07:10", result.reply)
        self.assertEqual(context.state.snoozed[0].event_id, "water-1-snooze")

    def test_summary_includes_upcoming_events_and_inbox(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            inbox_path = Path(temp_dir) / "inbox.md"
            inbox_path.write_text("- переслать видео\n", encoding="utf-8")
            context = self.make_context(inbox_path)

            result = handle_command("/summary", context)

        self.assertIn("Ближайшее", result.reply)
        self.assertIn("1 пв", result.reply)
        self.assertIn("переслать видео", result.reply)

    def test_today_command_returns_remaining_today_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")

            result = handle_command("/today", context)

        self.assertIn("Сегодня", result.reply)
        self.assertIn("07:00", result.reply)
        self.assertIn("1 пв", result.reply)

    def test_desktop_command_can_disable_notifications(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            calls = []
            context.set_desktop_enabled = calls.append

            result = handle_command("/desktop off", context)

        self.assertEqual(calls, [False])
        self.assertIn("выключены", result.reply)

    def test_desktop_command_can_enable_notifications(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            calls = []
            context.set_desktop_enabled = calls.append

            result = handle_command("/desktop on", context)

        self.assertEqual(calls, [True])
        self.assertIn("включены", result.reply)

    def test_desktop_status_command_reports_current_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            context.is_desktop_enabled = lambda: False

            result = handle_command("/desktop status", context)

        self.assertIn("выключены", result.reply)

    def test_recalc_food_command_writes_min_interval_day_override_without_water(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            reload_calls = []
            context.override_dir = Path(temp_dir) / "day_overrides"
            context.reload_schedule = lambda: reload_calls.append("reload")
            context.now = lambda: datetime(2026, 8, 31, 13, 12)

            result = handle_command("/recalc food 4", context)

            override_text = (context.override_dir / "2026-08-31.json").read_text(encoding="utf-8")

        self.assertEqual(reload_calls, ["reload"])
        self.assertIn("Пересчитал питание: 2:15 между концом еды и следующим приемом", result.reply)
        self.assertIn("окно еды 10 мин", result.reply)
        self.assertIn("15:27 2 пп", result.reply)
        self.assertIn("22:42 5 пп", result.reply)
        self.assertNotIn("пв", result.reply)
        self.assertIn("\"suppress_cycles\": [", override_text)
        self.assertIn("\"water-food-cycle\"", override_text)
        self.assertNotIn("пв", override_text)

    def test_meal_done_command_recalculates_remaining_food_from_now(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            reload_calls = []
            context.override_dir = Path(temp_dir) / "day_overrides"
            context.reload_schedule = lambda: reload_calls.append("reload")
            context.schedule = self.make_food_schedule()
            context.now = lambda: datetime(2026, 8, 31, 12, 25)

            result = handle_command("2 mi done", context)

            override_text = (context.override_dir / "2026-08-31.json").read_text(encoding="utf-8")

        self.assertEqual(reload_calls, ["reload"])
        self.assertIn("Принял: 2 пп завершен в 12:25.", result.reply)
        self.assertIn("Пересчитал остаток:", result.reply)
        self.assertIn("14:40 3 пп", result.reply)
        self.assertIn("17:05 4 пп", result.reply)
        self.assertNotIn("пв", result.reply)
        self.assertIn("\"water-food-cycle\"", override_text)
        self.assertNotIn("пв", override_text)

    def test_meal_done_command_accepts_aliases(self):
        for text in [
            "2 pp done",
            "2 пп done",
            "/2 mi done",
            "/2 pp done",
            "/ 2 mi done",
            "/mi2",
            "mi2",
            "/mi 2 done",
        ]:
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as temp_dir:
                    context = self.make_context(Path(temp_dir) / "inbox.md")
                    context.override_dir = Path(temp_dir) / "day_overrides"
                    context.schedule = self.make_food_schedule()
                    context.now = lambda: datetime(2026, 8, 31, 12, 25)

                    result = handle_command(text, context)

                self.assertIn("Принял: 2 пп завершен в 12:25.", result.reply)

    def test_botfather_meal_shortcut_marks_selected_meal_done(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            context.override_dir = Path(temp_dir) / "day_overrides"
            context.schedule = self.make_food_schedule()
            context.now = lambda: datetime(2026, 8, 31, 12, 25)

            result = handle_command("/mi1", context)

        self.assertIn("Принял: 1 пп завершен в 12:25.", result.reply)
        self.assertIn("14:40 2 пп", result.reply)

    def test_meal_done_command_rejects_invalid_meal_number(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            context.override_dir = Path(temp_dir) / "day_overrides"

            result = handle_command("0 mi done", context)

        self.assertIn("Используй: /2 mi done", result.reply)
        self.assertFalse(context.override_dir.exists())

    def test_sd_command_writes_override_and_reloads_schedule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            schedule_path = root / "schedule.json"
            schedule_path.write_text(
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
                                "items": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            context = self.make_context(root / "inbox.md")
            reload_calls = []
            context.override_dir = root / "day_overrides"
            context.schedule_path = schedule_path
            context.reload_schedule = lambda: reload_calls.append("reload")
            context.now = lambda: datetime(2026, 8, 31, 9, 0)

            result = handle_command("/sd 10:00", context)

            override_text = (context.override_dir / "2026-08-31.json").read_text(encoding="utf-8")
            data = json.loads(override_text)

        self.assertEqual(reload_calls, ["reload"])
        self.assertIn("Перенес день на 10:00", result.reply)
        self.assertIn("10:00 Подъем", result.reply)
        self.assertIn("12:25 2 пп", result.reply)
        self.assertIn("14:50 3 пп", result.reply)
        self.assertIn("water-food-cycle", data["suppress_cycles"])
        self.assertIn("wake-up", data["suppress_events"])
        self.assertNotIn("пв", override_text)

    def test_sd_command_accepts_plain_text_alias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            schedule_path = root / "schedule.json"
            schedule_path.write_text(
                json.dumps(
                    {
                        "events": [
                            {"id": "wake-up", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                            {"id": "bedtime", "time": "22:00", "title": "Отбой", "message": "Сон"},
                        ],
                        "cycles": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            context = self.make_context(root / "inbox.md")
            context.override_dir = root / "day_overrides"
            context.schedule_path = schedule_path
            context.now = lambda: datetime(2026, 8, 31, 9, 0)

            result = handle_command("sd 10:00", context)

        self.assertIn("Перенес день на 10:00", result.reply)

    def test_sd_command_rejects_invalid_time_without_writing_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            context = self.make_context(root / "inbox.md")
            context.override_dir = root / "day_overrides"
            context.schedule_path = root / "missing.json"
            context.now = lambda: datetime(2026, 8, 31, 9, 0)

            result = handle_command("/sd tomorrow", context)

        self.assertIn("Используй: /sd 10:00", result.reply)
        self.assertFalse((root / "day_overrides").exists())

    def test_bedtime_cleanup_command_uses_cleanup_callback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            calls = []
            context.cleanup_telegram_chat = (
                lambda: calls.append("cleanup") or "Отбой. Чат очищен: удалено 2, пропущено 0."
            )

            result = handle_command("/отбой", context)

        self.assertEqual(calls, ["cleanup"])
        self.assertEqual(result.reply, "Отбой. Чат очищен: удалено 2, пропущено 0.")

    def test_plain_bedtime_cleanup_text_uses_cleanup_callback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            context.cleanup_telegram_chat = lambda: "Отбой. Чат очищен: удалено 1, пропущено 0."

            result = handle_command("отбой", context)

        self.assertIn("Чат очищен", result.reply)

    def test_botfather_bedtime_alias_uses_cleanup_callback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            context.cleanup_telegram_chat = lambda: "Отбой. Чат очищен: удалено 1, пропущено 0."

            result = handle_command("/otboy", context)

        self.assertIn("Чат очищен", result.reply)

    def test_botfather_desktop_aliases_control_notifications(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")
            calls = []
            context.set_desktop_enabled = calls.append
            context.is_desktop_enabled = lambda: True

            on_result = handle_command("/desktop_on", context)
            off_result = handle_command("/desktop_off", context)
            status_result = handle_command("/desktop_status", context)

        self.assertEqual(calls, [True, False])
        self.assertIn("включены", on_result.reply)
        self.assertIn("выключены", off_result.reply)
        self.assertIn("сейчас включены", status_result.reply)

    def test_help_command_uses_botfather_safe_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self.make_context(Path(temp_dir) / "inbox.md")

            result = handle_command("/help", context)

        self.assertIn("/mi1 - съел 1 прием пищи", result.reply)
        self.assertIn("/sd - перенести старт дня", result.reply)


if __name__ == "__main__":
    unittest.main()
