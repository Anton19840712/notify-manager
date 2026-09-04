from __future__ import annotations

import re

from day_notifier.schedule import ScheduleEvent


BEDTIME_EVENT_ID_PATTERN = re.compile(r"^bedtime(?:-snooze)*$", re.IGNORECASE)
BEDTIME_TITLE_PATTERN = re.compile(r"^отбой(?:\s+\+\d+\s+мин)*$", re.IGNORECASE)


def is_bedtime_event(event: ScheduleEvent) -> bool:
    return bool(
        BEDTIME_EVENT_ID_PATTERN.match(event.event_id.strip())
        or BEDTIME_TITLE_PATTERN.match(event.title.strip())
    )


def is_base_bedtime_event(event: ScheduleEvent) -> bool:
    return event.event_id.strip().lower() == "bedtime" or event.title.strip().lower() == "отбой"


def is_sleep_countdown_event(event: ScheduleEvent) -> bool:
    return "до сна" in event.title.strip().lower() and not is_bedtime_event(event)
