## @file test_pricing.py
#  @brief Unit-тесты расчёта стоимости аренды
#  @author Колганов Иван
#  @date 2026-02-10
#  @version 2.0

from src.domain import Category, EquipmentModel, EquipmentUnit, Student, Teacher, Person, UserRole
from src.pricing import (
    BULK_DISCOUNT, LongRentalDiscount, PriceCalculator, PricingContext,
    RoleDiscount, BulkDiscount,
)


def make_unit(rate: float = 500.0) -> EquipmentUnit:
    model = EquipmentModel(1, "Модель", Category(1, "Ноутбуки"), "", rate)
    return EquipmentUnit(1, "INV-1", model)


def make_student() -> Student:
    return Student(1, "Иванов И.И.", "i@test.ru", "+79990000000",
                   "123", "ИТ-01", "ФИТ")


## @brief Тест базовой стоимости без скидок
def test_subtotal():
    calculator = PriceCalculator(rules=[])
    assert calculator.subtotal([make_unit(), make_unit()], 10) == 10000.0


## @brief Тест скидки по роли
def test_role_discount():
    rule = RoleDiscount()
    assert rule.discount(PricingContext(UserRole.STUDENT, 5, 1)) == 0.10
    assert rule.discount(PricingContext(UserRole.TEACHER, 5, 1)) == 0.05
    assert rule.discount(PricingContext(None, 5, 1)) == 0.0


## @brief Тест скидки за длительную аренду
def test_long_rental_discount():
    rule = LongRentalDiscount()
    assert rule.discount(PricingContext(None, 5, 1)) == 0.0
    assert rule.discount(PricingContext(None, 8, 1)) == 0.05
    assert rule.discount(PricingContext(None, 20, 1)) == 0.10


## @brief Тест скидки за объём
def test_bulk_discount():
    rule = BulkDiscount()
    assert rule.discount(PricingContext(None, 5, 2)) == 0.0
    assert rule.discount(PricingContext(None, 5, 3)) == BULK_DISCOUNT


## @brief Тест совместного применения скидок
def test_calculate_combines_discounts():
    calculator = PriceCalculator()
    breakdown = calculator.calculate([make_unit()], make_student(), 10)
    assert breakdown.subtotal == 5000.0
    # 5000 * 0.9 (роль) * 0.95 (срок) = 4275.0
    assert breakdown.total == 4275.0
    assert breakdown.discount == 725.0
    names = [name for name, _ in breakdown.applied]
    assert "Скидка по роли" in names


## @brief Тест расчёта для преподавателя без объёмной скидки
def test_calculate_teacher():
    teacher = Teacher(2, "Петров П.П.", "p@test.ru", "+79991111111",
                      "Кафедра", "Доцент")
    breakdown = PriceCalculator().calculate([make_unit()], teacher, 5)
    assert breakdown.total == 2375.0  # 2500 * 0.95


## @brief Тест описания применённых скидок
def test_breakdown_description():
    breakdown = PriceCalculator().calculate([make_unit()], make_student(), 3)
    assert breakdown.describe() == "Скидка по роли: 10%"


## @brief Тест, что нулевая стоимость не уходит в минус
def test_calculate_not_negative():
    person = Person(3, "Гость", "g@test.ru", "")
    breakdown = PriceCalculator().calculate([make_unit(0.0)], person, 3)
    assert breakdown.total == 0.0
