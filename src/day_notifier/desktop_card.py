from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from day_notifier.desktop_actions import DesktopAction, append_desktop_action


COLORS = {
    "critical": {"bar": "#d92d20", "bg": "#fff7f5", "text": "#1f2937"},
    "anchor": {"bar": "#2563eb", "bg": "#eff6ff", "text": "#111827"},
    "normal": {"bar": "#16a34a", "bg": "#f0fdf4", "text": "#111827"},
    "soft": {"bar": "#7c3aed", "bg": "#faf5ff", "text": "#111827"},
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Desktop notification card")
    parser.add_argument("--payload", type=Path, required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    return show_card(payload)


def show_card(payload: dict) -> int:
    try:
        import tkinter as tk
        from tkinter import ttk
        from tkinter.scrolledtext import ScrolledText
    except Exception:
        return 1

    importance = str(payload.get("importance", "normal"))
    colors = COLORS.get(importance, COLORS["normal"])

    root = tk.Tk()
    root.title(str(payload.get("title", "notify-manager")))
    root.attributes("-topmost", True)
    root.resizable(False, False)

    width = 600
    height = 420
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = max(0, int((screen_width - width) / 2))
    y = max(0, int((screen_height - height) / 2))
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg=colors["bg"])

    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    bar = tk.Frame(root, width=8, bg=colors["bar"])
    bar.grid(row=0, column=0, sticky="ns")

    frame = ttk.Frame(root, padding=(18, 16, 18, 14))
    frame.grid(row=0, column=1, sticky="nsew")
    frame.columnconfigure(0, weight=1)

    title = ttk.Label(frame, text=str(payload.get("title", "")), font=("Segoe UI", 16, "bold"))
    title.grid(row=0, column=0, sticky="w")

    status_text = str(payload.get("status", "")).strip()
    if status_text:
        status = ttk.Label(frame, text=status_text, font=("Segoe UI", 11))
        status.grid(row=1, column=0, sticky="w", pady=(4, 0))

    body = ScrolledText(
        frame,
        width=58,
        height=12,
        font=("Segoe UI", 10),
        bg=colors["bg"],
        fg=colors["text"],
        wrap="word",
        relief="flat",
        borderwidth=0,
    )
    body.insert("1.0", str(payload.get("body", "")))
    body.configure(state="disabled")
    body.grid(row=2, column=0, sticky="ew", pady=(14, 0))

    buttons = ttk.Frame(frame)
    buttons.grid(row=3, column=0, sticky="e", pady=(16, 0))

    for action in payload.get("actions", []):
        ttk.Button(
            buttons,
            text=str(action.get("label", action.get("action", ""))),
            command=lambda action_name=str(action.get("action", "")): _handle_action(payload, action_name, root),
        ).pack(side="left", padx=(0, 8))

    ttk.Button(buttons, text="Закрыть", command=root.destroy).pack(side="left")
    root.after(30 * 60 * 1000, root.destroy)
    root.mainloop()
    return 0


def _handle_action(payload: dict, action: str, root) -> None:
    queue_path = payload.get("action_queue_path")
    event = payload.get("event") or {}
    if queue_path and event:
        append_desktop_action(
            Path(str(queue_path)),
            DesktopAction(
                action_id=uuid4().hex,
                action=action,
                event_id=str(event["event_id"]),
                title=str(event["title"]),
                message=str(event.get("message", "")),
                when=datetime.fromisoformat(str(event["when"])),
            ),
        )
    root.destroy()


if __name__ == "__main__":
    sys.exit(main())
