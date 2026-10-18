## @file pricing.py
#  @brief Расчёт стоимости аренды «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details В версии 1.0 расчёт стоимости выполнялся одним методом сервиса
#  с вложенными условиями (цикломатическая сложность 6, связанность 16).
#  В версии 2.0 введены независимые правила скидок: каждое правило
#  реализует интерфейс @c DiscountRule и возвращает долю скидки.
#  Стоимость аренды равна произведению базовой суммы и множителей всех
#  сработавших правил. Добавление новой скидки не требует изменения
#  существующего кода (принцип открытости/закрытости).

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Protocol, Sequence, Tuple

from .domain import EquipmentUnit, Person, UserRole

#: Скидки по роли пользователя (доля от базовой стоимости).
ROLE_DISCOUNTS = {
    UserRole.STUDENT: 0.10,
    UserRole.TEACHER: 0.05,
}

#: Скидки за длительную аренду: (минимальное число суток, доля скидки).
LONG_RENTAL_DISCOUNTS: Tuple[Tuple[int, float], ...] = ((14, 0.10), (7, 0.05))

#: Скидка за аренду трёх и более единиц техники.
BULK_DISCOUNT = 0.03

#: Порог количества единиц для скидки за объём.
BULK_THRESHOLD = 3

#: Максимальный срок аренды в сутках.
MAX_RENTAL_DAYS = 30


## @brief Контекст расчёта стоимости
@dataclass(frozen=True)
class PricingContext:
    ## @brief Роль пользователя
    role: Optional[UserRole]
    ## @brief Количество суток аренды
    days: int
    ## @brief Количество единиц техники
    units_count: int


## @brief Интерфейс правила скидки
class DiscountRule(Protocol):
    ## @brief Название правила для отчёта о расчёте
    @property
    def name(self) -> str:
        ...

    ## @brief Доля скидки, которую даёт правило
    #  @param context Контекст расчёта
    #  @return Доля скидки в диапазоне 0..1
    def discount(self, context: PricingContext) -> float:
        ...


## @brief Скидка по роли пользователя
class RoleDiscount:
    ## @brief Название правила
    name = "Скидка по роли"

    ## @brief Доля скидки по роли
    #  @param context Контекст расчёта
    #  @return Доля скидки
    def discount(self, context: PricingContext) -> float:
        return ROLE_DISCOUNTS.get(context.role, 0.0)


## @brief Скидка за длительную аренду
class LongRentalDiscount:
    ## @brief Название правила
    name = "Скидка за длительную аренду"

    ## @brief Доля скидки за срок аренды
    #  @param context Контекст расчёта
    #  @return Доля скидки
    def discount(self, context: PricingContext) -> float:
        for threshold, rate in LONG_RENTAL_DISCOUNTS:
            if context.days > threshold:
                return rate
        return 0.0


## @brief Скидка за аренду нескольких единиц техники
class BulkDiscount:
    ## @brief Название правила
    name = "Скидка за объём"

    ## @brief Доля скидки за объём
    #  @param context Контекст расчёта
    #  @return Доля скидки
    def discount(self, context: PricingContext) -> float:
        return BULK_DISCOUNT if context.units_count >= BULK_THRESHOLD else 0.0


## @brief Результат расчёта стоимости
@dataclass(frozen=True)
class PriceBreakdown:
    ## @brief Базовая стоимость без скидок
    subtotal: float
    ## @brief Итоговая стоимость
    total: float
    ## @brief Сработавшие правила и их доли скидки
    applied: Tuple[Tuple[str, float], ...] = ()

    ## @brief Суммарная скидка в рублях
    @property
    def discount(self) -> float:
        return round(self.subtotal - self.total, 2)

    ## @brief Текстовое описание расчёта
    #  @return Строка со скидками
    def describe(self) -> str:
        if not self.applied:
            return "скидки не применены"
        parts = [f"{name}: {rate * 100:.0f}%" for name, rate in self.applied]
        return ", ".join(parts)


## @brief Калькулятор стоимости аренды
class PriceCalculator:
    ## @brief Конструктор
    #  @param rules Набор правил скидок (по умолчанию — все стандартные)
    def __init__(self, rules: Optional[Sequence[DiscountRule]] = None) -> None:
        self._rules = list(rules) if rules is not None else [
            RoleDiscount(), LongRentalDiscount(), BulkDiscount(),
        ]

    ## @brief Базовая стоимость аренды без скидок
    #  @param units Единицы техники
    #  @param days Количество суток
    #  @return Базовая стоимость
    def subtotal(self, units: Sequence[EquipmentUnit], days: int) -> float:
        return round(sum(unit.model.daily_rate * days for unit in units), 2)

    ## @brief Рассчитать стоимость аренды
    #  @param units Единицы техники
    #  @param user Пользователь-заявитель
    #  @param days Количество суток
    #  @return Структура с базовой и итоговой стоимостью
    def calculate(self, units: Sequence[EquipmentUnit], user: Person,
                  days: int) -> PriceBreakdown:
        context = PricingContext(role=user.role, days=days, units_count=len(units))
        subtotal = self.subtotal(units, days)
        multiplier = 1.0
        applied = []
        for rule in self._rules:
            rate = rule.discount(context)
            if rate > 0:
                multiplier *= 1.0 - rate
                applied.append((rule.name, rate))
        total = round(max(0.0, subtotal * multiplier), 2)
        return PriceBreakdown(subtotal=subtotal, total=total, applied=tuple(applied))
