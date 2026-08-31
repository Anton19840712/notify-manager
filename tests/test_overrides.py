import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.overrides import build_compressed_food_events, write_compressed_food_override
from day_notifier.schedule import load_day_overrides


class OverrideTests(unittest.TestCase):
    def test_builds_compressed_food_events_until_cutoff(self):
        events = build_compressed_food_events(
            anchor=datetime(2026, 8, 31, 13, 12),
            remaining_meals=4,
            cutoff_time="20:45",
            last_meal_number=1,
        )

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events],
            [
                ("override-water-2", "2 пв", "14:50"),
                ("override-meal-2", "2 пп", "15:05"),
                ("override-water-3", "3 пв", "16:44"),
                ("override-meal-3", "3 пп", "16:59"),
                ("override-water-4", "4 пв", "18:37"),
                ("override-meal-4", "4 пп", "18:52"),
                ("override-water-5", "5 пв", "20:30"),
                ("override-meal-5", "5 пп", "20:45"),
            ],
        )

    def test_write_compressed_food_override_suppresses_base_food_cycle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            override_dir = Path(temp_dir) / "day_overrides"

            events = write_compressed_food_override(
                override_dir=override_dir,
                anchor=datetime(2026, 8, 31, 13, 12),
                remaining_meals=4,
                cutoff_time="20:45",
                last_meal_number=1,
            )

            override_path = override_dir / "2026-08-31.json"
            data = json.loads(override_path.read_text(encoding="utf-8"))
            loaded = load_day_overrides(override_dir)

        self.assertEqual(events[-1].title, "5 пп")
        self.assertEqual(data["date"], "2026-08-31")
        self.assertEqual(data["suppress_cycles"], ["water-food-cycle"])
        self.assertEqual(data["events"][0]["time"], "14:50")
        self.assertIn("2026-08-31", loaded)


if __name__ == "__main__":
    unittest.main()
