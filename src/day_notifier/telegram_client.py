from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


Transport = Callable[[str, bytes], dict[str, Any]]
MEAL_DONE_TEXT_PATTERN = re.compile(r"^\d+\s+(?:mi|pp|пп)\s+done$", re.IGNORECASE)


@dataclass(frozen=True)
class TelegramCommand:
    update_id: int
    text: str
    message_id: int | None = None


@dataclass(frozen=True)
class DeleteSummary:
    deleted: int = 0
    failed: int = 0


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str, transport: Transport | None = None) -> None:
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.transport = transport or _urllib_transport

    def send_message(self, text: str) -> int | None:
        response = self._call("sendMessage", {"chat_id": self.chat_id, "text": text})
        result = response.get("result") or {}
        message_id = result.get("message_id")
        return int(message_id) if message_id is not None else None

    def get_commands(self, offset: int | None = None) -> list[TelegramCommand]:
        payload: dict[str, Any] = {"timeout": 0}
        if offset is not None:
            payload["offset"] = offset

        response = self._call("getUpdates", payload)
        commands: list[TelegramCommand] = []
        for item in response.get("result", []):
            message = item.get("message") or {}
            chat = message.get("chat") or {}
            text = str(message.get("text") or "")
            if str(chat.get("id")) == self.chat_id and _is_supported_command_text(text):
                raw_message_id = message.get("message_id")
                commands.append(
                    TelegramCommand(
                        update_id=int(item["update_id"]),
                        text=text,
                        message_id=int(raw_message_id) if raw_message_id is not None else None,
                    )
                )
        return commands

    def delete_messages(self, message_ids: list[int]) -> DeleteSummary:
        unique_ids = list(dict.fromkeys(int(message_id) for message_id in message_ids))
        deleted = 0
        failed = 0
        for batch in _chunks(unique_ids, 100):
            try:
                self._call("deleteMessages", {"chat_id": self.chat_id, "message_ids": batch})
                deleted += len(batch)
            except Exception:
                for message_id in batch:
                    try:
                        self._call("deleteMessage", {"chat_id": self.chat_id, "message_id": message_id})
                        deleted += 1
                    except Exception:
                        failed += 1
        return DeleteSummary(deleted=deleted, failed=failed)

    def _call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        response = self.transport(url, body)
        if not response.get("ok", False):
            raise RuntimeError(f"Telegram API error for {method}: {response}")
        return response


def _chunks(values: list[int], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _is_supported_command_text(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("/") or stripped.lower() == "отбой" or bool(MEAL_DONE_TEXT_PATTERN.match(stripped))


def _urllib_transport(url: str, payload: bytes) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))
