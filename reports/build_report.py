#!/usr/bin/env python3
## @file build_report.py
#  @brief Генератор отчёта по лабораторной работе №3 (метрики кода)
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 1.0
#
#  @details Скрипт собирает документ .docx из данных, сохранённых
#  инструментом @c metrics/code_metrics.py: таблицы метрик, список нарушений
#  порогов и диаграммы берутся из JSON-отчётов, поэтому отчёт всегда
#  согласован с результатами измерений.
#
#  @par Запуск (из каталога проекта):
#  @code
#  python reports/build_report.py
#  @endcode

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "metrics" / "reports"
OUT_PATH = ROOT / "reports" / "ЛР3_Отчет_метрики_кода.docx"

FONT = "Times New Roman"
MONO = "Courier New"
BODY_SIZE = 14
TABLE_SIZE = 10.5
CODE_SIZE = 9

V1 = json.loads((REPORTS / "v1.0" / "code-metrics-v1.0.json").read_text(encoding="utf-8"))
RAW = json.loads((REPORTS / "v2.0-raw" / "code-metrics-v2.0-raw.json").read_text(encoding="utf-8"))
FIN = json.loads((REPORTS / "v2.0" / "code-metrics-v2.0.json").read_text(encoding="utf-8"))
CMP = json.loads((REPORTS / "comparison" / "comparison.json").read_text(encoding="utf-8"))
AGG = dict(zip(CMP["labels"], CMP["aggregates"]))


## @brief Отформатировать число с русским десятичным разделителем
def ru(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


## @brief Плоский список узлов отчёта
def flatten(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def walk(node: Dict[str, Any], module: str, level: str) -> None:
        rows.append({"level": level, "module": module, "node": node})
        for child in node.get("children", []):
            child_level = "class" if child["kind"] == "class" else (
                "method" if level != "module" else "function")
            walk(child, module, child_level)

    for module in payload["modules"]:
        walk(module, module["qualname"], "module")
    return rows


V1_ROWS = flatten(V1)
RAW_ROWS = flatten(RAW)
FIN_ROWS = flatten(FIN)


## @brief Найти метрики узла по полному имени
def find_metrics(rows: Sequence[Dict[str, Any]], qualname: str) -> Dict[str, Any]:
    for row in rows:
        if row["node"]["qualname"] == qualname:
            return row["node"]["metrics"]
    raise KeyError(qualname)


## @brief Краткое имя модуля без пути снимка
def short_module(path: str) -> str:
    return path.split("src/", 1)[-1] if "src/" in path else path


## @brief Установить фон ячейки таблицы
def shade_cell(cell, color: str) -> None:
    element = OxmlElement("w:shd")
    element.set(qn("w:val"), "clear")
    element.set(qn("w:color"), "auto")
    element.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(element)


## @brief Добавить номер страницы в колонтитул
def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)
    run.font.name = FONT
    run.font.size = Pt(11)


## @brief Настроить стили и параметры страницы документа
def setup_document(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    style = document.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(BODY_SIZE)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_after = Pt(0)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(footer)


## @brief Добавить абзац основного текста
def body(document: Document, text: str, *, bold: bool = False,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent: float = 1.25,
         size: int = BODY_SIZE, space_before: int = 0, space_after: int = 0,
         italic: bool = False) -> Any:
    paragraph = document.add_paragraph()
    paragraph.alignment = align
    paragraph.paragraph_format.first_line_indent = Cm(indent)
    paragraph.paragraph_format.space_before = Pt(space_before)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.5
    run = paragraph.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return paragraph


## @brief Добавить заголовок раздела
def heading(document: Document, text: str, *, size: int = BODY_SIZE,
            center: bool = True, space_before: int = 14,
            space_after: int = 8) -> Any:
    paragraph = document.add_paragraph()
    paragraph.alignment = (WD_ALIGN_PARAGRAPH.CENTER if center
                           else WD_ALIGN_PARAGRAPH.LEFT)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(space_before)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = True
    return paragraph


## @brief Добавить маркированный пункт («– …»)
def bullet(document: Document, text: str) -> Any:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.left_indent = Cm(1.25)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.5
    run = paragraph.add_run("– " + text)
    run.font.name = FONT
    run.font.size = Pt(BODY_SIZE)
    return paragraph


## @brief Добавить подпись таблицы
def table_caption(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(12)
    run.italic = True


## @brief Добавить подпись рисунка
def figure_caption(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(10)
    run = paragraph.add_run(text)
    run.font.name = FONT
    run.font.size = Pt(12)
    run.italic = True


## @brief Добавить таблицу с заголовком
def add_table(document: Document, headers: Sequence[str],
              rows: Sequence[Sequence[str]], widths: Sequence[float],
              font_size: float = TABLE_SIZE,
              align: Sequence[str] = None) -> None:
    align = list(align) if align is not None else ["left"] * len(headers)
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header_cells = table.rows[0].cells
    for index, title in enumerate(headers):
        header_cells[index].text = ""
        paragraph = header_cells[index].paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        run = paragraph.add_run(title)
        run.font.name = FONT
        run.font.size = Pt(font_size)
        run.bold = True
        shade_cell(header_cells[index], "E8EDF3")
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = ""
            paragraph = cells[index].paragraphs[0]
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.alignment = {
                "left": WD_ALIGN_PARAGRAPH.LEFT,
                "center": WD_ALIGN_PARAGRAPH.CENTER,
                "right": WD_ALIGN_PARAGRAPH.RIGHT,
            }[align[index]]
            run = paragraph.add_run(str(value))
            run.font.name = FONT
            run.font.size = Pt(font_size)
    # фиксированная разметка: иначе Word/LibreOffice пересчитывают ширины
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    table._tbl.tblPr.append(layout)
    # повторять строку заголовка при переносе таблицы на следующую страницу
    header_row = table.rows[0]._tr
    header_props = header_row.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    header_props.append(repeat)
    for index, width in enumerate(widths):
        table.columns[index].width = Cm(width)
        for cell in table.columns[index].cells:
            cell.width = Cm(width)
    document.add_paragraph().paragraph_format.space_after = Pt(0)


## @brief Добавить листинг кода
def add_code(document: Document, lines: Sequence[str], *, caption: str = "") -> None:
    if caption:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_with_next = True
        run = paragraph.add_run(caption)
        run.font.name = FONT
        run.font.size = Pt(12)
        run.italic = True
    table = document.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    cell.width = Cm(16.5)
    shade_cell(cell, "F5F6F8")
    cell.paragraphs[0].text = ""
    first = True
    for line in lines:
        paragraph = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run(line if line else " ")
        run.font.name = MONO
        run.font.size = Pt(CODE_SIZE)
    document.add_paragraph().paragraph_format.space_after = Pt(0)


## @brief Добавить рисунок по центру
def add_picture(document: Document, path: Path, width_cm: float) -> None:
    document.add_picture(str(path), width=Cm(width_cm))
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.paragraphs[-1].paragraph_format.space_before = Pt(6)


## @brief Титульный лист отчёта
def build_title_page(document: Document) -> None:
    header_lines = [
        "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
        "Национальный исследовательский университет «Высшая школа экономики»",
        "МИЭМ / Компьютерные системы и сети",
    ]
    for index, line in enumerate(header_lines):
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(line)
        run.font.name = FONT
        run.font.size = Pt(12 if index else 12)
        run.bold = index == 0
    for _ in range(6):
        document.add_paragraph()
    for text, size, bold in [("ОТЧЁТ", 18, True),
                             ("по лабораторной работе №3", BODY_SIZE, False),
                             ("по дисциплине «Технологии разработки программного обеспечения»",
                              BODY_SIZE, False),
                             ("Метрики программного кода", BODY_SIZE, True)]:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(6)
        run = paragraph.add_run(text)
        run.font.name = FONT
        run.font.size = Pt(size)
        run.bold = bold
    for _ in range(4):
        document.add_paragraph()
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run("Состав команды:")
    run.font.name = FONT
    run.font.size = Pt(BODY_SIZE)
    for line in ["Арсланов Вадим — аналитик/менеджер",
                 "Ильин Андрей — разработчик",
                 "Колганов Иван — тестировщик"]:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(line)
        run.font.name = FONT
        run.font.size = Pt(BODY_SIZE)
    for _ in range(4):
        document.add_paragraph()
    for text in ["Проверил: Востриков А. В.", "Москва, 2026"]:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_after = Pt(4)
        run = paragraph.add_run(text)
        run.font.name = FONT
        run.font.size = Pt(BODY_SIZE)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


## @brief Раздел 1–2: цель и постановка задачи
def build_intro(document: Document) -> None:
    heading(document, "1. ЦЕЛЬ РАБОТЫ")
    body(document,
         "Цель работы — освоить метрики программного кода как инструмент оценки "
         "и контроля качества, изучить средства автоматического измерения метрик, "
         "научиться интерпретировать результаты измерений и принимать на их основе "
         "решения о рефакторинге. Объектом измерения является учебный проект "
         "«АрендаТех» — сервис аренды техники для учебных учреждений, который "
         "команда развивает с лабораторной работы №1.")

    heading(document, "2. ПОСТАНОВКА ЗАДАЧИ")
    body(document,
         "В соответствии с методическими указаниями к лабораторной работе №3 "
         "требовалось выполнить следующие шаги:")
    for text in [
        "построить не менее пяти метрик программного кода;",
        "проанализировать полученные результаты;",
        "оптимизировать код на основе анализа метрик;",
        "повторно построить метрики для улучшенного кода;",
        "сделать выводы.",
    ]:
        bullet(document, text)
    body(document,
         "Дополнительно требовалось продолжить развитие проекта: реализовать "
         "функциональность версии 2.0 (расчёт стоимости аренды, штрафы, статусы "
         "заявок, хранение состояния, интерфейс командной строки), подготовить "
         "unit-тесты и обновить README с инструкцией по запуску.", space_before=6)

    table_caption(document, "Таблица 1 — Инструменты, использованные в работе")
    add_table(document,
              ["Инструмент", "Версия", "Назначение"],
              [["Python", "3.10", "язык реализации проекта и анализатора метрик"],
               ["metrics/code_metrics.py", "2.0", "собственный анализатор метрик кода"],
               ["metrics/compare_metrics.py", "1.0", "сравнение версий, диаграммы"],
               ["pytest", "9.1", "запуск unit-тестов (56 тестов)"],
               ["Doxygen + Graphviz", "1.18", "документация по исходному коду"]],
              [5.2, 2.0, 9.3], font_size=10.5,
              align=["left", "right", "left"])

    body(document,
         "Анализаторы качества кода .NET (правила CA1501, CA1502, CA1505, CA1506 и "
         "команда «Анализ → Рассчитать метрики кода» в Visual Studio) применимы "
         "только к управляемому коду .NET, поэтому для Python-проекта был реализован "
         "собственный анализатор. Формулы метрик взяты из документации Microsoft: "
         "индекс сопровождаемости рассчитывается по той же формуле, что и в Visual "
         "Studio, а правила CA1501/CA1502/CA1505/CA1506 настраиваются в файле "
         "CodeMetricsConfig.txt в том же формате. Выходной XML повторяет структуру "
         "отчёта Metrics.exe (CodeMetricsReport), поэтому результаты сопоставимы "
         "с отчётами .NET-инструментов.", space_before=6)


## @brief Раздел 3: теоретические сведения о метриках
def build_theory(document: Document) -> None:
    heading(document, "3. МЕТРИКИ ПРОГРАММНОГО КОДА")
    body(document,
         "Метрики кода — это числовые оценки, которые характеризуют сложность, "
         "связность и сопровождаемость исходного кода. В работе измерялись шесть "
         "метрик, которые Visual Studio вычисляет для управляемого кода, а также "
         "две дополнительные метрики, полезные при анализе.")

    table_caption(document, "Таблица 2 — Измеряемые метрики")
    add_table(document,
              ["Метрика", "Что измеряет", "Направление улучшения"],
              [["Maintainability Index (MI)",
                "интегральная оценка трудоёмкости сопровождения кода (0…100)",
                "больше — лучше"],
               ["Cyclomatic Complexity (CC)",
                "число независимых путей выполнения (число точек ветвления + 1)",
                "меньше — лучше"],
               ["Depth of Inheritance (DIT)",
                "глубина иерархии наследования до базового класса",
                "меньше — лучше"],
               ["Class Coupling",
                "число внешних классов, на которые ссылается тип",
                "меньше — лучше"],
               ["Source Lines (SLOC)",
                "строки исходного кода, включая пустые и комментарии",
                "информационная метрика"],
               ["Executable Lines (EL)",
                "строки с исполняемыми операторами",
                "информационная метрика"],
               ["Halstead Volume (V)",
                "объём кода по числу уникальных операторов и операндов",
                "меньше — лучше"],
               ["Comment Lines",
                "строки комментариев (документирующие комментарии Doxygen)",
                "информационная метрика"]],
              [4.6, 8.3, 3.6], font_size=10.5,
              align=["left", "left", "center"])

    heading(document, "3.1 Индекс сопровождаемости", center=False, size=13)
    body(document,
         "Индекс сопровождаемости вычисляется по формуле Visual Studio, где "
         "V — объём Холстеда, CC — цикломатическая сложность, SLOC — количество "
         "строк исходного кода:")
    add_code(document, [
        "MI = max(0, (171 − 5,2 · ln(V) − 0,23 · CC − 16,2 · ln(SLOC)) · 100 / 171",
    ])
    body(document,
         "Значение MI интерпретируется по цветовым зонам: зелёная зона (20…100) — "
         "код хорошо сопровождается, жёлтая (10…19) — сопровождается умеренно, "
         "красная (0…9) — код трудно сопровождать. Формула чувствительна к размеру "
         "модуля: при прочих равных файл в 300 строк получит заметно меньший MI, "
         "чем файл в 60 строк, поэтому MI — индикатор «крупных» модулей, а не только "
         "сложных алгоритмов.")

    heading(document, "3.2 Пороговые правила и их настройка", center=False, size=13)
    body(document,
         "Правила анализаторов .NET по умолчанию отключены: их включают в файле "
         "EditorConfig или в файле пороговых значений. В проекте используется второй "
         "способ — файл metrics/CodeMetricsConfig.txt, где для каждого правила "
         "задаётся порог в формате «правило: значение». Анализатор читает этот файл "
         "и формирует список нарушений.")
    table_caption(document, "Таблица 3 — Настроенные пороговые правила")
    add_table(document,
              ["Правило", "Смысл", "Порог", "Обоснование порога"],
              [["CA1501", "избыточная глубина наследования", "3",
                "иерархия пользователей двухуровневая, иерархия исключений — "
                "тоже; 3 допускает такие иерархии"],
               ["CA1502", "избыточная цикломатическая сложность", "10",
                "стандарт Microsoft: метод сложнее 10 трудно покрыть тестами"],
               ["CA1505", "код трудно сопровождать (MI ниже порога)", "20",
                "стандарт Microsoft: граница зелёной зоны MI"],
               ["CA1506", "избыточная связанность классов", "20",
                "для сервисного слоя, агрегирующего типы домена, порог выше "
                "стандартного (10)"]],
              [2.0, 5.0, 1.5, 8.0], font_size=10,
              align=["left", "left", "right", "left"])
    add_code(document, [
        "# metrics/CodeMetricsConfig.txt",
        "CA1501: 3      # глубина наследования",
        "CA1502: 10     # цикломатическая сложность метода",
        "CA1505: 20     # минимальный индекс сопровождаемости",
        "CA1506: 20     # связанность классов",
    ], caption="Листинг 1 — Конфигурация порогов")

    heading(document, "3.3 Особенности применения метрик к Python-коду",
            center=False, size=13)
    body(document, "Поскольку проект написан на Python, часть метрик вычисляется "
                   "по эвристикам, которые зафиксированы в документации анализатора:")
    for text in [
        "CC = 1 + число точек ветвления: if, for, while, except, assert, "
        "тернарный оператор, and/or, генераторы списков, ветви match;",
        "DIT = 1 + глубина базового класса внутри проекта; для класса без базовых "
        "классов DIT = 1;",
        "Class Coupling = число уникальных имён классов (с заглавной буквы) в "
        "аннотациях, базовых классах и теле типа; константы (UPPER_CASE) и "
        "generic-типы typing (List, Optional) не учитываются;",
        "Halstead Volume оценивается по потоку токенов (tokenize): уникальные и "
        "общие количества операторов и операндов;",
        "SLOC учитывает все строки файла, включая документирующие комментарии, "
        "поэтому подробное документирование снижает MI — это известное ограничение "
        "метрики.",
    ]:
        bullet(document, text)


## @brief Раздел 4: методика измерений
def build_method(document: Document) -> None:
    heading(document, "4. МЕТОДИКА ИЗМЕРЕНИЙ")
    body(document,
         "Измерения выполнялись одним и тем же инструментом с одинаковыми порогами "
         "для трёх состояний проекта, поэтому результаты сопоставимы:")
    for text in [
        "v1.0 — состояние проекта после лабораторной работы №2 (снимок хранится в "
        "metrics/snapshots/v1_0);",
        "v2.0-черновик — первая реализация новой функциональности: весь функционал "
        "находился в классе RentalService (снимок metrics/snapshots/v2_0_raw);",
        "v2.0-итог — версия после рефакторинга по результатам анализа метрик "
        "(каталог src).",
    ]:
        bullet(document, text)
    body(document,
         "Анализировался только каталог src: тесты, документация и сами инструменты "
         "измерений в расчёт не включались, чтобы метрики отражали сопровождаемость "
         "приложения.", space_before=6)

    heading(document, "4.1 Запуск измерений", center=False, size=13)
    add_code(document, [
        "# метрики текущей версии: XML, CSV, Markdown и JSON",
        "python metrics/code_metrics.py src --root . \\",
        "    --out-dir metrics/reports/v2.0 --label code-metrics-v2.0",
        "",
        "# проверка в стиле CI: код возврата 1 при нарушениях порогов",
        "python metrics/code_metrics.py src --root . --fail-on-violation",
        "",
        "# сравнение версий и построение диаграмм",
        "python metrics/compare_metrics.py \\",
        "    metrics/reports/v1.0/code-metrics-v1.0.json \\",
        "    metrics/reports/v2.0-raw/code-metrics-v2.0-raw.json \\",
        "    metrics/reports/v2.0/code-metrics-v2.0.json \\",
        "    --labels \"v1.0 (ЛР2)\" \"v2.0 черновик\" \"v2.0 итог\"",
    ], caption="Листинг 2 — Команды запуска измерений")

    body(document, "Отчёт сохраняется в четырёх форматах:")
    table_caption(document, "Таблица 4 — Форматы отчётов о метриках")
    add_table(document,
              ["Файл", "Содержание"],
              [["*.xml", "дерево CodeMetricsReport (как у Metrics.exe) и блок RuleViolations"],
               ["*.csv", "построчная таблица метрик по модулям, классам и методам"],
               ["*.md", "сводка для отчёта и таблица нарушений"],
               ["*.json", "полное дерево метрик для сравнения версий"]],
              [2.2, 14.3], font_size=10.5, align=["left", "left"])

    heading(document, "4.2 Ограничения методики", center=False, size=13)
    for text in [
        "MI агрегируется по формуле для модуля и типа, поэтому крупные модули "
        "получают заниженную оценку даже при простых методах; для решений "
        "использовалась также метрика MI отдельных методов;",
        "Class Coupling учитывает только классы: связанность через строковые "
        "константы и словари метрика не видит, что важно для анализа первой "
        "версии (см. раздел 6);",
        "Halstead Volume для Python — оценка по токенам, а не по инструкциям "
        "виртуальной машины, поэтому абсолютные значения отличаются от .NET-аналога, "
        "но сравнение версий между собой корректно.",
    ]:
        bullet(document, text)


## @brief Таблица модулей версии
def module_table(document: Document, payload: Dict[str, Any],
                 caption: str) -> None:
    table_caption(document, caption)
    rows = []
    for module in payload["modules"]:
        metrics = module["metrics"]
        rows.append([
            short_module(module["file"]),
            metrics["source_lines"],
            metrics["executable_lines"],
            metrics["cyclomatic_complexity"],
            metrics["class_coupling"],
            metrics["depth_of_inheritance"],
            ru(metrics["maintainability_index"]),
            zone(metrics["maintainability_index"]),
        ])
    add_table(document,
              ["Модуль", "SLOC", "EL", "CC", "Связ.", "DIT", "MI", "Зона"],
              rows, [6.6, 1.4, 1.2, 1.2, 1.4, 1.2, 1.5, 2.0], font_size=9.5,
              align=["left", "right", "right", "right", "right", "right",
                     "right", "center"])


## @brief Название цветовой зоны MI
def zone(value: float) -> str:
    if value >= 20:
        return "зелёная"
    if value >= 10:
        return "жёлтая"
    return "красная"


## @brief Таблица нарушений пороговых правил
def violations_table(document: Document, payload: Dict[str, Any],
                     caption: str) -> None:
    table_caption(document, caption)
    rows = []
    for violation in payload["violations"]:
        rows.append([
            violation["rule"],
            violation["title"],
            violation["entity"],
            ru(violation["value"], 1),
            f'{violation["threshold"]:g}',
        ])
    add_table(document,
              ["Правило", "Нарушение", "Сущность", "Значение", "Порог"],
              rows, [1.8, 5.6, 5.4, 2.0, 1.7], font_size=9.5,
              align=["left", "left", "left", "right", "right"])


## @brief Таблица самых сложных методов
def top_table(document: Document, rows: List[Dict[str, Any]],
              caption: str, limit: int = 5) -> None:
    table_caption(document, caption)
    members = [row for row in rows if row["level"] in ("method", "function")]
    members.sort(key=lambda row: row["node"]["metrics"]["cyclomatic_complexity"],
                 reverse=True)
    data = []
    for row in members[:limit]:
        node = row["node"]
        metrics = node["metrics"]
        data.append([
            node["qualname"],
            f'{short_module(node["file"])}:{node["line"]}',
            metrics["cyclomatic_complexity"],
            ru(metrics["maintainability_index"]),
        ])
    add_table(document, ["Метод", "Файл:строка", "CC", "MI"], data,
              [6.6, 5.2, 1.6, 1.8], font_size=9.5,
              align=["left", "left", "right", "right"])


## @brief Раздел 5: результаты до оптимизации
def build_before(document: Document) -> None:
    heading(document, "5. РЕЗУЛЬТАТЫ ДО ОПТИМИЗАЦИИ")

    heading(document, "5.1 Версия 1.0 (после лабораторной работы №2)",
            center=False, size=13)
    body(document,
         "Исходная версия содержит четыре модуля предметной области и сервиса. "
         "Сложность методов минимальна, однако домен сосредоточен в одном файле "
         "объёмом 293 строки, что и определило низкий индекс сопровождаемости.")
    module_table(document, V1, "Таблица 5 — Метрики версии 1.0")
    body(document,
         "Нарушение одно: правило CA1505 для модуля domain.py — индекс "
         "сопровождаемости "
         f'{ru(find_metrics(V1_ROWS, "src.domain")["maintainability_index"])} '
         "при пороге 20 (жёлтая зона). Максимальная глубина наследования равна 3 "
         "(Technician → Administrator → Person): формально это не нарушает порог, "
         "но класс Technician не добавляет поведения — он только переопределяет роль, "
         "то есть наследование использовано там, где достаточно атрибута.")
    body(document,
         "Отдельно при подготовке измерений был обнаружен дефект: файл "
         "tests/test_domain.py начинался с постороннего символа «ё», из-за чего "
         "pytest не мог собрать тесты (NameError при импорте). Дефект исправлен, "
         "тесты переписаны и дополнены.", space_before=6)

    heading(document, "5.2 Версия 2.0, первая реализация функциональности",
            center=False, size=13)
    body(document,
         "Новая функциональность (расчёт стоимости со скидками, штрафы за просрочку, "
         "повреждение и утерю, статусы заявок, JSON-хранилище, отчётность) была "
         "реализована «первым проходом» — внутри класса RentalService и модуля "
         "domain.py. Метрики немедленно показали деградацию.")
    module_table(document, RAW, "Таблица 6 — Метрики первой реализации v2.0")
    body(document,
         "Получено шесть нарушений: два модуля оказались в красной зоне индекса "
         "сопровождаемости, а три метода превысили порог цикломатической сложности.")
    violations_table(document, RAW, "Таблица 7 — Нарушения в первой реализации v2.0")
    top_table(document, RAW_ROWS,
              "Таблица 8 — Самые сложные методы первой реализации")


## @brief Раздел 6: анализ и оптимизация
def build_optimization(document: Document) -> None:
    heading(document, "6. АНАЛИЗ И ОПТИМИЗАЦИЯ КОДА")
    body(document,
         "Анализ метрик позволил сформулировать четыре причины деградации и "
         "соответствующие им направления рефакторинга.")

    table_caption(document, "Таблица 9 — Проблемы, выявленные метриками, и решения")
    add_table(document,
              ["Проблема", "Метрика", "Решение"],
              [["return_equipment содержит 16 ветвей: просрочка, три состояния "
                "техники, разные коэффициенты ущерба",
                "CC = 16", "правила начисления штрафов (fines.py) и таблица "
                "соответствия состояний"],
               ["create_request смешивает валидацию периода, проверку "
                "доступности, бронирование и расчёт стоимости",
                "CC = 11", "сценарий RequestDesk и отдельные проверки"],
               ["build_report собирает отчёт ветвлениями в сервисе",
                "CC = 11", "класс RentalReport со статистикой"],
               ["Скидки и штрафы зашиты в условия, названия категорий — в коде",
                "CC, V", "правила DiscountRule и FineRule, коэффициенты в данных"],
               ["Сервис на 323 строки: бизнес-логика, JSON, уведомления, отчёт",
                "MI = 3,1", "фасад + сценарии + реестр + репозиторий"],
               ["Модуль domain.py на 310 строк, строковые статусы",
                "MI = 5,8", "разбиение на 8 модулей, перечисления Enum"],
               ["Глубина наследования Technician = 3",
                "DIT = 3", "класс Employee с ролью UserRole"],
               ["Ошибка в load_state: все выдачи ссылались на первую заявку",
                "тесты", "сериализация вынесена в пакет, добавлены тесты "
                "ссылочной целостности"]],
              [7.4, 2.4, 6.7], font_size=9.5,
              align=["left", "left", "left"])

    heading(document, "6.1 Скидки: правила вместо ветвлений", center=False, size=13)
    add_code(document, [
        "# v2.0-черновик: estimate_cost, CC = 8",
        "role = user.get_role()",
        "if role == \"student\":",
        "    base = base * 0.90",
        "elif role == \"teacher\":",
        "    base = base * 0.95",
        "if days > 14:",
        "    base = base * 0.90",
        "elif days > 7:",
        "    base = base * 0.95",
        "if len(units) >= 3:",
        "    base = base * 0.97",
    ], caption="Листинг 3 — Расчёт стоимости до рефакторинга")
    add_code(document, [
        "# v2.0: каждое правило — отдельный класс с одним методом",
        "class RoleDiscount:",
        "    name = \"Скидка по роли\"",
        "    def discount(self, context):",
        "        return ROLE_DISCOUNTS.get(context.role, 0.0)",
        "",
        "class LongRentalDiscount:",
        "    def discount(self, context):",
        "        for threshold, rate in LONG_RENTAL_DISCOUNTS:",
        "            if context.days > threshold:",
        "                return rate",
        "        return 0.0",
        "",
        "class PriceCalculator:",
        "    def calculate(self, units, user, days):",
        "        subtotal = self.subtotal(units, days)",
        "        multiplier = 1.0",
        "        for rule in self._rules:",
        "            multiplier *= 1.0 - rule.discount(context)",
        "        return PriceBreakdown(subtotal, round(subtotal * multiplier, 2))",
    ], caption="Листинг 4 — Расчёт стоимости после рефакторинга")

    heading(document, "6.2 Штрафы: правила и таблица состояний",
            center=False, size=13)
    body(document,
         "В черновике метод возврата содержал ветвление по состоянию техники и "
         "зашитые названия категорий («Проекторы», «Фототехника»). В итоговой версии "
         "основания штрафа оформлены правилами, коэффициент ущерба перенесён в "
         "категорию техники, а соответствие «результат возврата → новое состояние "
         "единицы» задано таблицей.")
    add_code(document, [
        "class DamageRule:",
        "    reason = FineReason.DAMAGE",
        "    def amount(self, context):",
        "        if context.condition is not ReturnCondition.DAMAGED:",
        "            return 0.0",
        "        return round(sum(unit.model.daily_rate",
        "                         * unit.model.category.damage_coefficient",
        "                         for unit in context.request.units), 2)",
        "",
        "RETURN_UNIT_STATUS = {",
        "    ReturnCondition.GOOD: UnitStatus.AVAILABLE,",
        "    ReturnCondition.DAMAGED: UnitStatus.IN_REPAIR,",
        "    ReturnCondition.LOST: UnitStatus.WRITTEN_OFF,",
        "}",
    ], caption="Листинг 5 — Правило штрафа за повреждение и таблица состояний")

    heading(document, "6.3 Статусы: перечисления и допустимые переходы",
            center=False, size=13)
    body(document,
         "Строковые статусы («На рассмотрении», «Одобрена» и т. д.) не позволяли "
         "контролировать переходы: заявку можно было закрыть без выдачи. В итоговой "
         "версии статус — перечисление, а допустимые переходы заданы таблицей, "
         "проверка выполняет один метод.")
    add_code(document, [
        "ALLOWED_TRANSITIONS = {",
        "    RequestStatus.PENDING: (RequestStatus.APPROVED, RequestStatus.REJECTED),",
        "    RequestStatus.APPROVED: (RequestStatus.ISSUED,),",
        "    RequestStatus.ISSUED: (RequestStatus.CLOSED,),",
        "    RequestStatus.REJECTED: (),",
        "    RequestStatus.CLOSED: (),",
        "}",
        "",
        "def transition(self, target):",
        "    if target not in ALLOWED_TRANSITIONS[self._status]:",
        "        raise InvalidTransition(...)",
        "    self._status = target",
    ], caption="Листинг 6 — Допустимые переходы статусов заявки")

    heading(document, "6.4 Разделение сервиса: фасад и сценарии",
            center=False, size=13)
    body(document,
         "Сервис разделён на фасад RentalService (151 строка, MI 23,8) и два сценария: "
         "RequestDesk (заявки) и IssueDesk (выдача и возврат). Общие данные хранит "
         "реестр RentalRegistry, проверка прав вынесена в функцию require_staff. "
         "Фасад только делегирует вызовы, поэтому его методы имеют CC = 1…2.")
    add_code(document, [
        "class RentalService:",
        "    def __init__(self, pricing=None, fines=None, journal=None, registry=None):",
        "        self._pricing = pricing or PriceCalculator()",
        "        self._journal = journal or NotificationJournal()",
        "        self._registry = registry or RentalRegistry()",
        "        self._request_desk = RequestDesk(self._registry, self._pricing,",
        "                                         self._journal)",
        "        self._issue_desk = IssueDesk(self._registry, self._pricing,",
        "                                     fines or FineCalculator(),",
        "                                     self._journal)",
        "",
        "    def create_request(self, user, units, start_date, end_date):",
        "        return self._request_desk.create(user, units, start_date, end_date)",
        "",
        "    def issue_equipment(self, request, employee, issue_date):",
        "        return self._issue_desk.issue(request, employee, issue_date)",
    ], caption="Листинг 7 — Фасад сервиса")

    heading(document, "6.5 Иерархия пользователей: роль вместо наследования",
            center=False, size=13)
    body(document,
         "В версии 1.0 иерархия Person → Administrator → Technician имела глубину 3, "
         "а класс Technician не добавлял ни полей, ни методов. Административные и "
         "технические роли вынесены в перечисление UserRole, сотрудники описываются "
         "классом Employee: глубина наследования снизилась до 2, дублирование "
         "исчезло, а проверка прав стала единой (require_staff).")
    add_code(document, [
        "class Employee(Person):",
        "    def __init__(self, id, fio, email, phone, employee_id,",
        "                 role=UserRole.ADMINISTRATOR):",
        "        if role not in (UserRole.ADMINISTRATOR, UserRole.TECHNICIAN):",
        "            raise ValidationError(f\"Роль «{role}» не является ролью сотрудника\")",
        "        super().__init__(id, fio, email, phone, role)",
        "        self._employee_id = employee_id",
        "",
        "    @property",
        "    def can_manage(self):",
        "        return True",
    ], caption="Листинг 8 — Единый класс сотрудника")

    heading(document, "6.6 Разбиение модулей и вынос инфраструктуры",
            center=False, size=13)
    body(document,
         "Монолитные модули разделены по зонам ответственности: domain.py (293 строки) "
         "превратился в пакет из восьми модулей (enums, errors, people, equipment, "
         "request, issue, fine, notification), а сервисный модуль — в фасад, сценарии "
         "и реестр. Сериализация вынесена в пакет serialization (5 модулей), "
         "хранилище — в repository.py с интерфейсом RentalRepository. Дополнительно "
         "исправлена ошибка восстановления состояния: в черновике все выдачи "
         "ссылались на первую заявку, теперь ссылки восстанавливаются по индексам "
         "и проверяются тестом.")
    body(document,
         "Тесты переписаны: вместо одного неработоспособного файла — семь модулей "
         "тестов (56 тестов), покрывающих предметную область, расчёт стоимости, "
         "штрафы, сервис, сериализацию, отчёты и сам анализатор метрик. Все тесты "
         "проходят.")


## @brief Раздел 7: результаты после оптимизации
def build_after(document: Document) -> None:
    heading(document, "7. РЕЗУЛЬТАТЫ ПОСЛЕ ОПТИМИЗАЦИИ")
    body(document,
         "После рефакторинга метрики перестроены тем же инструментом с теми же "
         "порогами. Нарушений правил не осталось ни одного.")
    table_caption(document, "Таблица 10 — Сравнение метрик трёх версий проекта")
    keys = [
        ("modules", "Модулей"),
        ("classes", "Классов"),
        ("members", "Методов и функций"),
        ("sloc", "SLOC"),
        ("executable_lines", "Строк исполняемого кода"),
        ("cc_total", "Суммарная CC"),
        ("cc_max", "Максимальная CC метода"),
        ("cc_mean", "Средняя CC метода"),
        ("cc_over_10", "Методов со CC больше 10"),
        ("coupling_max", "Максимальная связанность класса"),
        ("dit_max", "Максимальная глубина наследования"),
        ("mi_min", "Минимальный MI модуля"),
        ("mi_members_min", "Минимальный MI метода"),
        ("members_red_zone", "Методов в красной зоне MI"),
        ("violations", "Нарушений правил"),
    ]
    rows = []
    for key, title in keys:
        values = []
        for label in CMP["labels"]:
            value = AGG[label][key]
            values.append(ru(value, 2).rstrip("0").rstrip(",")
                          if isinstance(value, float) else str(value))
        rows.append([title] + values)
    add_table(document, ["Показатель"] + list(CMP["labels"]), rows,
              [7.0, 3.1, 3.1, 3.1], font_size=9.5,
              align=["left", "right", "right", "right"])

    body(document,
         "Динамика ключевых показателей приведена на рисунках 1 и 2: минимальный "
         "индекс сопровождаемости вырос с 13,7 до 21,0, все модули перешли в зелёную "
         "зону, максимальная цикломатическая сложность метода снизилась с 16 до 9, "
         "а число нарушений — с шести до нуля.", space_before=6)
    add_picture(document, REPORTS / "comparison" / "chart-maintainability.png", 15.5)
    figure_caption(document, "Рисунок 1 — Сопровождаемость кода по версиям проекта")
    add_picture(document, REPORTS / "comparison" / "chart-complexity.png", 15.5)
    figure_caption(document, "Рисунок 2 — Сложность и нарушения правил по версиям")

    body(document,
         "Метрики итоговой версии по модулям приведены в таблице 11: все 29 модулей "
         "находятся в зелёной зоне, максимальная связанность класса (16) не превышает "
         "порог 20 и относится к фасаду сервиса, который по определению агрегирует "
         "типы предметной области.")
    module_table(document, FIN, "Таблица 11 — Метрики итоговой версии 2.0")

    body(document,
         "Сопоставление ключевых методов, которые нарушали порог в черновике, "
         "показано в таблице 12. Сложность снизилась за счёт выделения правил и "
         "сценариев: каждый метод теперь отвечает за одну операцию.", space_before=6)
    table_caption(document, "Таблица 12 — Цикломатическая сложность ключевых методов")
    raw_metrics = find_metrics(RAW_ROWS, "RentalService.return_equipment")
    final_metrics = find_metrics(FIN_ROWS, "IssueDesk.return_equipment")
    pairs = [
        ("Расчёт стоимости аренды",
         find_metrics(RAW_ROWS, "RentalService.estimate_cost")["cyclomatic_complexity"],
         find_metrics(FIN_ROWS, "PriceCalculator.calculate")["cyclomatic_complexity"]),
        ("Создание заявки",
         find_metrics(RAW_ROWS, "RentalService.create_request")["cyclomatic_complexity"],
         find_metrics(FIN_ROWS, "RequestDesk.create")["cyclomatic_complexity"]),
        ("Выдача техники",
         find_metrics(RAW_ROWS, "RentalService.issue_equipment")["cyclomatic_complexity"],
         find_metrics(FIN_ROWS, "IssueDesk.issue")["cyclomatic_complexity"]),
        ("Возврат техники со штрафами",
         raw_metrics["cyclomatic_complexity"],
         final_metrics["cyclomatic_complexity"]),
        ("Построение отчёта",
         find_metrics(RAW_ROWS, "RentalService.build_report")["cyclomatic_complexity"],
         find_metrics(FIN_ROWS, "RentalReport.build")["cyclomatic_complexity"]),
    ]
    add_table(document, ["Операция", "CC в черновике", "CC в итоговой версии"],
              [[name, str(before), str(after)] for name, before, after in pairs],
              [8.0, 4.2, 4.3], font_size=10.5,
              align=["left", "right", "right"])

    body(document,
         "Остаточные ограничения: метод RentalReport.statistics имеет CC = 9 "
         "(близко к порогу) и может быть разделён на два метода; функция "
         "state_from_dict имеет CC = 8 и MI 51,9 — её планируется упростить за счёт "
         "фабрик по видам объектов. Эти задачи зафиксированы как план версии 2.1.",
         space_before=6)


## @brief Раздел 8: выводы
def build_conclusion(document: Document) -> None:
    heading(document, "8. ВЫВОДЫ")
    body(document, "В ходе лабораторной работы:")
    for text in [
        "освоены метрики программного кода (MI, CC, DIT, Class Coupling, SLOC, "
        "Executable Lines, Halstead Volume) и правила их пороговой проверки "
        "CA1501/CA1502/CA1505/CA1506;",
        "для Python-проекта реализован анализатор метрик, повторяющий формулы "
        "Visual Studio и формат отчёта Metrics.exe, с настраиваемыми порогами в "
        "файле CodeMetricsConfig.txt;",
        "измерения выполнены для трёх состояний проекта (v1.0, v2.0-черновик, "
        "v2.0-итог), что позволило отделить «естественный» рост сложности при "
        "добавлении функциональности от деградации архитектуры;",
        "по результатам анализа проведён рефакторинг: бизнес-правила вынесены в "
        "правила (скидки, штрафы), сценарии — в отдельные классы, монолитные модули "
        "разбиты, строковые статусы заменены перечислениями, иерархия наследования "
        "уплощена;",
        "метрики перестроены после оптимизации: нарушений порогов стало 0 вместо 6, "
        "максимальная CC метода снизилась с 16 до 9, минимальный MI модуля вырос с "
        "3,1 до 21,0, все 29 модулей находятся в зелёной зоне;",
        "подтверждено, что метрики полезны как инструмент поиска проблемных мест, "
        "но требуют интерпретации: MI чувствителен к размеру файла, а Class Coupling "
        "не учитывает связанность через строковые константы — поэтому метрики "
        "использовались вместе с анализом кода и тестами.",
    ]:
        bullet(document, text)
    body(document,
         "Практический результат работы — не только отчёт, но и работающая версия "
         "2.0 проекта: 56 модульных тестов, интерфейс командной строки, JSON-хранилище "
         "и обновлённая документация Doxygen.", space_before=6)


## @brief Список источников
def build_sources(document: Document) -> None:
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    heading(document, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")
    sources = [
        "Методические указания к лабораторной работе №3 «Метрики программного кода» "
        "по дисциплине «Технологии разработки программного обеспечения». — М.: НИУ ВШЭ, 2023.",
        "Значения метрик кода. Документация Microsoft. URL: "
        "https://learn.microsoft.com/ru-ru/visualstudio/code-quality/code-metrics-values",
        "Правила метрик кода (CA1501, CA1502, CA1505, CA1506). Документация Microsoft. "
        "URL: https://learn.microsoft.com/ru-ru/dotnet/fundamentals/code-analysis/quality-rules/",
        "Индекс удобства обслуживания (Maintainability Index): диапазон и значение. "
        "Документация Microsoft. URL: "
        "https://learn.microsoft.com/ru-ru/visualstudio/code-quality/code-metrics-maintainability-index-range-and-meaning",
        "Halstead M. H. Elements of Software Science. — New York: Elsevier, 1977.",
        "ГОСТ 19.402-78. Единая система программной документации. Описание программы.",
        "Официальная документация Python (модули ast, tokenize). URL: "
        "https://docs.python.org/3/library/ast.html",
    ]
    for index, source in enumerate(sources, start=1):
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        paragraph.paragraph_format.left_indent = Cm(0)
        paragraph.paragraph_format.first_line_indent = Cm(1.25)
        paragraph.paragraph_format.line_spacing = 1.5
        run = paragraph.add_run(f"{index}. {source}")
        run.font.name = FONT
        run.font.size = Pt(12)


## @brief Собрать документ целиком
def build() -> Path:
    document = Document()
    setup_document(document)
    build_title_page(document)
    build_intro(document)
    build_theory(document)
    build_method(document)
    build_before(document)
    build_optimization(document)
    build_after(document)
    build_conclusion(document)
    build_sources(document)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    path = build()
    print(f"Отчёт сохранён: {path}")
