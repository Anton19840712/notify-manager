from __future__ import annotations

import ctypes
import platform
import threading


class DesktopNotifier:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def show(self, title: str, message: str) -> None:
        if not self.enabled:
            return
        if platform.system().lower() == "windows":
            thread = threading.Thread(target=_show_windows_message_box, args=(title, message), daemon=True)
            thread.start()
            return
        print(f"{title}: {message}")


def _show_windows_message_box(title: str, message: str) -> None:
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x00001000)

