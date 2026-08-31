# Wake-Up Audio Sequence Design

## Goal

Before the existing `04:00` morning prayer audio starts, play `rota-podem.mp3`, wait two seconds, then start `morning-prayer.mp3`.

## Scope

`rota-podem.mp3` is an audio asset only. It is not parsed for instructions. This sequence belongs only to the `wake-up` event and does not apply to hourly Saint John Chrysostom prayer notifications.

## Behavior

- Store the cue file at `data/audio/rota-podem.mp3`.
- Keep the prayer file at `data/audio/morning-prayer.mp3`.
- On `event_id == "wake-up"`, open `rota-podem.mp3`, wait `2` seconds, then open `morning-prayer.mp3`.
- If the cue file is missing or cannot be opened, log the problem and still try to open `morning-prayer.mp3`.
- If the morning prayer file is missing or cannot be opened, log the problem and continue Telegram/desktop notification delivery.
- Non-`wake-up` events do not open either audio file.

## Testing

Use injected opener and sleeper functions so tests do not launch a real media player or actually wait two seconds. Verify the exact order: cue, sleep, morning prayer.
