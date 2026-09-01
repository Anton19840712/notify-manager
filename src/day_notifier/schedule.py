from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

MEAL_TITLE_PATTERN = re.compile(r"^\d+\s*пп$", re.IGNORECASE)
MEAL_EVENT_ID_PATTERN = re.compile(r"^(?:override-)?meal-\d+$", re.IGNORECASE)
PRE_MEAL_OFFSET_MINUTES = 10


@dataclass(frozen=True)
class ScheduleEvent:
    event_id: str
    title: str
    message: str
    when: datetime

    @property
    def key(self) -> str:
        return f"{self.event_id}@{self.when.isoformat(timespec='minutes')}"


class Schedule:
    def __init__(
        self,
        events: list[dict[str, Any]] | None = None,
        cycles: list[dict[str, Any]] | None = None,
        relative_cycles: list[dict[str, Any]] | None = None,
        rotating_events: list[dict[str, Any]] | None = None,
        day_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._events = events or []
        self._cycles = cycles or []
        self._relative_cycles = relative_cycles or []
        self._rotating_events = rotating_events or []
        self._day_overrides = day_overrides or {}

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        day_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> "Schedule":
        return cls(
            events=list(data.get("events", [])),
            cycles=list(data.get("cycles", [])),
            relative_cycles=list(data.get("relative_cycles", [])),
            rotating_events=list(data.get("rotating_events", [])),
            day_overrides=day_overrides,
        )

    def events_for_date(self, day: date) -> list[ScheduleEvent]:
        expanded: list[ScheduleEvent] = []
        override = self._day_overrides.get(day.isoformat(), {})
        suppressed_cycles = set(str(cycle_id) for cycle_id in override.get("suppress_cycles", []))
        suppressed_events = set(str(event_id) for event_id in override.get("suppress_events", []))

        for event in self._events:
            event_id = str(event["id"])
            if event_id in suppressed_events:
                continue
            expanded.append(
                ScheduleEvent(
                    event_id=event_id,
                    title=str(event["title"]),
                    message=str(event.get("message", event["title"])),
                    when=datetime.combine(day, _parse_time(str(event["time"]))),
                )
            )

        for cycle in self._cycles:
            if str(cycle.get("id", "")) in suppressed_cycles:
                continue
            start = datetime.combine(day, _parse_time(str(cycle["start_time"])))
            period = timedelta(minutes=int(cycle["period_minutes"]))
            count = int(cycle["count"])
            for cycle_index in range(1, count + 1):
                cycle_start = start + period * (cycle_index - 1)
                for item in cycle.get("items", []):
                    when = cycle_start + timedelta(minutes=int(item.get("offset_minutes", 0)))
                    expanded.append(
                        ScheduleEvent(
                            event_id=str(item["id_template"]).format(n=cycle_index),
                            title=str(item["title_template"]).format(n=cycle_index),
                            message=str(item.get("message_template", item["title_template"])).format(
                                n=cycle_index
                            ),
                            when=when,
                        )
                    )

        for event in override.get("events", []):
            expanded.append(
                ScheduleEvent(
                    event_id=str(event["id"]),
                    title=str(event["title"]),
                    message=str(event.get("message", event["title"])),
                    when=datetime.combine(day, _parse_time(str(event["time"]))),
                )
            )

        expanded.extend(self._expand_rotating_events(day, override))
        expanded.extend(self._expand_relative_cycles(day, expanded, override))
        expanded.extend(self._expand_pre_meal_events(day, expanded, override))
        return sorted(expanded, key=lambda event: event.when)

    def _expand_pre_meal_events(
        self,
        day: date,
        events: list[ScheduleEvent],
        override: dict[str, Any],
    ) -> list[ScheduleEvent]:
        suppressed_events = set(str(event_id) for event_id in override.get("suppress_events", []))
        existing_event_ids = {event.event_id for event in events}
        expanded: list[ScheduleEvent] = []
        for meal in events:
            if not _is_meal_event(meal):
                continue
            event_id = f"pre-{meal.event_id}"
            when = meal.when - timedelta(minutes=PRE_MEAL_OFFSET_MINUTES)
            if event_id in suppressed_events or event_id in existing_event_ids or when.date() != day:
                continue
            expanded.append(
                ScheduleEvent(
                    event_id=event_id,
                    title=f"{PRE_MEAL_OFFSET_MINUTES} минут до {meal.title}",
                    message=(
                        f"Через {PRE_MEAL_OFFSET_MINUTES} минут {meal.title}. "
                        "Не начинай сложные задачи; закрой текущий микрошаг."
                    ),
                    when=when,
                )
            )
        return expanded

    def _expand_rotating_events(
        self,
        day: date,
        override: dict[str, Any],
    ) -> list[ScheduleEvent]:
        suppressed_events = set(str(event_id) for event_id in override.get("suppress_events", []))
        suppressed_rotations = set(str(rotation_id) for rotation_id in override.get("suppress_rotations", []))
        expanded: list[ScheduleEvent] = []
        for rotation in self._rotating_events:
            rotation_id = str(rotation.get("id", ""))
            if rotation_id in suppressed_rotations:
                continue

            start_day = date.fromisoformat(str(rotation["start_date"]))
            delta_days = (day - start_day).days
            if delta_days < 0:
                continue

            period_days = int(rotation.get("period_days", 1))
            if period_days < 1:
                raise ValueError("rotating event period_days must be at least 1")

            current_offset = delta_days % period_days
            for item in rotation.get("items", []):
                if int(item.get("offset_days", 0)) != current_offset:
                    continue
                event_id = str(item["id"])
                if event_id in suppressed_events:
                    continue
                expanded.append(
                    ScheduleEvent(
                        event_id=event_id,
                        title=str(item["title"]),
                        message=str(item.get("message", item["title"])),
                        when=datetime.combine(day, _parse_time(str(item.get("time", rotation["time"])))),
                    )
                )
        return expanded

    def _expand_relative_cycles(
        self,
        day: date,
        events: list[ScheduleEvent],
        override: dict[str, Any],
    ) -> list[ScheduleEvent]:
        suppressed_cycles = set(str(cycle_id) for cycle_id in override.get("suppress_relative_cycles", []))
        expanded: list[ScheduleEvent] = []
        for cycle in self._relative_cycles:
            cycle_id = str(cycle.get("id", ""))
            if cycle_id in suppressed_cycles:
                continue
            if str(cycle.get("kind", "")) != "after_last_meal":
                continue
            if not _is_cycle_day(day, cycle):
                continue
            last_meal = _last_meal_event(events)
            if last_meal is None:
                continue
            anchor = last_meal.when + timedelta(minutes=int(cycle.get("anchor_offset_minutes", 0)))
            for item in cycle.get("items", []):
                when = anchor + timedelta(minutes=int(item.get("offset_minutes", 0)))
                if when.date() != day:
                    continue
                expanded.append(
                    ScheduleEvent(
                        event_id=str(item["id"]),
                        title=str(item["title"]),
                        message=str(item.get("message", item["title"])),
                        when=when,
                    )
                )
        return expanded

    def next_event(self, reference: datetime) -> ScheduleEvent:
        today_events = [event for event in self.events_for_date(reference.date()) if event.when > reference]
        if today_events:
            return today_events[0]

        tomorrow = reference.date() + timedelta(days=1)
        return self.events_for_date(tomorrow)[0]

    def remaining_today(self, reference: datetime, limit: int | None = None) -> list[ScheduleEvent]:
        events = [event for event in self.events_for_date(reference.date()) if event.when > reference]
        if limit is None:
            return events
        return events[:limit]

    def upcoming(self, reference: datetime, limit: int = 5) -> list[ScheduleEvent]:
        events = [event for event in self.events_for_date(reference.date()) if event.when > reference]
        if len(events) < limit:
            events.extend(self.events_for_date(reference.date() + timedelta(days=1)))
        return events[:limit]


def load_schedule(path: Path, override_dir: Path | None = None) -> Schedule:
    day_overrides = load_day_overrides(override_dir) if override_dir is not None else {}
    return Schedule.from_dict(json.loads(path.read_text(encoding="utf-8")), day_overrides=day_overrides)


def load_day_overrides(override_dir: Path) -> dict[str, dict[str, Any]]:
    if not override_dir.exists():
        return {}

    overrides: dict[str, dict[str, Any]] = {}
    for path in sorted(override_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        day_key = str(data.get("date") or path.stem)
        overrides[day_key] = data
    return overrides


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))


def _is_cycle_day(day: date, cycle: dict[str, Any]) -> bool:
    start_day = date.fromisoformat(str(cycle["start_date"]))
    period_days = int(cycle.get("period_days", 1))
    if period_days < 1:
        raise ValueError("relative cycle period_days must be at least 1")
    delta_days = (day - start_day).days
    return delta_days >= 0 and delta_days % period_days == 0


def _last_meal_event(events: list[ScheduleEvent]) -> ScheduleEvent | None:
    meals = [event for event in events if _is_meal_event(event)]
    return max(meals, key=lambda event: event.when) if meals else None


def _is_meal_event(event: ScheduleEvent) -> bool:
    return bool(MEAL_TITLE_PATTERN.match(event.title.strip()) or MEAL_EVENT_ID_PATTERN.match(event.event_id))
