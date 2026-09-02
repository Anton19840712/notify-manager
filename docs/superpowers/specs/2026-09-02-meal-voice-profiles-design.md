# Meal Voice Profiles Design

## Goal

Let Anton switch meal notification voice cues from Telegram without replacing audio files or restarting notify-manager.

## User Flow

- `/mv` shows the active meal voice and all available profiles.
- `/mv 3` switches by phone-friendly number.
- `/mv female_sonia` switches by stable profile id.
- The next `meal-N` or `override-meal-N` notification plays `data/audio/meal_voices/<profile>/meal-N.mp3`.

## Profiles

The first two profiles are the two male variants already sampled, followed by the five female variants:

1. `male_jarvis`
2. `male_commander`
3. `female_sonia`
4. `female_libby`
5. `female_ava`
6. `female_aria`
7. `female_svetlana`

`male_commander` remains the default when no state file exists.

## Data And Runtime State

Audio packs live under `data/audio/meal_voices/<profile>/meal-1.mp3` through `meal-5.mp3`. The active profile is runtime state in `data/audio/meal_voice_state.json` and is ignored by git.

If the active profile file is missing, playback falls back to the legacy root files `data/audio/meal-N.mp3` or `meal-N.wav`.

## Components

- `meal_voice.py`: profile registry, state reading/writing, status text.
- `audio.py`: resolve meal cue path from the active profile with legacy fallback.
- `commands.py`: route `/mv` and `/meal_voice`.
- `bot_commands.py`: expose `/mv` in Telegram menu and help text.
- `app.py`: pass Telegram commands to the profile state manager.

## Testing

Focused tests cover default profile selection, switching by id and number, invalid profile feedback, command routing, audio profile path resolution, legacy fallback, and Telegram processing.
