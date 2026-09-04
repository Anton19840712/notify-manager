from __future__ import annotations

import ctypes
import json
import platform
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from day_notifier.config import (
    DESKTOP_MODE_CARD,
    DESKTOP_MODE_MESSAGE_BOX,
    DESKTOP_MODE_OFF,
    normalize_desktop_mode,
)
from day_notifier.notification_view import NotificationViewModel


MessageBox = Callable[[str, str], None]
CardLauncher = Callable[[dict[str, Any]], bool]


class DesktopNotifier:
    def __init__(
        self,
        enabled: bool = True,
        mode: str = DESKTOP_MODE_MESSAGE_BOX,
        message_box: MessageBox | None = None,
        root: Path | None = None,
        action_queue_path: Path | None = None,
        card_launcher: CardLauncher | None = None,
    ) -> None:
        self.mode = normalize_desktop_mode(mode)
        self.enabled = enabled and self.mode != DESKTOP_MODE_OFF
        self.root = root or Path.cwd()
        self.action_queue_path = action_queue_path or (self.root / "data" / "desktop_actions.jsonl")
        self._message_box = message_box or _show_windows_message_box
        self._card_launcher = card_launcher or self._launch_card

    def show(self, title: str, message: str, blocking: bool = False) -> bool:
        if not self.enabled or self.mode == DESKTOP_MODE_OFF:
            return False
        if self.mode == DESKTOP_MODE_CARD and self._show_card_payload(
            {
                "title": title,
                "body": message,
                "status": "",
                "importance": "normal",
                "actions": [],
            }
        ):
            return True
        return self._show_message_box(title, message, blocking)

    def show_event(self, view_model: NotificationViewModel) -> bool:
        if not self.enabled or self.mode == DESKTOP_MODE_OFF:
            return False
        if self.mode == DESKTOP_MODE_CARD:
            payload = view_model.to_payload(str(self.action_queue_path))
            if self._show_card_payload(payload):
                return True
        return self._show_message_box(view_model.title, view_model.body, blocking=False)

    def configure(self, enabled: bool, mode: str | None = None) -> None:
        if mode is not None:
            self.mode = normalize_desktop_mode(mode)
        if not enabled:
            self.enabled = False
            self.mode = DESKTOP_MODE_OFF
            return
        self.enabled = True
        if self.mode == DESKTOP_MODE_OFF:
            self.mode = DESKTOP_MODE_MESSAGE_BOX

    def _show_message_box(self, title: str, message: str, blocking: bool = False) -> bool:
        if platform.system().lower() == "windows":
            if blocking:
                self._message_box(title, message)
                return True
            thread = threading.Thread(target=self._message_box, args=(title, message), daemon=False)
            thread.start()
            return True
        print(f"{title}: {message}")
        return True

    def _show_card_payload(self, payload: dict[str, Any]) -> bool:
        try:
            return self._card_launcher(payload)
        except Exception:
            return False

    def _launch_card(self, payload: dict[str, Any]) -> bool:
        if not _tkinter_available():
            return False
        payload_dir = self.root / "data" / "desktop_cards"
        payload_dir.mkdir(parents=True, exist_ok=True)
        payload_path = payload_dir / f"{uuid.uuid4().hex}.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        kwargs: dict[str, Any] = {
            "cwd": str(self.root),
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if platform.system().lower() == "windows":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            [sys.executable, "-m", "day_notifier.desktop_card", "--payload", str(payload_path)],
            **kwargs,
        )
        return True


def _show_windows_message_box(title: str, message: str) -> None:
    flags = 0x00001000 | 0x00010000 | 0x00040000
    ctypes.windll.user32.MessageBoxW(None, message, title, flags)


def _tkinter_available() -> bool:
    try:
        __import__("tkinter")
    except Exception:
        return False
    return True
