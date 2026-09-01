# Telegram Day Shift Design

## Goal

Let the user send a Telegram command to the already-running local notifier process when the day starts late. The command recalculates only today's reminders through a one-day override. The base `04:00` schedule remains unchanged for tomorrow and later days.

## Command

Start with one explicit command:

```text
/sd 10:00
```

The plain text form `sd 10:00` is accepted as the same command. The command means: "for today, rebuild start-of-day events as if the day began at 10:00."

## One-Day Override Model

The command writes `data/day_overrides/YYYY-MM-DD.json`, the same local ignored directory already used for emergency food recalculation.

The override needs to support:

- `suppress_cycles`: existing list for suppressing the base food/water cycle.
- `suppress_events`: new list of fixed event ids to suppress only for that date.
- `events`: replacement events for the shifted day.

This keeps `config/schedule.json` as the permanent baseline and makes every late-start day an explicit exception.

## Shifted Events

The shifted day should include start-relative events:

- wake-up;
- morning prayer/cardio block;
- cardio tail;
- spirit reset and anti-rumination;
- day optimization;
- engineering article;
- microservices reading;
- monitoring reading;
- morning buffer.

Sleep anchors stay fixed at their base times:

- `21:00` one hour before sleep;
- `21:45` fifteen minutes before sleep;
- `21:59` one minute before sleep;
- `22:00` bedtime.

Reason: late start should not push sleep into the next night by default.

## Emergency Food Flow

When the day is shifted, food switches to emergency flow for that date:

- no separate `пв` notifications;
- water is layered onto meals and between meals;
- each meal has a 10-minute eating window;
- the minimum gap is 2 hours 15 minutes between the end of one eating window and the start of the next meal.

Formula:

```text
next meal start = previous meal start + 10 minutes eating + 2 hours 15 minutes gap
```

So the step between meal starts is 2 hours 25 minutes.

Example:

```text
10:00-10:10  1 пп
12:25-12:35  2 пп
14:50-15:00  3 пп
17:15-17:25  4 пп
```

If the user has already eaten some meals, that remains a separate emergency food command such as `/recalc food 2 ...`, not part of the first `/sd` MVP.

## Telegram Feedback

After applying the override, the bot replies with a compact confirmation:

```text
Перенес день на 10:00.
Сегодня:
- 10:00 Подъем
- 10:01 Утренний блок: МП + кардио
- ...
- 12:25 2 пп
- 14:50 3 пп
- 17:15 4 пп
```

The running process reloads the schedule immediately through the existing `reload_schedule` callback.

## Error Handling

Invalid times return a human-readable Telegram reply and do not modify the override file.

If `override_dir` is unavailable, the command returns that shifting is unavailable in the current mode.

If shifted events would collide with fixed sleep anchors, the MVP still creates them and shows the resulting order in the reply. Later we can add a stricter policy such as trimming optional learning blocks.

## Testing

Add tests before implementation:

- schedule overrides can suppress fixed events through `suppress_events`;
- shift override generation preserves base schedule for other dates;
- emergency meal starts use `10 minutes + 2:15`, not `2:15` between starts;
- `/sd 10:00` writes today's override, reloads the schedule, and replies with the recalculated events;
- invalid `/sd` input does not write files.
