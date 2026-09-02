from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol

from day_notifier.bot_commands import format_bot_commands_help
from day_notifier.event_formatting import format_event_line
from day_notifier.inbox import append_inbox_item, read_inbox_items
from day_notifier.overrides import (
    format_min_interval_food_events,
    write_meal_done_override,
    write_min_interval_food_override,
    write_shifted_day_override,
)
from day_notifier.schedule import Schedule, ScheduleEvent


MEAL_DONE_USAGE = "Используй: /2 mi done, 2 mi done, 2 pp done, 2 пп done или /mi 2 done."
MEAL_DONE_PATTERNS = [
    re.compile(r"^/?\s*(\d+)\s+(?:mi|pp|пп)\s+done$", re.IGNORECASE),
    re.compile(r"^/mi\s+(\d+)\s+done$", re.IGNORECASE),
]
QUICK_MEAL_DONE_PATTERN = re.compile(r"^/?mi(\d+)$", re.IGNORECASE)
DEFAULT_BLOCK_ID = "chrysostom-prayers"
DESKTOP_COMMAND_ALIASES = {
    "/desktop_on": "on",
    "desktop_on": "on",
    "/desktop_off": "off",
    "desktop_off": "off",
    "/desktop_status": "status",
    "desktop_status": "status",
}
BLOCK_COMMAND_ALIASES: dict[str, tuple[str | None, bool | None]] = {
    "/blocks": (None, None),
    "blocks": (None, None),
    "/selfdev_on": ("self-development", True),
    "selfdev_on": ("self-development", True),
    "/selfdev_off": ("self-development", False),
    "selfdev_off": ("self-development", False),
    "/training_on": ("training", True),
    "training_on": ("training", True),
    "/training_off": ("training", False),
    "training_off": ("training", False),
    "/prayers_on": ("prayers", True),
    "prayers_on": ("prayers", True),
    "/prayers_off": ("prayers", False),
    "prayers_off": ("prayers", False),
    "/chrysostom_on": ("chrysostom-prayers", True),
    "chrysostom_on": ("chrysostom-prayers", True),
    "/chrysostom_off": ("chrysostom-prayers", False),
    "chrysostom_off": ("chrysostom-prayers", False),
}


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
    set_block_enabled: Callable[[str, bool], str] | None = None
    block_status: Callable[[str | None], str] | None = None
    override_dir: Path | None = None
    reload_schedule: Callable[[], None] | None = None
    schedule_path: Path | None = None
    cleanup_telegram_chat: Callable[[], str] | None = None
    request_shutdown: Callable[[], None] | None = None
    processes_today: Callable[[], str] | None = None


@dataclass(frozen=True)
class CommandResult:
    reply: str


def handle_command(text: str, context: CommandContext) -> CommandResult:
    stripped = text.strip()
    block_action = _parse_plain_block_command(stripped)
    if block_action is not None:
        enabled, block_id = block_action
        if enabled is None:
            return CommandResult(reply=_block_status(block_id or None, context))
        return CommandResult(reply=_set_block_enabled(block_id, enabled, context))

    meal_done_number = _parse_meal_done_number(stripped)
    if meal_done_number is not None:
        return CommandResult(reply=_meal_done(meal_done_number, context))
    quick_meal_done_number = _parse_quick_meal_done_number(stripped)
    if quick_meal_done_number is not None:
        return CommandResult(reply=_meal_done(quick_meal_done_number, context))

    command, _, argument = stripped.partition(" ")
    command = command.lower()

    if command in {"/help", "help"}:
        return CommandResult(reply=format_bot_commands_help())

    if command in {"/отбой", "отбой", "/otboy", "otboy"}:
        if context.cleanup_telegram_chat is None:
            return CommandResult(reply="Очистка Telegram-чата недоступна в этом режиме.")
        return CommandResult(reply=context.cleanup_telegram_chat())

    if command in {"/stop_bot", "stop_bot"}:
        if context.request_shutdown is None:
            return CommandResult(reply="Остановка notify-manager недоступна в этом режиме.")
        context.request_shutdown()
        return CommandResult(reply="Останавливаю notify-manager. Запусти снова через AHK или PowerShell.")

    if command == "/next":
        event = context.schedule.next_event(context.now(), include_pre_meal=False)
        return CommandResult(reply=_format_event("Следующее", event, context.now()))

    if command == "/summary":
        return CommandResult(reply=_summary(context))

    if command == "/today":
        return CommandResult(reply=_today(context))

    if command in {"/processes", "processes"}:
        return CommandResult(reply=_processes(context))

    if command == "/desktop":
        return CommandResult(reply=_desktop(argument, context))

    if command in DESKTOP_COMMAND_ALIASES:
        return CommandResult(reply=_desktop(DESKTOP_COMMAND_ALIASES[command], context))

    if command in BLOCK_COMMAND_ALIASES:
        block_id, enabled = BLOCK_COMMAND_ALIASES[command]
        if enabled is None:
            return CommandResult(reply=_block_status(None, context))
        return CommandResult(reply=_set_block_enabled(block_id or "", enabled, context))

    if command in {"/block_on", "block_on"}:
        return CommandResult(reply=_set_block_enabled(argument, True, context))

    if command in {"/block_off", "block_off"}:
        return CommandResult(reply=_set_block_enabled(argument, False, context))

    if command in {"/block_status", "block_status"}:
        return CommandResult(reply=_block_status(argument.strip() or None, context))

    if command in {"/block", "block"}:
        return CommandResult(reply=_block(argument, context))

    if command == "/recalc":
        return CommandResult(reply=_recalc(argument, context))

    if command in {"/sd", "sd"}:
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
        return CommandResult(reply=_format_event(f"Отложил на {minutes} мин", snoozed, context.now()))

    if command == "/done":
        event = context.state.last_event
        if event is None:
            return CommandResult(reply="Пока нет последнего события для отметки.")
        context.state.mark_done(event, context.now())
        return CommandResult(reply=f"Готово: {event.title}")

    return CommandResult(reply=format_bot_commands_help())


def _summary(context: CommandContext) -> str:
    current = context.now()
    upcoming = context.schedule.upcoming(current, limit=5, include_pre_meal=False)
    lines = ["Ближайшее:"]
    lines.extend(format_event_line(event, current) for event in upcoming)

    inbox_items = read_inbox_items(context.inbox_path, limit=5)
    if inbox_items:
        lines.append("")
        lines.append("Inbox:")
        lines.extend(inbox_items)

    processes = _processes_or_empty(context)
    if processes:
        lines.append("")
        lines.append(processes)

    return "\n".join(lines)


def _today(context: CommandContext) -> str:
    current = context.now()
    events = context.schedule.remaining_today(current, limit=10, include_pre_meal=False)
    if not events:
        processes = _processes_or_empty(context)
        return processes or "Сегодня больше нет событий."
    lines = ["Сегодня:"]
    lines.extend(format_event_line(event, current) for event in events)
    processes = _processes_or_empty(context)
    if processes:
        lines.append("")
        lines.append(processes)
    return "\n".join(lines)


def _processes(context: CommandContext) -> str:
    processes = _processes_or_empty(context)
    return processes or "На сегодня внеплановых процессов нет."


def _processes_or_empty(context: CommandContext) -> str:
    if context.processes_today is None:
        return ""
    return context.processes_today().strip()


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


def _set_block_enabled(argument: str, enabled: bool, context: CommandContext) -> str:
    if context.set_block_enabled is None:
        return "Подключаемые блоки недоступны в этом режиме."
    block_id = argument.strip() or DEFAULT_BLOCK_ID
    return context.set_block_enabled(block_id, enabled)


def _block_status(block_id: str | None, context: CommandContext) -> str:
    if context.block_status is None:
        return "Статус блоков недоступен в этом режиме."
    return context.block_status(block_id)


def _block(argument: str, context: CommandContext) -> str:
    parts = argument.strip().split(maxsplit=1)
    if not parts:
        return _block_status(None, context)

    action = parts[0].lower()
    block_id = parts[1] if len(parts) > 1 else ""
    if action in {"on", "enable", "вкл", "включить", "подключить"}:
        return _set_block_enabled(block_id, True, context)
    if action in {"off", "disable", "выкл", "выключить", "отключить"}:
        return _set_block_enabled(block_id, False, context)
    if action in {"status", "статус"}:
        return _block_status(block_id.strip() or None, context)
    return "Используй: /block_on chrysostom-prayers, /block_off chrysostom-prayers или /block_status."


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


def _meal_done(meal_number: int, context: CommandContext) -> str:
    if meal_number < 1:
        return MEAL_DONE_USAGE
    if context.override_dir is None:
        return "Пересчет питания недоступен в этом режиме."

    completed_at = context.now()
    try:
        events = write_meal_done_override(
            override_dir=context.override_dir,
            schedule=context.schedule,
            day=completed_at.date(),
            completed_meal_number=meal_number,
            completed_at=completed_at,
        )
    except ValueError as exc:
        return f"Не смог пересчитать питание: {exc}"

    if context.reload_schedule is not None:
        context.reload_schedule()
    return _format_meal_done_result(meal_number, completed_at, events)


def _shift(argument: str, context: CommandContext) -> str:
    parts = argument.strip().split()
    if len(parts) != 1 or not _looks_like_time(parts[0]):
        return "Используй: /sd 10:00."
    if context.override_dir is None or context.schedule_path is None:
        return "Перенос дня недоступен в этом режиме."

    try:
        schedule_data = json.loads(context.schedule_path.read_text(encoding="utf-8"))
        data = write_shifted_day_override(
            override_dir=context.override_dir,
            schedule_data=schedule_data,
            day=context.now().date(),
            start_time=parts[0],
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return f"Не смог перенести день: {exc}"

    if context.reload_schedule is not None:
        context.reload_schedule()
    return _format_shifted_day_result(parts[0], data)


def _format_event(prefix: str, event: ScheduleEvent, now: datetime) -> str:
    return f"{prefix}: {format_event_line(event, now).removeprefix('- ')}"


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


def _parse_meal_done_number(text: str) -> int | None:
    for pattern in MEAL_DONE_PATTERNS:
        match = pattern.match(text)
        if match:
            return int(match.group(1))
    return None


def _parse_quick_meal_done_number(text: str) -> int | None:
    match = QUICK_MEAL_DONE_PATTERN.match(text)
    return int(match.group(1)) if match else None


def _parse_plain_block_command(text: str) -> tuple[bool | None, str] | None:
    lowered = text.lower()
    for prefix, enabled in [
        ("подключить блок", True),
        ("включить блок", True),
        ("отключить блок", False),
        ("выключить блок", False),
    ]:
        if lowered == prefix:
            return enabled, ""
        if lowered.startswith(prefix + " "):
            return enabled, text[len(prefix) :].strip()

    for prefix in ["статус блока", "статус блоков"]:
        if lowered == prefix:
            return None, ""
        if lowered.startswith(prefix + " "):
            return None, text[len(prefix) :].strip()

    if lowered == "блоки":
        return None, ""
    return None


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


def _format_meal_done_result(
    meal_number: int,
    completed_at: datetime,
    events: list[ScheduleEvent],
) -> str:
    lines = [f"Принял: {meal_number} пп завершен в {completed_at:%H:%M}."]
    if not events:
        lines.append("Остаток питания на сегодня не нужен.")
        return "\n".join(lines)
    lines.append("Пересчитал остаток:")
    lines.extend(f"- {event.when:%H:%M} {event.title}" for event in events)
    return "\n".join(lines)
