import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.desktop_card_themes import (
    DESKTOP_CARD_THEME_IDS,
    DEFAULT_DESKTOP_CARD_THEME,
    normalize_desktop_card_theme,
    resolve_desktop_card_theme,
)


class DesktopCardThemeTests(unittest.TestCase):
    def test_rotate_daily_uses_all_ten_themes_and_wraps_by_date(self):
        self.assertEqual(len(DESKTOP_CARD_THEME_IDS), 10)
        first = resolve_desktop_card_theme(DEFAULT_DESKTOP_CARD_THEME, date(2026, 9, 4))
        second = resolve_desktop_card_theme(DEFAULT_DESKTOP_CARD_THEME, date(2026, 9, 5))
        wrapped = resolve_desktop_card_theme(DEFAULT_DESKTOP_CARD_THEME, date(2026, 9, 14))

        self.assertEqual(first.theme_id, DESKTOP_CARD_THEME_IDS[0])
        self.assertEqual(second.theme_id, DESKTOP_CARD_THEME_IDS[1])
        self.assertEqual(wrapped.theme_id, DESKTOP_CARD_THEME_IDS[0])

    def test_theme_can_be_pinned_by_id_or_number(self):
        self.assertEqual(normalize_desktop_card_theme("dark_glass_command"), "dark_glass_command")
        self.assertEqual(normalize_desktop_card_theme("3"), DESKTOP_CARD_THEME_IDS[2])

    def test_unknown_theme_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_desktop_card_theme("random")


if __name__ == "__main__":
    unittest.main()
