from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from day_notifier.desktop_card_themes import DEFAULT_DESKTOP_CARD_THEME, normalize_desktop_card_theme


DESKTOP_MODE_MESSAGE_BOX = "message_box"
DESKTOP_MODE_CARD = "card"
DESKTOP_MODE_OFF = "off"
DESKTOP_MODES = {DESKTOP_MODE_MESSAGE_BOX, DESKTOP_MODE_CARD, DESKTOP_MODE_OFF}
DESKTOP_MODE_ALIASES = {
    "message_box": DESKTOP_MODE_MESSAGE_BOX,
    "message-box": DESKTOP_MODE_MESSAGE_BOX,
    "messagebox": DESKTOP_MODE_MESSAGE_BOX,
    "msgbox": DESKTOP_MODE_MESSAGE_BOX,
    "box": DESKTOP_MODE_MESSAGE_BOX,
    "card": DESKTOP_MODE_CARD,
    "cards": DESKTOP_MODE_CARD,
    "off": DESKTOP_MODE_OFF,
}


@dataclass(frozen=True)
class Settings:
    bot_token: str | None = None
    chat_id: str | None = None
    check_interval_seconds: int = 15
    missed_event_grace_minutes: int = 5
    telegram_poll_seconds: int = 5
    desktop_enabled: bool = True
    desktop_mode: str = DESKTOP_MODE_MESSAGE_BOX
    desktop_card_theme: str = DEFAULT_DESKTOP_CARD_THEME
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
    legacy_enabled = bool(data.get("desktop_enabled", True))
    if not legacy_enabled:
        desktop_mode = DESKTOP_MODE_OFF
    elif "desktop_mode" in data:
        desktop_mode = normalize_desktop_mode(data.get("desktop_mode"))
    else:
        desktop_mode = DESKTOP_MODE_MESSAGE_BOX

    return Settings(
        bot_token=str(bot_token) if bot_token else None,
        chat_id=str(chat_id) if chat_id else None,
        check_interval_seconds=int(data.get("check_interval_seconds", 15)),
        missed_event_grace_minutes=int(data.get("missed_event_grace_minutes", 5)),
        telegram_poll_seconds=int(data.get("telegram_poll_seconds", 5)),
        desktop_enabled=desktop_mode != DESKTOP_MODE_OFF,
        desktop_mode=desktop_mode,
        desktop_card_theme=normalize_desktop_card_theme(data.get("desktop_card_theme")),
        startup_summary_enabled=bool(data.get("startup_summary_enabled", True)),
    )


def set_desktop_enabled(path: Path, enabled: bool) -> Settings:
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    data["desktop_enabled"] = enabled
    if enabled:
        current_mode = _safe_desktop_mode(data.get("desktop_mode"))
        data["desktop_mode"] = DESKTOP_MODE_MESSAGE_BOX if current_mode == DESKTOP_MODE_OFF else current_mode
    else:
        data["desktop_mode"] = DESKTOP_MODE_OFF
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return load_settings(path)


def set_desktop_mode(path: Path, mode: str) -> Settings:
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    desktop_mode = normalize_desktop_mode(mode)
    data["desktop_mode"] = desktop_mode
    data["desktop_enabled"] = desktop_mode != DESKTOP_MODE_OFF
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return load_settings(path)


def normalize_desktop_mode(value: Any) -> str:
    if value is None:
        return DESKTOP_MODE_MESSAGE_BOX
    raw = str(value).strip().lower()
    if raw in DESKTOP_MODES:
        return raw
    normalized = raw.replace(" ", "_")
    if normalized in DESKTOP_MODE_ALIASES:
        return DESKTOP_MODE_ALIASES[normalized]
    dashed = normalized.replace("_", "-")
    if dashed in DESKTOP_MODE_ALIASES:
        return DESKTOP_MODE_ALIASES[dashed]
    raise ValueError("desktop_mode must be one of: message_box, card, off")


def _safe_desktop_mode(value: Any) -> str:
    try:
        return normalize_desktop_mode(value)
    except ValueError:
        return DESKTOP_MODE_MESSAGE_BOX
