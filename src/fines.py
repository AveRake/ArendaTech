## @file fines.py
#  @brief Начисление штрафов «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details В версии 1.0 расчёт штрафов был частью метода @c return_equipment
#  (цикломатическая сложность 16) и содержал зашитые названия категорий
#  техники. В версии 2.0 каждое основание штрафа — отдельное правило
#  (@c OverdueRule, @c DamageRule, @c LossRule), а коэффициенты
#  хранятся в данных: категория техники знает свой коэффициент ущерба,
#  модель — стоимость возмещения при утере.

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Protocol, Sequence

from .domain import (
    FineReason, Issue, Request, ReturnCondition, ReturnCondition as Condition,
    UnitStatus,
)

#: Штраф за каждые сутки просрочки (доля суточной ставки).
OVERDUE_RATE = 0.5


## @brief Контекст начисления штрафа
@dataclass(frozen=True)
class FineContext:
    ## @brief Выдача, по которой оформляется возврат
    issue: Issue
    ## @brief Дата фактического возврата
    return_date: date
    ## @brief Состояние техники при возврате
    condition: ReturnCondition

    ## @brief Заявка, связанная с выдачей
    @property
    def request(self) -> Request:
        return self.issue.request


## @brief Интерфейс правила начисления штрафа
class FineRule(Protocol):
    ## @brief Основание штрафа
    @property
    def reason(self) -> FineReason:
        ...

    ## @brief Рассчитать сумму штрафа
    #  @param context Контекст возврата
    #  @return Сумма штрафа (0, если основание не применимо)
    def amount(self, context: FineContext) -> float:
        ...


## @brief Штраф за просрочку возврата
class OverdueRule:
    ## @brief Основание штрафа
    reason = FineReason.OVERDUE

    ## @brief Сумма штрафа за просрочку
    #  @param context Контекст возврата
    #  @return Сумма штрафа
    def amount(self, context: FineContext) -> float:
        overdue = context.issue.overdue_days(context.return_date)
        return round(sum(unit.model.daily_rate * OVERDUE_RATE * overdue
                         for unit in context.request.units), 2)


## @brief Штраф за повреждение техники
class DamageRule:
    ## @brief Основание штрафа
    reason = FineReason.DAMAGE

    ## @brief Сумма штрафа за повреждение
    #  @param context Контекст возврата
    #  @return Сумма штрафа
    def amount(self, context: FineContext) -> float:
        if context.condition is not ReturnCondition.DAMAGED:
            return 0.0
        return round(sum(unit.model.daily_rate * unit.model.category.damage_coefficient
                         for unit in context.request.units), 2)


## @brief Штраф за утерю техники
class LossRule:
    ## @brief Основание штрафа
    reason = FineReason.LOSS

    ## @brief Сумма штрафа за утерю
    #  @param context Контекст возврата
    #  @return Сумма штрафа
    def amount(self, context: FineContext) -> float:
        if context.condition is not ReturnCondition.LOST:
            return 0.0
        return round(sum(unit.model.replacement_cost for unit in context.request.units), 2)


## @brief Позиция начисления (основание и сумма)
@dataclass(frozen=True)
class FineItem:
    ## @brief Основание штрафа
    reason: FineReason
    ## @brief Сумма штрафа
    amount: float


## @brief Калькулятор штрафов
class FineCalculator:
    ## @brief Конструктор
    #  @param rules Набор правил (по умолчанию — просрочка, повреждение, утеря)
    def __init__(self, rules: Optional[Sequence[FineRule]] = None) -> None:
        self._rules = list(rules) if rules is not None else [
            OverdueRule(), DamageRule(), LossRule(),
        ]

    ## @brief Рассчитать штрафы по возврату
    #  @param issue Выдача
    #  @param condition Состояние техники
    #  @param return_date Дата возврата
    #  @return Список начислений с положительной суммой
    def calculate(self, issue: Issue, condition: ReturnCondition,
                  return_date: date) -> List[FineItem]:
        context = FineContext(issue=issue, return_date=return_date, condition=condition)
        items = []
        for rule in self._rules:
            amount = rule.amount(context)
            if amount > 0:
                items.append(FineItem(reason=rule.reason, amount=amount))
        return items


#: Состояние единицы техники после возврата.
RETURN_UNIT_STATUS = {
    ReturnCondition.GOOD: UnitStatus.AVAILABLE,
    ReturnCondition.DAMAGED: UnitStatus.IN_REPAIR,
    ReturnCondition.LOST: UnitStatus.WRITTEN_OFF,
}
