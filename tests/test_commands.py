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


if __name__ == "__main__":
    unittest.main()
