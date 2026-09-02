from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BlockInfo:
    block_id: str
    title: str
    enabled: bool


@dataclass(frozen=True)
class BlockToggleResult:
    block_id: str
    title: str
    enabled: bool
    changed: bool


def load_block_overrides(path: Path) -> dict[str, bool]:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    raw_blocks = data.get("blocks", {})
    if not isinstance(raw_blocks, dict):
        return {}

    overrides: dict[str, bool] = {}
    for block_id, block in raw_blocks.items():
        if isinstance(block, bool):
            overrides[str(block_id)] = block
        elif isinstance(block, dict) and "enabled" in block:
            overrides[str(block_id)] = bool(block["enabled"])
    return overrides


def set_block_enabled(schedule_path: Path, state_path: Path, block_id: str, enabled: bool) -> BlockToggleResult:
    block_id = block_id.strip()
    blocks = _read_schedule_blocks(schedule_path)
    if block_id not in blocks:
        raise ValueError(_unknown_block_message(block_id, blocks))

    current = _effective_enabled(blocks[block_id], load_block_overrides(state_path).get(block_id))
    state = _read_state(state_path)
    state_blocks = state.setdefault("blocks", {})
    if not isinstance(state_blocks, dict):
        state_blocks = {}
        state["blocks"] = state_blocks
    state_blocks[block_id] = {"enabled": enabled}
    _write_state(state_path, state)

    return BlockToggleResult(
        block_id=block_id,
        title=_block_title(block_id, blocks[block_id]),
        enabled=enabled,
        changed=current != enabled,
    )


def block_status(schedule_path: Path, state_path: Path, block_id: str | None = None) -> str:
    blocks = _read_schedule_blocks(schedule_path)
    overrides = load_block_overrides(state_path)
    statuses = [
        BlockInfo(
            block_id=current_id,
            title=_block_title(current_id, block),
            enabled=_effective_enabled(block, overrides.get(current_id)),
        )
        for current_id, block in blocks.items()
    ]
    if block_id:
        statuses = [status for status in statuses if status.block_id == block_id]
        if not statuses:
            raise ValueError(_unknown_block_message(block_id, blocks))

    if not statuses:
        return "Подключаемых блоков пока нет."

    lines = ["Блоки:"]
    for status in statuses:
        state = "включен" if status.enabled else "выключен"
        lines.append(f"- {status.block_id}: {state} ({status.title})")
    return "\n".join(lines)


def format_block_toggle_result(result: BlockToggleResult) -> str:
    state = "включен" if result.enabled else "выключен"
    if result.changed:
        return f"Блок {state}: {result.title} ({result.block_id})."
    return f"Блок уже {state}: {result.title} ({result.block_id})."


def _read_schedule_blocks(schedule_path: Path) -> dict[str, Any]:
    data = json.loads(schedule_path.read_text(encoding="utf-8"))
    blocks = data.get("blocks", {})
    return blocks if isinstance(blocks, dict) else {}


def _read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _write_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _effective_enabled(block: Any, override: bool | None) -> bool:
    if override is not None:
        return override
    if isinstance(block, bool):
        return block
    if isinstance(block, dict):
        return bool(block.get("enabled", True))
    return True


def _block_title(block_id: str, block: Any) -> str:
    if isinstance(block, dict):
        return str(block.get("title") or block_id)
    return block_id


def _unknown_block_message(block_id: str, blocks: dict[str, Any]) -> str:
    available = ", ".join(sorted(blocks)) or "нет доступных блоков"
    return f"неизвестный блок '{block_id}'. Доступно: {available}"
