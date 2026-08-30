import sys
import unittest
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.schedule import Schedule


class ScheduleTests(unittest.TestCase):
    def test_expands_water_and_food_cycle(self):
        schedule = Schedule.from_dict(
            {
                "events": [],
                "cycles": [
                    {
                        "id": "food-cycle",
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

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events],
            [
                ("water-1", "1 пв", "07:00"),
                ("meal-1", "1 пп", "07:15"),
                ("water-2", "2 пв", "09:25"),
                ("meal-2", "2 пп", "09:40"),
                ("water-3", "3 пв", "11:50"),
                ("meal-3", "3 пп", "12:05"),
                ("water-4", "4 пв", "14:15"),
                ("meal-4", "4 пп", "14:30"),
            ],
        )

    def test_includes_fixed_events_sorted_with_cycles(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "bed", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [
                    {
                        "id": "food-cycle",
                        "start_time": "07:00",
                        "period_minutes": 145,
                        "count": 1,
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

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual([event.event_id for event in events], ["wake", "meal-1", "bed"])

    def test_next_event_uses_reference_time(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "sleep", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [],
            }
        )

        event = schedule.next_event(datetime(2026, 8, 30, 5, 0))

        self.assertEqual(event.event_id, "sleep")


if __name__ == "__main__":
    unittest.main()

