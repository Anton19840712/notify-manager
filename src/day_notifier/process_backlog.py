from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


MAIN_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
EXCEL_EPOCH = datetime(1899, 12, 30)

DONE_STATUSES = {
    "done",
    "closed",
    "archive",
    "archived",
    "cancelled",
    "canceled",
    "сделано",
    "закрыто",
    "архив",
    "отмена",
    "отменено",
}
TODAY_STATUSES = {"today", "active", "now", "сегодня", "сейчас", "активно"}
TODAY_URGENCIES = {"today", "urgent", "asap", "сегодня", "срочно"}
ERRAND_CLASSES = {"errand", "external", "outside", "быт", "поручение", "внешнийвыход", "внешнеедело"}

HEADER_ALIASES = {
    "название": "title",
    "задача": "title",
    "процесс": "title",
    "чтосделать": "title",
    "title": "title",
    "name": "title",
    "класс": "process_class",
    "категория": "process_class",
    "тип": "process_class",
    "class": "process_class",
    "category": "process_class",
    "статус": "status",
    "status": "status",
    "важность": "importance",
    "priority": "importance",
    "importance": "importance",
    "срочность": "urgency",
    "urgency": "urgency",
    "дата": "due_date",
    "дедлайн": "due_date",
    "датадедлайн": "due_date",
    "duedate": "due_date",
    "deadline": "due_date",
    "повторяемость": "recurrence",
    "recurrence": "recurrence",
    "repeat": "recurrence",
    "длительность": "duration_minutes",
    "минут": "duration_minutes",
    "минуты": "duration_minutes",
    "duration": "duration_minutes",
    "durationminutes": "duration_minutes",
    "место": "place",
    "location": "place",
    "place": "place",
    "можнобатчитьс": "batch_with",
    "батч": "batch_with",
    "batchwith": "batch_with",
    "batch": "batch_with",
    "жесткийякорь": "hard_anchor",
    "якорь": "hard_anchor",
    "hardanchor": "hard_anchor",
    "комментарий": "comment",
    "comment": "comment",
    "notes": "comment",
}


@dataclass(frozen=True)
class ProcessItem:
    title: str
    process_class: str = ""
    status: str = ""
    importance: str = ""
    urgency: str = ""
    due_date: date | None = None
    recurrence: str = ""
    duration_minutes: int | None = None
    place: str = ""
    batch_with: str = ""
    hard_anchor: bool = False
    comment: str = ""

    def is_due_on(self, day: date) -> bool:
        if _normalized_token(self.status) in DONE_STATUSES:
            return False
        if _normalized_token(self.status) in TODAY_STATUSES:
            return True
        if _normalized_token(self.urgency) in TODAY_URGENCIES:
            return True
        return self.due_date is not None and self.due_date <= day


def read_process_items(path: Path) -> list[ProcessItem]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".csv":
        return _items_from_rows(_read_csv_rows(path))
    if path.suffix.lower() == ".tsv":
        return _items_from_rows(_read_csv_rows(path, delimiter="\t"))
    if path.suffix.lower() == ".xlsx":
        return _items_from_rows(_read_xlsx_rows(path))
    raise ValueError(f"Unsupported process backlog format: {path.suffix}")


def format_processes_today(items: Iterable[ProcessItem], day: date, limit: int = 12) -> str:
    due_items = [item for item in items if item.is_due_on(day)]
    if not due_items:
        return ""

    hard_items = [item for item in due_items if _is_hard_anchor(item)]
    external_items = [
        item
        for item in due_items
        if item not in hard_items and _is_external_errand(item)
    ]
    other_items = [
        item
        for item in due_items
        if item not in hard_items and item not in external_items
    ]

    lines = ["Процессы на сегодня:"]
    for item in hard_items:
        lines.append(f"- Жесткий якорь: {item.title}{_metadata_suffix(item)}")

    if external_items:
        places = _unique_nonempty(item.place or item.title for item in external_items)
        duration = _sum_duration(external_items)
        titles = "; ".join(item.title for item in external_items)
        lines.append(f"- Внешний выход: {' + '.join(places)}{_duration_suffix(duration)}: {titles}.")

    for item in other_items:
        label = _class_label(item.process_class)
        lines.append(f"- {label}: {item.title}{_metadata_suffix(item)}")

    if len(lines) > limit + 1:
        omitted = len(lines) - limit - 1
        lines = lines[: limit + 1]
        lines.append(f"- Еще процессов: {omitted}.")
    return "\n".join(lines)


def _read_csv_rows(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        return [dict(row) for row in reader]


def _read_xlsx_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        sheet_path = _first_sheet_path(archive)
        shared_strings = _shared_strings(archive)
        rows = _worksheet_rows(archive.read(sheet_path), shared_strings)

    header_row = next((row for row in rows if any(_cell_to_text(cell) for cell in row)), [])
    if not header_row:
        return []
    header_index = rows.index(header_row)
    headers = [_canonical_header(_cell_to_text(cell)) for cell in header_row]
    result: list[dict[str, str]] = []
    for row in rows[header_index + 1 :]:
        mapped: dict[str, str] = {}
        for index, key in enumerate(headers):
            if not key:
                continue
            value = _cell_to_text(row[index]) if index < len(row) else ""
            mapped[key] = value
        if any(value.strip() for value in mapped.values()):
            result.append(mapped)
    return result


def _first_sheet_path(archive: zipfile.ZipFile) -> str:
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    first_sheet = workbook.find("x:sheets/x:sheet", MAIN_NS)
    if first_sheet is None:
        return "xl/worksheets/sheet1.xml"

    relationship_id = first_sheet.attrib.get(f"{{{OFFICE_REL_NS}}}id")
    if not relationship_id:
        return "xl/worksheets/sheet1.xml"

    rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for rel in rels.findall("r:Relationship", REL_NS):
        if rel.attrib.get("Id") == relationship_id:
            target = rel.attrib.get("Target", "worksheets/sheet1.xml")
            target = target.lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    return "xl/worksheets/sheet1.xml"


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("x:si", MAIN_NS):
        strings.append("".join(node.text or "" for node in item.findall(".//x:t", MAIN_NS)))
    return strings


def _worksheet_rows(content: bytes, shared_strings: list[str]) -> list[list[str]]:
    root = ElementTree.fromstring(content)
    rows: list[list[str]] = []
    for row in root.findall(".//x:sheetData/x:row", MAIN_NS):
        values_by_index: dict[int, str] = {}
        for cell in row.findall("x:c", MAIN_NS):
            column_index = _column_index(cell.attrib.get("r", ""))
            values_by_index[column_index] = _xlsx_cell_value(cell, shared_strings)
        if values_by_index:
            max_index = max(values_by_index)
            rows.append([values_by_index.get(index, "") for index in range(max_index + 1)])
        else:
            rows.append([])
    return rows


def _xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", MAIN_NS)).strip()

    value = cell.find("x:v", MAIN_NS)
    if value is None or value.text is None:
        return ""
    raw = value.text.strip()
    if cell_type == "s":
        try:
            return shared_strings[int(raw)].strip()
        except (IndexError, ValueError):
            return ""
    if cell_type == "b":
        return "yes" if raw == "1" else "no"
    return raw


def _items_from_rows(rows: Iterable[dict[str, object]]) -> list[ProcessItem]:
    items: list[ProcessItem] = []
    for row in rows:
        canonical = {
            _canonical_header(str(key)): _cell_to_text(value)
            for key, value in row.items()
            if key is not None and _canonical_header(str(key))
        }
        title = canonical.get("title", "").strip()
        if not title:
            continue
        items.append(
            ProcessItem(
                title=title,
                process_class=canonical.get("process_class", "").strip(),
                status=canonical.get("status", "").strip(),
                importance=canonical.get("importance", "").strip(),
                urgency=canonical.get("urgency", "").strip(),
                due_date=_parse_date(canonical.get("due_date", "")),
                recurrence=canonical.get("recurrence", "").strip(),
                duration_minutes=_parse_duration_minutes(canonical.get("duration_minutes", "")),
                place=canonical.get("place", "").strip(),
                batch_with=canonical.get("batch_with", "").strip(),
                hard_anchor=_parse_bool(canonical.get("hard_anchor", "")),
                comment=canonical.get("comment", "").strip(),
            )
        )
    return items


def _canonical_header(value: str) -> str:
    return HEADER_ALIASES.get(_normalized_token(value), "")


def _normalized_token(value: str) -> str:
    return re.sub(r"[^0-9a-zа-яё]+", "", value.strip().lower())


def _cell_to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _parse_date(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        serial = float(text)
        if serial >= 20000:
            return (EXCEL_EPOCH + timedelta(days=serial)).date()
    return None


def _parse_duration_minutes(value: str) -> int | None:
    text = value.strip().lower()
    if not text:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return int(float(text))
    if ":" in text:
        hours, minutes = text.split(":", 1)
        if hours.strip().isdigit() and minutes.strip().isdigit():
            return int(hours) * 60 + int(minutes)
    hours_match = re.search(r"(\d+)\s*ч", text)
    minutes_match = re.search(r"(\d+)\s*м", text)
    if hours_match or minutes_match:
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        return hours * 60 + minutes
    first_number = re.search(r"\d+", text)
    return int(first_number.group(0)) if first_number else None


def _parse_bool(value: str) -> bool:
    return _normalized_token(value) in {"1", "yes", "true", "y", "да", "истина", "жесткий", "жёсткий"}


def _is_hard_anchor(item: ProcessItem) -> bool:
    urgency = _normalized_token(item.urgency)
    importance = _normalized_token(item.importance)
    return item.hard_anchor or urgency in {"harddeadline", "deadline", "дедлайн"} or importance in {"critical", "критично"}


def _is_external_errand(item: ProcessItem) -> bool:
    process_class = _normalized_token(item.process_class)
    return process_class in ERRAND_CLASSES or bool(item.place and process_class in {"", "быт"})


def _metadata_suffix(item: ProcessItem) -> str:
    parts: list[str] = []
    if item.due_date is not None:
        parts.append(f"дедлайн {item.due_date.isoformat()}")
    if item.recurrence:
        parts.append(item.recurrence)
    if item.duration_minutes is not None:
        parts.append(_format_duration(item.duration_minutes))
    if item.place:
        parts.append(item.place)
    return f" ({', '.join(parts)})." if parts else "."


def _duration_suffix(minutes: int | None) -> str:
    return f" ({_format_duration(minutes)})" if minutes else ""


def _format_duration(minutes: int | None) -> str:
    if minutes is None:
        return ""
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"~{hours} ч {rest} мин"
    if hours:
        return f"~{hours} ч"
    return f"~{rest} мин"


def _sum_duration(items: Iterable[ProcessItem]) -> int | None:
    durations = [item.duration_minutes for item in items if item.duration_minutes is not None]
    return sum(durations) if durations else None


def _unique_nonempty(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        if not stripped:
            continue
        key = stripped.lower()
        if key in seen:
            continue
        result.append(stripped)
        seen.add(key)
    return result


def _class_label(process_class: str) -> str:
    token = _normalized_token(process_class)
    if token == "health":
        return "Здоровье"
    if token in {"documents", "docs", "документы"}:
        return "Документы"
    if token in {"work", "job", "работа"}:
        return "Работа"
    if token in {"learning", "study", "обучение"}:
        return "Обучение"
    return process_class.strip() or "Процесс"


def _column_index(cell_reference: str) -> int:
    letters = "".join(ch for ch in cell_reference if ch.isalpha()).upper()
    if not letters:
        return 0
    result = 0
    for char in letters:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1
