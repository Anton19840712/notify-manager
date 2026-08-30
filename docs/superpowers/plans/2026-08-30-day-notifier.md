# Day Notifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Windows day notifier that reads a schedule file, shows desktop popups, sends Telegram reminders, and responds to basic Telegram commands.

**Architecture:** Keep the core schedule and command logic pure and testable. Wrap side effects in small adapters: Telegram client, desktop notifier, state store, and the main polling loop.

**Tech Stack:** Python standard library, `unittest`, Telegram Bot API over `urllib`, AutoHotkey launcher.

---

### Task 1: Schedule Engine

**Files:**
- Create: `tests/test_schedule.py`
- Create: `src/day_notifier/schedule.py`

- [ ] Write tests for fixed events and repeated water/meal cycles.
- [ ] Run `python -m unittest discover -s tests` and verify schedule imports fail before implementation.
- [ ] Implement `ScheduleEvent`, `Schedule`, `load_schedule`, and daily expansion.
- [ ] Run the focused tests and verify they pass.

### Task 2: Command Engine

**Files:**
- Create: `tests/test_commands.py`
- Create: `src/day_notifier/commands.py`
- Create: `src/day_notifier/inbox.py`

- [ ] Write tests for `/next`, `/summary`, `/snooze`, and `/inbox`.
- [ ] Run tests and verify command imports fail before implementation.
- [ ] Implement command parsing against a small context object.
- [ ] Run the focused tests and verify they pass.

### Task 3: Runtime Adapters

**Files:**
- Create: `src/day_notifier/config.py`
- Create: `src/day_notifier/state.py`
- Create: `src/day_notifier/telegram_client.py`
- Create: `src/day_notifier/desktop.py`
- Create: `src/day_notifier/app.py`
- Create: `src/day_notifier/__main__.py`

- [ ] Add tests for settings loading and state behavior where useful.
- [ ] Implement adapters using only the Python standard library.
- [ ] Keep Telegram optional when `settings.json` is absent.
- [ ] Run all unit tests.

### Task 4: Local Project Files

**Files:**
- Create: `config/schedule.json`
- Create: `config/settings.example.json`
- Create: `data/inbox.md`
- Create: `scripts/start-notifier.ps1`
- Create: `scripts/start-notifier.ahk`
- Create: `README.md`
- Create: `.gitignore`

- [ ] Add the default September schedule and launcher scripts.
- [ ] Document bot setup and commands.
- [ ] Ignore local secrets, runtime state, and logs.
- [ ] Run all tests and a dry-run smoke command.

### Task 5: Windows Process Control

**Files:**
- Modify: `scripts/start-notifier.ps1`
- Modify: `scripts/start-notifier.ahk`
- Modify: `src/day_notifier/app.py`
- Modify: `src/day_notifier/commands.py`
- Modify: `src/day_notifier/schedule.py`

- [ ] Add `/today` and a startup summary so Telegram confirms today's remaining reminders.
- [ ] Add PowerShell process control actions: start, stop, restart, status, foreground, today, and test Telegram.
- [ ] Add AutoHotkey tray menu actions for the same control surface.
- [ ] Run all tests and smoke commands.

### Task 6: Optional Desktop MsgBox Channel

**Files:**
- Modify: `src/day_notifier/desktop.py`
- Modify: `src/day_notifier/config.py`
- Modify: `src/day_notifier/app.py`
- Modify: `src/day_notifier/commands.py`
- Modify: `scripts/start-notifier.ps1`
- Modify: `scripts/start-notifier.ahk`

- [ ] Add a topmost center-screen Windows MsgBox notifier.
- [ ] Add Telegram and PowerShell commands to enable, disable, test, and inspect desktop notifications.
- [ ] Send startup summaries to desktop when the desktop channel is enabled.
- [ ] Run all tests and smoke commands.

### Self-Review

The plan covers schedule loading, notification delivery, Telegram commands, local launchers, docs, and secret handling. The first implementation intentionally excludes voice recognition and Windows service installation; those are later extensions after the process proves useful.
