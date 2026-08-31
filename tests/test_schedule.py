import json
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.schedule import Schedule


class ScheduleTests(unittest.TestCase):
    def test_day_override_can_suppress_fixed_events_for_one_day(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "learn", "time": "05:00", "title": "Учеба", "message": "Учиться"},
                    {"id": "bed", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [],
            },
            day_overrides={
                "2026-08-30": {
                    "suppress_events": ["wake", "learn"],
                    "events": [
                        {
                            "id": "wake",
                            "time": "10:00",
                            "title": "Подъем",
                            "message": "Сдвинутый подъем",
                        },
                        {
                            "id": "learn",
                            "time": "11:00",
                            "title": "Учеба",
                            "message": "Сдвинутая учеба",
                        },
                    ],
                }
            },
        )

        shifted_events = schedule.events_for_date(date(2026, 8, 30))
        base_events = schedule.events_for_date(date(2026, 8, 31))

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in shifted_events],
            [
                ("wake", "Подъем", "10:00"),
                ("learn", "Учеба", "11:00"),
                ("bed", "Отбой", "22:00"),
            ],
        )
        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in base_events],
            [
                ("wake", "Подъем", "04:00"),
                ("learn", "Учеба", "05:00"),
                ("bed", "Отбой", "22:00"),
            ],
        )

    def test_day_override_can_suppress_base_food_cycle_for_one_day(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                ],
                "cycles": [
                    {
                        "id": "food-cycle",
                        "start_time": "07:00",
                        "period_minutes": 145,
                        "count": 1,
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
            },
            day_overrides={
                "2026-08-30": {
                    "suppress_cycles": ["food-cycle"],
                    "events": [
                        {
                            "id": "override-meal-2",
                            "time": "15:05",
                            "title": "2 пп",
                            "message": "Сжатый прием пищи.",
                        }
                    ],
                }
            },
        )

        override_day_events = schedule.events_for_date(date(2026, 8, 30))
        base_day_events = schedule.events_for_date(date(2026, 8, 31))

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in override_day_events],
            [
                ("wake", "Подъем", "04:00"),
                ("override-meal-2", "2 пп", "15:05"),
            ],
        )
        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in base_day_events],
            [
                ("wake", "Подъем", "04:00"),
                ("water-1", "1 пв", "07:00"),
                ("meal-1", "1 пп", "07:15"),
            ],
        )

    def test_default_schedule_contains_detailed_morning_learning_sequence(self):
        schedule = Schedule.from_dict(
            json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        )

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events[:11]],
            [
                ("wake-up", "Подъем", "04:00"),
                ("morning-block", "Утренний блок: МП + кардио", "04:01"),
                ("morning-cardio-tail", "Кардио: закрепление состояния", "04:08"),
                ("spirit-reset", "Дух: добродетели + антируминация", "04:21"),
                ("day-optimization", "Оптимизация дня", "04:40"),
                ("target-engineering-article", "Целевая инженерная статья", "05:00"),
                ("microservices-reading", "Микросервисы", "06:00"),
                ("water-1", "1 пв", "07:00"),
                ("meal-1", "1 пп", "07:15"),
                ("monitoring-reading", "Мониторинг", "07:25"),
                ("morning-buffer", "Буфер / быт / подготовка к работе", "08:25"),
            ],
        )

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

    def test_remaining_today_excludes_past_events_and_tomorrow(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "bed", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [],
            }
        )

        events = schedule.remaining_today(datetime(2026, 8, 30, 21, 30))

        self.assertEqual([event.event_id for event in events], ["bed"])


if __name__ == "__main__":
    unittest.main()
