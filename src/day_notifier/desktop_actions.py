from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from day_notifier.schedule import ScheduleEvent


VALID_ACTIONS = {"done", "snooze_10", "skip"}


@dataclass(frozen=True)
class DesktopAction:
    action_id: str
    action: str
    event_id: str
    title: str
    message: str
    when: datetime

    @classmethod
    def from_event(
        cls,
        action: str,
        event: ScheduleEvent,
        action_id: str | None = None,
    ) -> "DesktopAction":
        return cls(
            action_id=action_id or uuid.uuid4().hex,
            action=action,
            event_id=event.event_id,
            title=event.title,
            message=event.message,
            when=event.when,
        )

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "DesktopAction":
        action = str(payload["action"])
        if action not in VALID_ACTIONS:
            raise ValueError(f"Unsupported desktop action: {action}")
        return cls(
            action_id=str(payload.get("action_id") or uuid.uuid4().hex),
            action=action,
            event_id=str(payload["event_id"]),
            title=str(payload["title"]),
            message=str(payload.get("message", "")),
            when=datetime.fromisoformat(str(payload["when"])),
        )

    def to_payload(self) -> dict[str, str]:
        if self.action not in VALID_ACTIONS:
            raise ValueError(f"Unsupported desktop action: {self.action}")
        return {
            "action_id": self.action_id,
            "action": self.action,
            "event_id": self.event_id,
            "title": self.title,
            "message": self.message,
            "when": self.when.isoformat(timespec="seconds"),
        }

    def to_event(self) -> ScheduleEvent:
        return ScheduleEvent(
            event_id=self.event_id,
            title=self.title,
            message=self.message,
            when=self.when,
        )


def append_desktop_action(path: Path, action: DesktopAction) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(action.to_payload(), ensure_ascii=False) + "\n")


def consume_desktop_actions(path: Path) -> list[DesktopAction]:
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    path.write_text("", encoding="utf-8")
    actions: list[DesktopAction] = []
    seen_action_ids: set[str] = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            action = DesktopAction.from_payload(json.loads(line))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        if action.action_id in seen_action_ids:
            continue
        seen_action_ids.add(action.action_id)
        actions.append(action)
    return actions
