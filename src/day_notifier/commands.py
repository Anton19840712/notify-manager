from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol

from day_notifier.inbox import append_inbox_item, read_inbox_items
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


@dataclass(frozen=True)
class CommandResult:
    reply: str


def handle_command(text: str, context: CommandContext) -> CommandResult:
    command, _, argument = text.strip().partition(" ")
    command = command.lower()

    if command == "/next":
        event = context.schedule.next_event(context.now())
        return CommandResult(reply=_format_event("Следующее", event))

    if command == "/summary":
        return CommandResult(reply=_summary(context))

    if command == "/today":
        return CommandResult(reply=_today(context))

    if command == "/desktop":
        return CommandResult(reply=_desktop(argument, context))

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
        reply="Команды: /summary, /today, /next, /done, /snooze 10, /desktop on|off|status, /inbox текст"
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


def _format_event(prefix: str, event: ScheduleEvent) -> str:
    return f"{prefix}: {event.when:%H:%M} - {event.title}"


def _parse_snooze_minutes(argument: str) -> int:
    value = argument.strip() or "10"
    minutes = int(value)
    if minutes < 1 or minutes > 240:
        raise ValueError("Snooze must be between 1 and 240 minutes.")
    return minutes
