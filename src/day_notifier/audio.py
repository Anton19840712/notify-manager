from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

from day_notifier.event_kinds import is_bedtime_event
from day_notifier.meal_voice import load_active_meal_voice_profile
from day_notifier.schedule import ScheduleEvent


WAKE_UP_EVENT_ID = "wake-up"
WAKE_UP_CUE_AUDIO_PATH = Path("data") / "audio" / "rota-podem.mp3"
MORNING_PRAYER_AUDIO_PATH = Path("data") / "audio" / "morning-prays.mp3"
BEDTIME_AUDIO_PATH = Path("data") / "audio" / "otboj.mp3"
MEAL_VOICE_DIR = Path("data") / "audio" / "meal_voices"
MEAL_VOICE_STATE_PATH = Path("data") / "audio" / "meal_voice_state.json"
WAKE_UP_CUE_DELAY_SECONDS = 2
WINDOWS_AUDIO_TIMEOUT_MINUTES = 15
MEAL_EVENT_ID_PATTERN = re.compile(r"^(?:override-)?meal-(\d+)$", re.IGNORECASE)
MEAL_TITLE_PATTERN = re.compile(r"^(\d+)\s*пп$", re.IGNORECASE)

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
        meal_voice_dir: Path = MEAL_VOICE_DIR,
        meal_voice_state_path: Path = MEAL_VOICE_STATE_PATH,
        cue_delay_seconds: int = WAKE_UP_CUE_DELAY_SECONDS,
        opener: OpenAudioFile | None = None,
        sleeper: Sleep | None = None,
        morning_prayer_enabled: IsMorningPrayerEnabled | None = None,
    ) -> None:
        self.prayer_path = root / audio_path
        self.audio_root = self.prayer_path.parent
        self.cue_path = root / cue_audio_path
        self.bedtime_path = root / bedtime_audio_path
        self.meal_voice_dir = root / meal_voice_dir
        self.meal_voice_state_path = root / meal_voice_state_path
        self.cue_delay_seconds = cue_delay_seconds
        self._opener = opener or _open_audio_file
        self._sleeper = sleeper or time.sleep
        self._morning_prayer_enabled = morning_prayer_enabled or (lambda: True)

    def play_for_event(self, event: ScheduleEvent) -> bool:
        if is_bedtime_event(event):
            return self._open_if_available(self.bedtime_path, "Bedtime audio")
        meal_number = _meal_number(event)
        if meal_number is not None:
            return self._open_if_available(
                self._meal_path(meal_number),
                f"Meal {meal_number} audio",
            )
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

    def _meal_path(self, meal_number: int) -> Path:
        active_profile = load_active_meal_voice_profile(self.meal_voice_state_path)
        filename = f"meal-{meal_number}"
        candidates = [
            self.meal_voice_dir / active_profile / f"{filename}.mp3",
            self.meal_voice_dir / active_profile / f"{filename}.wav",
            self.audio_root / f"{filename}.mp3",
            self.audio_root / f"{filename}.wav",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[-1]


def _open_audio_file(path: Path) -> None:
    if os.name == "nt":
        _open_windows_audio_file(path)
        return
    _open_default_audio_file(path)


def _open_windows_audio_file(path: Path) -> None:
    script = _windows_media_player_script(path.resolve().as_uri())
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-STA",
            "-Command",
            script,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _windows_media_player_script(audio_uri: str) -> str:
    audio_uri_literal = json.dumps(audio_uri, ensure_ascii=False)
    return "\n".join(
        [
            "$ErrorActionPreference = 'Stop'",
            "Add-Type -AssemblyName PresentationCore",
            "$done = $false",
            "$player = [System.Windows.Media.MediaPlayer]::new()",
            "$player.add_MediaEnded({ $script:done = $true })",
            "$player.add_MediaFailed({ $script:done = $true })",
            f"$player.Open([System.Uri]{audio_uri_literal})",
            "$player.Play()",
            f"$deadline = (Get-Date).AddMinutes({WINDOWS_AUDIO_TIMEOUT_MINUTES})",
            "while (-not $done -and (Get-Date) -lt $deadline) {",
            "    Start-Sleep -Milliseconds 100",
            "}",
            "$player.Stop()",
            "$player.Close()",
        ]
    )


def _open_default_audio_file(path: Path) -> None:
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen(
        [opener, str(path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _meal_number(event: ScheduleEvent) -> int | None:
    event_id_match = MEAL_EVENT_ID_PATTERN.match(event.event_id)
    if event_id_match:
        return int(event_id_match.group(1))
    title_match = MEAL_TITLE_PATTERN.match(event.title.strip())
    return int(title_match.group(1)) if title_match else None
