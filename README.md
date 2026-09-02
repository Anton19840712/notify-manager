# Day Notifier

Local Windows notifier for day practices. It reads `config/schedule.json`, shows desktop popups, sends Telegram Bot API messages, and accepts simple Telegram commands.

## Setup

1. Create a Telegram bot through BotFather.
2. Find your `chat_id`.
3. Copy `config/settings.example.json` to `config/settings.json`.
4. Put `bot_token` and `chat_id` into `config/settings.json`.

`config/settings.json` is ignored by git.

## Audio Cues

The wake-up event first opens `data/audio/rota-podem.mp3`, waits 2 seconds, then opens `data/audio/morning-prays.mp3`. If either file is missing or Windows cannot open it, the notifier logs the problem and still sends the regular Telegram and desktop reminders.

The bedtime event opens `data/audio/otboj.mp3` before sending the `Отбой` Telegram and desktop reminders.

## Optional Blocks

Optional practice blocks are stored in `config/schedule.json` under `blocks`. Events, rotations, and relative cycles with a `block` field stay in the schedule file, but they are delivered only when that block is enabled.

- `self-development` - engineering article, microservices, monitoring, and day optimization.
- `training` - strength rotation: thighs, calves, plus one base movement.
- `prayers` - morning prayer and spiritual reset block.
- `chrysostom-prayers` - 16 hourly Saint John Chrysostom prayers from `05:00` to `20:00`, disabled by default.

Hard anchors stay outside the block layer: wake-up, minimum cardio tail, food/water cycle, pre-meal reminders, work daily, lunch nap, batch-cooking, sleep countdown, and bedtime.

Use `/block_on`, `/block_off`, and `/block_status` in Telegram to toggle runtime block state. Runtime overrides are saved to `data/block_state.json`, so the base schedule stays clean while the live setting survives notifier restarts.

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
- `Sync Bot Commands`
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

Sync the Telegram bot command menu:

```powershell
.\scripts\start-notifier.ps1 -SyncBotCommands
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

- `/help` - generated command list.
- `/summary` - upcoming reminders and inbox.
- `/today` - remaining reminders for today.
- `/next` - next reminder.
- `/done` - mark last delivered reminder as done.
- `/snooze 10` - delay last or next reminder by 10 minutes.
- `/recalc food 4` - recalculate today's remaining food reminders with a 10-minute eating window and a 2:15 gap after eating.
- `/2 mi done`, `2 mi done`, `2 pp done`, `2 пп done`, `/ 2 mi done`, or `/mi 2 done` - mark meal 2 as completed now and recalculate today's remaining meal reminders.
- `/sd 10:00` or `sd 10:00` - rebuild today's start-relative reminders from 10:00; tomorrow keeps the base flow.
- `/mi1`, `/mi2`, `/mi3`, `/mi4` - mark the selected meal as completed now.
- `/otboy`, `/отбой`, or `отбой` - delete tracked bot-chat messages and leave one bedtime confirmation.
- `/desktop on`, `/desktop off`, `/desktop status`, `/desktop_on`, `/desktop_off`, `/desktop_status` - control center-screen MsgBox reminders.
- `/block_on self-development`, `/block_off training`, `/block_status`, or `/blocks` - connect, disconnect, or inspect optional practice blocks.
- `/selfdev_on`, `/selfdev_off`, `/training_on`, `/training_off`, `/prayers_on`, `/prayers_off`, `/chrysostom_on`, `/chrysostom_off` - quick BotFather-safe block toggles.
- `подключить блок self-development`, `отключить блок training`, or `блоки` - plain-text aliases for block control.
- `/stop_bot` - stop the local notifier process after sending a confirmation reply.
- `/inbox text` - append a small task to `data/inbox.md`.

Telegram menu command names are kept BotFather-safe: lowercase English letters, digits, and underscores only. Run `.\scripts\start-notifier.ps1 -SyncBotCommands` after changing commands so Telegram shows the same menu that the notifier understands.

Telegram cleanup can only delete messages whose `message_id` was tracked after this feature was enabled. Telegram may reject old messages outside its deletion window, and those are counted as skipped.

## Schedule

The default schedule uses a 145-minute water/food cycle:

- Self-development, strength training, and the morning prayer/spirit layer are toggleable blocks enabled by default.
- Saint John Chrysostom prayers are kept as the optional `chrysostom-prayers` block and are disabled by default.
- Work daily is fixed at `11:00`.
- Strength runs at `11:15` as a 7-day rotation: every day keeps thighs and calves, then adds one base movement.
- The strength base movement rotation starts on `2026-09-01`: pull-ups, bench press, row, dips, overhead/Viking press, trap-bar/RDL, core/posture.
- Lunch recovery sleep runs from `12:15` to `13:15`.
- `1 пв` at `07:00`, `1 пп` at `07:15`.
- `2 пв` at `09:25`, `2 пп` at `09:40`.
- `3 пв` at `11:50`, `3 пп` at `12:05`.
- `4 пв` at `14:15`, `4 пп` at `14:30`.
- Every active `пп` gets an automatic 10-minute pre-reminder with a short-task prompt. These service reminders are delivered when due, but hidden from `/summary`, `/today`, `/next`, and startup summaries. The fuller catalog is in `data/ten-minute-tasks.md`.
- Every third day from `2026-09-01`, batch-cooking starts 10 minutes after the last active `пп` event. If today's meals are shifted by a one-day override, the cooking cycle follows the shifted last meal.
- Batch-cooking is one long block: cook 12 prepared meals, put them into containers, clean the kitchen surfaces, and close the kitchen.

The living practice list is kept in `data/day-practices.md`.
