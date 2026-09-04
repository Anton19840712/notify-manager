import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.desktop import DesktopNotifier
from day_notifier.notification_view import build_notification_view
from day_notifier.schedule import ScheduleEvent


class DesktopNotifierTests(unittest.TestCase):
    def test_disabled_desktop_notifier_does_not_call_message_box(self):
        calls = []
        notifier = DesktopNotifier(enabled=False, message_box=lambda title, message: calls.append((title, message)))

        shown = notifier.show("Title", "Message", blocking=True)

        self.assertFalse(shown)
        self.assertEqual(calls, [])

    def test_blocking_desktop_notifier_calls_message_box(self):
        calls = []
        notifier = DesktopNotifier(enabled=True, message_box=lambda title, message: calls.append((title, message)))

        shown = notifier.show("Title", "Message", blocking=True)

        self.assertTrue(shown)
        self.assertEqual(calls, [("Title", "Message")])

    def test_card_mode_launches_card_renderer_for_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            calls = []
            notifier = DesktopNotifier(
                enabled=True,
                mode="card",
                card_theme="dark_glass_command",
                root=Path(temp_dir),
                card_launcher=lambda payload: calls.append(payload) or True,
            )
            event = ScheduleEvent(
                event_id="meal-1",
                title="1 пп",
                message="Контейнер.",
                when=datetime(2026, 9, 4, 7, 15),
            )
            view = build_notification_view(event, datetime(2026, 9, 4, 7, 10))

            shown = notifier.show_event(view)

        self.assertTrue(shown)
        self.assertEqual(calls[0]["event"]["event_id"], "meal-1")
        self.assertEqual(calls[0]["title"], "1 пп")
        self.assertEqual(calls[0]["theme"], "dark_glass_command")
        self.assertIn("до приема пищи", calls[0]["status"])
        self.assertIn("done", [action["action"] for action in calls[0]["actions"]])

    def test_card_mode_falls_back_to_message_box_when_renderer_fails(self):
        calls = []
        notifier = DesktopNotifier(
            enabled=True,
            mode="card",
            card_launcher=lambda payload: False,
            message_box=lambda title, message: calls.append((title, message)),
        )
        event = ScheduleEvent(
            event_id="water-1",
            title="1 пв",
            message="Выпей воду",
            when=datetime(2026, 9, 4, 7, 0),
        )
        view = build_notification_view(event, datetime(2026, 9, 4, 7, 0))

        shown = notifier.show_event(view)

        self.assertTrue(shown)
        self.assertEqual(calls[0][0], "1 пв")
        self.assertIn("Сейчас: 07:00", calls[0][1])

    def test_show_uses_card_mode_for_generic_messages(self):
        calls = []
        notifier = DesktopNotifier(
            enabled=True,
            mode="card",
            card_launcher=lambda payload: calls.append(payload) or True,
        )

        shown = notifier.show("notify-manager", "Тест", blocking=True)

        self.assertTrue(shown)
        self.assertEqual(calls[0]["title"], "notify-manager")
        self.assertEqual(calls[0]["body"], "Тест")


if __name__ == "__main__":
    unittest.main()
