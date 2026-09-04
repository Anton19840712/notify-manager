from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from day_notifier.event_formatting import format_notification_text
from day_notifier.schedule import ScheduleEvent


MEAL_TITLE_PATTERN = re.compile(r"^\d+\s*пп$", re.IGNORECASE)
MEAL_EVENT_ID_PATTERN = re.compile(r"^(?:override-)?meal-\d+$", re.IGNORECASE)
PRE_MEAL_EVENT_ID_PATTERN = re.compile(r"^pre-(?:override-)?meal-\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class NotificationAction:
    action: str
    label: str

    def to_payload(self) -> dict[str, str]:
        return {"action": self.action, "label": self.label}


@dataclass(frozen=True)
class NotificationViewModel:
    event_id: str
    event_key: str
    title: str
    message: str
    body: str
    when: datetime
    status: str
    importance: str
    actions: tuple[NotificationAction, ...]

    def to_payload(self, action_queue_path: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": self.title,
            "body": self.body,
            "status": self.status,
            "importance": self.importance,
            "actions": [action.to_payload() for action in self.actions],
            "event": {
                "event_id": self.event_id,
                "event_key": self.event_key,
                "title": self.title,
                "message": self.message,
                "when": self.when.isoformat(timespec="seconds"),
            },
        }
        if action_queue_path:
            payload["action_queue_path"] = action_queue_path
        return payload


def build_notification_view(event: ScheduleEvent, reference: datetime) -> NotificationViewModel:
    return NotificationViewModel(
        event_id=event.event_id,
        event_key=event.key,
        title=event.title,
        message=event.message,
        body=format_notification_text(event, reference, include_current_time=True),
        when=event.when,
        status=_status(event, reference),
        importance=_importance(event),
        actions=_actions_for_event(event),
    )


def _status(event: ScheduleEvent, reference: datetime) -> str:
    label = _countdown_label(event)
    seconds = int((event.when - reference).total_seconds())
    if seconds > 0:
        return f"{label}: {_format_duration(seconds)}" if label else f"через: {_format_duration(seconds)}"
    if seconds >= -59:
        return f"{label}: сейчас" if label else "сейчас"
    return f"опоздание: {_format_duration(abs(seconds))}"


def _countdown_label(event: ScheduleEvent) -> str | None:
    event_id = event.event_id.lower()
    title = event.title.strip().lower()
    if _is_meal_event(event):
        return "до приема пищи"
    if event_id == "bedtime" or title == "отбой":
        return "до сна"
    if event_id == "batch-cooking" or title.startswith("batch-cooking"):
        return "до batch-cooking"
    return None


def _importance(event: ScheduleEvent) -> str:
    event_id = event.event_id.lower()
    title = event.title.strip().lower()
    if event_id in {"wake-up", "bedtime"} or title in {"подъем", "отбой"} or _is_meal_event(event):
        return "critical"
    if event_id.startswith("full-body-circuit") or event_id == "batch-cooking" or "круговая" in title:
        return "anchor"
    if PRE_MEAL_EVENT_ID_PATTERN.match(event_id):
        return "soft"
    return "normal"


def _actions_for_event(event: ScheduleEvent) -> tuple[NotificationAction, ...]:
    if PRE_MEAL_EVENT_ID_PATTERN.match(event.event_id.lower()):
        return ()
    return (
        NotificationAction("done", "Готово"),
        NotificationAction("snooze_10", "+10"),
        NotificationAction("skip", "Пропустить"),
    )


def _is_meal_event(event: ScheduleEvent) -> bool:
    return bool(MEAL_TITLE_PATTERN.match(event.title.strip()) or MEAL_EVENT_ID_PATTERN.match(event.event_id))


def _format_duration(seconds: int) -> str:
    minutes = max(1, (seconds + 59) // 60)
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} ч {rest} мин"
    if hours:
        return f"{hours} ч"
    return f"{rest} мин"
