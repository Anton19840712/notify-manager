import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.desktop_actions import DesktopAction, append_desktop_action, consume_desktop_actions
from day_notifier.schedule import ScheduleEvent


class DesktopActionTests(unittest.TestCase):
    def test_append_and_consume_actions_clears_queue(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "data" / "desktop_actions.jsonl"
            event = ScheduleEvent(
                event_id="meal-1",
                title="1 пп",
                message="Контейнер.",
                when=datetime(2026, 9, 4, 7, 15),
            )
            action = DesktopAction.from_event("done", event, action_id="action-1")

            append_desktop_action(path, action)
            consumed = consume_desktop_actions(path)
            queue_text = path.read_text(encoding="utf-8")

        self.assertEqual(len(consumed), 1)
        self.assertEqual(consumed[0].action, "done")
        self.assertEqual(consumed[0].to_event().event_id, "meal-1")
        self.assertEqual(queue_text, "")

    def test_consume_actions_skips_invalid_lines_and_deduplicates_action_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "desktop_actions.jsonl"
            line = json.dumps(
                {
                    "action_id": "same",
                    "action": "skip",
                    "event_id": "water-1",
                    "title": "1 пв",
                    "message": "Выпей воду",
                    "when": "2026-09-04T07:00:00",
                },
                ensure_ascii=False,
            )
            path.write_text("\n".join([line, "not json", line]), encoding="utf-8")

            consumed = consume_desktop_actions(path)

        self.assertEqual(len(consumed), 1)
        self.assertEqual(consumed[0].action_id, "same")
        self.assertEqual(consumed[0].action, "skip")


if __name__ == "__main__":
    unittest.main()
