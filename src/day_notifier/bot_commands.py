from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


BOT_COMMAND_NAME_PATTERN = re.compile(r"^[a-z0-9_]{1,32}$")


@dataclass(frozen=True)
class BotCommandDefinition:
    command: str
    description: str


BOT_COMMANDS: tuple[BotCommandDefinition, ...] = (
    BotCommandDefinition("help", "список команд"),
    BotCommandDefinition("summary", "ближайшие события и inbox"),
    BotCommandDefinition("today", "события на сегодня"),
    BotCommandDefinition("next", "следующее событие"),
    BotCommandDefinition("done", "отметить последнее событие"),
    BotCommandDefinition("snooze", "отложить на 10 минут"),
    BotCommandDefinition("recalc", "пересчитать питание, пример /recalc food 4"),
    BotCommandDefinition("mi1", "съел 1 прием пищи"),
    BotCommandDefinition("mi2", "съел 2 прием пищи"),
    BotCommandDefinition("mi3", "съел 3 прием пищи"),
    BotCommandDefinition("mi4", "съел 4 прием пищи"),
    BotCommandDefinition("sd", "перенести старт дня, пример /sd 10:00"),
    BotCommandDefinition("desktop_on", "включить desktop окна"),
    BotCommandDefinition("desktop_off", "выключить desktop окна"),
    BotCommandDefinition("desktop_status", "статус desktop окон"),
    BotCommandDefinition("block_on", "подключить блок"),
    BotCommandDefinition("block_off", "отключить блок"),
    BotCommandDefinition("block_status", "статус блоков"),
    BotCommandDefinition("stop_bot", "остановить локальный notifier"),
    BotCommandDefinition("inbox", "добавить текст в inbox"),
    BotCommandDefinition("otboy", "очистить чат перед сном"),
)


def bot_command_payload(commands: Iterable[BotCommandDefinition] = BOT_COMMANDS) -> list[dict[str, str]]:
    command_list = list(commands)
    validate_bot_commands(command_list)
    return [
        {"command": command.command, "description": command.description}
        for command in command_list
    ]


def format_bot_commands_help(commands: Iterable[BotCommandDefinition] = BOT_COMMANDS) -> str:
    command_list = list(commands)
    validate_bot_commands(command_list)
    lines = ["Команды:"]
    lines.extend(f"/{command.command} - {command.description}" for command in command_list)
    lines.append("")
    lines.append("Аргументы: /sd 10:00, /snooze 10, /recalc food 4, /inbox текст.")
    lines.append("Блоки: /block_on, /block_off, /block_status или /block_on chrysostom-prayers.")
    lines.append("Прием пищи: /mi1, /mi2, /mi3, /mi4 или /2 mi done.")
    return "\n".join(lines)


def format_bot_command_sync_result(commands: Iterable[BotCommandDefinition] = BOT_COMMANDS) -> str:
    command_list = list(commands)
    validate_bot_commands(command_list)
    lines = [f"Синхронизировал команды Telegram-меню: {len(command_list)}."]
    lines.extend(f"/{command.command} - {command.description}" for command in command_list)
    return "\n".join(lines)


def validate_bot_commands(commands: Iterable[BotCommandDefinition]) -> None:
    seen: set[str] = set()
    for command in commands:
        if not BOT_COMMAND_NAME_PATTERN.match(command.command):
            raise ValueError(f"Invalid Telegram bot command name: {command.command}")
        if command.command in seen:
            raise ValueError(f"Duplicate Telegram bot command name: {command.command}")
        if len(command.description) < 1 or len(command.description) > 256:
            raise ValueError(f"Invalid Telegram bot command description for: {command.command}")
        seen.add(command.command)
