# Day Notifier

Local Windows notifier for day practices. It reads `config/schedule.json`, shows desktop popups, sends Telegram Bot API messages, and accepts simple Telegram commands.

## Setup

1. Create a Telegram bot through BotFather.
2. Find your `chat_id`.
3. Copy `config/settings.example.json` to `config/settings.json`.
4. Put `bot_token` and `chat_id` into `config/settings.json`.

`config/settings.json` is ignored by git.

## Run

From PowerShell:

```powershell
.\scripts\start-notifier.ps1
```

The default mode starts the notifier in the background and writes logs to `logs/`.

Process control:

```powershell
.\scripts\start-notifier.ps1 -Status
.\scripts\start-notifier.ps1 -Stop
.\scripts\start-notifier.ps1 -Restart
.\scripts\start-notifier.ps1 -Foreground
```

From AutoHotkey:

```text
Run scripts\start-notifier.ahk
```

The AutoHotkey script starts the notifier and adds tray menu actions:

- `Start`
- `Stop`
- `Restart`
- `Status`
- `Today`
- `Summary`
- `Test Telegram`

Install Windows autostart for the AutoHotkey control:

```powershell
.\scripts\install-startup-shortcut.ps1
```

Remove autostart:

```powershell
.\scripts\install-startup-shortcut.ps1 -Remove
```

One-cycle smoke run:

```powershell
.\scripts\start-notifier.ps1 -Once
```

Print upcoming schedule:

```powershell
.\scripts\start-notifier.ps1 -Summary
```

Print the remaining reminders for today:

```powershell
.\scripts\start-notifier.ps1 -Today
```

Send a test Telegram and desktop notification:

```powershell
.\scripts\start-notifier.ps1 -TestTelegram
```

## Telegram Commands

- `/summary` - upcoming reminders and inbox.
- `/today` - remaining reminders for today.
- `/next` - next reminder.
- `/done` - mark last delivered reminder as done.
- `/snooze 10` - delay last or next reminder by 10 minutes.
- `/inbox text` - append a small task to `data/inbox.md`.

## Schedule

The default schedule uses a 145-minute water/food cycle:

- `1 пв` at `07:00`, `1 пп` at `07:15`.
- `2 пв` at `09:25`, `2 пп` at `09:40`.
- `3 пв` at `11:50`, `3 пп` at `12:05`.
- `4 пв` at `14:15`, `4 пп` at `14:30`.
