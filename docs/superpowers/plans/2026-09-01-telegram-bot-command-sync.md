# Telegram Bot Command Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single source of truth for Telegram-safe bot menu commands and sync it to Telegram automatically.

**Architecture:** Create a small command registry that validates BotFather-compatible names, generates Telegram `setMyCommands` payloads, and produces in-chat help. Extend the existing Telegram client, command parser, CLI, PowerShell launcher, and AutoHotkey tray without changing the schedule engine.

**Tech Stack:** Python standard library, Telegram Bot API JSON calls, PowerShell launcher, AutoHotkey tray, `unittest`.

---

### Task 1: Registry and Aliases

**Files:**
- Create: `src/day_notifier/bot_commands.py`
- Modify: `src/day_notifier/commands.py`
- Test: `tests/test_bot_commands.py`
- Test: `tests/test_commands.py`

- [x] **Step 1: Write failing tests**

Add tests that expect BotFather-safe commands, generated help text, `/mi1`, `/mi2`, `/desktop_on`, `/desktop_off`, `/desktop_status`, `/otboy`, and `/help`.

- [x] **Step 2: Implement registry and parser aliases**

Add `BOT_COMMANDS`, payload generation, help formatting, meal shortcut parsing, desktop aliases, and the Latin bedtime cleanup alias.

- [x] **Step 3: Verify focused tests**

Run `python -m unittest discover -s tests -p "test_bot_commands.py"` and `python -m unittest discover -s tests -p "test_commands.py"`.

### Task 2: Telegram Sync

**Files:**
- Modify: `src/day_notifier/telegram_client.py`
- Modify: `src/day_notifier/app.py`
- Modify: `scripts/start-notifier.ps1`
- Modify: `scripts/start-notifier.ahk`
- Test: `tests/test_telegram_client.py`
- Test: `tests/test_config_state_app.py`

- [x] **Step 1: Write failing tests**

Add tests for `TelegramClient.set_my_commands()` and `NotifierApp.sync_bot_commands()`.

- [x] **Step 2: Implement sync path**

Post `{"commands": [...]}` to Telegram `setMyCommands`, add `--sync-bot-commands`, add `-SyncBotCommands`, and add the AHK tray action.

- [x] **Step 3: Verify sync path**

Run focused tests, full tests, compileall, diff check, placeholder-marker scan, and secret scan.

### Task 3: Private Rollout

**Files:**
- Modify: `README.md`
- Sync all changed files to `C:\мое программное обеспечение\notify-manager`.

- [x] **Step 1: Document sync**

Document `-SyncBotCommands`, menu-safe command names, and the difference between menu commands and argument forms.

- [x] **Step 2: Roll out**

Run private tests, commit, push `origin/main`, restart notifier, and run `.\scripts\start-notifier.ps1 -SyncBotCommands`.

## Self-Review

- Spec coverage: registry, aliases, Telegram payload, CLI, PowerShell, AHK, docs, private sync, and runtime sync are covered.
- Placeholder scan: no placeholder markers remain.
- Type consistency: `BOT_COMMANDS`, `bot_command_payload`, `set_my_commands`, `sync_bot_commands`, and `SyncBotCommands` are named consistently.
