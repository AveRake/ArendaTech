## @file test_fines.py
#  @brief Unit-тесты начисления штрафов
#  @author Колганов Иван
#  @date 2026-02-10
#  @version 2.0

from datetime import date

from src.domain import (
    Category, EquipmentModel, EquipmentUnit, FineReason, Issue, Person,
    Request, ReturnCondition, UnitStatus,
)
from src.fines import (
    DamageRule, FineCalculator, FineContext, LossRule, OverdueRule,
    RETURN_UNIT_STATUS,
)


def make_unit(rate: float = 500.0, category: Category = None,
              replacement: float = 0.0) -> EquipmentUnit:
    category = category or Category(1, "Ноутбуки", damage_coefficient=0.10)
    model = EquipmentModel(1, "Модель", category, "", rate, replacement)
    return EquipmentUnit(1, "INV-1", model)


def make_issue(units, end_date: date = date(2026, 2, 20)) -> Issue:
    request = Request(1, Person(1, "A", "a@a.ru", ""), units,
                      date(2026, 2, 10), end_date)
    return Issue(1, request, date(2026, 2, 10), 5000.0)


def make_context(issue: Issue, return_date: date,
                 condition: ReturnCondition) -> FineContext:
    return FineContext(issue=issue, return_date=return_date, condition=condition)


## @brief Тест штрафа за просрочку
def test_overdue_rule():
    issue = make_issue([make_unit()])
    context = make_context(issue, date(2026, 2, 24), ReturnCondition.GOOD)
    assert OverdueRule().amount(context) == 1000.0  # 500 * 0.5 * 4 сут.


## @brief Тест отсутствия просрочки
def test_no_overdue():
    issue = make_issue([make_unit()])
    context = make_context(issue, date(2026, 2, 18), ReturnCondition.GOOD)
    assert OverdueRule().amount(context) == 0.0


## @brief Тест штрафа за повреждение с учётом коэффициента категории
def test_damage_rule_uses_category_coefficient():
    fragile = Category(2, "Проекторы", damage_coefficient=0.20)
    issue = make_issue([make_unit(rate=700.0, category=fragile)])
    context = make_context(issue, date(2026, 2, 20), ReturnCondition.DAMAGED)
    assert DamageRule().amount(context) == 140.0  # 700 * 0.2


## @brief Тест штрафа за утерю
def test_loss_rule():
    issue = make_issue([make_unit(rate=500.0, replacement=5000.0)])
    context = make_context(issue, date(2026, 2, 20), ReturnCondition.LOST)
    assert LossRule().amount(context) == 5000.0


## @brief Тест начисления нескольких штрафов одновременно
def test_calculator_returns_several_items():
    issue = make_issue([make_unit()])
    items = FineCalculator().calculate(issue, ReturnCondition.DAMAGED,
                                       date(2026, 2, 24))
    reasons = {item.reason for item in items}
    assert reasons == {FineReason.OVERDUE, FineReason.DAMAGE}
    assert sum(item.amount for item in items) == 1050.0  # 1000 + 50


## @brief Тест отсутствия штрафов при исправном возврате в срок
def test_calculator_returns_empty_for_good_return():
    issue = make_issue([make_unit()])
    assert FineCalculator().calculate(issue, ReturnCondition.GOOD,
                                      date(2026, 2, 20)) == []


## @brief Тест соответствия состояния единицы результату возврата
def test_return_unit_status_mapping():
    assert RETURN_UNIT_STATUS[ReturnCondition.GOOD] is UnitStatus.AVAILABLE
    assert RETURN_UNIT_STATUS[ReturnCondition.DAMAGED] is UnitStatus.IN_REPAIR
    assert RETURN_UNIT_STATUS[ReturnCondition.LOST] is UnitStatus.WRITTEN_OFF
