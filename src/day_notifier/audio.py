from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable

from day_notifier.schedule import ScheduleEvent


WAKE_UP_EVENT_ID = "wake-up"
MORNING_PRAYER_AUDIO_PATH = Path("data") / "audio" / "morning-prayer.mp3"

OpenAudioFile = Callable[[Path], None]


class AudioCuePlayer:
    def __init__(
        self,
        root: Path,
        audio_path: Path = MORNING_PRAYER_AUDIO_PATH,
        opener: OpenAudioFile | None = None,
    ) -> None:
        self.path = root / audio_path
        self._opener = opener or _open_audio_file

    def play_for_event(self, event: ScheduleEvent) -> bool:
        if event.event_id != WAKE_UP_EVENT_ID:
            return False
        if not self.path.exists():
            logging.warning("Wake-up audio file is missing: %s", self.path)
            return False
        try:
            self._opener(self.path)
        except Exception:
            logging.exception("Wake-up audio playback failed: %s", self.path)
            return False
        return True


def _open_audio_file(path: Path) -> None:
    os.startfile(str(path))  # type: ignore[attr-defined]
