import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.desktop_card import _CardModel, _render_classic_header, _render_dense_header, _render_strip_header
from day_notifier.desktop_card_themes import resolve_desktop_card_theme


class DesktopCardLayoutTests(unittest.TestCase):
    def test_classic_header_constrains_long_title_before_time_column(self):
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            theme = resolve_desktop_card_theme("glass_classic_green")
            model = _CardModel(
                title="1 минута до сна +10 мин",
                current_time="22:09",
                target_time="22:09",
                status_label="",
                countdown="сейчас",
                message="Отбой почти сейчас.",
            )
            card = tk.Frame(root, bg=theme.panel_bg, width=theme.width, height=theme.height)
            card.grid_propagate(False)
            card.pack_propagate(False)
            card.pack(fill="both", expand=True)
            card.columnconfigure(0, weight=1)

            _render_classic_header(tk, card, model, theme)
            root.update_idletasks()

            header = card.winfo_children()[0]
            title_label, target_time_label = [
                child for child in header.winfo_children() if isinstance(child, tk.Label)
            ][:2]

            self.assertGreater(int(title_label.cget("wraplength")), 0)
            self.assertLessEqual(int(title_label.cget("wraplength")), theme.width - 260)
            self.assertGreaterEqual(int(header.grid_columnconfigure(1)["minsize"]), target_time_label.winfo_reqwidth())
        finally:
            root.destroy()

    def test_dense_header_constrains_metric_values(self):
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            theme = resolve_desktop_card_theme("calm_dense_light")
            card = _fixed_card(tk, root, theme)

            _render_dense_header(tk, card, _long_sleep_countdown_model(), theme)
            root.update_idletasks()

            value_labels = [
                label
                for label in _labels(card, tk)
                if str(label.cget("text")) in {"1 минута до сна +10 мин", "22:09", "сейчас"}
            ]

            self.assertTrue(value_labels)
            self.assertTrue(all(int(label.cget("wraplength")) > 0 for label in value_labels))
        finally:
            root.destroy()

    def test_strip_header_constrains_long_title(self):
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            theme = resolve_desktop_card_theme("compact_dark_strip")
            card = _fixed_card(tk, root, theme)

            _render_strip_header(tk, card, _long_sleep_countdown_model(), theme)
            root.update_idletasks()

            title_label = next(
                label for label in _labels(card, tk) if str(label.cget("text")) == "1 минута до сна +10 мин"
            )

            self.assertGreater(int(title_label.cget("wraplength")), 0)
        finally:
            root.destroy()


def _fixed_card(tk, root, theme):
    card = tk.Frame(root, bg=theme.panel_bg, width=theme.width, height=theme.height)
    card.grid_propagate(False)
    card.pack_propagate(False)
    card.pack(fill="both", expand=True)
    card.columnconfigure(0, weight=1)
    return card


def _long_sleep_countdown_model() -> _CardModel:
    return _CardModel(
        title="1 минута до сна +10 мин",
        current_time="22:09",
        target_time="22:09",
        status_label="",
        countdown="сейчас",
        message="Отбой почти сейчас.",
    )


def _labels(widget, tk):
    found = []
    for child in widget.winfo_children():
        if isinstance(child, tk.Label):
            found.append(child)
        found.extend(_labels(child, tk))
    return found


if __name__ == "__main__":
    unittest.main()
