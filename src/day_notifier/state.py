from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from day_notifier.schedule import ScheduleEvent


TELEGRAM_MESSAGE_LIMIT = 500


class JsonStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data = self._load()

    @property
    def last_event(self) -> ScheduleEvent | None:
        raw = self._data.get("last_event")
        return _event_from_dict(raw) if raw else None

    @property
    def telegram_offset(self) -> int | None:
        value = self._data.get("telegram_offset")
        return int(value) if value is not None else None

    @property
    def telegram_messages(self) -> list[dict[str, Any]]:
        return list(self._data.get("telegram_messages", []))

    def telegram_message_ids(self) -> list[int]:
        ids = []
        for item in self._data.get("telegram_messages", []):
            message_id = item.get("message_id")
            if message_id is not None:
                ids.append(int(message_id))
        return ids

    def set_telegram_offset(self, value: int) -> None:
        self._data["telegram_offset"] = int(value)
        self._save()

    def has_seen(self, event: ScheduleEvent) -> bool:
        return event.key in self._data.setdefault("seen", {})

    def mark_notified(self, event: ScheduleEvent) -> None:
        self._mark_seen(event, "notified")
        self._data["last_event"] = _event_to_dict(event)
        self._save()

    def mark_skipped(self, event: ScheduleEvent) -> None:
        self._mark_seen(event, "skipped")
        self._save()

    def mark_done(self, event: ScheduleEvent, when: datetime) -> None:
        self._data.setdefault("done", []).append(
            {"event_key": event.key, "event_id": event.event_id, "at": when.isoformat(timespec="seconds")}
        )
        self._save()

    def add_snooze(self, event: ScheduleEvent, minutes: int) -> ScheduleEvent:
        snoozed = ScheduleEvent(
            event_id=f"{event.event_id}-snooze",
            title=f"{event.title} +{minutes} мин",
            message=event.message,
            when=event.when + timedelta(minutes=minutes),
        )
        self._data.setdefault("snoozed", []).append(_event_to_dict(snoozed))
        self._save()
        return snoozed

    def due_snoozes(self, now: datetime) -> list[ScheduleEvent]:
        events = [_event_from_dict(item) for item in self._data.get("snoozed", [])]
        return [event for event in events if event.when <= now and not self.has_seen(event)]

    def track_telegram_message(self, message_id: int | None, direction: str, when: datetime | None = None) -> None:
        if message_id is None:
            return
        if direction not in {"incoming", "outgoing"}:
            raise ValueError("direction must be incoming or outgoing")
        item = {
            "message_id": int(message_id),
            "direction": direction,
            "at": (when or datetime.now()).isoformat(timespec="seconds"),
        }
        messages = self._data.setdefault("telegram_messages", [])
        messages.append(item)
        del messages[:-TELEGRAM_MESSAGE_LIMIT]
        self._save()

    def clear_telegram_messages(self) -> None:
        self._data["telegram_messages"] = []
        self._save()

    def _mark_seen(self, event: ScheduleEvent, status: str) -> None:
        self._data.setdefault("seen", {})[event.key] = {
            "event_id": event.event_id,
            "status": status,
            "at": datetime.now().isoformat(timespec="seconds"),
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"seen": {}, "done": [], "snoozed": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _event_to_dict(event: ScheduleEvent) -> dict[str, str]:
    return {
        "event_id": event.event_id,
        "title": event.title,
        "message": event.message,
        "when": event.when.isoformat(timespec="seconds"),
    }


def _event_from_dict(data: dict[str, Any]) -> ScheduleEvent:
    return ScheduleEvent(
        event_id=str(data["event_id"]),
        title=str(data["title"]),
        message=str(data["message"]),
        when=datetime.fromisoformat(str(data["when"])),
    )
