# Hourly Chrysostom Prayers Design

## Goal

Add hourly notifications with the first 16 prayers of Saint John Chrysostom from `05:00` through `20:00`.

## Source

Prayer texts are taken from the Orthodox prayer list commonly titled "Молитвы святого Иоанна Златоуста, по числу часов дня и ночи". The implementation uses the first 16 prayers in their listed order.

## Behavior

- Add fixed schedule events, not a repeating cycle.
- Times are clock-based: `05:00` is prayer 1, `06:00` is prayer 2, and so on through `20:00` as prayer 16.
- Use stable event ids: `chrysostom-prayer-01` through `chrysostom-prayer-16`.
- Use compact titles: `Молитва Иоанна Златоуста N/16`.
- Put the prayer text into the event message so Telegram, desktop, and watch notifications can display it.
- Keep existing work, learning, food, and sleep reminders unchanged.
- `/shift day` does not shift these prayers; they remain tied to the hour.

## Testing

Add a schedule test that loads `config/schedule.json`, extracts `chrysostom-prayer-*`, and verifies there are exactly 16 events at `05:00..20:00` with the expected first and last texts.
