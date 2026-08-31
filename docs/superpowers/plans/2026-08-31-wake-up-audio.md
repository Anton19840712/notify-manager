# Wake-Up Audio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Play `data/audio/morning-prayer.mp3` when the `wake-up` reminder is delivered.

**Architecture:** Add a small audio adapter that opens a local file for only the `wake-up` event. Wire it into `NotifierApp.notify()` before the usual Telegram and desktop notification path, while failures only log and do not block reminders.

**Tech Stack:** Python standard library, Windows default file opener, `unittest`.

---

## File Structure

- Create `day-notifier/src/day_notifier/audio.py`: local audio cue adapter with an injected opener for tests.
- Modify `day-notifier/src/day_notifier/app.py`: initialize the adapter and call it during scheduled notifications.
- Modify `day-notifier/tests/test_config_state_app.py`: app-level wake-up audio behavior.
- Create `day-notifier/tests/test_audio.py`: adapter behavior without opening a real player.
- Modify `day-notifier/README.md`: document the local MP3 path.
- Add `day-notifier/data/audio/morning-prayer.mp3`: attached audio asset.

---

### Task 1: Audio Adapter

**Files:**
- Create: `day-notifier/tests/test_audio.py`
- Create: `day-notifier/src/day_notifier/audio.py`

- [x] **Step 1: Write failing adapter tests**

Add tests for wake-up playback, non-wake-up no-op, and missing file no-op.

- [x] **Step 2: Run focused test**

Run `python -m unittest day-notifier\tests\test_audio.py`. Expected: import failure because `day_notifier.audio` does not exist.

- [x] **Step 3: Implement adapter**

Create `AudioCuePlayer` with `play_for_event(event)` and a default Windows opener based on `os.startfile`.

- [x] **Step 4: Run focused test**

Run `python -m unittest day-notifier\tests\test_audio.py`. Expected: all audio tests pass.

---

### Task 2: App Wiring

**Files:**
- Modify: `day-notifier/tests/test_config_state_app.py`
- Modify: `day-notifier/src/day_notifier/app.py`

- [x] **Step 1: Write failing app test**

Add an app-level test that a `wake-up` notification calls the audio adapter before marking the event notified.

- [x] **Step 2: Run focused app test**

Run `python -m unittest day-notifier\tests\test_config_state_app.py`. Expected: audio call is missing.

- [x] **Step 3: Wire adapter into app**

Initialize `self.audio = AudioCuePlayer(root)` in `NotifierApp.__init__()` and call `self.audio.play_for_event(event)` in `notify()`.

- [x] **Step 4: Run focused app test**

Run `python -m unittest day-notifier\tests\test_config_state_app.py`. Expected: app tests pass.

---

### Task 3: Asset, Docs, Verification, Rollout

**Files:**
- Modify: `day-notifier/README.md`
- Add: `day-notifier/data/audio/morning-prayer.mp3`
- Copy changed files to `C:\мое программное обеспечение\notify-manager`.

- [x] **Step 1: Copy MP3 asset**

Copy `C:\Users\MSI\Desktop\1-[AudioTrimmer.com]3x.mp3` to `day-notifier/data/audio/morning-prayer.mp3`.

- [x] **Step 2: Update README**

Document the local audio path and wake-up trigger.

- [x] **Step 3: Run full verification**

Run tests, compileall, diff check, TODO/FIXME scan, and secret scan.

- [ ] **Step 4: Commit, push, restart**

Commit mirror and private changes, push private `origin/main`, restart notifier, then check status and logs.

## Self-Review

- Spec coverage: covers local MP3 storage, wake-up-only trigger, shifted wake-up compatibility, missing-file behavior, and tests.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `AudioCuePlayer`, `play_for_event`, `wake-up`, and `data/audio/morning-prayer.mp3` are consistent.
