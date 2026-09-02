import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.overrides import (
    build_compressed_food_events,
    build_min_interval_food_events,
    build_shifted_day_override,
    write_meal_done_override,
    write_compressed_food_override,
    write_min_interval_food_override,
    write_shifted_day_override,
)
from day_notifier.schedule import Schedule, load_day_overrides


class OverrideTests(unittest.TestCase):
    def test_builds_meal_only_food_events_with_minimum_interval(self):
        events = build_min_interval_food_events(
            anchor=datetime(2026, 8, 31, 13, 12),
            remaining_meals=4,
            min_interval_minutes=135,
            last_meal_number=1,
        )

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events],
            [
                ("override-meal-2", "2 пп", "15:27"),
                ("override-meal-3", "3 пп", "17:52"),
                ("override-meal-4", "4 пп", "20:17"),
                ("override-meal-5", "5 пп", "22:42"),
            ],
        )

    def test_builds_emergency_meals_from_completed_meal_end_with_eating_window(self):
        events = build_min_interval_food_events(
            anchor=datetime(2026, 8, 31, 12, 25),
            remaining_meals=2,
            min_interval_minutes=135,
            last_meal_number=2,
            eating_minutes=10,
        )

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events],
            [
                ("override-meal-3", "3 пп", "14:40"),
                ("override-meal-4", "4 пп", "17:05"),
            ],
        )

    def test_write_min_interval_food_override_has_no_water_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            override_dir = Path(temp_dir) / "day_overrides"

            events = write_min_interval_food_override(
                override_dir=override_dir,
                anchor=datetime(2026, 8, 31, 13, 12),
                remaining_meals=4,
                min_interval_minutes=135,
                last_meal_number=1,
            )

            override_path = override_dir / "2026-08-31.json"
            override_text = override_path.read_text(encoding="utf-8")
            data = json.loads(override_text)

        self.assertEqual(events[-1].title, "5 пп")
        self.assertEqual(data["date"], "2026-08-31")
        self.assertEqual(data["suppress_cycles"], ["water-food-cycle"])
        self.assertEqual([event["title"] for event in data["events"]], ["2 пп", "3 пп", "4 пп", "5 пп"])
        self.assertNotIn("пв", override_text)

    def test_write_meal_done_override_recalculates_remaining_meals_from_completion_time(self):
        schedule = Schedule.from_dict(
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
        with tempfile.TemporaryDirectory() as temp_dir:
            override_dir = Path(temp_dir) / "day_overrides"

            events = write_meal_done_override(
                override_dir=override_dir,
                schedule=schedule,
                day=datetime(2026, 8, 31).date(),
                completed_meal_number=2,
                completed_at=datetime(2026, 8, 31, 12, 25),
            )

            data = json.loads((override_dir / "2026-08-31.json").read_text(encoding="utf-8"))

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events],
            [
                ("override-meal-3", "3 пп", "14:40"),
                ("override-meal-4", "4 пп", "17:05"),
            ],
        )
        self.assertEqual(data["suppress_cycles"], ["water-food-cycle"])
        self.assertEqual([event["title"] for event in data["events"]], ["3 пп", "4 пп"])
        self.assertNotIn("пв", json.dumps(data, ensure_ascii=False))

    def test_write_meal_done_override_preserves_shifted_non_food_events(self):
        schedule_data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            override_dir = Path(temp_dir) / "day_overrides"
            write_shifted_day_override(
                override_dir=override_dir,
                schedule_data=schedule_data,
                day=datetime(2026, 8, 31).date(),
                start_time="10:00",
            )
            schedule = Schedule.from_dict(schedule_data, day_overrides=load_day_overrides(override_dir))

            events = write_meal_done_override(
                override_dir=override_dir,
                schedule=schedule,
                day=datetime(2026, 8, 31).date(),
                completed_meal_number=2,
                completed_at=datetime(2026, 8, 31, 12, 25),
            )

            data = json.loads((override_dir / "2026-08-31.json").read_text(encoding="utf-8"))

        self.assertEqual([event.title for event in events], ["3 пп", "4 пп"])
        self.assertIn("wake-up", data["suppress_events"])
        self.assertIn(
            {
                "id": "wake-up",
                "time": "10:00",
                "title": "Подъем",
                "message": "Подъем. Минута на одежду, телефон не открывать фоном.",
            },
            data["events"],
        )
        self.assertNotIn("meal-3", [event["id"] for event in data["events"]])
        self.assertIn(
            {
                "id": "override-meal-3",
                "time": "14:40",
                "title": "3 пп",
                "message": "Пересчитанный день: 3 прием пищи. Воду пить поверх приема и между приемами.",
            },
            data["events"],
        )

    def test_build_shifted_day_override_keeps_sleep_fixed_and_uses_emergency_meals(self):
        schedule_data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))

        data = build_shifted_day_override(
            schedule_data=schedule_data,
            day=datetime(2026, 8, 31).date(),
            start_time="10:00",
        )

        self.assertIn("water-food-cycle", data["suppress_cycles"])
        self.assertIn("wake-up", data["suppress_events"])
        self.assertIn("morning-block", data["suppress_events"])
        self.assertNotIn("bedtime", data["suppress_events"])
        self.assertEqual(
            [(event["id"], event["time"], event["title"]) for event in data["events"][:6]],
            [
                ("wake-up", "10:00", "Подъем"),
                ("meal-1", "10:00", "1 пп"),
                ("morning-block", "10:01", "Утренний блок: МП + кардио"),
                ("morning-cardio-tail", "10:08", "Кардио: закрепление состояния"),
                ("spirit-reset", "10:21", "Дух: добродетели + антируминация"),
                ("day-optimization", "10:40", "Оптимизация дня"),
            ],
        )
        self.assertIn(
            {
                "id": "meal-2",
                "time": "12:25",
                "title": "2 пп",
                "message": "2 прием пищи. Воду пить поверх приема и между приемами.",
            },
            data["events"],
        )
        self.assertIn(
            {
                "id": "meal-3",
                "time": "14:50",
                "title": "3 пп",
                "message": "3 прием пищи. Воду пить поверх приема и между приемами.",
            },
            data["events"],
        )

    def test_build_shifted_day_override_preserves_block_metadata(self):
        schedule_data = {
            "events": [
                {"id": "wake-up", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                {
                    "id": "target-engineering-article",
                    "block": "self-development",
                    "time": "05:00",
                    "title": "Целевая инженерная статья",
                    "message": "Учиться.",
                },
            ],
            "cycles": [],
        }

        data = build_shifted_day_override(
            schedule_data=schedule_data,
            day=datetime(2026, 8, 31).date(),
            start_time="10:00",
        )

        shifted_article = next(event for event in data["events"] if event["id"] == "target-engineering-article")
        self.assertEqual(shifted_article["time"], "11:00")
        self.assertEqual(shifted_article["block"], "self-development")

    def test_build_shifted_day_override_drops_events_after_midnight(self):
        schedule_data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))

        data = build_shifted_day_override(
            schedule_data=schedule_data,
            day=datetime(2026, 8, 31).date(),
            start_time="20:00",
        )

        event_ids = [event["id"] for event in data["events"]]
        self.assertIn("meal-2", event_ids)
        self.assertNotIn("meal-3", event_ids)
        self.assertNotIn("morning-buffer", event_ids)
        self.assertTrue(all(event["time"] >= "20:00" for event in data["events"]))

    def test_write_shifted_day_override_preserves_base_schedule_for_other_dates(self):
        schedule_data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            override_dir = Path(temp_dir) / "day_overrides"

            write_shifted_day_override(
                override_dir=override_dir,
                schedule_data=schedule_data,
                day=datetime(2026, 8, 31).date(),
                start_time="10:00",
            )

            loaded = load_day_overrides(override_dir)

        self.assertIn("2026-08-31", loaded)
        self.assertEqual(loaded["2026-08-31"]["events"][0]["time"], "10:00")
        self.assertIn("wake-up", loaded["2026-08-31"]["suppress_events"])

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
