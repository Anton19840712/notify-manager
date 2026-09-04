from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from day_notifier.desktop_actions import DesktopAction, append_desktop_action
from day_notifier.desktop_card_themes import DEFAULT_DESKTOP_CARD_THEME, DesktopCardTheme, resolve_desktop_card_theme


CURRENT_TIME_PATTERN = re.compile(r"Сейчас:\s*(\d{2}:\d{2})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Desktop notification card")
    parser.add_argument("--payload", type=Path, required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    return show_card(payload)


def show_card(payload: dict) -> int:
    try:
        import tkinter as tk
        from tkinter.scrolledtext import ScrolledText
    except Exception:
        return 1

    theme = resolve_desktop_card_theme(payload.get("theme", DEFAULT_DESKTOP_CARD_THEME), _payload_date(payload))
    model = _CardModel.from_payload(payload)
    long_body = len(model.message) > 260 or model.message.count("\n") >= 4
    width = theme.width
    height = max(theme.height, 430 if long_body else theme.height)

    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.bind("<Escape>", lambda _event: root.destroy())

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = max(0, int((screen_width - width) / 2))
    y = max(0, int((screen_height - height) / 2))
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg=theme.shell_bg)
    root.deiconify()

    card = tk.Frame(root, bg=theme.panel_bg, highlightbackground=theme.border, highlightthickness=1)
    card.pack(fill="both", expand=True, padx=6, pady=6)
    card.columnconfigure(0, weight=1)
    card.rowconfigure(1, weight=1)

    if theme.layout == "dense":
        _render_dense_header(tk, card, model, theme)
    elif theme.layout == "strip":
        _render_strip_header(tk, card, model, theme)
    else:
        _render_classic_header(tk, card, model, theme)

    _render_body(tk, ScrolledText, card, model, theme, long_body)
    _render_buttons(tk, card, payload, root, theme)

    root.after(30 * 60 * 1000, root.destroy)
    root.mainloop()
    return 0


class _CardModel:
    def __init__(self, title: str, current_time: str, target_time: str, status_label: str, countdown: str, message: str):
        self.title = title
        self.current_time = current_time
        self.target_time = target_time
        self.status_label = status_label
        self.countdown = countdown
        self.message = message

    @classmethod
    def from_payload(cls, payload: dict) -> "_CardModel":
        status_label, countdown = _split_status(str(payload.get("status", "")).strip())
        return cls(
            title=str(payload.get("title", "")).strip() or "notify-manager",
            current_time=_current_time(payload),
            target_time=_target_time(payload),
            status_label=status_label,
            countdown=countdown,
            message=_message(payload),
        )


def _render_classic_header(tk, card, model: _CardModel, theme: DesktopCardTheme) -> None:
    header = tk.Frame(card, bg=theme.panel_bg)
    header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 0))
    header.columnconfigure(0, weight=1)
    header.columnconfigure(1, weight=1)

    tk.Label(
        header,
        text=model.title,
        bg=theme.panel_bg,
        fg=theme.title_fg,
        font=("Segoe UI", 32, "bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        header,
        text=model.target_time,
        bg=theme.panel_bg,
        fg=theme.time_fg,
        font=("Segoe UI", 32, "bold"),
        anchor="e",
    ).grid(row=0, column=1, sticky="e")
    tk.Label(
        header,
        text=f"Сейчас: {model.current_time}",
        bg=theme.panel_bg,
        fg=theme.muted_fg,
        font=("Segoe UI", 13),
        anchor="w",
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))
    status_text = _status_text(model)
    tk.Label(
        header,
        text=status_text,
        bg=theme.panel_bg,
        fg=theme.status_fg,
        font=("Segoe UI", 13),
        anchor="e",
    ).grid(row=1, column=1, sticky="e", pady=(4, 0))
    _divider(tk, header, theme).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(18, 0))


def _render_dense_header(tk, card, model: _CardModel, theme: DesktopCardTheme) -> None:
    header = tk.Frame(card, bg=theme.panel_bg)
    header.grid(row=0, column=0, sticky="ew", padx=26, pady=(22, 0))
    for column in range(3):
        header.columnconfigure(column, weight=1)

    _metric(tk, header, "Событие", model.title, theme.title_fg, theme, 0)
    _metric(tk, header, "Время", model.target_time, theme.time_fg, theme, 1)
    _metric(tk, header, model.status_label or "Осталось", model.countdown or "сейчас", theme.countdown_fg, theme, 2)
    tk.Label(
        header,
        text=f"Сейчас: {model.current_time}",
        bg=theme.panel_bg,
        fg=theme.muted_fg,
        font=("Segoe UI", 12),
        anchor="w",
    ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
    _divider(tk, header, theme).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(14, 0))


def _render_strip_header(tk, card, model: _CardModel, theme: DesktopCardTheme) -> None:
    header = tk.Frame(card, bg=theme.panel_bg)
    header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 0))
    header.columnconfigure(0, weight=0)
    header.columnconfigure(1, weight=1)
    header.columnconfigure(2, weight=0)

    tk.Label(
        header,
        text=model.title,
        bg=theme.panel_bg,
        fg=theme.title_fg,
        font=("Segoe UI", 28, "bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        header,
        text=f"Сейчас: {model.current_time}  ->  {model.target_time}",
        bg=theme.panel_bg,
        fg=theme.time_fg,
        font=("Segoe UI", 18),
        anchor="w",
    ).grid(row=0, column=1, sticky="w", padx=(24, 0))
    tk.Label(
        header,
        text=model.countdown or "сейчас",
        bg=theme.panel_bg,
        fg=theme.countdown_fg,
        font=("Segoe UI", 34, "bold"),
        anchor="e",
    ).grid(row=0, column=2, sticky="e", padx=(18, 0))
    tk.Label(
        header,
        text=model.status_label,
        bg=theme.panel_bg,
        fg=theme.status_fg,
        font=("Segoe UI", 13),
        anchor="e",
    ).grid(row=1, column=2, sticky="e")
    _divider(tk, header, theme).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(14, 0))


def _render_body(tk, scrolled_text, card, model: _CardModel, theme: DesktopCardTheme, long_body: bool) -> None:
    body_frame = tk.Frame(card, bg=theme.panel_bg)
    body_frame.grid(row=1, column=0, sticky="nsew", padx=28, pady=(18, 0))
    body_frame.columnconfigure(0, weight=1)
    body_frame.rowconfigure(0, weight=1)

    if long_body:
        body = scrolled_text(
            body_frame,
            width=64,
            height=10,
            font=("Segoe UI", 10),
            bg=theme.panel_bg,
            fg=theme.body_fg,
            wrap="word",
            relief="flat",
            borderwidth=0,
            insertbackground=theme.body_fg,
        )
        body.insert("1.0", model.message)
        body.configure(state="disabled")
        body.grid(row=0, column=0, sticky="nsew")
        return

    tk.Label(
        body_frame,
        text=model.message,
        bg=theme.panel_bg,
        fg=theme.body_fg,
        font=("Segoe UI", 15),
        justify="left",
        anchor="nw",
        wraplength=max(360, theme.width - 90),
    ).grid(row=0, column=0, sticky="nsew")


def _render_buttons(tk, card, payload: dict, root, theme: DesktopCardTheme) -> None:
    actions = list(payload.get("actions", [])) or [{"action": "close", "label": "Закрыть"}]
    buttons = tk.Frame(card, bg=theme.panel_bg)
    buttons.grid(row=2, column=0, sticky="ew", padx=28, pady=(18, 24))
    for column in range(len(actions)):
        buttons.columnconfigure(column, weight=1, uniform="actions")

    for index, action in enumerate(actions):
        label = _button_label(str(action.get("label", action.get("action", ""))))
        is_primary = index == 0 and action.get("action") != "close"
        button = tk.Button(
            buttons,
            text=label,
            font=(theme.button_font, 13),
            cursor="hand2",
            bg=theme.primary_bg if is_primary else theme.secondary_bg,
            fg=theme.primary_fg if is_primary else theme.secondary_fg,
            activebackground=theme.primary_bg if is_primary else theme.secondary_bg,
            activeforeground=theme.primary_fg if is_primary else theme.secondary_fg,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=theme.primary_border if is_primary else theme.secondary_border,
            highlightcolor=theme.primary_border if is_primary else theme.secondary_border,
            command=lambda action_name=str(action.get("action", "")): _handle_button(payload, action_name, root),
        )
        button.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 8, 0), ipady=11)


def _metric(tk, parent, label: str, value: str, value_color: str, theme: DesktopCardTheme, column: int) -> None:
    frame = tk.Frame(parent, bg=theme.panel_bg)
    frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 16, 0))
    tk.Label(
        frame,
        text=label,
        bg=theme.panel_bg,
        fg=theme.muted_fg,
        font=("Segoe UI", 11),
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        frame,
        text=value,
        bg=theme.panel_bg,
        fg=value_color,
        font=("Segoe UI", 28, "bold"),
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))


def _divider(tk, parent, theme: DesktopCardTheme):
    return tk.Frame(parent, height=1, bg=theme.divider)


def _button_label(label: str) -> str:
    label = label.strip()
    if not label:
        return "Закрыть"
    return label if label.startswith(">") else f">  {label}"


def _handle_button(payload: dict, action: str, root) -> None:
    if action == "close":
        root.destroy()
        return
    _handle_action(payload, action, root)


def _status_text(model: _CardModel) -> str:
    if model.status_label and model.countdown:
        return f"{model.status_label}: {model.countdown}"
    return model.status_label or model.countdown


def _split_status(status: str) -> tuple[str, str]:
    if ":" not in status:
        return status, ""
    label, value = status.split(":", 1)
    return label.strip(), value.strip()


def _current_time(payload: dict) -> str:
    match = CURRENT_TIME_PATTERN.search(str(payload.get("body", "")))
    if match:
        return match.group(1)
    return datetime.now().strftime("%H:%M")


def _target_time(payload: dict) -> str:
    event = payload.get("event") or {}
    when = event.get("when")
    if when:
        try:
            return datetime.fromisoformat(str(when)).strftime("%H:%M")
        except ValueError:
            pass
    return ""


def _message(payload: dict) -> str:
    event = payload.get("event") or {}
    message = str(event.get("message", "")).strip()
    if message:
        return message
    return str(payload.get("body", "")).strip()


def _payload_date(payload: dict):
    event = payload.get("event") or {}
    when = event.get("when")
    if when:
        try:
            return datetime.fromisoformat(str(when))
        except ValueError:
            return None
    return None


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
