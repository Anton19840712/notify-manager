from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path

from day_notifier.schedule import Schedule, ScheduleEvent


FOOD_CYCLE_ID = "water-food-cycle"
DEFAULT_MIN_MEAL_INTERVAL_MINUTES = 135
DEFAULT_EATING_WINDOW_MINUTES = 10
MEAL_TITLE_PATTERN = re.compile(r"^(\d+)\s*пп$", re.IGNORECASE)
FOOD_EVENT_ID_PATTERN = re.compile(r"^(override-)?(meal|water)-\d+$", re.IGNORECASE)
SHIFTED_DAY_BASE_EVENT_ID = "wake-up"
SHIFTED_DAY_EVENT_IDS = [
    "wake-up",
    "morning-block",
    "morning-cardio-tail",
    "spirit-reset",
    "day-optimization",
    "target-engineering-article",
    "microservices-reading",
    "monitoring-reading",
    "morning-buffer",
]


def build_min_interval_food_events(
    anchor: datetime,
    remaining_meals: int,
    min_interval_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    last_meal_number: int = 1,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> list[ScheduleEvent]:
    if remaining_meals < 1:
        raise ValueError("remaining meals must be at least 1")
    if min_interval_minutes < 1:
        raise ValueError("minimum interval must be at least 1 minute")
    if eating_minutes < 1:
        raise ValueError("eating window must be at least 1 minute")
    if last_meal_number < 0:
        raise ValueError("last meal number must be 0 or greater")

    anchor_minute = anchor.replace(second=0, microsecond=0)
    events: list[ScheduleEvent] = []
    for index in range(1, remaining_meals + 1):
        meal_number = last_meal_number + index
        meal_at = anchor_minute + timedelta(
            minutes=min_interval_minutes + (min_interval_minutes + eating_minutes) * (index - 1)
        )
        events.append(
            ScheduleEvent(
                event_id=f"override-meal-{meal_number}",
                title=f"{meal_number} пп",
                message=(
                    f"Пересчитанный день: {meal_number} прием пищи. "
                    "Воду пить поверх приема и между приемами."
                ),
                when=meal_at,
            )
        )
    return events


def write_min_interval_food_override(
    override_dir: Path,
    anchor: datetime,
    remaining_meals: int,
    min_interval_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    last_meal_number: int = 1,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> list[ScheduleEvent]:
    events = build_min_interval_food_events(
        anchor=anchor,
        remaining_meals=remaining_meals,
        min_interval_minutes=min_interval_minutes,
        last_meal_number=last_meal_number,
        eating_minutes=eating_minutes,
    )
    data = {
        "date": anchor.date().isoformat(),
        "suppress_cycles": [FOOD_CYCLE_ID],
        "events": [_event_to_override_dict(event) for event in events],
    }

    override_dir.mkdir(parents=True, exist_ok=True)
    path = override_dir / f"{anchor.date().isoformat()}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return events


def write_meal_done_override(
    override_dir: Path,
    schedule: Schedule,
    day: date,
    completed_meal_number: int,
    completed_at: datetime,
    min_interval_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> list[ScheduleEvent]:
    if completed_meal_number < 1:
        raise ValueError("meal number must be at least 1")

    total_meals = max([completed_meal_number] + _active_meal_numbers(schedule, day))
    remaining_meals = total_meals - completed_meal_number
    events = (
        build_min_interval_food_events(
            anchor=completed_at,
            remaining_meals=remaining_meals,
            min_interval_minutes=min_interval_minutes,
            last_meal_number=completed_meal_number,
            eating_minutes=eating_minutes,
        )
        if remaining_meals > 0
        else []
    )

    existing = _load_override(override_dir, day)
    suppress_cycles = list(dict.fromkeys([*existing.get("suppress_cycles", []), FOOD_CYCLE_ID]))
    preserved_events = [
        event
        for event in existing.get("events", [])
        if not _is_food_override_event(event)
    ]
    data = {
        "date": day.isoformat(),
        "suppress_cycles": suppress_cycles,
        "events": sorted(
            [*preserved_events, *[_event_to_override_dict(event) for event in events]],
            key=lambda event: event["time"],
        ),
    }
    if "suppress_events" in existing:
        data["suppress_events"] = existing["suppress_events"]

    override_dir.mkdir(parents=True, exist_ok=True)
    path = override_dir / f"{day.isoformat()}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return events


def build_shift_start_meal_events(
    start_at: datetime,
    meal_count: int = 4,
    min_gap_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> list[ScheduleEvent]:
    if meal_count < 1:
        raise ValueError("meal count must be at least 1")
    if min_gap_minutes < 1:
        raise ValueError("minimum meal gap must be at least 1 minute")
    if eating_minutes < 1:
        raise ValueError("eating window must be at least 1 minute")

    start_minute = start_at.replace(second=0, microsecond=0)
    step_minutes = min_gap_minutes + eating_minutes
    events: list[ScheduleEvent] = []
    for index in range(meal_count):
        meal_number = index + 1
        meal_at = start_minute + timedelta(minutes=step_minutes * index)
        events.append(
            ScheduleEvent(
                event_id=f"meal-{meal_number}",
                title=f"{meal_number} пп",
                message=f"{meal_number} прием пищи. Воду пить поверх приема и между приемами.",
                when=meal_at,
            )
        )
    return events


def build_shifted_day_override(
    schedule_data: dict,
    day: date,
    start_time: str,
    meal_count: int = 4,
    min_meal_gap_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> dict:
    start_at = datetime.combine(day, _parse_time(start_time))
    base_events = {str(event["id"]): event for event in schedule_data.get("events", [])}
    if SHIFTED_DAY_BASE_EVENT_ID not in base_events:
        raise ValueError("base schedule has no wake-up event")

    base_start = datetime.combine(day, _parse_time(str(base_events[SHIFTED_DAY_BASE_EVENT_ID]["time"])))
    replacement_events = []
    for event_id in SHIFTED_DAY_EVENT_IDS:
        if event_id not in base_events:
            continue
        event = base_events[event_id]
        original_at = datetime.combine(day, _parse_time(str(event["time"])))
        shifted_at = start_at + (original_at - base_start)
        if shifted_at.date() != day:
            continue
        replacement_events.append(
            {
                "id": event_id,
                "time": shifted_at.strftime("%H:%M"),
                "title": str(event["title"]),
                "message": str(event.get("message", event["title"])),
            }
        )

    replacement_events.extend(
        _event_to_override_dict(event)
        for event in build_shift_start_meal_events(
            start_at=start_at,
            meal_count=meal_count,
            min_gap_minutes=min_meal_gap_minutes,
            eating_minutes=eating_minutes,
        )
        if event.when.date() == day
    )

    return {
        "date": day.isoformat(),
        "suppress_cycles": [FOOD_CYCLE_ID],
        "suppress_events": SHIFTED_DAY_EVENT_IDS,
        "events": sorted(replacement_events, key=lambda event: event["time"]),
    }


def write_shifted_day_override(
    override_dir: Path,
    schedule_data: dict,
    day: date,
    start_time: str,
    meal_count: int = 4,
    min_meal_gap_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> dict:
    data = build_shifted_day_override(
        schedule_data=schedule_data,
        day=day,
        start_time=start_time,
        meal_count=meal_count,
        min_meal_gap_minutes=min_meal_gap_minutes,
        eating_minutes=eating_minutes,
    )
    override_dir.mkdir(parents=True, exist_ok=True)
    path = override_dir / f"{day.isoformat()}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def build_compressed_food_events(
    anchor: datetime,
    remaining_meals: int,
    cutoff_time: str = "20:45",
    last_meal_number: int = 1,
    water_offset_minutes: int = 15,
) -> list[ScheduleEvent]:
    if remaining_meals < 1:
        raise ValueError("remaining meals must be at least 1")
    if last_meal_number < 0:
        raise ValueError("last meal number must be 0 or greater")
    if water_offset_minutes < 1:
        raise ValueError("water offset must be at least 1 minute")

    anchor_minute = anchor.replace(second=0, microsecond=0)
    cutoff = datetime.combine(anchor.date(), _parse_time(cutoff_time))
    total_minutes = int((cutoff - anchor_minute).total_seconds() // 60)
    if total_minutes <= 0:
        raise ValueError("cutoff must be after the anchor time")

    first_meal_offset = _round_half_up(total_minutes / remaining_meals)
    if first_meal_offset <= water_offset_minutes:
        raise ValueError("window is too tight for water-before-food reminders")

    events: list[ScheduleEvent] = []
    for index in range(1, remaining_meals + 1):
        meal_number = last_meal_number + index
        meal_offset = _round_half_up(total_minutes * index / remaining_meals)
        meal_at = anchor_minute + timedelta(minutes=meal_offset)
        water_at = meal_at - timedelta(minutes=water_offset_minutes)
        events.append(
            ScheduleEvent(
                event_id=f"override-water-{meal_number}",
                title=f"{meal_number} пв",
                message=(
                    f"Сжатый день: {meal_number} прием воды. "
                    f"Через {water_offset_minutes} минут прием пищи."
                ),
                when=water_at,
            )
        )
        events.append(
            ScheduleEvent(
                event_id=f"override-meal-{meal_number}",
                title=f"{meal_number} пп",
                message=f"Сжатый день: {meal_number} прием пищи. Контейнер, быстро, без хаотичного телефона.",
                when=meal_at,
            )
        )
    return events


def write_compressed_food_override(
    override_dir: Path,
    anchor: datetime,
    remaining_meals: int,
    cutoff_time: str = "20:45",
    last_meal_number: int = 1,
) -> list[ScheduleEvent]:
    events = build_compressed_food_events(
        anchor=anchor,
        remaining_meals=remaining_meals,
        cutoff_time=cutoff_time,
        last_meal_number=last_meal_number,
    )
    data = {
        "date": anchor.date().isoformat(),
        "suppress_cycles": [FOOD_CYCLE_ID],
        "events": [_event_to_override_dict(event) for event in events],
    }

    override_dir.mkdir(parents=True, exist_ok=True)
    path = override_dir / f"{anchor.date().isoformat()}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return events


def format_recalculated_food_events(events: list[ScheduleEvent], cutoff_time: str) -> str:
    lines = [f"Сжал питание до {cutoff_time}:"]
    lines.extend(f"- {event.when:%H:%M} {event.title}" for event in events)
    return "\n".join(lines)


def format_min_interval_food_events(
    events: list[ScheduleEvent],
    min_interval_minutes: int,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> str:
    lines = [
        (
            f"Пересчитал питание: {_format_interval(min_interval_minutes)} "
            f"между концом еды и следующим приемом, окно еды {eating_minutes} мин:"
        )
    ]
    lines.extend(f"- {event.when:%H:%M} {event.title}" for event in events)
    return "\n".join(lines)


def _event_to_override_dict(event: ScheduleEvent) -> dict[str, str]:
    return {
        "id": event.event_id,
        "time": event.when.strftime("%H:%M"),
        "title": event.title,
        "message": event.message,
    }


def _active_meal_numbers(schedule: Schedule, day: date) -> list[int]:
    numbers = []
    for event in schedule.events_for_date(day):
        meal_number = _meal_number_from_event(event)
        if meal_number is not None:
            numbers.append(meal_number)
    return numbers


def _meal_number_from_event(event: ScheduleEvent) -> int | None:
    title_match = MEAL_TITLE_PATTERN.match(event.title.strip())
    if title_match:
        return int(title_match.group(1))
    id_match = re.match(r"^(?:override-)?meal-(\d+)$", event.event_id, re.IGNORECASE)
    if id_match:
        return int(id_match.group(1))
    return None


def _is_food_override_event(event: dict) -> bool:
    event_id = str(event.get("id", ""))
    title = str(event.get("title", ""))
    if FOOD_EVENT_ID_PATTERN.match(event_id):
        return True
    return bool(re.match(r"^\d+\s*п[вп]$", title.strip(), re.IGNORECASE))


def _load_override(override_dir: Path, day: date) -> dict:
    path = override_dir / f"{day.isoformat()}.json"
    if not path.exists():
        return {"date": day.isoformat(), "suppress_cycles": [], "events": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))


def _round_half_up(value: float) -> int:
    return int(value + 0.5)


def _format_interval(minutes: int) -> str:
    hours, rest = divmod(minutes, 60)
    return f"{hours}:{rest:02d}"
