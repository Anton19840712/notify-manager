from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Callable

from day_notifier.schedule import ScheduleEvent


WAKE_UP_EVENT_ID = "wake-up"
BEDTIME_EVENT_ID = "bedtime"
WAKE_UP_CUE_AUDIO_PATH = Path("data") / "audio" / "rota-podem.mp3"
MORNING_PRAYER_AUDIO_PATH = Path("data") / "audio" / "morning-prays.mp3"
BEDTIME_AUDIO_PATH = Path("data") / "audio" / "otboj.mp3"
WAKE_UP_CUE_DELAY_SECONDS = 2

OpenAudioFile = Callable[[Path], None]
Sleep = Callable[[int], None]
IsMorningPrayerEnabled = Callable[[], bool]


class AudioCuePlayer:
    def __init__(
        self,
        root: Path,
        audio_path: Path = MORNING_PRAYER_AUDIO_PATH,
        cue_audio_path: Path = WAKE_UP_CUE_AUDIO_PATH,
        bedtime_audio_path: Path = BEDTIME_AUDIO_PATH,
        cue_delay_seconds: int = WAKE_UP_CUE_DELAY_SECONDS,
        opener: OpenAudioFile | None = None,
        sleeper: Sleep | None = None,
        morning_prayer_enabled: IsMorningPrayerEnabled | None = None,
    ) -> None:
        self.prayer_path = root / audio_path
        self.cue_path = root / cue_audio_path
        self.bedtime_path = root / bedtime_audio_path
        self.cue_delay_seconds = cue_delay_seconds
        self._opener = opener or _open_audio_file
        self._sleeper = sleeper or time.sleep
        self._morning_prayer_enabled = morning_prayer_enabled or (lambda: True)

    def play_for_event(self, event: ScheduleEvent) -> bool:
        if event.event_id == BEDTIME_EVENT_ID:
            return self._open_if_available(self.bedtime_path, "Bedtime audio")
        if event.event_id != WAKE_UP_EVENT_ID:
            return False
        played_cue = self._open_if_available(self.cue_path, "Wake-up cue audio")
        if not self._morning_prayer_enabled():
            return played_cue
        if played_cue and self.cue_delay_seconds > 0:
            self._sleeper(self.cue_delay_seconds)
        played_prayer = self._open_if_available(self.prayer_path, "Wake-up prayer audio")
        return played_cue or played_prayer

    def _open_if_available(self, path: Path, label: str) -> bool:
        if not path.exists():
            logging.warning("%s file is missing: %s", label, path)
            return False
        try:
            self._opener(path)
        except Exception:
            logging.exception("%s playback failed: %s", label, path)
            return False
        return True


def _open_audio_file(path: Path) -> None:
    os.startfile(str(path))  # type: ignore[attr-defined]
