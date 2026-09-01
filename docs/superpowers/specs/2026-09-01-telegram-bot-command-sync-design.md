# Telegram Bot Command Sync Design

## Goal

Keep Telegram's bot menu synchronized with the commands that the local notifier actually understands, without manually typing the command list into BotFather.

## Telegram Command Format

Telegram bot menu commands must be 1-32 characters and use only lowercase English letters, digits, and underscores. Commands with spaces, slashes inside the command name, Cyrillic command names, or camelCase are not valid menu commands.

## Command Mapping

The notifier keeps one registry of menu commands:

- `summary`, `today`, `next`, `done`, `snooze`, `recalc`, `sd`, `inbox`;
- `mi1`, `mi2`, `mi3`, `mi4` for meal completion shortcuts;
- `desktop_on`, `desktop_off`, `desktop_status`;
- `stop_bot` for stopping the local notifier process from the authorized Telegram chat;
- `otboy` for the bedtime chat cleanup command;
- `help` for the generated command list.

The registry produces the payload for Telegram Bot API `setMyCommands` and the in-chat help text. Button-friendly aliases such as `/mi1`, `/desktop_on`, `/stop_bot`, and `/otboy` are translated into the existing internal command actions.

## Runtime Sync

The local CLI exposes `--sync-bot-commands`; the PowerShell launcher exposes `-SyncBotCommands`; the AutoHotkey tray exposes `Sync Bot Commands`. The sync command calls Telegram `setMyCommands` through the existing `TelegramClient` transport and returns a Russian confirmation with the number of commands sent.

## Error Handling

If Telegram credentials are missing, sync returns a readable message. If Telegram rejects the call or the network fails, sync logs the exception and returns a readable failure without printing the bot token.

## Testing

Tests cover command-name validation, payload generation, TelegramClient `setMyCommands`, notifier sync, generated help text, and menu aliases for meals, desktop controls, local stop, and bedtime cleanup.
