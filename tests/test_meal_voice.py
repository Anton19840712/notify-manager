import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.meal_voice import (
    DEFAULT_MEAL_VOICE_PROFILE,
    MEAL_VOICE_PROFILES,
    format_meal_voice_status,
    load_active_meal_voice_profile,
    set_meal_voice_profile,
)


class MealVoiceTests(unittest.TestCase):
    def test_default_profile_is_commander_when_state_file_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "meal_voice_state.json"

            active = load_active_meal_voice_profile(state_path)

        self.assertEqual(active, DEFAULT_MEAL_VOICE_PROFILE)
        self.assertEqual(active, "male_commander")

    def test_switches_profile_by_number_and_writes_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "data" / "audio" / "meal_voice_state.json"

            result = set_meal_voice_profile(state_path, "3")
            active = load_active_meal_voice_profile(state_path)
            data = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(active, "female_sonia")
        self.assertEqual(data["active_profile"], "female_sonia")
        self.assertIn("female_sonia", result)

    def test_switches_profile_by_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "meal_voice_state.json"

            result = set_meal_voice_profile(state_path, "female_aria")
            active = load_active_meal_voice_profile(state_path)

        self.assertIn("female_aria", result)
        self.assertEqual(active, "female_aria")

    def test_invalid_profile_returns_options_without_writing_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "meal_voice_state.json"

            result = set_meal_voice_profile(state_path, "optimus_prime_exact")

        self.assertIn("Не знаю такой голос", result)
        self.assertIn("Варианты", result)
        self.assertFalse(state_path.exists())

    def test_status_lists_active_profile_and_all_options(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "meal_voice_state.json"
            set_meal_voice_profile(state_path, "7")

            status = format_meal_voice_status(state_path)

        self.assertIn("Активный: 7. female_svetlana", status)
        for index, profile in enumerate(MEAL_VOICE_PROFILES, start=1):
            self.assertIn(f"{index}. {profile.profile_id}", status)
        self.assertIn("/mv 3", status)


if __name__ == "__main__":
    unittest.main()
