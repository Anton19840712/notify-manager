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
        self.assertIn("Пересчитал питание с интервалом 2:15", result.reply)
        self.assertIn("15:27 2 пп", result.reply)
        self.assertIn("22:12 5 пп", result.reply)
        self.assertNotIn("пв", result.reply)
        self.assertIn("\"suppress_cycles\": [", override_text)
        self.assertIn("\"water-food-cycle\"", override_text)
        self.assertNotIn("пв", override_text)


if __name__ == "__main__":
    unittest.main()
