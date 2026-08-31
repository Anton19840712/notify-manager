# Wake-Up Audio Design

## Goal

Play the attached local morning prayer MP3 on the PC when the notifier delivers the `wake-up` event.

## Scope

The MP3 is an asset only. It is not parsed for instructions. The notifier keeps using `config/schedule.json` as the source of schedule behavior.

## Behavior

- Store the file at `data/audio/morning-prayer.mp3`.
- When `NotifierApp.notify()` handles an event with `event_id == "wake-up"`, start the audio file through the local OS file opener.
- Keep Telegram and desktop notifications working the same way.
- If the file is missing or Windows cannot open it, log the failure and continue with the normal notification path.
- Shifted-day overrides keep working because they preserve the `wake-up` event id.

## Testing

Use an injected opener in tests so no real media player opens during the test suite. Verify:

- wake-up starts the configured MP3 before the event is marked notified;
- non-wake-up events do not start audio;
- a missing file returns `False` and does not raise.
