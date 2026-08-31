# Wake-Up Audio Sequence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Play `data/audio/rota-podem.mp3` two seconds before `data/audio/morning-prays.mp3` on the `04:00` wake-up event.

**Architecture:** Extend `AudioCuePlayer` with a wake-up cue path and injected sleeper. Keep `NotifierApp.notify()` unchanged except for using the existing audio adapter call, so Telegram and desktop behavior remain centralized.

**Tech Stack:** Python standard library, Windows default file opener, `unittest`, local MP3 assets.

---

## File Structure

- Modify `day-notifier/src/day_notifier/audio.py`: add cue path, delay, and per-file tolerant open behavior.
- Modify `day-notifier/tests/test_audio.py`: assert cue -> sleep -> prayer ordering and missing-cue fallback.
- Modify `day-notifier/README.md`: document the wake-up audio sequence.
- Add `day-notifier/data/audio/rota-podem.mp3`: attached cue asset.

---

### Task 1: Audio Sequence Tests

**Files:**
- Modify: `day-notifier/tests/test_audio.py`

- [x] **Step 1: Write failing sequence test**

Assert that a `wake-up` event opens `rota-podem.mp3`, sleeps for 2 seconds, then opens `morning-prays.mp3`.

- [x] **Step 2: Write fallback test**

Assert that a missing cue logs a warning but still opens `morning-prays.mp3`.

- [x] **Step 3: Run focused test**

Run `python -m unittest day-notifier\tests\test_audio.py`. Expected: failure because `AudioCuePlayer` does not support a cue file or injected sleeper yet.

---

### Task 2: Audio Sequence Implementation

**Files:**
- Modify: `day-notifier/src/day_notifier/audio.py`

- [x] **Step 1: Implement sequence**

Add `WAKE_UP_CUE_AUDIO_PATH`, `WAKE_UP_CUE_DELAY_SECONDS`, `cue_audio_path`, and `sleeper`. Play cue first, sleep only after a successful cue open, then play morning prayer.

- [x] **Step 2: Run focused test**

Run `python -m unittest day-notifier\tests\test_audio.py`. Expected: all audio tests pass.

---

### Task 3: Asset, Docs, Verification, Rollout

**Files:**
- Modify: `day-notifier/README.md`
- Add: `day-notifier/data/audio/rota-podem.mp3`
- Copy changed files to `C:\мое программное обеспечение\notify-manager`.

- [x] **Step 1: Copy cue asset**

Copy `C:\Users\MSI\Desktop\rota-podem.mp3` to `day-notifier/data/audio/rota-podem.mp3`.

- [x] **Step 2: Update README**

Document the wake-up sequence: cue, two-second pause, morning prayer.

- [x] **Step 3: Run full mirror verification**

Run tests, compileall, diff check, placeholder scan, and secret scan.

- [x] **Step 4: Copy to private project**

Copy audio code, tests, README, MP3 asset, spec, and plan to the private project.

- [x] **Step 5: Run private verification**

Run tests, compileall, diff check, placeholder scan, secret scan, and `-Today` in `C:\мое программное обеспечение\notify-manager`.

- [x] **Step 6: Commit, push, restart**

Commit mirror and private changes, push private `origin/main`, restart notifier, then check status and logs.

## Self-Review

- Spec coverage: covers cue file, two-second delay, morning prayer fallback, non-wake-up no-op, local assets, tests, sync, push, and restart.
- Placeholder scan: no unfinished placeholders remain.
- Type consistency: `rota-podem.mp3`, `morning-prays.mp3`, `WAKE_UP_CUE_DELAY_SECONDS`, and `wake-up` are consistent.
