import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.telegram_client import TelegramClient


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, url, payload):
        self.calls.append((url, payload))
        return self.response


class TelegramClientTests(unittest.TestCase):
    def test_send_message_posts_to_bot_api(self):
        transport = FakeTransport({"ok": True, "result": {}})
        client = TelegramClient("123:abc", "456", transport=transport)

        client.send_message("hello")

        url, payload = transport.calls[0]
        self.assertTrue(url.endswith("/bot123:abc/sendMessage"))
        self.assertEqual(json.loads(payload.decode("utf-8")), {"chat_id": "456", "text": "hello"})

    def test_send_message_returns_message_id(self):
        transport = FakeTransport({"ok": True, "result": {"message_id": 42}})
        client = TelegramClient("123:abc", "456", transport=transport)

        message_id = client.send_message("hello")

        self.assertEqual(message_id, 42)

    def test_get_commands_filters_by_chat_id(self):
        transport = FakeTransport(
            {
                "ok": True,
                "result": [
                    {"update_id": 10, "message": {"chat": {"id": 456}, "text": "/next"}},
                    {"update_id": 11, "message": {"chat": {"id": 999}, "text": "/summary"}},
                    {"update_id": 12, "message": {"chat": {"id": 456}, "text": "not a command"}},
                ],
            }
        )
        client = TelegramClient("123:abc", "456", transport=transport)

        commands = client.get_commands(offset=7)

        self.assertEqual([(command.update_id, command.text) for command in commands], [(10, "/next")])
        url, payload = transport.calls[0]
        self.assertTrue(url.endswith("/bot123:abc/getUpdates"))
        self.assertEqual(json.loads(payload.decode("utf-8")), {"timeout": 0, "offset": 7})

    def test_get_commands_includes_incoming_message_id_and_plain_bedtime_text(self):
        transport = FakeTransport(
            {
                "ok": True,
                "result": [
                    {
                        "update_id": 10,
                        "message": {
                            "message_id": 77,
                            "chat": {"id": 456},
                            "text": "отбой",
                        },
                    }
                ],
            }
        )
        client = TelegramClient("123:abc", "456", transport=transport)

        commands = client.get_commands()

        self.assertEqual(commands[0].update_id, 10)
        self.assertEqual(commands[0].message_id, 77)
        self.assertEqual(commands[0].text, "отбой")

    def test_delete_messages_uses_batch_api(self):
        transport = FakeTransport({"ok": True, "result": True})
        client = TelegramClient("123:abc", "456", transport=transport)

        summary = client.delete_messages([1, 2, 3])

        url, payload = transport.calls[0]
        self.assertEqual(summary.deleted, 3)
        self.assertEqual(summary.failed, 0)
        self.assertTrue(url.endswith("/bot123:abc/deleteMessages"))
        self.assertEqual(
            json.loads(payload.decode("utf-8")),
            {"chat_id": "456", "message_ids": [1, 2, 3]},
        )


if __name__ == "__main__":
    unittest.main()
