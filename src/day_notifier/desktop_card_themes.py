from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


DEFAULT_DESKTOP_CARD_THEME = "rotate_daily"
ROTATION_START_DATE = date(2026, 9, 4)


@dataclass(frozen=True)
class DesktopCardTheme:
    theme_id: str
    layout: str
    width: int
    height: int
    shell_bg: str
    panel_bg: str
    border: str
    divider: str
    title_fg: str
    time_fg: str
    status_fg: str
    countdown_fg: str
    body_fg: str
    muted_fg: str
    primary_bg: str
    primary_fg: str
    primary_border: str
    secondary_bg: str
    secondary_fg: str
    secondary_border: str
    arrow_fg: str
    button_font: str = "Segoe UI"


DESKTOP_CARD_THEMES: tuple[DesktopCardTheme, ...] = (
    DesktopCardTheme(
        theme_id="glass_classic_green",
        layout="classic",
        width=600,
        height=330,
        shell_bg="#dce8f6",
        panel_bg="#f4f8fc",
        border="#c4d2df",
        divider="#cfd8e3",
        title_fg="#0f4c35",
        time_fg="#0f4c35",
        status_fg="#27313b",
        countdown_fg="#0f7a44",
        body_fg="#111827",
        muted_fg="#687583",
        primary_bg="#0f5132",
        primary_fg="#ffffff",
        primary_border="#0f5132",
        secondary_bg="#f8fbfd",
        secondary_fg="#0f5132",
        secondary_border="#82928a",
        arrow_fg="#0f5132",
    ),
    DesktopCardTheme(
        theme_id="soft_green_classic",
        layout="classic",
        width=580,
        height=320,
        shell_bg="#eef2f0",
        panel_bg="#fbfcfb",
        border="#cfd8d2",
        divider="#d9dfdc",
        title_fg="#134e35",
        time_fg="#134e35",
        status_fg="#2f3833",
        countdown_fg="#146c43",
        body_fg="#121614",
        muted_fg="#707973",
        primary_bg="#14532d",
        primary_fg="#ffffff",
        primary_border="#14532d",
        secondary_bg="#fbfcfb",
        secondary_fg="#174c35",
        secondary_border="#87948d",
        arrow_fg="#174c35",
    ),
    DesktopCardTheme(
        theme_id="dark_glass_command",
        layout="classic",
        width=600,
        height=330,
        shell_bg="#07111d",
        panel_bg="#101923",
        border="#41505f",
        divider="#2f3a45",
        title_fg="#f8fafc",
        time_fg="#f8fafc",
        status_fg="#cbd5e1",
        countdown_fg="#70e17b",
        body_fg="#f3f4f6",
        muted_fg="#a7b0bd",
        primary_bg="#111923",
        primary_fg="#77ef83",
        primary_border="#77ef83",
        secondary_bg="#111923",
        secondary_fg="#67e8f9",
        secondary_border="#67e8f9",
        arrow_fg="#67e8f9",
        button_font="Consolas",
    ),
    DesktopCardTheme(
        theme_id="native_monochrome",
        layout="classic",
        width=570,
        height=320,
        shell_bg="#f1f1f1",
        panel_bg="#ffffff",
        border="#bfc3c7",
        divider="#d7d7d7",
        title_fg="#050505",
        time_fg="#050505",
        status_fg="#161616",
        countdown_fg="#d9531e",
        body_fg="#101010",
        muted_fg="#5f6368",
        primary_bg="#0b0b0b",
        primary_fg="#ffffff",
        primary_border="#0b0b0b",
        secondary_bg="#ffffff",
        secondary_fg="#111111",
        secondary_border="#9ca3af",
        arrow_fg="#111111",
    ),
    DesktopCardTheme(
        theme_id="calm_dense_light",
        layout="dense",
        width=620,
        height=320,
        shell_bg="#dce8f4",
        panel_bg="#f2f7fb",
        border="#b9cad9",
        divider="#c5d2dd",
        title_fg="#0f4c35",
        time_fg="#0f6f85",
        status_fg="#3e4a55",
        countdown_fg="#0f7a44",
        body_fg="#1f2937",
        muted_fg="#667482",
        primary_bg="#0f5132",
        primary_fg="#ffffff",
        primary_border="#0f5132",
        secondary_bg="#eef5fa",
        secondary_fg="#0f6f85",
        secondary_border="#7aa7b5",
        arrow_fg="#0f6f85",
    ),
    DesktopCardTheme(
        theme_id="quiet_white_slip",
        layout="classic",
        width=560,
        height=300,
        shell_bg="#edf1f3",
        panel_bg="#ffffff",
        border="#d5dadd",
        divider="#e2e5e7",
        title_fg="#12613f",
        time_fg="#12613f",
        status_fg="#4b5563",
        countdown_fg="#12613f",
        body_fg="#111111",
        muted_fg="#6b7280",
        primary_bg="#14703f",
        primary_fg="#ffffff",
        primary_border="#14703f",
        secondary_bg="#ffffff",
        secondary_fg="#174c35",
        secondary_border="#a7b0ad",
        arrow_fg="#174c35",
    ),
    DesktopCardTheme(
        theme_id="midnight_mint",
        layout="classic",
        width=590,
        height=320,
        shell_bg="#151f26",
        panel_bg="#20282e",
        border="#4c5860",
        divider="#3a444b",
        title_fg="#9ce7bb",
        time_fg="#9ce7bb",
        status_fg="#c8d0d5",
        countdown_fg="#9ce7bb",
        body_fg="#f1f5f9",
        muted_fg="#aeb8bf",
        primary_bg="#20282e",
        primary_fg="#a7f3c1",
        primary_border="#80dba5",
        secondary_bg="#20282e",
        secondary_fg="#c8d0d5",
        secondary_border="#5b6770",
        arrow_fg="#a7f3c1",
        button_font="Consolas",
    ),
    DesktopCardTheme(
        theme_id="precision_status",
        layout="dense",
        width=630,
        height=300,
        shell_bg="#d9e3eb",
        panel_bg="#edf3f7",
        border="#b8c6d0",
        divider="#c4ced6",
        title_fg="#1f2937",
        time_fg="#1f2937",
        status_fg="#35404b",
        countdown_fg="#c94c16",
        body_fg="#1f2937",
        muted_fg="#5f6b76",
        primary_bg="#0f6b43",
        primary_fg="#ffffff",
        primary_border="#0f6b43",
        secondary_bg="#edf3f7",
        secondary_fg="#1f2937",
        secondary_border="#8795a1",
        arrow_fg="#1f2937",
    ),
    DesktopCardTheme(
        theme_id="blue_glass_classic",
        layout="classic",
        width=600,
        height=330,
        shell_bg="#cddff4",
        panel_bg="#eaf4ff",
        border="#aec4dc",
        divider="#c1d2e3",
        title_fg="#111827",
        time_fg="#0f5db8",
        status_fg="#1f2937",
        countdown_fg="#0f7a44",
        body_fg="#111827",
        muted_fg="#59677a",
        primary_bg="#0f5db8",
        primary_fg="#ffffff",
        primary_border="#0f5db8",
        secondary_bg="#edf6ff",
        secondary_fg="#0f5db8",
        secondary_border="#94adc8",
        arrow_fg="#0f5db8",
    ),
    DesktopCardTheme(
        theme_id="compact_dark_strip",
        layout="strip",
        width=720,
        height=250,
        shell_bg="#0b1419",
        panel_bg="#111c22",
        border="#46545d",
        divider="#34414a",
        title_fg="#f8fafc",
        time_fg="#67d7f5",
        status_fg="#c9d1d9",
        countdown_fg="#72d65f",
        body_fg="#f1f5f9",
        muted_fg="#a2adb8",
        primary_bg="#111c22",
        primary_fg="#72d65f",
        primary_border="#72d65f",
        secondary_bg="#111c22",
        secondary_fg="#67d7f5",
        secondary_border="#67d7f5",
        arrow_fg="#67d7f5",
        button_font="Consolas",
    ),
)

DESKTOP_CARD_THEME_IDS = tuple(theme.theme_id for theme in DESKTOP_CARD_THEMES)
THEMES_BY_ID = {theme.theme_id: theme for theme in DESKTOP_CARD_THEMES}

THEME_ALIASES = {
    "auto": DEFAULT_DESKTOP_CARD_THEME,
    "daily": DEFAULT_DESKTOP_CARD_THEME,
    "rotate": DEFAULT_DESKTOP_CARD_THEME,
    "rotate-daily": DEFAULT_DESKTOP_CARD_THEME,
    "rotate_daily": DEFAULT_DESKTOP_CARD_THEME,
}


def normalize_desktop_card_theme(value: Any) -> str:
    if value is None:
        return DEFAULT_DESKTOP_CARD_THEME
    raw = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if not raw:
        return DEFAULT_DESKTOP_CARD_THEME
    if raw.isdigit():
        index = int(raw)
        if 1 <= index <= len(DESKTOP_CARD_THEME_IDS):
            return DESKTOP_CARD_THEME_IDS[index - 1]
    if raw in THEME_ALIASES:
        return THEME_ALIASES[raw]
    if raw in THEMES_BY_ID:
        return raw
    raise ValueError(
        "desktop_card_theme must be rotate_daily, a theme id, or a number from 1 to 10"
    )


def resolve_desktop_card_theme(value: Any, reference: date | datetime | None = None) -> DesktopCardTheme:
    theme_id = normalize_desktop_card_theme(value)
    if theme_id != DEFAULT_DESKTOP_CARD_THEME:
        return THEMES_BY_ID[theme_id]

    current_date = _to_date(reference)
    offset = current_date.toordinal() - ROTATION_START_DATE.toordinal()
    return DESKTOP_CARD_THEMES[offset % len(DESKTOP_CARD_THEMES)]


def _to_date(value: date | datetime | None) -> date:
    if value is None:
        return datetime.now().date()
    if isinstance(value, datetime):
        return value.date()
    return value
