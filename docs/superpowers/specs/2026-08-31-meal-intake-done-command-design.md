# Meal Intake Done Command Design

## Goal

Let the user tell the notifier that a meal was finished earlier or later than planned, then recalculate only the remaining meal notifications for today.

## Command

Support these command forms:

```text
2 mi done
2 pp done
2 пп done
/mi 2 done
```

`mi` means meal intake for the command language, but user-facing replies should use `пп`.

## Semantics

`2 mi done` means: "the second meal has just been completed at the current time."

The notifier should calculate the remaining meals from the currently active schedule for today. If the active day contains meals 1-4 and the user sends `2 mi done`, the notifier creates reminders for meals 3 and 4.

Timing:

```text
next meal start = command time + 2:15
later meal starts = previous meal start + 10 minutes eating + 2:15
```

Example for command time `12:25`:

```text
Принял: 2 пп завершен в 12:25.
Пересчитал остаток:
- 14:40 3 пп
- 17:05 4 пп
```

This works both forward and backward versus the base flow. If no meal-done command is sent, the base flow remains unchanged.

## Override Behavior

The command writes today's one-day override in `data/day_overrides/YYYY-MM-DD.json`.

It should:

- suppress the base `water-food-cycle` for today;
- replace today's food/water override events with recalculated meal-only events;
- preserve non-food override events, such as shifted morning reminders from `/shift day 10:00`;
- preserve `suppress_events` if they already exist;
- keep tomorrow and later days on the base schedule.

## Telegram Input

The Telegram polling path should accept plain `2 mi done`, not only slash commands. It should still ignore unrelated plain text.

## Error Handling

Invalid meal numbers return a usage hint and do not write override files.

If the meal number is the last known meal for the active day, the command suppresses the remaining base food cycle and replies that no further meal reminders are needed today.

## Testing

Add tests before implementation:

- command parsing for `2 mi done`, `2 pp done`, `2 пп done`, and `/mi 2 done`;
- command writes today's override with `14:40 3 пп` and `17:05 4 пп` for `12:25`;
- no separate `пв` reminders are created;
- shifted non-food override events are preserved;
- Telegram client accepts plain meal-done commands but still ignores unrelated plain text.
