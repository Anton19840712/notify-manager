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
- `Test Desktop MsgBox`
- `Desktop On`
- `Desktop Off`
- `Desktop Status`

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

Show a blocking center-screen desktop message box:

```powershell
.\scripts\start-notifier.ps1 -TestDesktop
```

Control the desktop channel:

```powershell
.\scripts\start-notifier.ps1 -DesktopOn
.\scripts\start-notifier.ps1 -DesktopOff
.\scripts\start-notifier.ps1 -DesktopStatus
```

Recalculate today's food cycle without changing the base schedule:

```powershell
.\scripts\start-notifier.ps1 -RecalcFood 4 -RecalcAnchor 13:12 -RecalcMinInterval 135
```

Shift only today's day start without changing the base `04:00` schedule:

```powershell
.\scripts\start-notifier.ps1 -ShiftDay 10:00
```

This writes a local one-day override to `data/day_overrides/`. Override files are ignored by git.

## Telegram Commands

- `/summary` - upcoming reminders and inbox.
- `/today` - remaining reminders for today.
- `/next` - next reminder.
- `/done` - mark last delivered reminder as done.
- `/snooze 10` - delay last or next reminder by 10 minutes.
- `/recalc food 4` - recalculate today's remaining food reminders with a 10-minute eating window and a 2:15 gap after eating.
- `2 mi done`, `2 pp done`, `2 пп done`, or `/mi 2 done` - mark meal 2 as completed now and recalculate today's remaining meal reminders.
- `/shift day 10:00` - rebuild today's start-relative reminders from 10:00; tomorrow keeps the base flow.
- `/отбой` or `отбой` - delete tracked bot-chat messages and leave one bedtime confirmation.
- `/desktop on`, `/desktop off`, `/desktop status` - control center-screen MsgBox reminders.
- `/inbox text` - append a small task to `data/inbox.md`.

Telegram cleanup can only delete messages whose `message_id` was tracked after this feature was enabled. Telegram may reject old messages outside its deletion window, and those are counted as skipped.

## Schedule

The default schedule uses a 145-minute water/food cycle:

- `1 пв` at `07:00`, `1 пп` at `07:15`.
- `2 пв` at `09:25`, `2 пп` at `09:40`.
- `3 пв` at `11:50`, `3 пп` at `12:05`.
- `4 пв` at `14:15`, `4 пп` at `14:30`.

The living practice list is kept in `data/day-practices.md`.
