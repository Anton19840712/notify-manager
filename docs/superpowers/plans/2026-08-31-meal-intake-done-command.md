# Meal Intake Done Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `2 mi done` style command that marks a meal completed now and recalculates remaining meal reminders for today.

**Architecture:** Reuse the existing one-day override and emergency meal helpers. Add a food-only override writer that preserves non-food override events, add command parsing in `commands.py`, and teach the Telegram client to pass through plain meal-done text.

**Tech Stack:** Python standard library, `unittest`, JSON day overrides, existing Telegram Bot API polling.

---

## File Structure

- Modify `src/day_notifier/overrides.py`: add meal-number detection and a writer that recalculates remaining meals while preserving non-food override events.
- Modify `src/day_notifier/commands.py`: parse `2 mi done`, aliases, and `/mi 2 done`.
- Modify `src/day_notifier/telegram_client.py`: accept plain meal-done commands from Telegram.
- Modify `README.md`: document the new command.
- Modify tests:
  - `tests/test_overrides.py`
  - `tests/test_commands.py`
  - `tests/test_telegram_client.py`

---

### Task 1: Food Override Writer

**Files:**
- Modify: `tests/test_overrides.py`
- Modify: `src/day_notifier/overrides.py`

- [x] **Step 1: Write failing tests**

Add tests that verify `write_meal_done_override()` produces `14:40 3 пп` and `17:05 4 пп` after meal 2 is completed at `12:25`, removes water events, and preserves non-food shifted override events.

- [x] **Step 2: Run focused tests**

Run `python -m unittest day-notifier\tests\test_overrides.py`. Expected: import failure for `write_meal_done_override`.

- [x] **Step 3: Implement helper**

Implement `write_meal_done_override()` in `src/day_notifier/overrides.py`. It should inspect the active schedule for today's highest meal number, calculate remaining meals with `build_min_interval_food_events()`, preserve non-food override events, union `water-food-cycle` into `suppress_cycles`, and write the one-day override.

- [x] **Step 4: Run focused tests**

Run `python -m unittest day-notifier\tests\test_overrides.py`. Expected: all override tests pass.

- [x] **Step 5: Commit**

Commit mirror changes with `feat: recalc meals from done command mirror`.

---

### Task 2: Command Parser

**Files:**
- Modify: `tests/test_commands.py`
- Modify: `src/day_notifier/commands.py`

- [x] **Step 1: Write failing command tests**

Add command tests for `2 mi done`, `2 pp done`, `2 пп done`, and `/mi 2 done`. The main test should assert the reply includes:

```text
Принял: 2 пп завершен в 12:25.
Пересчитал остаток:
- 14:40 3 пп
- 17:05 4 пп
```

- [x] **Step 2: Run focused tests**

Run `python -m unittest day-notifier\tests\test_commands.py`. Expected: command falls through to the help reply.

- [x] **Step 3: Implement parsing and dispatch**

Add a parser for the four forms. On success, call `write_meal_done_override()`, reload the schedule, and return the confirmation text. Invalid forms should return a usage hint.

- [x] **Step 4: Run focused tests**

Run `python -m unittest day-notifier\tests\test_commands.py`. Expected: all command tests pass.

- [x] **Step 5: Commit**

Commit mirror changes with `feat: add meal done command mirror`.

---

### Task 3: Telegram Plain Text Acceptance

**Files:**
- Modify: `tests/test_telegram_client.py`
- Modify: `src/day_notifier/telegram_client.py`

- [x] **Step 1: Write failing tests**

Add a test that plain `2 mi done` is returned by `get_commands()`, while unrelated plain text is ignored.

- [x] **Step 2: Run focused tests**

Run `python -m unittest day-notifier\tests\test_telegram_client.py`. Expected: plain meal-done text is ignored.

- [x] **Step 3: Implement Telegram text predicate**

Add a small helper that accepts slash commands, plain `отбой`, and plain meal-done commands.

- [x] **Step 4: Run focused tests and full mirror suite**

Run `python -m unittest day-notifier\tests\test_telegram_client.py` and `python -m unittest discover -s day-notifier\tests`. Expected: all tests pass.

- [x] **Step 5: Commit**

Commit mirror changes with `feat: accept meal done telegram text mirror`.

---

### Task 4: Docs, Private Sync, Push, Restart

**Files:**
- Modify: `README.md`
- Copy changed files to `C:\мое программное обеспечение\notify-manager`.

- [x] **Step 1: Update README**

Document `2 mi done`, aliases, and the fact that it recalculates remaining meals only for today.

- [x] **Step 2: Full mirror verification**

Run tests, compileall, diff check, TODO/FIXME scan, and secret scan.

- [x] **Step 3: Copy to private project**

Copy changed source, tests, README, spec, and plan files to the private project.

- [x] **Step 4: Private verification**

Run the same checks in `C:\мое программное обеспечение\notify-manager`.

- [ ] **Step 5: Commit, push, restart**

Commit private changes, push `origin/main`, restart the notifier, check `-Status`, `-Today`, and logs.

---

## Self-Review

- Spec coverage: the plan covers command aliases, active-day meal counting, backward/forward timing, base flow preservation, shifted override preservation, Telegram input, README, private sync, push, and restart.
- Placeholder scan: no unfilled implementation placeholders remain.
- Type consistency: `write_meal_done_override`, meal numbers, `2 mi done`, and one-day override terms are consistent across tasks.
