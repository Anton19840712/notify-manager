from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


Transport = Callable[[str, bytes], dict[str, Any]]


@dataclass(frozen=True)
class TelegramCommand:
    update_id: int
    text: str


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str, transport: Transport | None = None) -> None:
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.transport = transport or _urllib_transport

    def send_message(self, text: str) -> None:
        self._call("sendMessage", {"chat_id": self.chat_id, "text": text})

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
            if str(chat.get("id")) == self.chat_id and text.startswith("/"):
                commands.append(TelegramCommand(update_id=int(item["update_id"]), text=text))
        return commands

    def _call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        response = self.transport(url, body)
        if not response.get("ok", False):
            raise RuntimeError(f"Telegram API error for {method}: {response}")
        return response


def _urllib_transport(url: str, payload: bytes) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

