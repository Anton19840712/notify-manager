# Meal Voice Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Telegram-controlled meal voice profiles for all selected male and female meal cue variants.

**Architecture:** Add a small profile registry and runtime state file, then route audio playback through the selected profile directory with legacy fallback. Keep Telegram command parsing thin by delegating status and switching to application callbacks.

**Tech Stack:** Python stdlib, unittest, existing notify-manager Telegram command pipeline, MP3 assets generated with edge-tts.

---

### Task 1: Profile State Tests

**Files:**
- Create: `day-notifier/tests/test_meal_voice.py`
- Create: `day-notifier/src/day_notifier/meal_voice.py`

- [ ] **Step 1: Write failing tests**

```python
def test_default_profile_is_commander_when_state_file_is_missing():
    assert load_active_meal_voice_profile(path) == "male_commander"

def test_switches_profile_by_number_and_writes_state():
    result = set_meal_voice_profile(path, "3")
    assert "female_sonia" in result
    assert load_active_meal_voice_profile(path) == "female_sonia"
```

- [ ] **Step 2: Run `python -m unittest tests.test_meal_voice -v` and confirm import/function failures.**

- [ ] **Step 3: Implement `meal_voice.py` with profile constants, JSON state loading, aliases, status formatting, and switching.**

- [ ] **Step 4: Rerun `python -m unittest tests.test_meal_voice -v` and confirm all tests pass.**

### Task 2: Command And App Wiring

**Files:**
- Modify: `day-notifier/tests/test_commands.py`
- Modify: `day-notifier/tests/test_config_state_app.py`
- Modify: `day-notifier/tests/test_bot_commands.py`
- Modify: `day-notifier/src/day_notifier/commands.py`
- Modify: `day-notifier/src/day_notifier/app.py`
- Modify: `day-notifier/src/day_notifier/bot_commands.py`

- [ ] **Step 1: Write failing tests for `/mv`, `/meal_voice 3`, BotFather payload, and app-level Telegram processing.**

- [ ] **Step 2: Run focused tests and confirm failures are caused by missing command wiring.**

- [ ] **Step 3: Add command callbacks to `CommandContext`, route `/mv` and `/meal_voice`, expose `/mv` in BotFather registry, and add `NotifierApp` methods for status and switching.**

- [ ] **Step 4: Rerun focused tests and confirm they pass.**

### Task 3: Audio Profile Resolution

**Files:**
- Modify: `day-notifier/tests/test_audio.py`
- Modify: `day-notifier/src/day_notifier/audio.py`

- [ ] **Step 1: Write failing tests for profile directory playback and root-file fallback.**

- [ ] **Step 2: Run `python -m unittest tests.test_audio -v` and confirm the profile test fails.**

- [ ] **Step 3: Update `AudioCuePlayer._meal_path` to read the active profile and prefer `data/audio/meal_voices/<profile>/meal-N.mp3`.**

- [ ] **Step 4: Rerun audio tests and confirm they pass.**

### Task 4: Assets, Docs, Verification, Deploy

**Files:**
- Modify: `.gitignore`
- Modify: `day-notifier/README.md`
- Create: `day-notifier/data/audio/meal_voices/*/meal-*.mp3`

- [ ] **Step 1: Add `day-notifier/data/audio/meal_voice_state.json` to gitignore.**

- [ ] **Step 2: Generate all seven profile packs with `meal-1.mp3` through `meal-5.mp3`.**

- [ ] **Step 3: Update README command docs for `/mv`.**

- [ ] **Step 4: Run full unittest suite and compileall.**

- [ ] **Step 5: Sync live repo, run live tests, sync Telegram menu, restart notifier, commit, and push.**
