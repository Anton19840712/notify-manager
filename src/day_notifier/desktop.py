from __future__ import annotations

import ctypes
import platform
import threading
from typing import Callable


MessageBox = Callable[[str, str], None]


class DesktopNotifier:
    def __init__(self, enabled: bool = True, message_box: MessageBox | None = None) -> None:
        self.enabled = enabled
        self._message_box = message_box or _show_windows_message_box

    def show(self, title: str, message: str, blocking: bool = False) -> bool:
        if not self.enabled:
            return False
        if platform.system().lower() == "windows":
            if blocking:
                self._message_box(title, message)
                return True
            thread = threading.Thread(target=self._message_box, args=(title, message), daemon=False)
            thread.start()
            return True
        print(f"{title}: {message}")
        return True


def _show_windows_message_box(title: str, message: str) -> None:
    flags = 0x00001000 | 0x00010000 | 0x00040000
    ctypes.windll.user32.MessageBoxW(None, message, title, flags)
