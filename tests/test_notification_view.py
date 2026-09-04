import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.notification_view import build_notification_view
from day_notifier.schedule import ScheduleEvent


class NotificationViewTests(unittest.TestCase):
    def test_meal_view_has_countdown_and_actions(self):
        event = ScheduleEvent(
            event_id="meal-2",
            title="2 пп",
            message="Контейнер, без хаотичного телефона.",
            when=datetime(2026, 9, 4, 12, 35),
        )

        view = build_notification_view(event, datetime(2026, 9, 4, 12, 15))

        self.assertEqual(view.event_id, "meal-2")
        self.assertEqual(view.importance, "critical")
        self.assertEqual(view.status, "до приема пищи: 20 мин")
        self.assertIn("Сейчас: 12:15", view.body)
        self.assertIn("12:35 - 2 пп", view.body)
        self.assertEqual([action.action for action in view.actions], ["done", "snooze_10", "skip"])

    def test_due_now_view_does_not_add_pointless_countdown_suffix(self):
        event = ScheduleEvent(
            event_id="meal-1",
            title="1 пп",
            message="Контейнер.",
            when=datetime(2026, 9, 4, 7, 15),
        )

        view = build_notification_view(event, datetime(2026, 9, 4, 7, 15))

        self.assertEqual(view.status, "до приема пищи: сейчас")
        self.assertIn("07:15 - 1 пп", view.body)
        self.assertNotIn("(до приема пищи:", view.body)

    def test_generic_view_has_normal_importance(self):
        event = ScheduleEvent(
            event_id="work-daily",
            title="Дейли по работе",
            message="Сроки, риски, архитектура.",
            when=datetime(2026, 9, 4, 11, 0),
        )

        view = build_notification_view(event, datetime(2026, 9, 4, 10, 50))

        self.assertEqual(view.importance, "normal")
        self.assertEqual(view.status, "через: 10 мин")
        self.assertEqual([action.action for action in view.actions], ["done", "snooze_10", "skip"])


if __name__ == "__main__":
    unittest.main()
