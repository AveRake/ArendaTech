## @file test_metrics.py
#  @brief Unit-тесты анализатора метрик кода
#  @author Колганов Иван
#  @date 2026-02-10
#  @version 1.0
#
#  @details Проверяется корректность формул (CC, MI), чтение пороговых
#  значений из CodeMetricsConfig.txt и срабатывание правил CA1501/CA1502/
#  CA1505/CA1506 на синтетическом модуле.

from pathlib import Path

from metrics.code_metrics import (
    Analyzer, Config, load_config, maintainability_index, mi_zone,
)

SAMPLE_SOURCE = '''
"""Пример модуля для тестов метрик."""

from typing import List


class Base:
    """Базовый класс."""

    def __init__(self, value: int) -> None:
        self._value = value


class Child(Base):
    """Производный класс."""

    def choose(self, flag: bool, items: List[int]) -> int:
        """Метод с большим числом ветвлений."""
        total = 0
        if flag and items:
            for item in items:
                if item > 0:
                    total += item
                elif item < 0:
                    total -= item
                else:
                    total += 1
        elif flag or not items:
            total = self._value
        else:
            total = 0
        return total
'''


def analyze_sample(tmp_path: Path):
    path = tmp_path / "sample.py"
    path.write_text(SAMPLE_SOURCE, encoding="utf-8")
    analyzer = Analyzer([path], tmp_path, Config())
    return analyzer.analyze()


## @brief Тест цветовых зон индекса сопровождаемости
def test_mi_zones():
    assert mi_zone(95) == "green"
    assert mi_zone(20) == "green"
    assert mi_zone(15) == "yellow"
    assert mi_zone(5) == "red"


## @brief Тест границ индекса сопровождаемости
def test_maintainability_index_bounds():
    assert 0 <= maintainability_index(0.0, 1, 1) <= 100
    assert maintainability_index(100.0, 1, 50) > maintainability_index(100.0, 30, 50)


## @brief Тест чтения порогов из файла конфигурации
def test_load_config(tmp_path):
    path = tmp_path / "CodeMetricsConfig.txt"
    path.write_text("# комментарий\nCA1502: 7\nCA1505: 30\n", encoding="utf-8")
    config = load_config(path)
    assert config.ca1502_cyclomatic_complexity == 7
    assert config.ca1505_maintainability_index == 30
    assert config.ca1501_depth_of_inheritance == 2  # значение по умолчанию


## @brief Тест анализа синтетического модуля
def test_analyzer_finds_types_and_methods(tmp_path):
    modules, _ = analyze_sample(tmp_path)
    assert len(modules) == 1
    names = {child.name for child in modules[0].children}
    assert names == {"Base", "Child"}


## @brief Тест глубины наследования и связанности классов
def test_depth_of_inheritance_and_coupling(tmp_path):
    modules, _ = analyze_sample(tmp_path)
    classes = {child.name: child for child in modules[0].children}
    assert classes["Base"].metrics.depth_of_inheritance == 1
    assert classes["Child"].metrics.depth_of_inheritance == 2
    assert classes["Child"].metrics.class_coupling >= 1


## @brief Тест срабатывания правил CA1502 и CA1501 при строгих порогах
def test_rules_trigger_on_synthetic_code(tmp_path):
    path = tmp_path / "sample.py"
    path.write_text(SAMPLE_SOURCE, encoding="utf-8")
    config = Config(ca1502_cyclomatic_complexity=3,
                    ca1501_depth_of_inheritance=1,
                    ca1506_class_coupling=0)
    _, violations = Analyzer([path], tmp_path, config).analyze()
    rules = {violation.rule for violation in violations}
    assert "CA1502" in rules
    assert "CA1501" in rules
    assert "CA1506" in rules


## @brief Тест отсутствия нарушений при мягких порогах
def test_no_violations_with_default_config(tmp_path):
    _, violations = analyze_sample(tmp_path)
    assert violations == []
