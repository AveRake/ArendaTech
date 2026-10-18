## @file reports.py
#  @brief Отчёты по работе сервиса «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details В версии 1.0 отчёт собирался методом @c build_report сервиса
#  (цикломатическая сложность 11). В версии 2.0 отчёт вынесен в отдельный
#  класс @c RentalReport, который принимает данные и не зависит от
#  сервиса: его можно использовать и для сохранённого состояния.

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Sequence

from .domain import EquipmentUnit, Fine, Issue, Request


## @brief Сводные показатели сервиса
@dataclass(frozen=True)
class RentalStatistics:
    ## @brief Количество единиц техники
    units_total: int
    ## @brief Количество свободных единиц
    units_free: int
    ## @brief Количество единиц на руках
    units_busy: int
    ## @brief Количество заявок
    requests_total: int
    ## @brief Количество выдач
    issues_total: int
    ## @brief Количество активных выдач
    issues_active: int
    ## @brief Начисленный доход
    income: float
    ## @brief Сумма штрафов
    fines_total: float
    ## @brief Неоплаченные штрафы
    fines_unpaid: float
    ## @brief Количество единиц по категориям
    by_category: Dict[str, int]


## @brief Построитель текстового отчёта
class RentalReport:
    ## @brief Конструктор
    #  @param units Единицы техники
    #  @param requests Заявки
    #  @param issues Выдачи
    #  @param fines Штрафы
    def __init__(self, units: Sequence[EquipmentUnit], requests: Sequence[Request],
                 issues: Sequence[Issue], fines: Sequence[Fine]) -> None:
        self._units = list(units)
        self._requests = list(requests)
        self._issues = list(issues)
        self._fines = list(fines)

    ## @brief Рассчитать сводные показатели
    #  @return Структура со статистикой
    def statistics(self) -> RentalStatistics:
        free = sum(1 for unit in self._units if unit.is_available)
        active = [issue for issue in self._issues if issue.is_open]
        return RentalStatistics(
            units_total=len(self._units),
            units_free=free,
            units_busy=len(self._units) - free,
            requests_total=len(self._requests),
            issues_total=len(self._issues),
            issues_active=len(active),
            income=round(sum(issue.cost for issue in self._issues), 2),
            fines_total=round(sum(fine.amount for fine in self._fines), 2),
            fines_unpaid=round(sum(fine.amount for fine in self._fines
                                   if not fine.is_paid), 2),
            by_category=self._category_counts(),
        )

    ## @brief Количество единиц по категориям
    #  @return Словарь «категория → количество»
    def _category_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for unit in self._units:
            name = unit.model.category.name
            counts[name] = counts.get(name, 0) + 1
        return counts

    ## @brief Активные выдачи
    #  @return Список открытых выдач
    def active_issues(self) -> List[Issue]:
        return [issue for issue in self._issues if issue.is_open]

    ## @brief Текстовый отчёт
    #  @return Многострочный отчёт
    def build(self) -> str:
        stats = self.statistics()
        lines = [
            "ОТЧЁТ СЕРВИСА «АРЕНДАТЕХ»",
            f"Единиц техники: {stats.units_total} "
            f"(свободно {stats.units_free}, занято {stats.units_busy})",
            f"Заявок: {stats.requests_total}",
            f"Выдач: {stats.issues_total} (активных {stats.issues_active})",
            f"Начисленный доход: {stats.income:.2f} руб.",
            f"Штрафы: {stats.fines_total:.2f} руб. "
            f"(не оплачено {stats.fines_unpaid:.2f} руб.)",
        ]
        lines.extend(f"  {name}: {count} ед."
                     for name, count in sorted(stats.by_category.items()))
        lines.extend(self._active_lines())
        return "\n".join(lines)

    ## @brief Строки отчёта по активным выдачам
    #  @return Список строк
    def _active_lines(self) -> List[str]:
        active = self.active_issues()
        if not active:
            return []
        lines = ["Активные выдачи:"]
        for issue in active:
            request = issue.request
            lines.append(
                f"  выдача №{issue.id}, заявка №{request.id}, "
                f"{request.user.fio}, до {request.end_date.isoformat()}")
        return lines
