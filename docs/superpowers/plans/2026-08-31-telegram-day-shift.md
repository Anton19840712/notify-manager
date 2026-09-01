# Telegram Day Shift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Telegram command that shifts only today's day-start schedule through a one-day override while preserving the permanent `04:00` base flow.

**Architecture:** Keep the Telegram polling path unchanged: `TelegramClient.get_commands()` already feeds slash commands into `handle_command()`. Add pure override helpers for shifted days and emergency meals, extend `Schedule` to suppress fixed events for a date, then wire `/sd HH:MM` through the existing `CommandContext.reload_schedule` callback.

**Tech Stack:** Python standard library, `unittest`, JSON one-day overrides, existing Telegram Bot API polling.

---

## File Structure

- Modify `src/day_notifier/schedule.py`: teach one-day overrides to suppress fixed event ids through `suppress_events`.
- Modify `src/day_notifier/overrides.py`: add emergency meal generation with a 10-minute eating window and day-shift override writing.
- Modify `src/day_notifier/commands.py`: add `/sd HH:MM` command and reuse existing context/reload flow.
- Modify `src/day_notifier/app.py`: add optional CLI support for manual local smoke testing of day shift.
- Modify `scripts/start-notifier.ps1`: expose the CLI day-shift smoke command.
- Modify `README.md`: document `/sd 10:00`, emergency meal timing, and baseline preservation.
- Modify `data/day-practices.md`: keep the living practice list aligned with the new command.
- Modify tests:
  - `tests/test_schedule.py`
  - `tests/test_overrides.py`
  - `tests/test_commands.py`
  - `tests/test_config_state_app.py`

---

### Task 1: Fixed Event Suppression

**Files:**
- Modify: `tests/test_schedule.py`
- Modify: `src/day_notifier/schedule.py`

- [ ] **Step 1: Write the failing test**

Add this test to `ScheduleTests` in `tests/test_schedule.py`:

```python
    def test_day_override_can_suppress_fixed_events_for_one_day(self):
        schedule = Schedule.from_dict(
            {
                "events": [
                    {"id": "wake", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "learn", "time": "05:00", "title": "Учеба", "message": "Учиться"},
                    {"id": "bed", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [],
            },
            day_overrides={
                "2026-08-30": {
                    "suppress_events": ["wake", "learn"],
                    "events": [
                        {
                            "id": "wake",
                            "time": "10:00",
                            "title": "Подъем",
                            "message": "Сдвинутый подъем",
                        },
                        {
                            "id": "learn",
                            "time": "11:00",
                            "title": "Учеба",
                            "message": "Сдвинутая учеба",
                        },
                    ],
                }
            },
        )

        shifted_events = schedule.events_for_date(date(2026, 8, 30))
        base_events = schedule.events_for_date(date(2026, 8, 31))

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in shifted_events],
            [
                ("wake", "Подъем", "10:00"),
                ("learn", "Учеба", "11:00"),
                ("bed", "Отбой", "22:00"),
            ],
        )
        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in base_events],
            [
                ("wake", "Подъем", "04:00"),
                ("learn", "Учеба", "05:00"),
                ("bed", "Отбой", "22:00"),
            ],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests\test_schedule.py
```

Expected: `FAIL` because `events_for_date()` still includes the original `04:00` and `05:00` fixed events on the override day.

- [ ] **Step 3: Implement minimal suppression**

In `src/day_notifier/schedule.py`, update `events_for_date()` near the existing `suppressed_cycles` calculation:

```python
        suppressed_cycles = set(str(cycle_id) for cycle_id in override.get("suppress_cycles", []))
        suppressed_events = set(str(event_id) for event_id in override.get("suppress_events", []))

        for event in self._events:
            event_id = str(event["id"])
            if event_id in suppressed_events:
                continue
            expanded.append(
                ScheduleEvent(
                    event_id=event_id,
                    title=str(event["title"]),
                    message=str(event.get("message", event["title"])),
                    when=datetime.combine(day, _parse_time(str(event["time"]))),
                )
            )
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest tests\test_schedule.py
```

Expected: all schedule tests pass.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_schedule.py src/day_notifier/schedule.py
git commit -m "feat: allow day overrides to suppress fixed events"
```

---

### Task 2: Emergency Meal Timing With Eating Window

**Files:**
- Modify: `tests/test_overrides.py`
- Modify: `src/day_notifier/overrides.py`

- [ ] **Step 1: Write failing tests**

Add this test to `OverrideTests` in `tests/test_overrides.py`:

```python
    def test_builds_emergency_meals_from_completed_meal_end_with_eating_window(self):
        events = build_min_interval_food_events(
            anchor=datetime(2026, 8, 31, 12, 25),
            remaining_meals=2,
            min_interval_minutes=135,
            last_meal_number=2,
            eating_minutes=10,
        )

        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events],
            [
                ("override-meal-3", "3 пп", "14:40"),
                ("override-meal-4", "4 пп", "17:05"),
            ],
        )
```

Update the existing `test_builds_meal_only_food_events_with_minimum_interval` expected values so the second and later meals include the eating window:

```python
        self.assertEqual(
            [(event.event_id, event.title, event.when.strftime("%H:%M")) for event in events],
            [
                ("override-meal-2", "2 пп", "15:27"),
                ("override-meal-3", "3 пп", "17:52"),
                ("override-meal-4", "4 пп", "20:17"),
                ("override-meal-5", "5 пп", "22:42"),
            ],
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests\test_overrides.py
```

Expected: failures show the previous implementation schedules repeated meals every `2:15` from the anchor instead of `10 minutes eating + 2:15 gap`.

- [ ] **Step 3: Implement eating-window-aware emergency meals**

Change `build_min_interval_food_events()` signature and loop in `src/day_notifier/overrides.py`:

```python
def build_min_interval_food_events(
    anchor: datetime,
    remaining_meals: int,
    min_interval_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    last_meal_number: int = 1,
    eating_minutes: int = 10,
) -> list[ScheduleEvent]:
    if remaining_meals < 1:
        raise ValueError("remaining meals must be at least 1")
    if min_interval_minutes < 1:
        raise ValueError("minimum interval must be at least 1 minute")
    if eating_minutes < 1:
        raise ValueError("eating window must be at least 1 minute")
    if last_meal_number < 0:
        raise ValueError("last meal number must be 0 or greater")

    anchor_minute = anchor.replace(second=0, microsecond=0)
    events: list[ScheduleEvent] = []
    for index in range(1, remaining_meals + 1):
        meal_number = last_meal_number + index
        first_gap = min_interval_minutes
        later_gap = min_interval_minutes + eating_minutes
        meal_at = anchor_minute + timedelta(minutes=first_gap + later_gap * (index - 1))
        events.append(
            ScheduleEvent(
                event_id=f"override-meal-{meal_number}",
                title=f"{meal_number} пп",
                message=(
                    f"Пересчитанный день: {meal_number} прием пищи. "
                    "Воду пить поверх приема и между приемами."
                ),
                when=meal_at,
            )
        )
    return events
```

Pass `eating_minutes` through `write_min_interval_food_override()`:

```python
def write_min_interval_food_override(
    override_dir: Path,
    anchor: datetime,
    remaining_meals: int,
    min_interval_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    last_meal_number: int = 1,
    eating_minutes: int = 10,
) -> list[ScheduleEvent]:
    events = build_min_interval_food_events(
        anchor=anchor,
        remaining_meals=remaining_meals,
        min_interval_minutes=min_interval_minutes,
        last_meal_number=last_meal_number,
        eating_minutes=eating_minutes,
    )
```

- [ ] **Step 4: Update formatting text**

Change `format_min_interval_food_events()` to make the semantics explicit:

```python
def format_min_interval_food_events(
    events: list[ScheduleEvent],
    min_interval_minutes: int,
    eating_minutes: int = 10,
) -> str:
    lines = [
        (
            f"Пересчитал питание: {_format_interval(min_interval_minutes)} "
            f"между концом еды и следующим приемом, окно еды {eating_minutes} мин:"
        )
    ]
    lines.extend(f"- {event.when:%H:%M} {event.title}" for event in events)
    return "\n".join(lines)
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m unittest tests\test_overrides.py
```

Expected: all override tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tests/test_overrides.py src/day_notifier/overrides.py
git commit -m "fix: include eating window in emergency meal gaps"
```

---

### Task 3: Shifted Day Override Generation

**Files:**
- Modify: `tests/test_overrides.py`
- Modify: `src/day_notifier/overrides.py`

- [ ] **Step 1: Write failing tests**

Add imports in `tests/test_overrides.py`:

```python
from day_notifier.overrides import (
    build_compressed_food_events,
    build_min_interval_food_events,
    build_shifted_day_override,
    write_compressed_food_override,
    write_min_interval_food_override,
    write_shifted_day_override,
)
```

Add this test:

```python
    def test_build_shifted_day_override_keeps_sleep_fixed_and_uses_emergency_meals(self):
        schedule_data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))

        data = build_shifted_day_override(
            schedule_data=schedule_data,
            day=datetime(2026, 8, 31).date(),
            start_time="10:00",
        )

        self.assertIn("water-food-cycle", data["suppress_cycles"])
        self.assertIn("wake-up", data["suppress_events"])
        self.assertIn("morning-block", data["suppress_events"])
        self.assertNotIn("bedtime", data["suppress_events"])
        self.assertEqual(
            [(event["id"], event["time"], event["title"]) for event in data["events"][:6]],
            [
                ("wake-up", "10:00", "Подъем"),
                ("meal-1", "10:00", "1 пп"),
                ("morning-block", "10:01", "Утренний блок: МП + кардио"),
                ("morning-cardio-tail", "10:08", "Кардио: закрепление состояния"),
                ("spirit-reset", "10:21", "Дух: добродетели + антируминация"),
                ("day-optimization", "10:40", "Оптимизация дня"),
            ],
        )
        self.assertIn(
            {"id": "meal-2", "time": "12:25", "title": "2 пп", "message": "2 прием пищи. Воду пить поверх приема и между приемами."},
            data["events"],
        )
        self.assertIn(
            {"id": "meal-3", "time": "14:50", "title": "3 пп", "message": "3 прием пищи. Воду пить поверх приема и между приемами."},
            data["events"],
        )
```

Add this write/load test:

```python
    def test_write_shifted_day_override_preserves_base_schedule_for_other_dates(self):
        schedule_data = json.loads((ROOT / "config" / "schedule.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            override_dir = Path(temp_dir) / "day_overrides"

            write_shifted_day_override(
                override_dir=override_dir,
                schedule_data=schedule_data,
                day=datetime(2026, 8, 31).date(),
                start_time="10:00",
            )

            loaded = load_day_overrides(override_dir)

        self.assertIn("2026-08-31", loaded)
        self.assertEqual(loaded["2026-08-31"]["events"][0]["time"], "10:00")
        self.assertIn("wake-up", loaded["2026-08-31"]["suppress_events"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests\test_overrides.py
```

Expected: import failure for `build_shifted_day_override` and `write_shifted_day_override`.

- [ ] **Step 3: Add constants and helpers**

In `src/day_notifier/overrides.py`, add:

```python
SHIFTED_DAY_EVENT_IDS = [
    "wake-up",
    "morning-block",
    "morning-cardio-tail",
    "spirit-reset",
    "day-optimization",
    "target-engineering-article",
    "microservices-reading",
    "monitoring-reading",
    "morning-buffer",
]

SHIFTED_DAY_BASE_EVENT_ID = "wake-up"
DEFAULT_EATING_WINDOW_MINUTES = 10
```

Add helper functions:

```python
def build_shifted_day_override(
    schedule_data: dict,
    day,
    start_time: str,
    meal_count: int = 4,
    min_meal_gap_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> dict:
    start_at = datetime.combine(day, _parse_time(start_time))
    base_events = {str(event["id"]): event for event in schedule_data.get("events", [])}
    if SHIFTED_DAY_BASE_EVENT_ID not in base_events:
        raise ValueError("base schedule has no wake-up event")

    base_start = datetime.combine(day, _parse_time(str(base_events[SHIFTED_DAY_BASE_EVENT_ID]["time"])))
    replacement_events = []

    for event_id in SHIFTED_DAY_EVENT_IDS:
        if event_id not in base_events:
            continue
        event = base_events[event_id]
        original_at = datetime.combine(day, _parse_time(str(event["time"])))
        shifted_at = start_at + (original_at - base_start)
        replacement_events.append(
            {
                "id": event_id,
                "time": shifted_at.strftime("%H:%M"),
                "title": str(event["title"]),
                "message": str(event.get("message", event["title"])),
            }
        )

    replacement_events.extend(
        _event_to_override_dict(event)
        for event in build_shift_start_meal_events(
            start_at=start_at,
            meal_count=meal_count,
            min_gap_minutes=min_meal_gap_minutes,
            eating_minutes=eating_minutes,
        )
    )

    return {
        "date": day.isoformat(),
        "suppress_cycles": [FOOD_CYCLE_ID],
        "suppress_events": SHIFTED_DAY_EVENT_IDS,
        "events": sorted(replacement_events, key=lambda event: event["time"]),
    }


def build_shift_start_meal_events(
    start_at: datetime,
    meal_count: int = 4,
    min_gap_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> list[ScheduleEvent]:
    if meal_count < 1:
        raise ValueError("meal count must be at least 1")
    if min_gap_minutes < 1:
        raise ValueError("minimum meal gap must be at least 1 minute")
    if eating_minutes < 1:
        raise ValueError("eating window must be at least 1 minute")

    start_minute = start_at.replace(second=0, microsecond=0)
    step_minutes = min_gap_minutes + eating_minutes
    events = []
    for index in range(meal_count):
        meal_number = index + 1
        meal_at = start_minute + timedelta(minutes=step_minutes * index)
        events.append(
            ScheduleEvent(
                event_id=f"meal-{meal_number}",
                title=f"{meal_number} пп",
                message=f"{meal_number} прием пищи. Воду пить поверх приема и между приемами.",
                when=meal_at,
            )
        )
    return events
```

- [ ] **Step 4: Add writer**

Add:

```python
def write_shifted_day_override(
    override_dir: Path,
    schedule_data: dict,
    day,
    start_time: str,
    meal_count: int = 4,
    min_meal_gap_minutes: int = DEFAULT_MIN_MEAL_INTERVAL_MINUTES,
    eating_minutes: int = DEFAULT_EATING_WINDOW_MINUTES,
) -> dict:
    data = build_shifted_day_override(
        schedule_data=schedule_data,
        day=day,
        start_time=start_time,
        meal_count=meal_count,
        min_meal_gap_minutes=min_meal_gap_minutes,
        eating_minutes=eating_minutes,
    )
    override_dir.mkdir(parents=True, exist_ok=True)
    path = override_dir / f"{day.isoformat()}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m unittest tests\test_overrides.py
```

Expected: all override tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tests/test_overrides.py src/day_notifier/overrides.py
git commit -m "feat: build shifted day overrides"
```

---

### Task 4: Telegram `/sd HH:MM` Command

**Files:**
- Modify: `tests/test_commands.py`
- Modify: `src/day_notifier/commands.py`

- [ ] **Step 1: Write failing command tests**

Add this test to `CommandTests`:

```python
    def test_shift_day_command_writes_override_and_reloads_schedule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            schedule_path = root / "schedule.json"
            schedule_path.write_text(
                json.dumps(
                    {
                        "events": [
                            {"id": "wake-up", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                            {"id": "morning-block", "time": "04:01", "title": "Утренний блок: МП + кардио", "message": "МП"},
                            {"id": "bedtime", "time": "22:00", "title": "Отбой", "message": "Сон"},
                        ],
                        "cycles": [
                            {
                                "id": "water-food-cycle",
                                "start_time": "07:00",
                                "period_minutes": 145,
                                "count": 4,
                                "items": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            context = self.make_context(root / "inbox.md")
            reload_calls = []
            context.override_dir = root / "day_overrides"
            context.schedule_path = schedule_path
            context.reload_schedule = lambda: reload_calls.append("reload")
            context.now = lambda: datetime(2026, 8, 31, 9, 0)

            result = handle_command("/sd 10:00", context)

            override_text = (context.override_dir / "2026-08-31.json").read_text(encoding="utf-8")
            data = json.loads(override_text)

        self.assertEqual(reload_calls, ["reload"])
        self.assertIn("Перенес день на 10:00", result.reply)
        self.assertIn("10:00 Подъем", result.reply)
        self.assertIn("12:25 2 пп", result.reply)
        self.assertIn("14:50 3 пп", result.reply)
        self.assertIn("water-food-cycle", data["suppress_cycles"])
        self.assertIn("wake-up", data["suppress_events"])
        self.assertNotIn("пв", override_text)
```

Add invalid input test:

```python
    def test_shift_day_command_rejects_invalid_time_without_writing_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            context = self.make_context(root / "inbox.md")
            context.override_dir = root / "day_overrides"
            context.schedule_path = root / "missing.json"
            context.now = lambda: datetime(2026, 8, 31, 9, 0)

            result = handle_command("/sd tomorrow", context)

        self.assertIn("Используй: /sd 10:00", result.reply)
        self.assertFalse((root / "day_overrides").exists())
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests\test_commands.py
```

Expected: failure because `CommandContext` has no `schedule_path` field and `/sd` is not implemented.

- [ ] **Step 3: Extend command context**

In `src/day_notifier/commands.py`, add `schedule_path`:

```python
@dataclass
class CommandContext:
    schedule: Schedule
    state: RuntimeState
    inbox_path: Path
    now: Callable[[], datetime]
    set_desktop_enabled: Callable[[bool], None] | None = None
    is_desktop_enabled: Callable[[], bool] | None = None
    override_dir: Path | None = None
    reload_schedule: Callable[[], None] | None = None
    schedule_path: Path | None = None
```

- [ ] **Step 4: Wire imports and command dispatch**

Change imports:

```python
import json
```

```python
from day_notifier.overrides import (
    format_min_interval_food_events,
    write_min_interval_food_override,
    write_shifted_day_override,
)
```

Add dispatch:

```python
    if command in {"/sd", "sd"}:
        return CommandResult(reply=_shift(argument, context))
```

Update the unknown-command reply to include `/sd 10:00`.

- [ ] **Step 5: Implement `_shift`**

Add:

```python
def _shift(argument: str, context: CommandContext) -> str:
    parts = argument.strip().split()
    if len(parts) != 1 or not _looks_like_time(parts[0]):
        return "Используй: /sd 10:00."
    if context.override_dir is None or context.schedule_path is None:
        return "Перенос дня недоступен в этом режиме."

    try:
        schedule_data = json.loads(context.schedule_path.read_text(encoding="utf-8"))
        data = write_shifted_day_override(
            override_dir=context.override_dir,
            schedule_data=schedule_data,
            day=context.now().date(),
            start_time=parts[0],
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return f"Не смог перенести день: {exc}"

    if context.reload_schedule is not None:
        context.reload_schedule()
    return _format_shifted_day_result(parts[0], data)
```

Add helpers:

```python
def _looks_like_time(value: str) -> bool:
    parts = value.split(":", 1)
    if len(parts) != 2:
        return False
    hour, minute = parts
    if not hour.isdigit() or not minute.isdigit():
        return False
    return 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59


def _format_shifted_day_result(start_time: str, data: dict) -> str:
    lines = [f"Перенес день на {start_time}.", "Сегодня:"]
    for event in data.get("events", [])[:10]:
        lines.append(f"- {event['time']} {event['title']}")
    return "\n".join(lines)
```

- [ ] **Step 6: Run command tests**

Run:

```powershell
python -m unittest tests\test_commands.py
```

Expected: all command tests pass.

- [ ] **Step 7: Commit**

```powershell
git add tests/test_commands.py src/day_notifier/commands.py
git commit -m "feat: add telegram day shift command"
```

---

### Task 5: Runtime Wiring and Local Smoke Command

**Files:**
- Modify: `tests/test_config_state_app.py`
- Modify: `src/day_notifier/app.py`
- Modify: `scripts/start-notifier.ps1`
- Modify: `README.md`

- [ ] **Step 1: Write failing app/context test**

Add imports in `tests/test_config_state_app.py`:

```python
import json

from day_notifier.telegram_client import TelegramCommand
```

Add this helper above `RecordingTelegram`:

```python
def write_project_files(root: Path) -> None:
    (root / "config").mkdir(parents=True)
    (root / "data").mkdir(parents=True)
    (root / "config" / "schedule.json").write_text(
        json.dumps(
            {
                "events": [
                    {"id": "wake-up", "time": "04:00", "title": "Подъем", "message": "Подъем"},
                    {"id": "morning-block", "time": "04:01", "title": "Утренний блок: МП + кардио", "message": "МП"},
                    {"id": "bedtime", "time": "22:00", "title": "Отбой", "message": "Сон"},
                ],
                "cycles": [
                    {
                        "id": "water-food-cycle",
                        "start_time": "07:00",
                        "period_minutes": 145,
                        "count": 4,
                        "items": [
                            {
                                "offset_minutes": 0,
                                "id_template": "water-{n}",
                                "title_template": "{n} пв",
                                "message_template": "{n} прием воды",
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
```

Update `RecordingTelegram` to accept commands:

Use this shape:

```python
class RecordingTelegram:
    def __init__(self, calls, commands=None):
        self.calls = calls
        self.commands = commands or []

    def send_message(self, text):
        self.calls.append(("telegram", text))

    def get_commands(self, offset=None):
        self.calls.append(("get_commands", offset))
        return self.commands
```

Add this test:

```python
    def test_process_telegram_shift_command_writes_day_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            app = NotifierApp(root)
            calls = []
            app.telegram = RecordingTelegram(
                calls,
                commands=[TelegramCommand(update_id=10, text="/sd 10:00")],
            )

            app.process_telegram_commands()

            override_files = list((root / "data" / "day_overrides").glob("*.json"))
            self.assertEqual(len(override_files), 1)
            override_text = override_files[0].read_text(encoding="utf-8")

        self.assertIn("Перенес день на 10:00", calls[-1][1])
        self.assertIn('"suppress_events"', override_text)
        self.assertNotIn("пв", override_text)
```

- [ ] **Step 2: Run focused app tests**

Run:

```powershell
python -m unittest tests\test_config_state_app.py
```

Expected: failure if `schedule_path` is not passed into `CommandContext`.

- [ ] **Step 3: Pass schedule path into command context**

In `src/day_notifier/app.py`, update `process_telegram_commands()`:

```python
        context = CommandContext(
            schedule=self.schedule,
            state=self.state,
            inbox_path=self.inbox_path,
            now=datetime.now,
            set_desktop_enabled=self.set_desktop_enabled,
            is_desktop_enabled=self.is_desktop_enabled,
            override_dir=self.override_dir,
            reload_schedule=self.reload_schedule,
            schedule_path=self.schedule_path,
        )
```

- [ ] **Step 4: Add optional CLI smoke support**

In `src/day_notifier/app.py`, add the JSON import:

```python
import json
```

In `src/day_notifier/app.py`, import the writer:

```python
from day_notifier.overrides import (
    format_min_interval_food_events,
    write_min_interval_food_override,
    write_shifted_day_override,
)
```

Add method:

```python
    def shift_day(self, start_time: str, now: datetime | None = None) -> str:
        current = now or datetime.now()
        schedule_data = json.loads(self.schedule_path.read_text(encoding="utf-8"))
        data = write_shifted_day_override(
            override_dir=self.override_dir,
            schedule_data=schedule_data,
            day=current.date(),
            start_time=start_time,
        )
        self.reload_schedule()
        lines = [f"Перенес день на {start_time}.", "Сегодня:"]
        lines.extend(f"- {event['time']} {event['title']}" for event in data.get("events", [])[:10])
        return "\n".join(lines)
```

Add CLI argument:

```python
    parser.add_argument("--shift-day", help="Create a one-day shifted schedule override, for example 10:00")
```

Add branch in `main()` before `--once`:

```python
    if args.shift_day:
        print(app.shift_day(args.shift_day))
        return 0
```

- [ ] **Step 5: Update PowerShell launcher**

In `scripts/start-notifier.ps1`, add parameter:

```powershell
    [string]$ShiftDay = "",
```

Add action before `$Once`:

```powershell
if ($ShiftDay) {
    & $PythonExe -m day_notifier --root $Root --shift-day $ShiftDay
    exit $LASTEXITCODE
}
```

- [ ] **Step 6: Update README**

Add this command documentation to `README.md`:

- Text: `Shift only today's day start without changing the base 04:00 schedule:`
- PowerShell example: `.\scripts\start-notifier.ps1 -ShiftDay 10:00`
- Telegram command bullet: ``/sd 10:00` - rebuild today's start-relative reminders from `10:00`; base flow stays unchanged for tomorrow.`

- [ ] **Step 7: Run tests**

Run:

```powershell
python -m unittest discover -s tests
python -m compileall src
```

Expected: all tests pass, compileall exits 0.

- [ ] **Step 8: Commit**

```powershell
git add tests/test_config_state_app.py src/day_notifier/app.py scripts/start-notifier.ps1 README.md
git commit -m "feat: wire day shift into runtime"
```

---

### Task 6: Local Runtime Verification

**Files:**
- No source changes expected.

- [ ] **Step 1: Run CLI smoke command**

Run in the private project:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-notifier.ps1 -ShiftDay 10:00
```

Expected output includes:

```text
Перенес день на 10:00.
Сегодня:
- 10:00 Подъем
- 10:00 1 пп
- 10:01 Утренний блок: МП + кардио
- 12:25 2 пп
- 14:50 3 пп
```

- [ ] **Step 2: Verify today's remaining schedule**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-notifier.ps1 -Today
```

Expected: today's remaining list comes from the one-day override; base `пв` events are suppressed for today only.

- [ ] **Step 3: Verify tomorrow still uses base flow**

Run:

```powershell
python -c "import json, pathlib, sys; from datetime import date; sys.path.insert(0, 'src'); from day_notifier.schedule import load_schedule; s=load_schedule(pathlib.Path('config/schedule.json'), pathlib.Path('data/day_overrides')); print([(e.event_id, e.when.strftime('%H:%M')) for e in s.events_for_date(date(2026, 9, 1)) if e.event_id.startswith(('water-', 'meal-'))])"
```

Expected:

```text
[('water-1', '07:00'), ('meal-1', '07:15'), ('water-2', '09:25'), ('meal-2', '09:40'), ('water-3', '11:50'), ('meal-3', '12:05'), ('water-4', '14:15'), ('meal-4', '14:30')]
```

- [ ] **Step 4: Restart notifier**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-notifier.ps1 -Restart
```

Expected: previous PID stops and a new Python PID starts.

- [ ] **Step 5: Final self-check**

Run:

```powershell
python -m unittest discover -s tests
python -m compileall src
git diff --check
rg -n "placeholder-marker|api\.telegram\.org/bot[0-9]|[0-9]{8,}:[A-Za-z0-9_-]{20,}" .
git status --short --branch --ignored
```

Expected:

- tests pass;
- compileall exits 0;
- `git diff --check` exits 0;
- secret scan returns no matches;
- only ignored runtime files remain untracked.

- [ ] **Step 6: Push final commits**

```powershell
git push
```

Expected: remote `main` advances to the final implementation commit.

---

## Self-Review

- Spec coverage: the plan covers Telegram command input, one-day override output, fixed-event suppression, baseline preservation, sleep anchors, emergency food water overlay, 10-minute eating windows, `2:15` after eating, bot feedback, invalid input, testing, local smoke, restart, and push.
- Placeholder scan: no placeholder markers remain.
- Type consistency: `suppress_events`, `write_shifted_day_override`, `build_shifted_day_override`, `build_shift_start_meal_events`, `schedule_path`, and `/sd HH:MM` are named consistently across tests and implementation steps.
