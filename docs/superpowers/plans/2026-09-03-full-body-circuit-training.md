# Full Body Circuit Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace notify-manager's old strength rotation with the approved one-hour full-body endurance circuit plus assault/regular bike tail and shower note.

**Architecture:** Keep the existing schedule data model and `training` block. Only update configuration, practice documentation, README, and schedule tests; no new runtime code is required.

**Tech Stack:** JSON schedule configuration, Python unittest schedule tests, Markdown docs.

---

### Task 1: Schedule Test

**Files:**
- Modify: `day-notifier/tests/test_schedule.py`

- [ ] **Step 1: Write the failing test expectation**

Update `test_default_schedule_contains_strength_rotation_and_lunch_nap` so it expects:

```python
("full-body-circuit-back-squat", "Круговая A: присед на спине + жим стоя", "11:15")
("full-body-circuit-bench", "Круговая B: жим лежа + треп-гриф", "11:15")
("full-body-circuit-front-squat", "Круговая A: фронтальный присед + жим стоя", "11:15")
("full-body-circuit-incline", "Круговая B: жим наклонный + треп-гриф", "11:15")
```

Also assert that the first day's message contains `assault bike`, `обычный bike`, `душ`, and `Тяга штанги к поясу в наклоне`.

- [ ] **Step 2: Run the focused test**

Run:

```powershell
python -m unittest tests.test_schedule.ScheduleTests.test_default_schedule_contains_strength_rotation_and_lunch_nap -v
```

Expected: it fails because `config/schedule.json` still contains the old `strength-*` rotation.

### Task 2: Schedule And Docs

**Files:**
- Modify: `day-notifier/config/schedule.json`
- Modify: `day-notifier/README.md`
- Modify: `day-notifier/data/day-practices.md`

- [ ] **Step 1: Update `training` block description**

Set the description to:

```json
"Круговая тренировка всего тела: 10 упражнений по 10 повторений, до 10 кругов за час. Остаток часа - assault bike или обычный bike, потом душ."
```

- [ ] **Step 2: Replace rotating events**

Set `period_days` to `4` and replace the old seven items with the four approved A/B templates.

- [ ] **Step 3: Update README and day practice notes**

Describe the new four-day rotation and the bike/shower rule.

- [ ] **Step 4: Run the focused test again**

Expected: it passes.

### Task 3: Verification And Live Sync

**Files:**
- Same files as Task 2 in both mirror and live project.

- [ ] **Step 1: Run full mirror verification**

Run:

```powershell
python -m unittest discover -s tests -v
python -m compileall src
```

- [ ] **Step 2: Copy changed files to `C:\мое программное обеспечение\notify-manager`**

Copy `config/schedule.json`, `README.md`, `data/day-practices.md`, and the spec/plan docs.

- [ ] **Step 3: Run full live verification**

Run the same unittest and compileall commands in the live project.

- [ ] **Step 4: Restart live notifier**

Run:

```powershell
.\scripts\start-notifier.ps1 -Restart
```

- [ ] **Step 5: Commit and push**

Commit mirror and live changes, then push live `main`.
