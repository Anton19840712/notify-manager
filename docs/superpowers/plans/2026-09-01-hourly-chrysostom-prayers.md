# Hourly Chrysostom Prayers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 16 hourly Saint John Chrysostom prayer reminders from `05:00` through `20:00`.

**Architecture:** Implement the feature as fixed `config/schedule.json` events with stable ids and full prayer text in each message. Avoid new runtime code because the existing schedule engine already supports fixed events and duplicate timestamps.

**Tech Stack:** JSON schedule configuration, Python `unittest`, existing notifier runtime.

---

## File Structure

- Modify `day-notifier/config/schedule.json`: add 16 fixed `chrysostom-prayer-*` events.
- Modify `day-notifier/tests/test_schedule.py`: verify the default schedule contains the exact hourly prayer sequence.
- Modify `day-notifier/README.md`: document the hourly prayer reminders and source note.

---

### Task 1: Schedule Test

**Files:**
- Modify: `day-notifier/tests/test_schedule.py`

- [x] **Step 1: Write failing test**

Add a test that loads the default schedule and asserts there are 16 `chrysostom-prayer-*` events at `05:00` through `20:00`, with title `Молитва Иоанна Златоуста N/16`.

- [x] **Step 2: Run focused test**

Run `python -m unittest day-notifier\tests\test_schedule.py`. Expected: the new test fails because the prayer events are not in `config/schedule.json` yet.

---

### Task 2: Schedule Events

**Files:**
- Modify: `day-notifier/config/schedule.json`

- [x] **Step 1: Add events**

Add `chrysostom-prayer-01` through `chrysostom-prayer-16` as fixed events from `05:00` through `20:00`.

- [x] **Step 2: Run focused test**

Run `python -m unittest day-notifier\tests\test_schedule.py`. Expected: all schedule tests pass.

---

### Task 3: Docs, Sync, Verification, Rollout

**Files:**
- Modify: `day-notifier/README.md`
- Copy changed files to `C:\мое программное обеспечение\notify-manager`.

- [x] **Step 1: Update README**

Document the hourly prayer window and that these events are clock-based.

- [x] **Step 2: Run full mirror verification**

Run tests, compileall, diff check, placeholder scan, and secret scan.

- [x] **Step 3: Copy to private project**

Copy schedule, tests, README, spec, and plan files to the private project.

- [x] **Step 4: Run private verification**

Run the same checks in `C:\мое программное обеспечение\notify-manager`.

- [x] **Step 5: Commit, push, restart**

Commit mirror and private changes, push private `origin/main`, restart notifier, check status, today output, and logs.

## Self-Review

- Spec coverage: the plan covers times, ids, titles, messages, docs, tests, private sync, push, and restart.
- Placeholder scan: no unfinished placeholders remain.
- Type consistency: `chrysostom-prayer-*`, `Молитва Иоанна Златоуста N/16`, and `05:00..20:00` are consistent.
