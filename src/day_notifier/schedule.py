from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any


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
    ) -> None:
        self._events = events or []
        self._cycles = cycles or []

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        return cls(events=list(data.get("events", [])), cycles=list(data.get("cycles", [])))

    def events_for_date(self, day: date) -> list[ScheduleEvent]:
        expanded: list[ScheduleEvent] = []

        for event in self._events:
            expanded.append(
                ScheduleEvent(
                    event_id=str(event["id"]),
                    title=str(event["title"]),
                    message=str(event.get("message", event["title"])),
                    when=datetime.combine(day, _parse_time(str(event["time"]))),
                )
            )

        for cycle in self._cycles:
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

        return sorted(expanded, key=lambda event: event.when)

    def next_event(self, reference: datetime) -> ScheduleEvent:
        today_events = [event for event in self.events_for_date(reference.date()) if event.when > reference]
        if today_events:
            return today_events[0]

        tomorrow = reference.date() + timedelta(days=1)
        return self.events_for_date(tomorrow)[0]

    def upcoming(self, reference: datetime, limit: int = 5) -> list[ScheduleEvent]:
        events = [event for event in self.events_for_date(reference.date()) if event.when > reference]
        if len(events) < limit:
            events.extend(self.events_for_date(reference.date() + timedelta(days=1)))
        return events[:limit]


def load_schedule(path: Path) -> Schedule:
    return Schedule.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))

