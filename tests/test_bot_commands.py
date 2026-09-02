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
        self.assertIn({"command": "stop_bot", "description": "остановить локальный notifier"}, payload)
        self.assertIn({"command": "otboy", "description": "очистить чат перед сном"}, payload)
        self.assertIn({"command": "block_on", "description": "подключить блок"}, payload)
        self.assertIn({"command": "block_off", "description": "отключить блок"}, payload)
        self.assertIn({"command": "block_status", "description": "статус блоков"}, payload)
        self.assertIn({"command": "blocks", "description": "статус всех блоков"}, payload)
        self.assertIn({"command": "selfdev_on", "description": "включить саморазвитие"}, payload)
        self.assertIn({"command": "selfdev_off", "description": "выключить саморазвитие"}, payload)
        self.assertIn({"command": "training_on", "description": "включить тренировки"}, payload)
        self.assertIn({"command": "training_off", "description": "выключить тренировки"}, payload)
        self.assertIn({"command": "prayers_on", "description": "включить молитвы"}, payload)
        self.assertIn({"command": "prayers_off", "description": "выключить молитвы"}, payload)
        self.assertIn({"command": "chrysostom_on", "description": "включить молитвы Златоуста"}, payload)
        self.assertIn({"command": "chrysostom_off", "description": "выключить молитвы Златоуста"}, payload)

    def test_help_text_is_generated_from_same_registry(self):
        help_text = format_bot_commands_help()

        self.assertIn("/mi1 - съел 1 прием пищи", help_text)
        self.assertIn("/desktop_on - включить desktop окна", help_text)
        self.assertIn("/stop_bot - остановить локальный notifier", help_text)
        self.assertIn("/sd - перенести старт дня, пример /sd 10:00", help_text)
        self.assertIn("/block_on - подключить блок", help_text)
        self.assertIn("/selfdev_off - выключить саморазвитие", help_text)
        self.assertIn("/training_off - выключить тренировки", help_text)
        self.assertIn("/prayers_off - выключить молитвы", help_text)


if __name__ == "__main__":
    unittest.main()
