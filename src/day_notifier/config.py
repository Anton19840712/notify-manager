from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    bot_token: str | None = None
    chat_id: str | None = None
    check_interval_seconds: int = 15
    missed_event_grace_minutes: int = 5
    telegram_poll_seconds: int = 5
    desktop_enabled: bool = True
    startup_summary_enabled: bool = True

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)


def load_settings(path: Path) -> Settings:
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))

    bot_token = data.get("bot_token") or os.environ.get("DAY_NOTIFIER_BOT_TOKEN")
    chat_id = data.get("chat_id") or os.environ.get("DAY_NOTIFIER_CHAT_ID")

    return Settings(
        bot_token=str(bot_token) if bot_token else None,
        chat_id=str(chat_id) if chat_id else None,
        check_interval_seconds=int(data.get("check_interval_seconds", 15)),
        missed_event_grace_minutes=int(data.get("missed_event_grace_minutes", 5)),
        telegram_poll_seconds=int(data.get("telegram_poll_seconds", 5)),
        desktop_enabled=bool(data.get("desktop_enabled", True)),
        startup_summary_enabled=bool(data.get("startup_summary_enabled", True)),
    )
