from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol

from day_notifier.inbox import append_inbox_item, read_inbox_items
from day_notifier.overrides import (
    format_min_interval_food_events,
    write_min_interval_food_override,
    write_shifted_day_override,
)
from day_notifier.schedule import Schedule, ScheduleEvent


class RuntimeState(Protocol):
    last_event: ScheduleEvent | None

    def add_snooze(self, event: ScheduleEvent, minutes: int) -> ScheduleEvent:
        ...

    def mark_done(self, event: ScheduleEvent, when: datetime) -> None:
        ...


@dataclass
class CommandContext:
    schedule: Schedule
    state: RuntimeState
    inbox_path: Path
    now: Callable[[], datetime]
    set_desktop_enabled: Callable[[bool], None] | None = None
    is_desktop_enabled: Callable[[], bool] | None = None
    override_dir: Path | None = None
    reload_schedule: Callable[[], None] | None = None
    schedule_path: Path | None = None
    cleanup_telegram_chat: Callable[[], str] | None = None


@dataclass(frozen=True)
class CommandResult:
    reply: str


def handle_command(text: str, context: CommandContext) -> CommandResult:
    command, _, argument = text.strip().partition(" ")
    command = command.lower()

    if command in {"/отбой", "отбой"}:
        if context.cleanup_telegram_chat is None:
            return CommandResult(reply="Очистка Telegram-чата недоступна в этом режиме.")
        return CommandResult(reply=context.cleanup_telegram_chat())

    if command == "/next":
        event = context.schedule.next_event(context.now())
        return CommandResult(reply=_format_event("Следующее", event))

    if command == "/summary":
        return CommandResult(reply=_summary(context))

    if command == "/today":
        return CommandResult(reply=_today(context))

    if command == "/desktop":
        return CommandResult(reply=_desktop(argument, context))

    if command == "/recalc":
        return CommandResult(reply=_recalc(argument, context))

    if command == "/shift":
        return CommandResult(reply=_shift(argument, context))

    if command == "/inbox":
        if not argument.strip():
            return CommandResult(reply="Напиши текст после /inbox.")
        append_inbox_item(context.inbox_path, argument, context.now())
        return CommandResult(reply=f"Добавил в inbox: {argument.strip()}")

    if command == "/snooze":
        minutes = _parse_snooze_minutes(argument)
        event = context.state.last_event or context.schedule.next_event(context.now())
        snoozed = context.state.add_snooze(event, minutes)
        return CommandResult(reply=_format_event(f"Отложил на {minutes} мин", snoozed))

    if command == "/done":
        event = context.state.last_event
        if event is None:
            return CommandResult(reply="Пока нет последнего события для отметки.")
        context.state.mark_done(event, context.now())
        return CommandResult(reply=f"Готово: {event.title}")

    return CommandResult(
        reply=(
            "Команды: /summary, /today, /next, /done, /snooze 10, "
            "/recalc food 4, /shift day 10:00, /отбой, /desktop on|off|status, /inbox текст"
        )
    )


def _summary(context: CommandContext) -> str:
    upcoming = context.schedule.upcoming(context.now(), limit=5)
    lines = ["Ближайшее:"]
    lines.extend(f"- {event.when:%H:%M} {event.title}" for event in upcoming)

    inbox_items = read_inbox_items(context.inbox_path, limit=5)
    if inbox_items:
        lines.append("")
        lines.append("Inbox:")
        lines.extend(inbox_items)

    return "\n".join(lines)


def _today(context: CommandContext) -> str:
    events = context.schedule.remaining_today(context.now(), limit=10)
    if not events:
        return "Сегодня больше нет событий."
    lines = ["Сегодня:"]
    lines.extend(f"- {event.when:%H:%M} {event.title}" for event in events)
    return "\n".join(lines)


def _desktop(argument: str, context: CommandContext) -> str:
    value = argument.strip().lower()
    if value in {"on", "вкл", "включить"}:
        if context.set_desktop_enabled is None:
            return "Desktop-канал недоступен в этом режиме."
        context.set_desktop_enabled(True)
        return "Desktop-уведомления включены."
    if value in {"off", "выкл", "выключить"}:
        if context.set_desktop_enabled is None:
            return "Desktop-канал недоступен в этом режиме."
        context.set_desktop_enabled(False)
        return "Desktop-уведомления выключены."
    if value in {"status", "статус", ""}:
        if context.is_desktop_enabled is None:
            return "Desktop-канал недоступен в этом режиме."
        state = "включены" if context.is_desktop_enabled() else "выключены"
        return f"Desktop-уведомления сейчас {state}."
    return "Используй: /desktop on, /desktop off или /desktop status."


def _recalc(argument: str, context: CommandContext) -> str:
    parts = argument.strip().split()
    if len(parts) < 2 or parts[0].lower() not in {"food", "meal", "meals", "еда", "питание"}:
        return "Используй: /recalc food 4 или /recalc food 4 2:15."
    if context.override_dir is None:
        return "Пересчет дня недоступен в этом режиме."

    try:
        remaining_meals = int(parts[1])
        min_interval_minutes = _parse_interval_minutes(parts[2]) if len(parts) >= 3 else 135
        last_meal_number = int(parts[3]) if len(parts) >= 4 else 1
        events = write_min_interval_food_override(
            override_dir=context.override_dir,
            anchor=context.now(),
            remaining_meals=remaining_meals,
            min_interval_minutes=min_interval_minutes,
            last_meal_number=last_meal_number,
        )
    except ValueError as exc:
        return f"Не смог пересчитать день: {exc}"

    if context.reload_schedule is not None:
        context.reload_schedule()
    return format_min_interval_food_events(events, min_interval_minutes)


def _shift(argument: str, context: CommandContext) -> str:
    parts = argument.strip().split()
    if len(parts) != 2 or parts[0].lower() not in {"day", "день"} or not _looks_like_time(parts[1]):
        return "Используй: /shift day 10:00."
    if context.override_dir is None or context.schedule_path is None:
        return "Перенос дня недоступен в этом режиме."

    try:
        schedule_data = json.loads(context.schedule_path.read_text(encoding="utf-8"))
        data = write_shifted_day_override(
            override_dir=context.override_dir,
            schedule_data=schedule_data,
            day=context.now().date(),
            start_time=parts[1],
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return f"Не смог перенести день: {exc}"

    if context.reload_schedule is not None:
        context.reload_schedule()
    return _format_shifted_day_result(parts[1], data)


def _format_event(prefix: str, event: ScheduleEvent) -> str:
    return f"{prefix}: {event.when:%H:%M} - {event.title}"


def _parse_snooze_minutes(argument: str) -> int:
    value = argument.strip() or "10"
    minutes = int(value)
    if minutes < 1 or minutes > 240:
        raise ValueError("Snooze must be between 1 and 240 minutes.")
    return minutes


def _parse_interval_minutes(value: str) -> int:
    if ":" not in value:
        return int(value)
    hours, minutes = value.split(":", 1)
    return int(hours) * 60 + int(minutes)


def _looks_like_time(value: str) -> bool:
    parts = value.split(":", 1)
    if len(parts) != 2:
        return False
    hour, minute = parts
    if not hour.isdigit() or not minute.isdigit():
        return False
    return 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59


def _format_shifted_day_result(start_time: str, data: dict) -> str:
    lines = [f"Перенес день на {start_time}.", "Сегодня:"]
    for event in data.get("events", []):
        lines.append(f"- {event['time']} {event['title']}")
    return "\n".join(lines)
