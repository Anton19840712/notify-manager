import json
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.schedule import Schedule


class ScheduleTests(unittest.TestCase):
    def test_disabled_event_block_keeps_events_out_of_day(self):
        schedule = Schedule.from_dict(
            {
                "blocks": {
                    "optional-prayers": {
                        "enabled": False,
                    }
                },
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {
                        "id": "optional-prayer-1",
                        "block": "optional-prayers",
                        "time": "05:00",
                        "title": "Опциональная молитва",
                        "message": "Текст молитвы",
                    },
                ],
                "cycles": [],
            },
        )

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual([event.event_id for event in events], ["wake"])

    def test_enabled_event_block_restores_events_to_day(self):
        schedule = Schedule.from_dict(
            {
                "blocks": {
                    "optional-prayers": {
                        "enabled": True,
                    }
                },
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {
                        "id": "optional-prayer-1",
                        "block": "optional-prayers",
                        "time": "05:00",
                        "title": "Опциональная молитва",
                        "message": "Текст молитвы",
                    },
                ],
                "cycles": [],
            },
        )

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual([event.event_id for event in events], ["wake", "optional-prayer-1"])

    def test_block_override_can_enable_disabled_event_block(self):
        schedule = Schedule.from_dict(
            {
                "blocks": {
                    "optional-prayers": {
                        "enabled": False,
                    }
                },
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {
                        "id": "optional-prayer-1",
                        "block": "optional-prayers",
                        "time": "05:00",
                        "title": "Опциональная молитва",
                        "message": "Текст молитвы",
                    },
                ],
                "cycles": [],
            },
            block_overrides={"optional-prayers": True},
        )

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual([event.event_id for event in events], ["wake", "optional-prayer-1"])

    def test_block_override_can_disable_enabled_event_block(self):
        schedule = Schedule.from_dict(
            {
                "blocks": {
                    "optional-prayers": {
                        "enabled": True,
                    }
                },
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {
                        "id": "optional-prayer-1",
                        "block": "optional-prayers",
                        "time": "05:00",
                        "title": "Опциональная молитва",
                        "message": "Текст молитвы",
                    },
                ],
                "cycles": [],
            },
            block_overrides={"optional-prayers": False},
        )

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual([event.event_id for event in events], ["wake"])

    def test_block_override_can_disable_override_event_block(self):
        schedule = Schedule.from_dict(
            {
                "blocks": {
                    "self-development": {
                        "enabled": True,
                    }
                },
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {
                        "id": "learn",
                        "block": "self-development",
                        "time": "05:00",
                        "title": "Учеба",
                        "message": "Учиться",
                    },
                ],
                "cycles": [],
            },
            day_overrides={
                "2026-08-30": {
                    "suppress_events": ["learn"],
                    "events": [
                        {
                            "id": "learn",
                            "block": "self-development",
                            "time": "10:00",
                            "title": "Учеба",
                            "message": "Сдвинутая учеба",
                        }
                    ],
                }
            },
            block_overrides={"self-development": False},
        )

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual([event.event_id for event in events], ["wake"])

    def test_rotating_event_block_can_be_disabled(self):
        schedule = Schedule.from_dict(
            {
                "blocks": {
                    "training": {
                        "enabled": True,
                    }
                },
                "events": [],
                "cycles": [],
                "rotating_events": [
                    {
                        "id": "strength-rotation",
                        "block": "training",
                        "start_date": "2026-09-01",
                        "time": "11:15",
                        "period_days": 7,
                        "items": [
                            {
                                "offset_days": 0,
                                "id": "strength-pullups",
                                "title": "Силовой блок",
                                "message": "Бедра + голень.",
                            },
                        ],
                    }
                ],
            },
            block_overrides={"training": False},
        )

        events = schedule.events_for_date(date(2026, 9, 1))

        self.assertEqual(events, [])

    def test_relative_cycle_block_can_be_disabled(self):
        schedule = Schedule.from_dict(
            {
                "blocks": {
                    "home-maintenance": {
                        "enabled": True,
                    }
                },
                "events": [],
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
                "relative_cycles": [
                    {
                        "id": "optional-cleanup",
                        "block": "home-maintenance",
                        "kind": "after_last_meal",
                        "start_date": "2026-09-01",
                        "period_days": 1,
                        "anchor_offset_minutes": 10,
                        "items": [
                            {
                                "offset_minutes": 0,
                                "id": "cleanup",
                                "title": "Уборка",
                                "message": "Опциональная уборка.",
                            },
                        ],
                    }
                ],
            },
            block_overrides={"home-maintenance": False},
        )

        events = schedule.events_for_date(date(2026, 9, 1))

        self.assertEqual([event.event_id for event in events], ["pre-meal-1", "meal-1"])

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
                ("pre-override-meal-2", "10 минут до 2 пп", "14:55"),
                ("override-meal-2", "2 пп", "15:05"),
            ],
        )
        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in base_day_events],
            [
                ("wake", "Подъем", "04:00"),
                ("water-1", "1 пв", "07:00"),
                ("pre-meal-1", "10 минут до 1 пп", "07:05"),
                ("meal-1", "1 пп", "07:15"),
            ],
        )

    def test_meal_prep_reminders_are_generated_for_base_and_override_meals(self):
        schedule = Schedule.from_dict(
            {
                "events": [],
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
                            },
                        ],
                    }
                ],
            },
            day_overrides={
                "2026-08-31": {
                    "suppress_cycles": ["food-cycle"],
                    "events": [
                        {
                            "id": "override-meal-4",
                            "time": "19:25",
                            "title": "4 пп",
                            "message": "Пересчитанный прием пищи.",
                        }
                    ],
                }
            },
        )

        base_events = schedule.events_for_date(date(2026, 8, 30))
        override_events = schedule.events_for_date(date(2026, 8, 31))

        self.assertEqual(
            [(event.event_id, event.title, event.message, event.when.strftime("%H:%M")) for event in base_events],
            [
                (
                    "pre-meal-1",
                    "10 минут до 1 пп",
                    "Через 10 минут 1 пп. Выбери 1 микрозадачу: пыль, вещи по местам, пол, бритье или inbox. Сложное не открывать.",
                    "07:05",
                ),
                ("meal-1", "1 пп", "1 прием пищи", "07:15"),
            ],
        )
        self.assertEqual(
            [(event.event_id, event.title, event.message, event.when.strftime("%H:%M")) for event in override_events],
            [
                (
                    "pre-override-meal-4",
                    "10 минут до 4 пп",
                    "Через 10 минут 4 пп. Выбери 1 микрозадачу: пыль, вещи по местам, пол, бритье или inbox. Сложное не открывать.",
                    "19:15",
                ),
                ("override-meal-4", "4 пп", "Пересчитанный прием пищи.", "19:25"),
            ],
        )

    def test_ten_minute_task_catalog_exists_for_pre_meal_reminders(self):
        text = (ROOT / "data" / "ten-minute-tasks.md").read_text(encoding="utf-8")

        self.assertIn("Протереть пыль", text)
        self.assertIn("Вещи по местам", text)
        self.assertIn("Побриться", text)
        self.assertIn("Не брать в 10 минут", text)

    def test_relative_cycle_runs_every_third_day_after_last_meal_from_override(self):
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
                                "offset_minutes": 15,
                                "id_template": "meal-{n}",
                                "title_template": "{n} пп",
                                "message_template": "{n} прием пищи",
                            }
                        ],
                    }
                ],
                "relative_cycles": [
                    {
                        "id": "batch-cooking-3-day-cycle",
                        "kind": "after_last_meal",
                        "start_date": "2026-09-01",
                        "period_days": 3,
                        "anchor_offset_minutes": 10,
                        "items": [
                            {
                                "offset_minutes": 0,
                                "id": "batch-cooking",
                                "title": "Batch-cooking: 12 приемов на 3 дня",
                                "message": "Один длинный цикл готовки.",
                            },
                        ],
                    }
                ],
            },
            day_overrides={
                "2026-09-01": {
                    "suppress_cycles": ["food-cycle"],
                    "events": [
                        {
                            "id": "override-meal-4",
                            "time": "19:07",
                            "title": "4 пп",
                            "message": "Последний прием пищи.",
                        }
                    ],
                }
            },
        )

        cooking_day = schedule.events_for_date(date(2026, 9, 1))
        off_day = schedule.events_for_date(date(2026, 9, 2))
        next_cooking_day = schedule.events_for_date(date(2026, 9, 4))

        self.assertEqual(
            [(event.event_id, event.when.strftime("%H:%M")) for event in cooking_day if event.event_id.startswith("batch-cooking")],
            [
                ("batch-cooking", "19:17"),
            ],
        )
        self.assertFalse(any(event.event_id.startswith("batch-cooking") for event in off_day))
        self.assertEqual(
            [(event.event_id, event.when.strftime("%H:%M")) for event in next_cooking_day if event.event_id.startswith("batch-cooking")],
            [
                ("batch-cooking", "14:40"),
            ],
        )

    def test_rotating_events_select_item_by_day_offset(self):
        schedule = Schedule.from_dict(
            {
                "events": [],
                "cycles": [],
                "rotating_events": [
                    {
                        "id": "strength-rotation",
                        "start_date": "2026-09-01",
                        "time": "11:15",
                        "period_days": 7,
                        "items": [
                            {
                                "offset_days": 0,
                                "id": "strength-pullups",
                                "title": "Силовой блок: подтягивания",
                                "message": "Подтягивания.",
                            },
                            {
                                "offset_days": 1,
                                "id": "strength-bench-press",
                                "title": "Силовой блок: жим лежа",
                                "message": "Жим лежа.",
                            },
                        ],
                    }
                ],
            },
            day_overrides={
                "2026-09-02": {
                    "suppress_events": ["strength-bench-press"],
                }
            },
        )

        before_start = schedule.events_for_date(date(2026, 8, 31))
        day_zero = schedule.events_for_date(date(2026, 9, 1))
        suppressed_day = schedule.events_for_date(date(2026, 9, 2))
        repeated_day_zero = schedule.events_for_date(date(2026, 9, 8))

        self.assertEqual(before_start, [])
        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in day_zero],
            [
                ("strength-pullups", "Силовой блок: подтягивания", "11:15"),
            ],
        )
        self.assertEqual(suppressed_day, [])
        self.assertEqual([event.event_id for event in repeated_day_zero], ["strength-pullups"])

    def test_default_schedule_contains_detailed_morning_learning_sequence(self):
        schedule = Schedule.from_dict(
            json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        )

        events = schedule.events_for_date(date(2026, 8, 30))

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events[:12]],
            [
                ("wake-up", "Подъем", "04:00"),
                ("morning-block", "Утренний блок: МП + кардио", "04:01"),
                ("morning-cardio-tail", "Кардио: закрепление состояния", "04:08"),
                ("spirit-reset", "Дух: добродетели + антируминация", "04:21"),
                ("day-optimization", "Оптимизация дня", "04:40"),
                ("target-engineering-article", "Целевая инженерная статья", "05:00"),
                ("microservices-reading", "Микросервисы", "06:00"),
                ("water-1", "1 пв", "07:00"),
                ("pre-meal-1", "10 минут до 1 пп", "07:05"),
                ("meal-1", "1 пп", "07:15"),
                ("monitoring-reading", "Мониторинг", "07:25"),
                ("morning-buffer", "Буфер / быт / подготовка к работе", "08:25"),
            ],
        )

    def test_default_schedule_keeps_chrysostom_prayers_as_disabled_block(self):
        data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        schedule = Schedule.from_dict(data)

        events = schedule.events_for_date(date(2026, 8, 30))
        prayers = [event for event in events if event.event_id.startswith("chrysostom-prayer-")]
        configured_prayers = [event for event in data["events"] if event.get("block") == "chrysostom-prayers"]

        self.assertFalse(data["blocks"]["chrysostom-prayers"]["enabled"])
        self.assertEqual(len(configured_prayers), 16)
        self.assertEqual(prayers, [])

    def test_chrysostom_prayer_block_can_be_enabled_from_config(self):
        data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        data["blocks"]["chrysostom-prayers"]["enabled"] = True
        schedule = Schedule.from_dict(data)

        events = schedule.events_for_date(date(2026, 8, 30))
        prayers = [event for event in events if event.event_id.startswith("chrysostom-prayer-")]

        self.assertEqual(len(prayers), 16)
        self.assertEqual([event.event_id for event in prayers], [f"chrysostom-prayer-{index:02d}" for index in range(1, 17)])
        self.assertEqual([event.when.strftime("%H:%M") for event in prayers], [f"{hour:02d}:00" for hour in range(5, 21)])
        self.assertEqual(prayers[0].title, "Молитва Иоанна Златоуста 1/16")
        self.assertEqual(prayers[-1].title, "Молитва Иоанна Златоуста 16/16")

    def test_default_schedule_contains_batch_cooking_every_third_day(self):
        schedule = Schedule.from_dict(
            json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        )

        first_cooking_day = schedule.events_for_date(date(2026, 9, 1))
        off_day = schedule.events_for_date(date(2026, 9, 2))
        next_cooking_day = schedule.events_for_date(date(2026, 9, 4))

        self.assertEqual(
            [(event.title, event.when.strftime("%H:%M")) for event in first_cooking_day if event.event_id.startswith("batch-cooking")],
            [
                ("Batch-cooking: 12 приемов на 3 дня", "14:40"),
            ],
        )
        self.assertFalse(any(event.event_id.startswith("batch-cooking") for event in off_day))
        self.assertTrue(any(event.event_id == "batch-cooking" for event in next_cooking_day))
        self.assertFalse(any(event.title == "Контейнеры + кухня" for event in first_cooking_day))

    def test_default_schedule_has_toggleable_self_development_training_and_prayer_blocks(self):
        data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))

        self.assertTrue(data["blocks"]["self-development"]["enabled"])
        self.assertTrue(data["blocks"]["training"]["enabled"])
        self.assertTrue(data["blocks"]["prayers"]["enabled"])
        self.assertFalse(data["blocks"]["chrysostom-prayers"]["enabled"])
        self.assertEqual(data["rotating_events"][0]["block"], "training")
        self.assertNotIn("block", data["cycles"][0])
        self.assertNotIn("block", data["relative_cycles"][0])

    def test_default_schedule_can_disable_self_development_without_dropping_food(self):
        data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        schedule = Schedule.from_dict(data, block_overrides={"self-development": False})

        events = schedule.events_for_date(date(2026, 8, 30))
        event_ids = [event.event_id for event in events]

        self.assertIn("wake-up", event_ids)
        self.assertIn("meal-1", event_ids)
        self.assertNotIn("day-optimization", event_ids)
        self.assertNotIn("target-engineering-article", event_ids)
        self.assertNotIn("microservices-reading", event_ids)
        self.assertNotIn("monitoring-reading", event_ids)

    def test_default_schedule_can_disable_training_without_dropping_food_or_work(self):
        data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        schedule = Schedule.from_dict(data, block_overrides={"training": False})

        events = schedule.events_for_date(date(2026, 9, 1))
        event_ids = [event.event_id for event in events]

        self.assertIn("work-daily", event_ids)
        self.assertIn("meal-3", event_ids)
        self.assertNotIn("strength-pullups", event_ids)

    def test_default_schedule_can_disable_prayers_without_dropping_wake_food_or_sleep(self):
        data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        schedule = Schedule.from_dict(data, block_overrides={"prayers": False})

        events = schedule.events_for_date(date(2026, 8, 30))
        event_ids = [event.event_id for event in events]

        self.assertIn("wake-up", event_ids)
        self.assertIn("meal-1", event_ids)
        self.assertIn("bedtime", event_ids)
        self.assertNotIn("morning-block", event_ids)
        self.assertNotIn("spirit-reset", event_ids)

    def test_default_schedule_contains_strength_rotation_and_lunch_nap(self):
        schedule = Schedule.from_dict(
            json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        )

        first_day = schedule.events_for_date(date(2026, 9, 1))
        second_day = schedule.events_for_date(date(2026, 9, 2))

        self.assertIn(
            ("work-daily", "Дейли по работе", "11:00"),
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in first_day],
        )
        self.assertIn(
            ("strength-pullups", "Силовой блок: бедра + голень + подтягивания", "11:15"),
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in first_day],
        )
        self.assertIn(
            ("lunch-nap-start", "Досып / восстановление", "12:15"),
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in first_day],
        )
        self.assertIn(
            ("lunch-nap-end", "Подъем после досыпа", "13:15"),
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in first_day],
        )
        self.assertIn(
            ("strength-bench-press", "Силовой блок: бедра + голень + жим лежа", "11:15"),
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in second_day],
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
                ("pre-meal-1", "10 минут до 1 пп", "07:05"),
                ("meal-1", "1 пп", "07:15"),
                ("water-2", "2 пв", "09:25"),
                ("pre-meal-2", "10 минут до 2 пп", "09:30"),
                ("meal-2", "2 пп", "09:40"),
                ("water-3", "3 пв", "11:50"),
                ("pre-meal-3", "10 минут до 3 пп", "11:55"),
                ("meal-3", "3 пп", "12:05"),
                ("water-4", "4 пв", "14:15"),
                ("pre-meal-4", "10 минут до 4 пп", "14:20"),
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

        self.assertEqual([event.event_id for event in events], ["wake", "pre-meal-1", "meal-1", "bed"])

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
