import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.bot_commands import BOT_COMMANDS, bot_command_payload, format_bot_commands_help


class BotCommandRegistryTests(unittest.TestCase):
    def test_bot_commands_are_telegram_safe(self):
        command_pattern = re.compile(r"^[a-z0-9_]{1,32}$")

        for command in BOT_COMMANDS:
            with self.subTest(command=command.command):
                self.assertRegex(command.command, command_pattern)
                self.assertGreaterEqual(len(command.description), 1)
                self.assertLessEqual(len(command.description), 256)

    def test_bot_command_payload_contains_phone_friendly_shortcuts(self):
        payload = bot_command_payload()

        self.assertIn({"command": "mi1", "description": "съел 1 прием пищи"}, payload)
        self.assertIn({"command": "mi4", "description": "съел 4 прием пищи"}, payload)
        self.assertIn({"command": "sd", "description": "перенести старт дня, пример /sd 10:00"}, payload)
        self.assertIn({"command": "otboy", "description": "очистить чат перед сном"}, payload)

    def test_help_text_is_generated_from_same_registry(self):
        help_text = format_bot_commands_help()

        self.assertIn("/mi1 - съел 1 прием пищи", help_text)
        self.assertIn("/desktop_on - включить desktop окна", help_text)
        self.assertIn("/sd - перенести старт дня, пример /sd 10:00", help_text)


if __name__ == "__main__":
    unittest.main()
