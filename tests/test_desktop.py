import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.desktop import DesktopNotifier


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


if __name__ == "__main__":
    unittest.main()

