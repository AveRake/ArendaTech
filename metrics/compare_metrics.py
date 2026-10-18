#!/usr/bin/env python3
## @file compare_metrics.py
#  @brief Сравнение отчётов о метриках кода разных версий проекта
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 1.0
#
#  @details Скрипт читает JSON-отчёты, полученные @ref code_metrics.py,
#  и формирует:
#  - сводную таблицу метрик по версиям (CSV и Markdown);
#  - таблицы самых сложных методов каждой версии;
#  - диаграммы динамики метрик (PNG, если доступна библиотека Pillow).
#
#  @par Использование:
#  @code
#  python metrics/compare_metrics.py \
#      metrics/reports/v1.0/code-metrics-v1.0.json \
#      metrics/reports/v2.0-raw/code-metrics-v2.0-raw.json \
#      metrics/reports/v2.0/code-metrics-v2.0.json \
#      --labels "v1.0 (ЛР2)" "v2.0 (черновик)" "v2.0 (итог)" \
#      --out-dir metrics/reports/comparison --label comparison
#  @endcode

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


## @brief Загрузить JSON-отчёт о метриках
#  @param path Путь к файлу отчёта
#  @return Словарь с данными отчёта
def load_report(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


## @brief Собрать все узлы отчёта
#  @param payload Данные отчёта
#  @return Список плоских записей (уровень, модуль, имя, метрики)
def flatten_report(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def walk(node: Dict[str, Any], module: str, level: str) -> None:
        rows.append({
            "level": level,
            "module": module,
            "name": node["qualname"],
            "file": node["file"],
            "line": node["line"],
            "metrics": node["metrics"],
        })
        for child in node.get("children", []):
            child_level = "class" if child["kind"] == "class" else (
                "method" if level != "module" else "function")
            walk(child, module, child_level)

    for module in payload.get("modules", []):
        walk(module, module["qualname"], "module")
    return rows


## @brief Агрегированные показатели версии
#  @param payload Данные отчёта
#  @param rows Плоский список записей
#  @return Словарь агрегатов
def aggregate(payload: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    modules = [row for row in rows if row["level"] == "module"]
    classes = [row for row in rows if row["level"] == "class"]
    members = [row for row in rows if row["level"] in ("method", "function")]
    module_mi = [row["metrics"]["maintainability_index"] for row in modules]
    member_cc = [row["metrics"]["cyclomatic_complexity"] for row in members]
    member_mi = [row["metrics"]["maintainability_index"] for row in members]
    return {
        "modules": len(modules),
        "classes": len(classes),
        "members": len(members),
        "sloc": sum(row["metrics"]["source_lines"] for row in modules),
        "executable_lines": sum(row["metrics"]["executable_lines"]
                                for row in modules),
        "cc_total": sum(row["metrics"]["cyclomatic_complexity"]
                        for row in modules),
        "cc_max": max(member_cc, default=0),
        "cc_mean": round(sum(member_cc) / max(len(member_cc), 1), 2),
        "cc_over_10": sum(1 for value in member_cc if value > 10),
        "coupling_max": max((row["metrics"]["class_coupling"]
                             for row in classes), default=0),
        "dit_max": max((row["metrics"]["depth_of_inheritance"]
                        for row in classes), default=1),
        "mi_avg": round(sum(module_mi) / max(len(module_mi), 1), 1),
        "mi_min": round(min(module_mi, default=100.0), 1),
        "mi_green_share": round(
            100.0 * sum(1 for value in module_mi if value >= 20)
            / max(len(module_mi), 1), 1),
        "mi_members_avg": round(sum(member_mi) / max(len(member_mi), 1), 1),
        "mi_members_min": round(min(member_mi, default=100.0), 1),
        "members_red_zone": sum(1 for value in member_mi if value < 10),
        "violations": len(payload.get("violations", [])),
        "violations_by_rule": _violation_counts(payload.get("violations", [])),
    }


## @brief Количество нарушений по правилам
#  @param violations Список нарушений
#  @return Словарь «правило → количество»
def _violation_counts(violations: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for violation in violations:
        counts[violation["rule"]] = counts.get(violation["rule"], 0) + 1
    return counts


## @brief Самые сложные методы версии
#  @param rows Плоский список записей
#  @param limit Сколько методов вернуть
#  @return Список записей, отсортированный по убыванию CC
def top_members(rows: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    members = [row for row in rows if row["level"] in ("method", "function")]
    return sorted(members,
                  key=lambda row: row["metrics"]["cyclomatic_complexity"],
                  reverse=True)[:limit]


## @brief Записать сводную таблицу сравнения в CSV
#  @param labels Подписи версий
#  @param aggregates Агрегаты по версиям
#  @param path Путь к CSV-файлу
def write_csv(labels: Sequence[str], aggregates: Sequence[Dict[str, Any]],
              path: Path) -> None:
    keys = [
        ("modules", "Модулей"),
        ("classes", "Классов"),
        ("members", "Методов и функций"),
        ("sloc", "SLOC"),
        ("executable_lines", "Строк исполняемого кода"),
        ("cc_total", "Суммарная CC"),
        ("cc_max", "Максимальная CC метода"),
        ("cc_mean", "Средняя CC метода"),
        ("cc_over_10", "Методов со CC > 10"),
        ("coupling_max", "Максимальная связанность класса"),
        ("dit_max", "Максимальная глубина наследования"),
        ("mi_avg", "Средний MI модулей"),
        ("mi_min", "Минимальный MI модуля"),
        ("mi_members_avg", "Средний MI методов"),
        ("mi_members_min", "Минимальный MI метода"),
        ("members_red_zone", "Методов в красной зоне MI"),
        ("violations", "Нарушений правил"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["Показатель"] + list(labels))
        for key, title in keys:
            writer.writerow([title] + [aggregate[key] for aggregate in aggregates])


## @brief Записать сводку сравнения в Markdown
#  @param labels Подписи версий
#  @param aggregates Агрегаты по версиям
#  @param tops Самые сложные методы по версиям
#  @param path Путь к md-файлу
def write_markdown(labels: Sequence[str], aggregates: Sequence[Dict[str, Any]],
                   tops: Sequence[List[Dict[str, Any]]], path: Path) -> None:
    keys = [
        ("modules", "Модулей"),
        ("classes", "Классов"),
        ("members", "Методов и функций"),
        ("sloc", "SLOC"),
        ("executable_lines", "Строк исполняемого кода"),
        ("cc_total", "Суммарная CC"),
        ("cc_max", "Максимальная CC метода"),
        ("cc_mean", "Средняя CC метода"),
        ("cc_over_10", "Методов со CC > 10"),
        ("coupling_max", "Максимальная связанность класса"),
        ("dit_max", "Максимальная глубина наследования"),
        ("mi_avg", "Средний MI модулей"),
        ("mi_min", "Минимальный MI модуля"),
        ("mi_members_avg", "Средний MI методов"),
        ("mi_members_min", "Минимальный MI метода"),
        ("members_red_zone", "Методов в красной зоне MI"),
        ("violations", "Нарушений правил"),
    ]
    header = "| Показатель | " + " | ".join(labels) + " |"
    separator = "|---|" + "---|" * len(labels)
    lines = ["# Сравнение метрик кода", "", header, separator]
    for key, title in keys:
        values = " | ".join(str(aggregate[key]) for aggregate in aggregates)
        lines.append(f"| {title} | {values} |")
    lines += ["", "## Самые сложные методы", ""]
    for label, top in zip(labels, tops):
        lines += [f"### {label}", "",
                  "| Метод | Файл:строка | CC | MI | Связанность |",
                  "|---|---|---|---|---|"]
        for row in top:
            metrics = row["metrics"]
            lines.append(
                f"| `{row['name']}` | {row['file']}:{row['line']} | "
                f"{metrics['cyclomatic_complexity']} | "
                f"{metrics['maintainability_index']:.1f} | "
                f"{metrics['class_coupling']} |")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


## @brief Нарисовать сгруппированную столбчатую диаграмму
#  @param path Путь к PNG-файлу
#  @param categories Подписи по оси X
#  @param series Пары «название серии → значения»
#  @param title Заголовок диаграммы
#  @param ylabel Подпись оси Y
#  @return True, если диаграмма построена
def draw_chart(path: Path, categories: Sequence[str],
               series: Sequence[Tuple[str, Sequence[float]]],
               title: str, ylabel: str) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:  # pragma: no cover - Pillow необязательна
        return False
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    title_font = (ImageFont.truetype(str(font_path), 20)
                  if font_path.exists() else ImageFont.load_default())
    label_font = (ImageFont.truetype(str(font_path), 14)
                  if font_path.exists() else ImageFont.load_default())
    width, height = 900, 480
    left, top, bottom = 90, 60, 90
    plot_width = width - left - 40
    plot_height = height - top - bottom
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((left, 18), title, fill="#1f2937", font=title_font)
    maximum = max([value for _, values in series for value in values] + [1.0])
    step = plot_width / max(len(categories), 1)
    bar_width = step / (len(series) + 1)
    palette = ["#94a3b8", "#f59e0b", "#2563eb", "#16a34a"]
    draw.line((left, top + plot_height, left + plot_width, top + plot_height),
              fill="#374151", width=2)
    for index, category in enumerate(categories):
        for series_index, (name, values) in enumerate(series):
            value = values[index]
            bar_height = plot_height * (value / maximum)
            x = left + index * step + bar_width * (series_index + 0.5)
            y = top + plot_height - bar_height
            draw.rectangle((x, y, x + bar_width * 0.9, top + plot_height),
                           fill=palette[series_index % len(palette)])
            draw.text((x, y - 18), f"{value:g}", fill="#111827", font=label_font)
        draw.text((left + index * step + step * 0.25, top + plot_height + 10),
                  category, fill="#111827", font=label_font)
    draw.text((10, top + plot_height / 2), ylabel, fill="#111827",
              font=label_font)
    for series_index, (name, _) in enumerate(series):
        x = left + series_index * 260
        y = height - 34
        draw.rectangle((x, y, x + 18, y + 18),
                       fill=palette[series_index % len(palette)])
        draw.text((x + 24, y), name, fill="#111827", font=label_font)
    image.save(path)
    return True


## @brief Точка входа скрипта сравнения
#  @param argv Аргументы командной строки
#  @return Код возврата
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="compare_metrics.py",
        description="Сравнение метрик кода разных версий проекта «АрендаТех».")
    parser.add_argument("reports", nargs="+", help="JSON-отчёты code_metrics.py")
    parser.add_argument("--labels", nargs="+", required=True,
                        help="Подписи версий в том же порядке")
    parser.add_argument("--out-dir", default="metrics/reports/comparison")
    parser.add_argument("--label", default="comparison")
    args = parser.parse_args(argv)

    if len(args.reports) != len(args.labels):
        print("Число отчётов и подписей должно совпадать", file=sys.stderr)
        return 2

    payloads = [load_report(Path(item)) for item in args.reports]
    rows_by_version = [flatten_report(payload) for payload in payloads]
    aggregates = [aggregate(payload, rows)
                  for payload, rows in zip(payloads, rows_by_version)]
    tops = [top_members(rows) for rows in rows_by_version]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.labels, aggregates, out_dir / f"{args.label}.csv")
    write_markdown(args.labels, aggregates, tops, out_dir / f"{args.label}.md")
    (out_dir / f"{args.label}.json").write_text(
        json.dumps({"labels": args.labels, "aggregates": aggregates},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    draw_chart(out_dir / "chart-maintainability.png", args.labels,
               [("Минимальный MI модуля", [item["mi_min"] for item in aggregates]),
                ("Модулей в зелёной зоне, %", [item["mi_green_share"] for item in aggregates])],
               "Сопровождаемость кода по версиям проекта", "MI, баллы / %")
    draw_chart(out_dir / "chart-complexity.png", args.labels,
               [("Максимальная CC метода", [item["cc_max"] for item in aggregates]),
                ("Нарушений правил", [item["violations"] for item in aggregates])],
               "Сложность и нарушения правил по версиям проекта", "значение")

    for label, aggregate_row in zip(args.labels, aggregates):
        print(f"{label}: SLOC={aggregate_row['sloc']}, "
              f"CC_max={aggregate_row['cc_max']}, "
              f"MI_avg={aggregate_row['mi_avg']}, "
              f"violations={aggregate_row['violations']}")
    print(f"Результаты сохранены в {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
