#!/usr/bin/env python3
## @file code_metrics.py
#  @brief Анализатор метрик программного кода проекта «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#  @copyright ЗАО "АБС"
#
#  @details Инструмент командной строки, который вычисляет метрики кода,
#  аналогичные метрикам Visual Studio («Анализ» → «Рассчитать метрики кода»):
#  - индекс удобства обслуживания (Maintainability Index, MI);
#  - цикломатическая сложность (Cyclomatic Complexity, CC);
#  - глубина наследования (Depth of Inheritance, DIT);
#  - связность классов (Class Coupling);
#  - строки исходного кода (Source Lines);
#  - строки исполняемого кода (Executable Lines).
#  Дополнительно вычисляются метрики Холстеда (Halstead Volume) и
#  количество строк комментариев (Comment Lines), а также проверяются
#  пороговые правила CA1501, CA1502, CA1505, CA1506 из конфигурационного
#  файла CodeMetricsConfig.txt.
#
#  @par Метрики (формулы):
#  - CC = 1 + число точек ветвления (if, for, while, except, and/or,
#    тернарный оператор, assert, comprehension, case в match);
#  - DIT = 1 + максимальная DIT базового класса (внутри проекта),
#    для класса без базовых классов DIT = 1;
#  - Class Coupling = число уникальных внешних классов, на которые
#    ссылается тип (базовые классы, аннотации, имена классов с заглавной
#    буквы, кроме собственного имени и стандартных generic-типов typing);
#  - Halstead Volume = (N1 + N2) * log2(n1 + n2), где n1/n2 — число
#    уникальных операторов/операндов, N1/N2 — общее число вхождений;
#  - MI = max(0, (171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(SLOC)) * 100 / 171);
#    диапазоны: 20..100 — зелёный, 10..19 — жёлтый, 0..9 — красный.
#
#  @par Использование:
#  @code
#  python metrics/code_metrics.py src --out-dir metrics/reports/after --label after
#  @endcode
#
#  @par Выходные форматы:
#  XML (совместим по структуре с CodeMetricsReport от Metrics.exe), CSV,
#  Markdown-сводка и JSON (используется скриптом compare_metrics.py).

from __future__ import annotations

import argparse
import ast
import builtins
import csv
import io
import json
import keyword
import math
import os
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

#: Имена из модуля typing, которые не считаются классами предметной области.
TYPING_GENERICS: Set[str] = {
    "Any", "Callable", "ClassVar", "Dict", "Final", "FrozenSet", "Generic",
    "Iterable", "Iterator", "List", "Literal", "Mapping", "MutableMapping",
    "Optional", "Protocol", "Sequence", "Set", "Tuple", "Type", "TypedDict",
    "Union", "AbstractSet", "DefaultDict", "Deque", "NamedTuple",
}

#: Имена, которые никогда не считаются внешними классами.
IGNORED_NAMES: Set[str] = set(dir(builtins)) | TYPING_GENERICS | {"self", "cls", "super"}

#: Расширения файлов, которые анализирует инструмент.
SUPPORTED_SUFFIXES = (".py",)


## @brief Набор числовых метрик одной программной сущности
@dataclass
class Metrics:
    ## @brief Индекс удобства обслуживания (0..100)
    maintainability_index: float = 100.0
    ## @brief Цикломатическая сложность
    cyclomatic_complexity: int = 1
    ## @brief Связность классов
    class_coupling: int = 0
    ## @brief Глубина наследования
    depth_of_inheritance: int = 1
    ## @brief Строки исходного кода (включая пустые и комментарии)
    source_lines: int = 0
    ## @brief Строки исполняемого кода
    executable_lines: int = 0
    ## @brief Объём Холстеда
    halstead_volume: float = 0.0
    ## @brief Строки комментариев
    comment_lines: int = 0

    ## @brief Представить метрики в виде словаря
    #  @return Словарь «имя метрики → значение»
    def as_dict(self) -> Dict[str, Any]:
        return {
            "maintainability_index": round(self.maintainability_index, 2),
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "class_coupling": self.class_coupling,
            "depth_of_inheritance": self.depth_of_inheritance,
            "source_lines": self.source_lines,
            "executable_lines": self.executable_lines,
            "halstead_volume": round(self.halstead_volume, 2),
            "comment_lines": self.comment_lines,
        }


## @brief Узел дерева метрик: модуль, класс или метод
@dataclass
class Node:
    ## @brief Тип узла: module, class, function
    kind: str
    ## @brief Локальное имя сущности
    name: str
    ## @brief Полное (квалифицированное) имя сущности
    qualname: str
    ## @brief Путь к файлу относительно корня проекта
    file: str
    ## @brief Номер строки объявления
    line: int
    ## @brief Метрики сущности
    metrics: Metrics = field(default_factory=Metrics)
    ## @brief Вложенные сущности (классы и методы)
    children: List["Node"] = field(default_factory=list)
    ## @brief Сигнатура метода (используется в отчётах)
    signature: str = ""
    ## @brief Номера исполняемых строк (для агрегации, в отчёты не попадает)
    exec_lines: Set[int] = field(default_factory=set)

    ## @brief Рекурсивно обойти узел и всех потомков
    #  @return Итератор по узлам
    def walk(self) -> Iterable["Node"]:
        yield self
        for child in self.children:
            yield from child.walk()

    ## @brief Представить узел в виде словаря для JSON
    #  @return Словарь с метриками и потомками
    def as_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "qualname": self.qualname,
            "file": self.file,
            "line": self.line,
            "signature": self.signature,
            "metrics": self.metrics.as_dict(),
            "children": [child.as_dict() for child in self.children],
        }


## @brief Нарушение порогового правила метрик
@dataclass
class Violation:
    ## @brief Правило (CA1501 / CA1502 / CA1505 / CA1506)
    rule: str
    ## @brief Человекочитаемое название правила
    title: str
    ## @brief Уровень: error или warning
    severity: str
    ## @brief Метрика, по которой сработало правило
    metric: str
    ## @brief Значение метрики
    value: float
    ## @brief Порог из конфигурации
    threshold: float
    ## @brief Сущность, где найдено нарушение
    entity: str
    ## @brief Файл и строка
    file: str
    line: int
    ## @brief Пояснение
    message: str

    ## @brief Представить нарушение в виде словаря
    #  @return Словарь для JSON/CSV
    def as_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "title": self.title,
            "severity": self.severity,
            "metric": self.metric,
            "value": round(self.value, 2),
            "threshold": self.threshold,
            "entity": self.entity,
            "file": self.file,
            "line": self.line,
            "message": self.message,
        }


## @brief Конфигурация пороговых значений (аналог CodeMetricsConfig.txt)
@dataclass
class Config:
    ## @brief CA1501 — максимальная допустимая глубина наследования
    ca1501_depth_of_inheritance: float = 2.0
    ## @brief CA1502 — максимальная допустимая цикломатическая сложность
    ca1502_cyclomatic_complexity: float = 10.0
    ## @brief CA1505 — минимальный допустимый индекс сопровождаемости
    ca1505_maintainability_index: float = 20.0
    ## @brief CA1506 — максимальная допустимая связность классов
    ca1506_class_coupling: float = 10.0


# --------------------------------------------------------------------------
# Вспомогательные функции разбора исходного кода
# --------------------------------------------------------------------------

def read_source(path: Path) -> str:
    ## @brief Прочитать исходный файл с учётом BOM
    #  @param path Путь к файлу
    #  @return Текст файла
    return path.read_text(encoding="utf-8-sig", errors="replace")


def is_docstring(node: ast.AST) -> bool:
    ## @brief Проверить, является ли узел строковым литералом-докстрингом
    #  @param node Узел AST
    #  @return True, если это docstring
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


class _ComplexityVisitor(ast.NodeVisitor):
    ## @brief Посетитель AST, считающий точки ветвления
    ## @details Вложенные функции и лямбды не обходятся: они измеряются
    ## отдельными сущностями.

    def __init__(self) -> None:
        self.score = 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        return

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        self.score += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:  # noqa: N802
        self.score += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        self.score += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:  # noqa: N802
        self.score += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:  # noqa: N802
        self.score += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # noqa: N802
        self.score += 1
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:  # noqa: N802
        self.score += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:  # noqa: N802
        self.score += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:  # noqa: N802
        self.score += 1 + len(node.ifs)
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:  # noqa: N802
        self.score += max(1, len(node.cases))
        self.generic_visit(node)


def cyclomatic_complexity(body: Sequence[ast.AST]) -> int:
    ## @brief Вычислить цикломатическую сложность по телу функции/модуля
    #  @param body Список узлов тела
    #  @return Значение CC (минимум 1)
    visitor = _ComplexityVisitor()
    for node in body:
        visitor.visit(node)
    return visitor.score


def collect_stmt_lines(body: Sequence[ast.stmt]) -> Set[int]:
    ## @brief Собрать номера строк исполняемых операторов
    ## @param body Тело функции, класса или модуля
    ## @return Множество номеров строк
    lines: Set[int] = set()

    def walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(child, ast.stmt):
                if not is_docstring(child):
                    lines.add(child.lineno)
                walk(child)
            else:
                walk(child)

    for statement in body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if is_docstring(statement):
            continue
        lines.add(statement.lineno)
        walk(statement)
    return lines


def count_comment_lines(text: str) -> int:
    ## @brief Посчитать строки комментариев (начинающиеся с #)
    #  @param text Текст фрагмента
    #  @return Количество строк комментариев
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("#"))


def halstead_volume(text: str) -> float:
    ## @brief Оценить объём Холстеда по потоку токенов
    ## @param text Текст фрагмента исходного кода
    ## @return Объём Холстеда (0.0, если токенов нет)
    operators: Set[str] = set()
    operands: Set[str] = set()
    total_operators = 0
    total_operands = 0
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return 0.0
    ignored = {
        tokenize.ENCODING, tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
        tokenize.DEDENT, tokenize.ENDMARKER, tokenize.COMMENT,
    }
    for token in tokens:
        if token.type in ignored:
            continue
        if token.type == tokenize.OP:
            operators.add(token.string)
            total_operators += 1
        elif token.type == tokenize.NAME and not keyword.iskeyword(token.string):
            operands.add(token.string)
            total_operands += 1
        elif token.type in (tokenize.NUMBER, tokenize.STRING):
            operands.add(token.string)
            total_operands += 1
        else:
            operators.add(token.string)
            total_operators += 1
    distinct = len(operators) + len(operands)
    if distinct <= 1 or (total_operators + total_operands) == 0:
        return 0.0
    return (total_operators + total_operands) * math.log2(distinct)


def maintainability_index(volume: float, complexity: int, source_lines: int) -> float:
    ## @brief Вычислить индекс удобства обслуживания по формуле Visual Studio
    #  @param volume Объём Холстеда
    #  @param complexity Цикломатическая сложность
    #  @param source_lines Количество строк исходного кода
    #  @return Значение MI в диапазоне 0..100
    safe_volume = max(volume, 1.0)
    safe_lines = max(source_lines, 1)
    safe_complexity = max(complexity, 1)
    value = (
        171.0
        - 5.2 * math.log(safe_volume)
        - 0.23 * safe_complexity
        - 16.2 * math.log(safe_lines)
    ) * 100.0 / 171.0
    return max(0.0, min(100.0, value))


def mi_zone(value: float) -> str:
    ## @brief Определить цветовую зону индекса сопровождаемости
    #  @param value Значение MI
    #  @return green / yellow / red
    if value >= 20:
        return "green"
    if value >= 10:
        return "yellow"
    return "red"


def type_names_in(node: ast.AST) -> Set[str]:
    ## @brief Найти имена классов, на которые ссылается фрагмент AST
    #  @param node Узел AST
    #  @return Множество имён классов (по эвристике «с заглавной буквы»)
    names: Set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            if child.id in IGNORED_NAMES or child.id.isupper():
                continue
            if child.id[:1].isupper():
                names.add(child.id)
        elif isinstance(child, ast.Attribute):
            if child.attr in IGNORED_NAMES or child.attr.isupper():
                continue
            if child.attr[:1].isupper():
                names.add(child.attr)
    return names


def format_signature(name: str, arguments: ast.arguments, returns: Optional[ast.AST]) -> str:
    ## @brief Построить читаемую сигнатуру функции
    #  @param name Имя функции
    #  @param arguments Аргументы функции
    #  @param returns Аннотация возвращаемого значения
    #  @return Строка сигнатуры
    parts: List[str] = []
    for arg in arguments.posonlyargs + arguments.args:
        annotation = ast.unparse(arg.annotation) if arg.annotation is not None else ""
        parts.append(f"{arg.arg}: {annotation}" if annotation else arg.arg)
    if arguments.vararg is not None:
        parts.append("*" + arguments.vararg.arg)
    for arg in arguments.kwonlyargs:
        annotation = ast.unparse(arg.annotation) if arg.annotation is not None else ""
        parts.append(f"{arg.arg}: {annotation}" if annotation else arg.arg)
    if arguments.kwarg is not None:
        parts.append("**" + arguments.kwarg.arg)
    result = "" if returns is None else ast.unparse(returns)
    return f"{result} {name}({', '.join(parts)})".strip()


# --------------------------------------------------------------------------
# Анализатор
# --------------------------------------------------------------------------

class Analyzer:
    ## @brief Анализатор метрик по набору файлов проекта

    def __init__(self, paths: Sequence[Path], root: Path, config: Config) -> None:
        ## @brief Конструктор
        #  @param paths Список анализируемых файлов и каталогов
        #  @param root Корень проекта (для относительных путей)
        #  @param config Пороговые значения
        self.paths = list(paths)
        self.root = root
        self.config = config
        self._class_bases: Dict[str, List[str]] = {}

    ## @brief Собрать список файлов для анализа
    #  @return Отсортированный список путей
    def discover_files(self) -> List[Path]:
        files: List[Path] = []
        for path in self.paths:
            if path.is_dir():
                for child in sorted(path.rglob("*.py")):
                    if "__pycache__" in child.parts:
                        continue
                    files.append(child)
            elif path.suffix in SUPPORTED_SUFFIXES:
                files.append(path)
        unique: List[Path] = []
        seen: Set[Path] = set()
        for item in files:
            resolved = item.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique.append(item)
        return unique

    ## @brief Относительный путь файла для отчётов
    #  @param path Путь к файлу
    #  @return Путь относительно корня проекта
    def relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    ## @brief Имя модуля (namespace) для файла
    #  @param path Путь к файлу
    #  @param input_root Каталог, указанный в аргументах
    #  @return Точка-разделённое имя модуля
    def module_name(self, path: Path, input_root: Optional[Path]) -> str:
        base = input_root or path.parent
        try:
            relative = path.resolve().relative_to(base.resolve())
        except ValueError:
            relative = Path(path.name)
        parts = [base.name] + list(relative.with_suffix("").parts)
        return ".".join(parts)

    ## @brief Первый проход: собрать карту наследования
    #  @param files Список файлов
    def collect_hierarchy(self, files: Sequence[Path]) -> None:
        for path in files:
            try:
                tree = ast.parse(read_source(path))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = [ast.unparse(base).split(".")[-1].split("[")[0]
                             for base in node.bases]
                    self._class_bases.setdefault(node.name, bases)

    ## @brief Глубина наследования класса
    #  @param name Имя класса
    #  @param visited Множество уже посещённых классов (защита от циклов)
    #  @return Значение DIT
    def depth_of_inheritance(self, name: str, visited: Optional[Set[str]] = None) -> int:
        if visited is None:
            visited = set()
        if name in visited:
            return 1
        visited.add(name)
        bases = [base for base in self._class_bases.get(name, []) if base != "object"]
        if not bases:
            return 1
        return 1 + max(self.depth_of_inheritance(base, visited) for base in bases)

    ## @brief Метрики функции или метода
    #  @param node Узел функции
    #  @param text Текст файла
    #  @param file_rel Путь файла
    #  @param kind Тип узла: function или method
    #  @param owner Имя класса-владельца (для методов)
    #  @return Узел с метриками
    def measure_function(self, node: ast.AST, text: str, file_rel: str,
                         kind: str, owner: str = "") -> Node:
        body = getattr(node, "body", [])
        start = node.lineno
        end = getattr(node, "end_lineno", start) or start
        segment = "\n".join(text.splitlines()[start - 1:end])
        complexity = cyclomatic_complexity(body)
        executable = collect_stmt_lines(body)
        source_lines = end - start + 1
        volume = halstead_volume(segment)
        names = type_names_in(node)
        if owner:
            names.discard(owner)
        metrics = Metrics(
            maintainability_index=maintainability_index(volume, complexity, source_lines),
            cyclomatic_complexity=complexity,
            class_coupling=len(names),
            depth_of_inheritance=1,
            source_lines=source_lines,
            executable_lines=len(executable),
            halstead_volume=volume,
            comment_lines=count_comment_lines(segment),
        )
        name = node.name
        qualname = f"{owner}.{name}" if owner else name
        return Node(
            kind=kind,
            name=name,
            qualname=qualname,
            file=file_rel,
            line=start,
            metrics=metrics,
            signature=format_signature(name, node.args, node.returns),
            exec_lines=executable,
        )

    ## @brief Метрики класса
    #  @param node Узел класса
    #  @param text Текст файла
    #  @param file_rel Путь файла
    #  @return Узел класса с вложенными методами
    def measure_class(self, node: ast.ClassDef, text: str, file_rel: str) -> Node:
        start = node.lineno
        end = getattr(node, "end_lineno", start) or start
        segment = "\n".join(text.splitlines()[start - 1:end])
        members: List[Node] = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                members.append(self.measure_function(child, text, file_rel, "method", node.name))
        own_lines = collect_stmt_lines(node.body)
        executable = set(own_lines)
        for member in members:
            executable |= member.exec_lines
        names: Set[str] = set(type_names_in(node))
        names.discard(node.name)
        complexity = 1 + sum(member.metrics.cyclomatic_complexity for member in members)
        source_lines = end - start + 1
        volume = halstead_volume(segment)
        metrics = Metrics(
            maintainability_index=maintainability_index(volume, complexity, source_lines),
            cyclomatic_complexity=complexity,
            class_coupling=len(names),
            depth_of_inheritance=self.depth_of_inheritance(node.name),
            source_lines=source_lines,
            executable_lines=len(executable),
            halstead_volume=volume,
            comment_lines=count_comment_lines(segment),
        )
        return Node(
            kind="class",
            name=node.name,
            qualname=node.name,
            file=file_rel,
            line=start,
            metrics=metrics,
            children=members,
            signature=node.name,
            exec_lines=executable,
        )

    ## @brief Метрики модуля (файла)
    #  @param path Путь к файлу
    #  @param input_root Каталог из аргументов командной строки
    #  @return Узел модуля
    def measure_module(self, path: Path, input_root: Optional[Path]) -> Node:
        text = read_source(path)
        tree = ast.parse(text)
        file_rel = self.relative(path)
        module = Node(
            kind="module",
            name=path.stem,
            qualname=self.module_name(path, input_root),
            file=file_rel,
            line=1,
        )
        for child in tree.body:
            if isinstance(child, ast.ClassDef):
                module.children.append(self.measure_class(child, text, file_rel))
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                module.children.append(self.measure_function(child, text, file_rel, "function"))
        executable = collect_stmt_lines(tree.body)
        for member in module.children:
            executable |= member.exec_lines
        complexity = 1 + sum(child.metrics.cyclomatic_complexity for child in module.children)
        total_lines = len(text.splitlines())
        volume = halstead_volume(text)
        coupling = max([child.metrics.class_coupling for child in module.children] or [0])
        module.metrics = Metrics(
            maintainability_index=maintainability_index(volume, complexity, total_lines),
            cyclomatic_complexity=complexity,
            class_coupling=coupling,
            depth_of_inheritance=max([child.metrics.depth_of_inheritance for child in module.children] or [1]),
            source_lines=total_lines,
            executable_lines=len(executable),
            halstead_volume=volume,
            comment_lines=count_comment_lines(text),
        )
        module.exec_lines = executable
        return module

    ## @brief Полный анализ проекта
    #  @return Список узлов-модулей и список нарушений правил
    def analyze(self) -> Tuple[List[Node], List[Violation]]:
        files = self.discover_files()
        self.collect_hierarchy(files)
        modules: List[Node] = []
        for path in files:
            input_root = next((p for p in self.paths if p.is_dir() and path.is_relative_to(p)), None)
            try:
                modules.append(self.measure_module(path, input_root))
            except SyntaxError as error:
                print(f"  [skip] {path}: синтаксическая ошибка: {error}", file=sys.stderr)
        violations: List[Violation] = []
        for module in modules:
            violations.extend(self._check_rules(module))
        return modules, violations

    ## @brief Проверить пороговые правила для поддерева
    #  @param module Узел модуля
    #  @return Список найденных нарушений
    def _check_rules(self, module: Node) -> List[Violation]:
        violations: List[Violation] = []
        for node in module.walk():
            metrics = node.metrics
            if node.kind == "function" or node.kind == "method":
                if metrics.cyclomatic_complexity > self.config.ca1502_cyclomatic_complexity:
                    violations.append(Violation(
                        rule="CA1502", title="Избыточная сложность", severity="error",
                        metric="CyclomaticComplexity", value=metrics.cyclomatic_complexity,
                        threshold=self.config.ca1502_cyclomatic_complexity,
                        entity=node.qualname, file=node.file, line=node.line,
                        message=(f"Цикломатическая сложность метода {node.qualname} равна "
                                 f"{metrics.cyclomatic_complexity}, порог — "
                                 f"{self.config.ca1502_cyclomatic_complexity:g}; метод трудно тестировать."),
                    ))
            if node.kind == "class":
                if metrics.depth_of_inheritance > self.config.ca1501_depth_of_inheritance:
                    violations.append(Violation(
                        rule="CA1501", title="Избыточная глубина наследования", severity="warning",
                        metric="DepthOfInheritance", value=metrics.depth_of_inheritance,
                        threshold=self.config.ca1501_depth_of_inheritance,
                        entity=node.qualname, file=node.file, line=node.line,
                        message=(f"Глубина наследования класса {node.qualname} равна "
                                 f"{metrics.depth_of_inheritance}, порог — "
                                 f"{self.config.ca1501_depth_of_inheritance:g}; изменение базового класса "
                                 f"затрагивает всю иерархию."),
                    ))
                if metrics.class_coupling > self.config.ca1506_class_coupling:
                    violations.append(Violation(
                        rule="CA1506", title="Избыточная связанность классов", severity="error",
                        metric="ClassCoupling", value=metrics.class_coupling,
                        threshold=self.config.ca1506_class_coupling,
                        entity=node.qualname, file=node.file, line=node.line,
                        message=(f"Класс {node.qualname} ссылается на {metrics.class_coupling} "
                                 f"внешних классов, порог — {self.config.ca1506_class_coupling:g}."),
                    ))
            if metrics.maintainability_index < self.config.ca1505_maintainability_index:
                violations.append(Violation(
                    rule="CA1505", title="Код трудно сопровождать", severity="warning",
                    metric="MaintainabilityIndex", value=metrics.maintainability_index,
                    threshold=self.config.ca1505_maintainability_index,
                    entity=node.qualname, file=node.file, line=node.line,
                    message=(f"Индекс сопровождаемости {node.qualname} равен "
                             f"{metrics.maintainability_index:.1f}, минимальный порог — "
                             f"{self.config.ca1505_maintainability_index:g}."),
                ))
        return violations


# --------------------------------------------------------------------------
# Вывод отчётов
# --------------------------------------------------------------------------

def write_xml(modules: Sequence[Node], violations: Sequence[Violation], project: str,
              target_path: Path) -> None:
    ## @brief Записать отчёт в формате CodeMetricsReport (XML)
    #  @param modules Модули с метриками
    #  @param violations Нарушения правил
    #  @param project Имя проекта
    #  @param target_path Путь к XML-файлу
    def metrics_block(metrics: Metrics, indent: str) -> List[str]:
        lines = [f"{indent}<Metrics>"]
        for name in ("MaintainabilityIndex", "CyclomaticComplexity", "ClassCoupling",
                     "DepthOfInheritance", "SourceLines", "ExecutableLines",
                     "HalsteadVolume", "CommentLines"):
            attr = {
                "MaintainabilityIndex": metrics.maintainability_index,
                "CyclomaticComplexity": metrics.cyclomatic_complexity,
                "ClassCoupling": metrics.class_coupling,
                "DepthOfInheritance": metrics.depth_of_inheritance,
                "SourceLines": metrics.source_lines,
                "ExecutableLines": metrics.executable_lines,
                "HalsteadVolume": metrics.halstead_volume,
                "CommentLines": metrics.comment_lines,
            }[name]
            value = round(attr, 2) if isinstance(attr, float) else attr
            lines.append(f'{indent}  <Metric Name="{name}" Value="{value}" />')
        lines.append(f"{indent}</Metrics>")
        return lines

    def node_block(node: Node, tag: str, indent: str) -> List[str]:
        lines = [f'{indent}<{tag} Name="{escape(node.signature or node.name)}" '
                 f'File="{escape(node.file)}" Line="{node.line}">']
        lines += metrics_block(node.metrics, indent + "  ")
        if node.children:
            lines.append(f"{indent}  <Members>")
            for child in node.children:
                child_tag = "Method" if child.kind == "method" else "NamedType"
                lines += node_block(child, child_tag, indent + "    ")
            lines.append(f"{indent}  </Members>")
        lines.append(f"{indent}</{tag}>")
        return lines

    lines: List[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<CodeMetricsReport Version="1.0">',
        "  <Targets>",
        f'    <Target Name="{escape(project)}">',
        f'      <Assembly Name="{escape(project)}">',
    ]
    total = Metrics(
        maintainability_index=min((m.metrics.maintainability_index for m in modules), default=100.0),
        cyclomatic_complexity=sum(m.metrics.cyclomatic_complexity for m in modules),
        class_coupling=max((m.metrics.class_coupling for m in modules), default=0),
        depth_of_inheritance=max((m.metrics.depth_of_inheritance for m in modules), default=1),
        source_lines=sum(m.metrics.source_lines for m in modules),
        executable_lines=sum(m.metrics.executable_lines for m in modules),
        halstead_volume=sum(m.metrics.halstead_volume for m in modules),
        comment_lines=sum(m.metrics.comment_lines for m in modules),
    )
    lines += metrics_block(total, "        ")
    lines.append("        <Namespaces>")
    for module in modules:
        lines.append(f'          <Namespace Name="{escape(module.qualname)}">')
        lines += metrics_block(module.metrics, "            ")
        lines.append("            <Types>")
        for child in module.children:
            tag = "NamedType" if child.kind == "class" else "Method"
            lines += node_block(child, tag, "              ")
        lines.append("            </Types>")
        lines.append("          </Namespace>")
    lines.append("        </Namespaces>")
    lines.append("      </Assembly>")
    lines.append("    </Target>")
    lines.append("  </Targets>")
    lines.append("  <RuleViolations>")
    for violation in violations:
        lines.append(
            f'    <Violation Rule="{violation.rule}" Severity="{violation.severity}" '
            f'Metric="{violation.metric}" Value="{violation.value:.2f}" '
            f'Threshold="{violation.threshold:g}" Entity="{escape(violation.entity)}" '
            f'File="{escape(violation.file)}" Line="{violation.line}" />'
        )
    lines.append("  </RuleViolations>")
    lines.append("</CodeMetricsReport>")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def escape(text: str) -> str:
    ## @brief Экранировать специальные символы XML
    #  @param text Исходный текст
    #  @return Экранированная строка
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def write_csv(modules: Sequence[Node], violations: Sequence[Violation], target_path: Path) -> None:
    ## @brief Записать отчёт в формате CSV
    #  @param modules Модули с метриками
    #  @param violations Нарушения правил
    #  @param target_path Путь к CSV-файлу
    violation_by_entity: Dict[Tuple[str, int], List[str]] = {}
    for violation in violations:
        violation_by_entity.setdefault((violation.entity, violation.line), []).append(violation.rule)
    with target_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow([
            "level", "module", "type", "member", "file", "line",
            "MaintainabilityIndex", "CyclomaticComplexity", "ClassCoupling",
            "DepthOfInheritance", "SourceLines", "ExecutableLines",
            "HalsteadVolume", "CommentLines", "Violations",
        ])
        for module in modules:
            rows: List[Tuple[str, str, str, str, Node]] = []
            for node in module.walk():
                if node.kind == "module":
                    rows.append(("module", node.qualname, "", "", node))
                elif node.kind == "class":
                    rows.append(("class", module.qualname, node.name, "", node))
                else:
                    owner = node.qualname.split(".")[-2] if "." in node.qualname else ""
                    rows.append(("method", module.qualname, owner, node.name, node))
            for level, module_name, type_name, member_name, node in rows:
                metrics = node.metrics
                rules = ",".join(sorted(set(violation_by_entity.get((node.qualname,
                                                                     node.line), []))))
                writer.writerow([
                    level, module_name, type_name, member_name, node.file, node.line,
                    f"{metrics.maintainability_index:.2f}", metrics.cyclomatic_complexity,
                    metrics.class_coupling, metrics.depth_of_inheritance,
                    metrics.source_lines, metrics.executable_lines,
                    f"{metrics.halstead_volume:.2f}", metrics.comment_lines, rules,
                ])


def write_markdown(modules: Sequence[Node], violations: Sequence[Violation],
                   project: str, target_path: Path) -> None:
    ## @brief Записать отчёт в формате Markdown
    #  @param modules Модули с метриками
    #  @param violations Нарушения правил
    #  @param project Имя проекта
    #  @param target_path Путь к md-файлу
    lines: List[str] = [f"# Метрики кода проекта «{project}»", ""]
    total_sloc = sum(m.metrics.source_lines for m in modules)
    total_el = sum(m.metrics.executable_lines for m in modules)
    total_cc = sum(m.metrics.cyclomatic_complexity for m in modules)
    classes = sum(1 for m in modules for c in m.children if c.kind == "class")
    members = sum(1 for m in modules for c in m.children for x in c.children)
    functions = sum(1 for m in modules for c in m.children if c.kind == "function")
    avg_mi = sum(m.metrics.maintainability_index for m in modules) / max(len(modules), 1)
    lines += [
        "## Сводка",
        "",
        "| Показатель | Значение |",
        "|---|---|",
        f"| Модулей | {len(modules)} |",
        f"| Классов | {classes} |",
        f"| Методов классов | {members} |",
        f"| Функций модулей | {functions} |",
        f"| Строк исходного кода (SLOC) | {total_sloc} |",
        f"| Строк исполняемого кода | {total_el} |",
        f"| Суммарная цикломатическая сложность | {total_cc} |",
        f"| Средний индекс сопровождаемости | {avg_mi:.1f} |",
        f"| Нарушений правил | {len(violations)} |",
        "",
        "## Метрики по модулям",
        "",
        "| Модуль | SLOC | EL | CC | Coupling | DIT | MI | Зона |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for module in modules:
        m = module.metrics
        lines.append(
            f"| `{module.file}` | {m.source_lines} | {m.executable_lines} | "
            f"{m.cyclomatic_complexity} | {m.class_coupling} | {m.depth_of_inheritance} | "
            f"{m.maintainability_index:.1f} | {mi_zone(m.maintainability_index)} |"
        )
    worst = sorted(
        (node for module in modules for node in module.walk()
         if node.kind in ("method", "function")),
        key=lambda n: n.metrics.cyclomatic_complexity, reverse=True,
    )[:10]
    lines += ["", "## Наиболее сложные методы (топ-10 по CC)", "",
              "| Сущность | Файл:строка | CC | MI | Coupling |", "|---|---|---|---|---|"]
    for node in worst:
        lines.append(
            f"| `{node.qualname}` | {node.file}:{node.line} | "
            f"{node.metrics.cyclomatic_complexity} | {node.metrics.maintainability_index:.1f} | "
            f"{node.metrics.class_coupling} |"
        )
    lines += ["", "## Нарушения пороговых правил", ""]
    if violations:
        lines += ["| Правило | Уровень | Сущность | Значение | Порог |", "|---|---|---|---|---|"]
        for violation in violations:
            lines.append(
                f"| {violation.rule} ({violation.title}) | {violation.severity} | "
                f"`{violation.entity}` {violation.file}:{violation.line} | "
                f"{violation.value:.2f} | {violation.threshold:g} |"
            )
    else:
        lines.append("Нарушений не обнаружено.")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(modules: Sequence[Node], violations: Sequence[Violation], project: str,
               target_path: Path) -> None:
    ## @brief Записать отчёт в формате JSON
    #  @param modules Модули с метриками
    #  @param violations Нарушения правил
    #  @param project Имя проекта
    #  @param target_path Путь к JSON-файлу
    payload = {
        "project": project,
        "modules": [module.as_dict() for module in modules],
        "violations": [violation.as_dict() for violation in violations],
    }
    target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path: Optional[Path]) -> Config:
    ## @brief Прочитать пороговые значения из файла конфигурации
    #  @param path Путь к CodeMetricsConfig.txt (может быть None)
    #  @return Объект конфигурации
    config = Config()
    if path is None or not path.exists():
        return config
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().upper()
        try:
            number = float(value.strip())
        except ValueError:
            continue
        if key == "CA1501":
            config.ca1501_depth_of_inheritance = number
        elif key == "CA1502":
            config.ca1502_cyclomatic_complexity = number
        elif key == "CA1505":
            config.ca1505_maintainability_index = number
        elif key == "CA1506":
            config.ca1506_class_coupling = number
    return config


def print_summary(modules: Sequence[Node], violations: Sequence[Violation]) -> None:
    ## @brief Вывести сводку в консоль
    #  @param modules Модули с метриками
    #  @param violations Нарушения правил
    print("")
    print("Модуль                                   SLOC    EL    CC  Coupl  DIT     MI  Зона")
    print("-" * 82)
    for module in modules:
        m = module.metrics
        print(f"{module.file:<38} {m.source_lines:>5} {m.executable_lines:>5} "
              f"{m.cyclomatic_complexity:>5} {m.class_coupling:>6} "
              f"{m.depth_of_inheritance:>4} {m.maintainability_index:>6.1f}  "
              f"{mi_zone(m.maintainability_index)}")
    print("-" * 82)
    print(f"Нарушений правил: {len(violations)}")
    for violation in violations:
        print(f"  [{violation.severity}] {violation.rule}: {violation.message}")


## @brief Точка входа инструмента
#  @param argv Аргументы командной строки (по умолчанию sys.argv[1:])
#  @return Код возврата: 0 — успех, 1 — есть нарушения при --fail-on-violation
def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="code_metrics.py",
        description="Анализатор метрик кода проекта «АрендаТех» (аналог Metrics.exe).",
    )
    parser.add_argument("paths", nargs="+", help="Файлы и каталоги с исходным кодом")
    parser.add_argument("--root", default=".", help="Корень проекта для относительных путей")
    parser.add_argument("--config", default="metrics/CodeMetricsConfig.txt",
                        help="Файл пороговых значений (CodeMetricsConfig.txt)")
    parser.add_argument("--out-dir", default="metrics/reports", help="Каталог для отчётов")
    parser.add_argument("--label", default="code-metrics", help="Префикс имён файлов отчётов")
    parser.add_argument("--project", default="ArendaTech", help="Имя проекта в отчётах")
    parser.add_argument("--fail-on-violation", action="store_true",
                        help="Вернуть код 1, если есть нарушения правил")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    paths = [Path(item) for item in args.paths]
    config = load_config(Path(args.config))
    analyzer = Analyzer(paths, root, config)
    modules, violations = analyzer.analyze()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_xml(modules, violations, args.project, out_dir / f"{args.label}.xml")
    write_csv(modules, violations, out_dir / f"{args.label}.csv")
    write_markdown(modules, violations, args.project, out_dir / f"{args.label}.md")
    write_json(modules, violations, args.project, out_dir / f"{args.label}.json")

    print_summary(modules, violations)
    print(f"\nОтчёты сохранены в {out_dir}")
    if args.fail_on_violation and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
