from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MealVoiceProfile:
    profile_id: str
    title: str


DEFAULT_MEAL_VOICE_PROFILE = "male_commander"

MEAL_VOICE_PROFILES: tuple[MealVoiceProfile, ...] = (
    MealVoiceProfile("male_jarvis", "мужской ассистент EN"),
    MealVoiceProfile("male_commander", "мужской командный EN"),
    MealVoiceProfile("female_sonia", "женский британский Sonia"),
    MealVoiceProfile("female_libby", "женский британский Libby"),
    MealVoiceProfile("female_ava", "женский американский Ava"),
    MealVoiceProfile("female_aria", "женский американский Aria"),
    MealVoiceProfile("female_svetlana", "женский русский Svetlana"),
)

_PROFILE_BY_ID = {profile.profile_id: profile for profile in MEAL_VOICE_PROFILES}
_PROFILE_INDEX_BY_ID = {
    profile.profile_id: index
    for index, profile in enumerate(MEAL_VOICE_PROFILES, start=1)
}
_ALIASES: dict[str, str] = {
    str(index): profile.profile_id
    for index, profile in enumerate(MEAL_VOICE_PROFILES, start=1)
}
_ALIASES.update(
    {
        "jarvis": "male_jarvis",
        "assistant": "male_jarvis",
        "commander": "male_commander",
        "sonia": "female_sonia",
        "libby": "female_libby",
        "ava": "female_ava",
        "aria": "female_aria",
        "svetlana": "female_svetlana",
    }
)


def load_active_meal_voice_profile(state_path: Path) -> str:
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_MEAL_VOICE_PROFILE

    profile_id = normalize_meal_voice_profile(str(data.get("active_profile", "")))
    return profile_id or DEFAULT_MEAL_VOICE_PROFILE


def set_meal_voice_profile(state_path: Path, value: str) -> str:
    profile_id = normalize_meal_voice_profile(value)
    if profile_id is None:
        return f"Не знаю такой голос: {value.strip()}.\n\n{format_meal_voice_status(state_path)}"

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"active_profile": profile_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    profile = _PROFILE_BY_ID[profile_id]
    index = _PROFILE_INDEX_BY_ID[profile_id]
    return f"Голос приема пищи переключен: {index}. {profile.profile_id} - {profile.title}."


def format_meal_voice_status(state_path: Path) -> str:
    active_id = load_active_meal_voice_profile(state_path)
    active = _PROFILE_BY_ID[active_id]
    active_index = _PROFILE_INDEX_BY_ID[active_id]
    lines = [
        "Голос приема пищи:",
        f"Активный: {active_index}. {active.profile_id} - {active.title}",
        "",
        "Варианты:",
    ]
    lines.extend(
        f"{index}. {profile.profile_id} - {profile.title}"
        for index, profile in enumerate(MEAL_VOICE_PROFILES, start=1)
    )
    lines.append("")
    lines.append("Переключение: /mv 3 или /mv female_sonia.")
    return "\n".join(lines)


def normalize_meal_voice_profile(value: str) -> str | None:
    key = _normalize_key(value)
    if not key:
        return None
    if key in _PROFILE_BY_ID:
        return key
    return _ALIASES.get(key)


def _normalize_key(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", value.strip().lower()).strip("_")
