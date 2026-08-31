from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from pathlib import Path

from day_notifier.schedule import ScheduleEvent


FOOD_CYCLE_ID = "water-food-cycle"


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


def _event_to_override_dict(event: ScheduleEvent) -> dict[str, str]:
    return {
        "id": event.event_id,
        "time": event.when.strftime("%H:%M"),
        "title": event.title,
        "message": event.message,
    }


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))


def _round_half_up(value: float) -> int:
    return int(value + 0.5)
