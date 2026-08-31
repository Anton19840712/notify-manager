# Telegram Chat Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `отбой` Telegram command that deletes tracked notifier chat messages and leaves the bot chat clean for the next day.

**Architecture:** Track Telegram `message_id` values in `data/state.json` whenever the app observes an incoming command or sends an outgoing message. Add Telegram client delete helpers, then route `/отбой` and `отбой` through command handling with a cleanup callback supplied by `NotifierApp`. Keep deletion best-effort because Telegram can reject old or already-deleted messages.

**Tech Stack:** Python standard library, `unittest`, Telegram Bot API `sendMessage`, `deleteMessages`, and `deleteMessage`, existing JSON state store.

---

## File Structure

- Modify `src/day_notifier/telegram_client.py`: return sent `message_id`, include incoming `message_id`, and add delete helpers with a small summary type.
- Modify `src/day_notifier/state.py`: store and cap tracked Telegram message ids.
- Modify `src/day_notifier/commands.py`: add `/отбой` and `отбой` command handling through a cleanup callback.
- Modify `src/day_notifier/app.py`: record incoming/outgoing message ids and implement the cleanup callback.
- Modify `README.md`: document the bedtime cleanup command and Telegram deletion limits.
- Modify tests:
  - `tests/test_telegram_client.py`
  - `tests/test_config_state_app.py`
  - `tests/test_commands.py`

---

### Task 1: Telegram Message Ids and Delete API

**Files:**
- Modify: `tests/test_telegram_client.py`
- Modify: `src/day_notifier/telegram_client.py`

- [ ] **Step 1: Write failing tests**

Add tests in `tests/test_telegram_client.py`:

```python
    def test_send_message_returns_message_id(self):
        calls = []

        def transport(url, payload):
            calls.append((url, json.loads(payload.decode("utf-8"))))
            return {"ok": True, "result": {"message_id": 42}}

        client = TelegramClient("token", "123", transport=transport)

        message_id = client.send_message("hello")

        self.assertEqual(message_id, 42)
        self.assertTrue(calls[0][0].endswith("/sendMessage"))

    def test_get_commands_includes_incoming_message_id_and_plain_bedtime_text(self):
        def transport(url, payload):
            return {
                "ok": True,
                "result": [
                    {
                        "update_id": 10,
                        "message": {
                            "message_id": 77,
                            "chat": {"id": 123},
                            "text": "отбой",
                        },
                    }
                ],
            }

        client = TelegramClient("token", "123", transport=transport)

        commands = client.get_commands()

        self.assertEqual(commands[0].update_id, 10)
        self.assertEqual(commands[0].message_id, 77)
        self.assertEqual(commands[0].text, "отбой")

    def test_delete_messages_uses_batch_api(self):
        calls = []

        def transport(url, payload):
            calls.append((url, json.loads(payload.decode("utf-8"))))
            return {"ok": True, "result": True}

        client = TelegramClient("token", "123", transport=transport)

        summary = client.delete_messages([1, 2, 3])

        self.assertEqual(summary.deleted, 3)
        self.assertEqual(summary.failed, 0)
        self.assertTrue(calls[0][0].endswith("/deleteMessages"))
        self.assertEqual(calls[0][1]["message_ids"], [1, 2, 3])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests\test_telegram_client.py
```

Expected: failures because `send_message()` returns `None`, `TelegramCommand` has no `message_id`, plain `отбой` is not accepted, and `delete_messages()` does not exist.

- [ ] **Step 3: Implement Telegram client changes**

In `src/day_notifier/telegram_client.py`, update data classes:

```python
@dataclass(frozen=True)
class TelegramCommand:
    update_id: int
    text: str
    message_id: int | None = None


@dataclass(frozen=True)
class DeleteSummary:
    deleted: int = 0
    failed: int = 0
```

Change `send_message`:

```python
    def send_message(self, text: str) -> int | None:
        response = self._call("sendMessage", {"chat_id": self.chat_id, "text": text})
        result = response.get("result") or {}
        message_id = result.get("message_id")
        return int(message_id) if message_id is not None else None
```

Change `get_commands` so it accepts slash commands and plain `отбой`:

```python
            if str(chat.get("id")) == self.chat_id and (text.startswith("/") or text.lower() == "отбой"):
                commands.append(
                    TelegramCommand(
                        update_id=int(item["update_id"]),
                        text=text,
                        message_id=int(message["message_id"]) if message.get("message_id") is not None else None,
                    )
                )
```

Add delete helper:

```python
    def delete_messages(self, message_ids: list[int]) -> DeleteSummary:
        unique_ids = list(dict.fromkeys(int(message_id) for message_id in message_ids))
        deleted = 0
        failed = 0
        for batch in _chunks(unique_ids, 100):
            try:
                self._call("deleteMessages", {"chat_id": self.chat_id, "message_ids": batch})
                deleted += len(batch)
            except Exception:
                for message_id in batch:
                    try:
                        self._call("deleteMessage", {"chat_id": self.chat_id, "message_id": message_id})
                        deleted += 1
                    except Exception:
                        failed += 1
        return DeleteSummary(deleted=deleted, failed=failed)
```

Add module helper:

```python
def _chunks(values: list[int], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest tests\test_telegram_client.py
```

Expected: all Telegram client tests pass.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_telegram_client.py src/day_notifier/telegram_client.py
git commit -m "feat: track telegram message ids"
```

---

### Task 2: State Store for Tracked Telegram Messages

**Files:**
- Modify: `tests/test_config_state_app.py`
- Modify: `src/day_notifier/state.py`

- [ ] **Step 1: Write failing tests**

Add tests to `ConfigStateAppTests`:

```python
    def test_state_tracks_telegram_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            state = JsonStateStore(path)

            state.track_telegram_message(10, "incoming", datetime(2026, 8, 31, 21, 0))
            state.track_telegram_message(11, "outgoing", datetime(2026, 8, 31, 21, 1))
            reloaded = JsonStateStore(path)

        self.assertEqual(
            reloaded.telegram_messages,
            [
                {"message_id": 10, "direction": "incoming", "at": "2026-08-31T21:00:00"},
                {"message_id": 11, "direction": "outgoing", "at": "2026-08-31T21:01:00"},
            ],
        )

    def test_state_clears_tracked_telegram_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            state = JsonStateStore(path)
            state.track_telegram_message(10, "incoming", datetime(2026, 8, 31, 21, 0))

            state.clear_telegram_messages()
            reloaded = JsonStateStore(path)

        self.assertEqual(reloaded.telegram_messages, [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests\test_config_state_app.py
```

Expected: failures because `telegram_messages`, `track_telegram_message()`, and `clear_telegram_messages()` do not exist.

- [ ] **Step 3: Implement state methods**

In `src/day_notifier/state.py`, add:

```python
TELEGRAM_MESSAGE_LIMIT = 500
```

Add property and methods to `JsonStateStore`:

```python
    @property
    def telegram_messages(self) -> list[dict[str, Any]]:
        return list(self._data.get("telegram_messages", []))

    def telegram_message_ids(self) -> list[int]:
        ids = []
        for item in self._data.get("telegram_messages", []):
            message_id = item.get("message_id")
            if message_id is not None:
                ids.append(int(message_id))
        return ids

    def track_telegram_message(self, message_id: int | None, direction: str, when: datetime | None = None) -> None:
        if message_id is None:
            return
        if direction not in {"incoming", "outgoing"}:
            raise ValueError("direction must be incoming or outgoing")
        item = {
            "message_id": int(message_id),
            "direction": direction,
            "at": (when or datetime.now()).isoformat(timespec="seconds"),
        }
        messages = self._data.setdefault("telegram_messages", [])
        messages.append(item)
        del messages[:-TELEGRAM_MESSAGE_LIMIT]
        self._save()

    def clear_telegram_messages(self) -> None:
        self._data["telegram_messages"] = []
        self._save()
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest tests\test_config_state_app.py
```

Expected: all config/state/app tests pass.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_config_state_app.py src/day_notifier/state.py
git commit -m "feat: store tracked telegram messages"
```

---

### Task 3: Bedtime Cleanup Command

**Files:**
- Modify: `tests/test_commands.py`
- Modify: `src/day_notifier/commands.py`

- [ ] **Step 1: Write failing tests**

Extend `CommandContext` tests by adding:

```python
    def test_bedtime_cleanup_command_uses_cleanup_callback(self):
        context = self.make_context()
        calls = []
        context.cleanup_telegram_chat = lambda: calls.append("cleanup") or "Отбой. Чат очищен: удалено 2, пропущено 0."

        result = handle_command("/отбой", context)

        self.assertEqual(calls, ["cleanup"])
        self.assertEqual(result.reply, "Отбой. Чат очищен: удалено 2, пропущено 0.")

    def test_plain_bedtime_cleanup_text_uses_cleanup_callback(self):
        context = self.make_context()
        context.cleanup_telegram_chat = lambda: "Отбой. Чат очищен: удалено 1, пропущено 0."

        result = handle_command("отбой", context)

        self.assertIn("Чат очищен", result.reply)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests\test_commands.py
```

Expected: failures because `CommandContext` has no cleanup callback and command dispatch does not handle `отбой`.

- [ ] **Step 3: Implement command callback**

In `src/day_notifier/commands.py`, add field:

```python
    cleanup_telegram_chat: Callable[[], str] | None = None
```

Add dispatch near the top of `handle_command()`:

```python
    if command in {"/отбой", "отбой"}:
        if context.cleanup_telegram_chat is None:
            return CommandResult(reply="Очистка Telegram-чата недоступна в этом режиме.")
        return CommandResult(reply=context.cleanup_telegram_chat())
```

Update unknown-command help to include `/отбой`.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest tests\test_commands.py
```

Expected: all command tests pass.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_commands.py src/day_notifier/commands.py
git commit -m "feat: add bedtime cleanup command"
```

---

### Task 4: Runtime Tracking and Cleanup

**Files:**
- Modify: `tests/test_config_state_app.py`
- Modify: `src/day_notifier/app.py`

- [ ] **Step 1: Write failing runtime tests**

Update `RecordingTelegram.send_message()` in `tests/test_config_state_app.py`:

```python
    def send_message(self, text):
        self.calls.append(("telegram", text))
        return 101 + len(self.calls)
```

Add method:

```python
    def delete_messages(self, message_ids):
        self.calls.append(("delete_messages", list(message_ids)))
        return DeleteSummary(deleted=len(message_ids), failed=0)
```

Import `DeleteSummary` from `day_notifier.telegram_client`.

Add tests:

```python
    def test_scheduled_notification_records_outgoing_telegram_message_id(self):
        calls = []
        app = NotifierApp.__new__(NotifierApp)
        app.telegram = RecordingTelegram(calls)
        app.desktop = RecordingDesktop(calls)
        app.state = JsonStateStore(Path(tempfile.mkdtemp()) / "state.json")
        event = ScheduleEvent("water-1", "1 пв", "Выпей воду", datetime(2026, 8, 30, 7, 0))

        app.notify(event)

        self.assertEqual(app.state.telegram_messages[0]["direction"], "outgoing")

    def test_process_telegram_records_incoming_and_reply_message_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_project_files(root)
            app = NotifierApp(root)
            app.telegram = RecordingTelegram(
                [],
                commands=[TelegramCommand(update_id=10, text="/next", message_id=77)],
            )

            app.process_telegram_commands()

        self.assertEqual([item["direction"] for item in app.state.telegram_messages], ["incoming", "outgoing"])

    def test_cleanup_telegram_chat_deletes_tracked_messages_and_tracks_confirmation(self):
        calls = []
        app = NotifierApp.__new__(NotifierApp)
        app.telegram = RecordingTelegram(calls)
        app.state = JsonStateStore(Path(tempfile.mkdtemp()) / "state.json")
        app.state.track_telegram_message(10, "incoming", datetime(2026, 8, 31, 21, 0))
        app.state.track_telegram_message(11, "outgoing", datetime(2026, 8, 31, 21, 1))

        result = app.cleanup_telegram_chat()

        self.assertIn("Отбой. Чат очищен", result)
        self.assertIn(("delete_messages", [10, 11]), calls)
        self.assertEqual(len(app.state.telegram_messages), 1)
        self.assertEqual(app.state.telegram_messages[0]["direction"], "outgoing")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests\test_config_state_app.py
```

Expected: failures because runtime code does not record message ids and `cleanup_telegram_chat()` does not exist.

- [ ] **Step 3: Implement outgoing tracking helper**

In `src/day_notifier/app.py`, add:

```python
    def send_telegram_message(self, text: str, track: bool = True) -> int | None:
        if self.telegram is None:
            return None
        message_id = self.telegram.send_message(text)
        if track:
            self.state.track_telegram_message(message_id, "outgoing")
        return message_id
```

Replace direct `self.telegram.send_message(...)` calls in `notify()`, `send_startup_summary()`, `send_test_notification()`, and `process_telegram_commands()` with this helper where state is available.

- [ ] **Step 4: Implement incoming tracking and callback wiring**

In `process_telegram_commands()`, add callback to `CommandContext`:

```python
            cleanup_telegram_chat=self.cleanup_telegram_chat,
```

Before handling each command:

```python
                self.state.track_telegram_message(command.message_id, "incoming")
```

- [ ] **Step 5: Implement cleanup runtime method**

Add:

```python
    def cleanup_telegram_chat(self) -> str:
        if self.telegram is None:
            return "Очистка Telegram-чата недоступна: Telegram выключен."
        message_ids = self.state.telegram_message_ids()
        if not message_ids:
            return "Отбой. Пока нечего очищать: бот еще не накопил отслеживаемые сообщения."
        summary = self.telegram.delete_messages(message_ids)
        self.state.clear_telegram_messages()
        text = f"Отбой. Чат очищен: удалено {summary.deleted}, пропущено {summary.failed}."
        self.send_telegram_message(text, track=True)
        return text
```

- [ ] **Step 6: Run focused tests**

Run:

```powershell
python -m unittest tests\test_config_state_app.py
```

Expected: all config/state/app tests pass.

- [ ] **Step 7: Commit**

```powershell
git add tests/test_config_state_app.py src/day_notifier/app.py
git commit -m "feat: clean telegram chat at bedtime"
```

---

### Task 5: Documentation and Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add Telegram command bullet:

```markdown
- `/отбой` or `отбой` - delete tracked bot-chat messages and leave one bedtime confirmation.
```

Add note near Telegram commands:

```markdown
Telegram cleanup can only delete messages whose `message_id` was tracked after this feature was enabled. Telegram may reject old messages outside its deletion window, and those are counted as skipped.
```

- [ ] **Step 2: Run full verification**

Run:

```powershell
python -m unittest discover -s tests
python -m compileall src
git diff --check
rg -n "TODO|FIXME|api\.telegram\.org/bot[0-9]|[0-9]{8,}:[A-Za-z0-9_-]{20,}" README.md data docs scripts src tests
```

Expected:

- all tests pass;
- compileall exits 0;
- `git diff --check` exits 0;
- secret scan returns no matches.

- [ ] **Step 3: Commit**

```powershell
git add README.md
git commit -m "docs: document telegram chat cleanup"
```

---

### Task 6: Private Project Sync and Runtime Smoke

**Files:**
- Sync all changed implementation files from the mirror to `C:\мое программное обеспечение\notify-manager`.

- [ ] **Step 1: Copy changed files to private project**

Copy:

```text
src/day_notifier/telegram_client.py
src/day_notifier/state.py
src/day_notifier/commands.py
src/day_notifier/app.py
tests/test_telegram_client.py
tests/test_config_state_app.py
tests/test_commands.py
README.md
docs/superpowers/plans/2026-08-31-telegram-chat-cleanup.md
```

- [ ] **Step 2: Run private verification**

Run in `C:\мое программное обеспечение\notify-manager`:

```powershell
python -m unittest discover -s tests
python -m compileall src
git diff --check
rg -n "TODO|FIXME|api\.telegram\.org/bot[0-9]|[0-9]{8,}:[A-Za-z0-9_-]{20,}" README.md data docs scripts src tests
git status --short --branch --ignored
```

Expected:

- tests pass;
- compileall exits 0;
- no diff whitespace errors;
- no secret matches;
- only ignored runtime files remain untracked besides intentional staged files.

- [ ] **Step 3: Commit and push private project**

```powershell
git add README.md docs/superpowers/plans/2026-08-31-telegram-chat-cleanup.md src/day_notifier/telegram_client.py src/day_notifier/state.py src/day_notifier/commands.py src/day_notifier/app.py tests/test_telegram_client.py tests/test_config_state_app.py tests/test_commands.py
git commit -m "feat: clean telegram chat at bedtime"
git push
```

- [ ] **Step 4: Restart live notifier**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-notifier.ps1 -Restart
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-notifier.ps1 -Status
```

Expected: the old Python process stops, a new process starts, and status reports the new PID.

- [ ] **Step 5: Safe runtime check**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-notifier.ps1 -Today
Get-Content -Tail 60 logs\notifier.err.log
```

Expected: schedule prints without changing today's override, and the error log has no traceback from startup.

Do not send a live `отбой` smoke command during implementation because it would delete the user's real Telegram chat. The unit tests cover deletion behavior using fake Telegram transport.

---

## Self-Review

- Spec coverage: the plan covers tracked message ids, incoming/outgoing directions, capped state, batch delete, per-message fallback, `/отбой`, plain `отбой`, final confirmation, Telegram-disabled behavior, README notes, private sync, push, and restart.
- Placeholder scan: no `TBD`, `TODO`, "implement later", or vague edge handling remains.
- Type consistency: `TelegramCommand.message_id`, `DeleteSummary`, `telegram_messages`, `track_telegram_message`, `clear_telegram_messages`, `telegram_message_ids`, and `cleanup_telegram_chat` are named consistently across tasks.
