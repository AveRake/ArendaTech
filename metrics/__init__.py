## @file __init__.py
#  @brief Пакет инструментов измерения метрик кода «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 1.0
#
#  @details Содержит @ref code_metrics.py — анализатор метрик (аналог
#  Metrics.exe) и @ref compare_metrics.py — сравнение отчётов разных версий
#  проекта. Пакет оформлен как модуль Python, чтобы анализатор можно было
#  импортировать в unit-тестах (@c tests/test_metrics.py).

__all__ = ["code_metrics", "compare_metrics"]
