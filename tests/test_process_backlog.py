import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from day_notifier.process_backlog import (
    format_processes_today,
    read_process_items,
)


class ProcessBacklogTests(unittest.TestCase):
    def test_reads_csv_backlog_and_normalizes_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "process-backlog.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        "Название",
                        "Класс",
                        "Статус",
                        "Важность",
                        "Срочность",
                        "Дата/дедлайн",
                        "Повторяемость",
                        "Длительность",
                        "Место",
                        "Можно батчить с",
                        "Жесткий якорь?",
                        "Комментарий",
                    ]
                )
                writer.writerow(
                    [
                        "Сходить в магазин за кока-колой",
                        "errand",
                        "today",
                        "low",
                        "today",
                        "02.09.2026",
                        "",
                        "15",
                        "магазин",
                        "Wildberries; ремонт",
                        "нет",
                        "Купить по пути.",
                    ]
                )

            items = read_process_items(path)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.title, "Сходить в магазин за кока-колой")
        self.assertEqual(item.process_class, "errand")
        self.assertEqual(item.due_date, date(2026, 9, 2))
        self.assertEqual(item.duration_minutes, 15)
        self.assertFalse(item.hard_anchor)

    def test_formats_due_processes_and_batches_external_errands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "process-backlog.csv"
            path.write_text(
                "\n".join(
                    [
                        "Название,Класс,Статус,Важность,Срочность,Дата/дедлайн,Повторяемость,Длительность,Место,Можно батчить с,Жесткий якорь?,Комментарий",
                        "Сходить в магазин за кока-колой,errand,today,low,today,2026-09-02,,15,магазин,Wildberries,no,Купить по пути.",
                        "Забрать вещи из Wildberries,errand,today,medium,today,2026-09-02,,20,Wildberries,магазин,no,Проверить срок хранения.",
                        "Забрать документы ВНЖ,documents,scheduled,critical,hard_deadline,2026-09-02,,90,МФЦ,,yes,Жесткий приход за документами.",
                        "Сдать кровь на гормоны,health,scheduled,high,date_bound,2026-09-23,every_21_days,60,лаборатория,,yes,Поставить точную дату.",
                        "Архивное дело,errand,done,low,none,2026-09-02,,5,,,,",
                    ]
                ),
                encoding="utf-8",
            )
            items = read_process_items(path)

        text = format_processes_today(items, date(2026, 9, 2))

        self.assertIn("Процессы на сегодня", text)
        self.assertIn("Внешний выход", text)
        self.assertIn("магазин", text)
        self.assertIn("Wildberries", text)
        self.assertIn("~35 мин", text)
        self.assertIn("Жесткий якорь: Забрать документы ВНЖ", text)
        self.assertNotIn("Сдать кровь", text)
        self.assertNotIn("Архивное дело", text)

    def test_missing_backlog_file_returns_empty_list_and_empty_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            items = read_process_items(Path(temp_dir) / "missing.xlsx")

        self.assertEqual(items, [])
        self.assertEqual(format_processes_today(items, date(2026, 9, 2)), "")

    def test_reads_xlsx_template_created_for_user(self):
        path = ROOT / "data" / "process-backlog.xlsx"

        items = read_process_items(path)

        titles = [item.title for item in items]
        self.assertIn("Сходить в магазин за кока-колой", titles)
        self.assertIn("Забрать вещи из Wildberries", titles)


if __name__ == "__main__":
    unittest.main()
