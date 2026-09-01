from __future__ import annotations

import re
from datetime import datetime

from day_notifier.schedule import ScheduleEvent


MEAL_TITLE_PATTERN = re.compile(r"^\d+\s*пп$", re.IGNORECASE)
MEAL_EVENT_ID_PATTERN = re.compile(r"^(?:override-)?meal-\d+$", re.IGNORECASE)


def format_event_line(event: ScheduleEvent, reference: datetime, include_date: bool = False) -> str:
    timestamp = event.when.strftime("%Y-%m-%d %H:%M" if include_date else "%H:%M")
    return f"- {timestamp} {event.title}{_countdown_suffix(event, reference)}"


def format_notification_text(
    event: ScheduleEvent,
    reference: datetime,
    include_current_time: bool = False,
) -> str:
    lines: list[str] = []
    if include_current_time:
        lines.append(f"Сейчас: {reference:%H:%M}")
    lines.append(f"{event.when:%H:%M} - {event.title}{_countdown_suffix(event, reference)}")
    lines.append(event.message)
    return "\n".join(lines)


def _countdown_suffix(event: ScheduleEvent, reference: datetime) -> str:
    label = _countdown_label(event)
    if label is None:
        return ""
    return f" ({_format_countdown(label, event.when, reference)})"


def _countdown_label(event: ScheduleEvent) -> str | None:
    event_id = event.event_id.lower()
    title = event.title.strip().lower()
    if MEAL_TITLE_PATTERN.match(event.title.strip()) or MEAL_EVENT_ID_PATTERN.match(event_id):
        return "до приема пищи"
    if event_id == "bedtime" or title == "отбой":
        return "до сна"
    if event_id == "batch-cooking" or title.startswith("batch-cooking"):
        return "до batch-cooking"
    return None


def _format_countdown(label: str, target: datetime, reference: datetime) -> str:
    seconds = int((target - reference).total_seconds())
    if -59 <= seconds <= 59:
        return f"{label}: сейчас"
    if seconds > 0:
        return f"{label}: {_format_duration(seconds)}"
    return f"опоздание: {_format_duration(-seconds)}"


def _format_duration(seconds: int) -> str:
    minutes = max(1, (seconds + 59) // 60)
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} ч {rest} мин"
    if hours:
        return f"{hours} ч"
    return f"{rest} мин"
