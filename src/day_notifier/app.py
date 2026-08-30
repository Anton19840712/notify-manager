from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from day_notifier.commands import CommandContext, handle_command
from day_notifier.config import Settings, load_settings, set_desktop_enabled
from day_notifier.desktop import DesktopNotifier
from day_notifier.schedule import Schedule, ScheduleEvent, load_schedule
from day_notifier.state import JsonStateStore
from day_notifier.telegram_client import TelegramClient


def select_due_events(
    events: list[ScheduleEvent],
    state: JsonStateStore,
    now: datetime,
    grace_minutes: int,
) -> list[ScheduleEvent]:
    due: list[ScheduleEvent] = []
    grace_seconds = grace_minutes * 60
    for event in events:
        if state.has_seen(event) or event.when > now:
            continue
        age_seconds = (now - event.when).total_seconds()
        if age_seconds <= grace_seconds:
            due.append(event)
        else:
            state.mark_skipped(event)
    return due


class NotifierApp:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.schedule = load_schedule(root / "config" / "schedule.json")
        self.settings_path = root / "config" / "settings.json"
        self.settings = load_settings(self.settings_path)
        self.state = JsonStateStore(root / "data" / "state.json")
        self.inbox_path = root / "data" / "inbox.md"
        self.desktop = DesktopNotifier(enabled=self.settings.desktop_enabled)
        self.telegram = _make_telegram_client(self.settings)

    def run_forever(self) -> None:
        logging.info("Day notifier started in %s", self.root)
        if self.settings.startup_summary_enabled:
            self.send_startup_summary()
        while True:
            self.run_once()
            time.sleep(self.settings.check_interval_seconds)

    def run_once(self, now: datetime | None = None) -> None:
        self.refresh_settings()
        current = now or datetime.now()
        events = self.schedule.events_for_date(current.date()) + self.state.due_snoozes(current)
        due = select_due_events(
            events,
            self.state,
            current,
            grace_minutes=self.settings.missed_event_grace_minutes,
        )
        for event in due:
            self.notify(event)
        self.process_telegram_commands()

    def notify(self, event: ScheduleEvent) -> None:
        text = f"{event.when:%H:%M} - {event.title}\n{event.message}"
        self.desktop.show(event.title, text)
        if self.telegram is not None:
            try:
                self.telegram.send_message(text)
            except Exception:
                logging.exception("Telegram notification failed")
        self.state.mark_notified(event)

    def process_telegram_commands(self) -> None:
        if self.telegram is None:
            return
        try:
            commands = self.telegram.get_commands(offset=self.state.telegram_offset)
        except Exception:
            logging.exception("Telegram command polling failed")
            return

        context = CommandContext(
            schedule=self.schedule,
            state=self.state,
            inbox_path=self.inbox_path,
            now=datetime.now,
            set_desktop_enabled=self.set_desktop_enabled,
            is_desktop_enabled=self.is_desktop_enabled,
        )
        for command in commands:
            try:
                result = handle_command(command.text, context)
                self.telegram.send_message(result.reply)
                self.state.set_telegram_offset(command.update_id + 1)
            except Exception:
                logging.exception("Telegram command handling failed: %s", command.text)

    def summary(self, now: datetime | None = None) -> str:
        current = now or datetime.now()
        lines = ["Ближайшие события:"]
        lines.extend(f"- {event.when:%Y-%m-%d %H:%M} {event.title}" for event in self.schedule.upcoming(current, 10))
        return "\n".join(lines)

    def today(self, now: datetime | None = None) -> str:
        return format_startup_summary(self.schedule, now or datetime.now())

    def send_startup_summary(self) -> None:
        text = format_startup_summary(self.schedule, datetime.now())
        self.desktop.show("notify-manager", text)
        if self.telegram is None:
            return
        try:
            self.telegram.send_message(text)
        except Exception:
            logging.exception("Telegram startup summary failed")

    def send_test_notification(self) -> None:
        text = "Тест notify-manager: канал уведомлений работает."
        self.desktop.show("notify-manager", text, blocking=True)
        if self.telegram is None:
            logging.warning("Telegram settings are missing; test sent only to desktop.")
            return
        self.telegram.send_message(text)

    def test_desktop_notification(self) -> None:
        self.desktop.show("notify-manager", "Тест desktop MsgBox: центральное окно работает.", blocking=True)

    def set_desktop_enabled(self, enabled: bool) -> None:
        self.settings = set_desktop_enabled(self.settings_path, enabled)
        self.desktop.enabled = self.settings.desktop_enabled

    def is_desktop_enabled(self) -> bool:
        return self.desktop.enabled

    def refresh_settings(self) -> None:
        previous = self.settings
        self.settings = load_settings(self.settings_path)
        self.desktop.enabled = self.settings.desktop_enabled
        if (previous.bot_token, previous.chat_id) != (self.settings.bot_token, self.settings.chat_id):
            self.telegram = _make_telegram_client(self.settings)


def format_startup_summary(schedule: Schedule, now: datetime, limit: int = 10) -> str:
    events = schedule.remaining_today(now, limit=limit)
    lines = ["notify-manager запущен."]
    if not events:
        lines.append("Сегодня больше нет событий.")
        return "\n".join(lines)
    lines.append("Сегодня осталось:")
    lines.extend(f"- {event.when:%H:%M} {event.title}" for event in events)
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local day schedule notifier")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--once", action="store_true", help="Run one polling cycle and exit")
    parser.add_argument("--summary", action="store_true", help="Print upcoming events and exit")
    parser.add_argument("--today", action="store_true", help="Print remaining events for today and exit")
    parser.add_argument("--test-telegram", action="store_true", help="Send a test desktop and Telegram notification")
    parser.add_argument("--test-desktop", action="store_true", help="Show a blocking desktop message box")
    parser.add_argument("--desktop-on", action="store_true", help="Enable desktop message boxes")
    parser.add_argument("--desktop-off", action="store_true", help="Disable desktop message boxes")
    parser.add_argument("--desktop-status", action="store_true", help="Print desktop message box status")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_arg_parser().parse_args()
    app = NotifierApp(args.root.resolve())
    if args.summary:
        print(app.summary())
        return 0
    if args.today:
        print(app.today())
        return 0
    if args.test_telegram:
        app.send_test_notification()
        return 0
    if args.test_desktop:
        app.test_desktop_notification()
        return 0
    if args.desktop_on:
        app.set_desktop_enabled(True)
        print("Desktop-уведомления включены.")
        return 0
    if args.desktop_off:
        app.set_desktop_enabled(False)
        print("Desktop-уведомления выключены.")
        return 0
    if args.desktop_status:
        state = "включены" if app.is_desktop_enabled() else "выключены"
        print(f"Desktop-уведомления сейчас {state}.")
        return 0
    if args.once:
        app.run_once()
        return 0
    app.run_forever()
    return 0


def _make_telegram_client(settings: Settings) -> TelegramClient | None:
    if not settings.telegram_enabled:
        logging.warning("Telegram settings are missing; desktop notifications only.")
        return None
    return TelegramClient(settings.bot_token or "", settings.chat_id or "")
