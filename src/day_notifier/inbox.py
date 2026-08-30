from __future__ import annotations

from datetime import datetime
from pathlib import Path


def append_inbox_item(path: Path, text: str, now: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = now.strftime("%Y-%m-%d %H:%M")
    with path.open("a", encoding="utf-8") as file:
        file.write(f"- [{prefix}] {text.strip()}\n")


def read_inbox_items(path: Path, limit: int = 5) -> list[str]:
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    items = [line for line in lines if line.startswith("- ")]
    return items[-limit:]

