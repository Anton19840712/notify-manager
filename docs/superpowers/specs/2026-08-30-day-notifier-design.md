# Day Notifier Design

## Goal

Create a local Windows process that reads a day schedule from files, shows desktop reminders, sends the same reminders to Telegram, and accepts simple Telegram commands for self-control.

## Scope

The first version is a small local Python application with no external dependencies. It is started manually or through an AutoHotkey script. It supports fixed daily events, repeated water/meal cycles, sleep countdown notifications, a local inbox for small tasks, and Telegram Bot API notifications.

## Files

- `config/schedule.json`: editable schedule with fixed events and repeated cycles.
- `config/settings.example.json`: safe example of Telegram settings.
- `config/settings.json`: local secret settings, ignored by git.
- `data/inbox.md`: small incoming tasks and notes.
- `data/state.json`: runtime notification state.
- `src/day_notifier`: application package.
- `scripts/start-notifier.ps1`: PowerShell launcher.
- `scripts/start-notifier.ahk`: AutoHotkey launcher.

## Behavior

The process checks the schedule every 15 seconds by default. It sends each event once, using both a desktop popup and Telegram when Telegram settings are present.

The PowerShell launcher can start the notifier in the background, stop it, restart it, show status, print the remaining events for today, and send a test Telegram notification. The AutoHotkey launcher wraps these actions in a tray menu.

The default schedule includes:

- `04:00`: wake up.
- Morning prayer rule and bike/treadmill block.
- Four water events: `1 пв`, `2 пв`, `3 пв`, `4 пв`.
- Four food events 15 minutes after each water event: `1 пп`, `2 пп`, `3 пп`, `4 пп`.
- The water/food cycle repeats every 145 minutes.
- Sleep countdown: 1 hour, 15 minutes, and 1 minute before bedtime.
- Bedtime notification.

If the computer was asleep or the process was stopped, the application skips old missed events beyond a configured grace window instead of spamming old notifications.

## Telegram

Telegram uses the Bot API. The user creates a bot through BotFather and writes `bot_token` and `chat_id` into `config/settings.json`. Secrets are not committed.

Supported commands:

- `/summary`: show upcoming reminders and inbox items.
- `/today`: show remaining reminders for the current day.
- `/next`: show the next reminder.
- `/done`: mark the last delivered reminder as done.
- `/snooze 10`: delay the next or last reminder by 10 minutes.
- `/inbox text`: append a small task to `data/inbox.md`.

## Desktop

The first version uses a Windows message box in a background thread. On non-Windows systems it prints the notification text to the console.

## Error Handling

Telegram failures are written to the log and do not block desktop reminders. Invalid schedule/config files fail early with a clear error. Missing Telegram settings are allowed, so the app can run as a desktop-only notifier while the user prepares the bot.
