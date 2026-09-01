import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.event_formatting import format_event_line, format_notification_text
from day_notifier.schedule import ScheduleEvent


class EventFormattingTests(unittest.TestCase):
    def test_event_line_adds_countdowns_for_requested_events(self):
        now = datetime(2026, 9, 1, 20, 45)
        meal = ScheduleEvent("meal-4", "4 пп", "Контейнер.", datetime(2026, 9, 1, 21, 0))
        batch = ScheduleEvent(
            "batch-cooking",
            "Batch-cooking: 12 приемов на 3 дня",
            "Готовка.",
            datetime(2026, 9, 1, 21, 30),
        )
        bedtime = ScheduleEvent("bedtime", "Отбой", "Сон.", datetime(2026, 9, 1, 22, 0))

        self.assertEqual(format_event_line(meal, now), "- 21:00 4 пп (до приема пищи: 15 мин)")
        self.assertEqual(
            format_event_line(batch, now),
            "- 21:30 Batch-cooking: 12 приемов на 3 дня (до batch-cooking: 45 мин)",
        )
        self.assertEqual(format_event_line(bedtime, now), "- 22:00 Отбой (до сна: 1 ч 15 мин)")

    def test_notification_text_can_include_current_time_for_desktop(self):
        event = ScheduleEvent("meal-4", "4 пп", "Контейнер.", datetime(2026, 9, 1, 21, 0))
        now = datetime(2026, 9, 1, 20, 45)

        self.assertEqual(
            format_notification_text(event, now, include_current_time=True),
            "Сейчас: 20:45\n21:00 - 4 пп (до приема пищи: 15 мин)\nКонтейнер.",
        )
        self.assertEqual(
            format_notification_text(event, now, include_current_time=False),
            "21:00 - 4 пп (до приема пищи: 15 мин)\nКонтейнер.",
        )

    def test_notification_text_omits_countdown_when_event_is_due_now(self):
        event = ScheduleEvent("meal-4", "4 пп", "Контейнер.", datetime(2026, 9, 1, 21, 0))
        now = datetime(2026, 9, 1, 21, 0)

        self.assertEqual(
            format_notification_text(event, now, include_current_time=True),
            "Сейчас: 21:00\n21:00 - 4 пп\nКонтейнер.",
        )

    def test_notification_text_omits_countdown_when_event_is_late(self):
        event = ScheduleEvent("bedtime", "Отбой", "Сон.", datetime(2026, 9, 1, 22, 0))
        now = datetime(2026, 9, 1, 22, 3)

        self.assertEqual(
            format_notification_text(event, now, include_current_time=True),
            "Сейчас: 22:03\n22:00 - Отбой\nСон.",
        )


if __name__ == "__main__":
    unittest.main()
