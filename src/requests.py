## @file requests.py
#  @brief Сценарий работы с заявками на аренду
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Сценарий объединяет создание заявки, проверку периода и
#  доступности единиц техники, а также согласование и отклонение заявки.
#  В версии 1.0 эта логика находилась в методе @c create_request сервиса
#  (цикломатическая сложность 11).

from __future__ import annotations
from datetime import date
from typing import Sequence

from .domain import (
    EquipmentUnit, InvalidTransition, Person, Request, RequestStatus,
    ValidationError,
)
from .notifications import NotificationJournal
from .permissions import require_staff
from .pricing import MAX_RENTAL_DAYS, PriceCalculator
from .registry import RentalRegistry


## @brief Сценарий работы с заявками на аренду
class RequestDesk:
    ## @brief Конструктор
    #  @param registry Реестр объектов сервиса
    #  @param pricing Калькулятор стоимости аренды
    #  @param journal Журнал уведомлений
    def __init__(self, registry: RentalRegistry, pricing: PriceCalculator,
                 journal: NotificationJournal) -> None:
        self._registry = registry
        self._pricing = pricing
        self._journal = journal

    ## @brief Создать заявку на аренду
    #  @param user Пользователь-заявитель
    #  @param units Единицы техники
    #  @param start_date Дата начала аренды
    #  @param end_date Дата окончания аренды
    #  @return Созданная заявка
    #  @throw ValidationError Если период или состав заявки некорректны
    def create(self, user: Person, units: Sequence[EquipmentUnit],
               start_date: date, end_date: date) -> Request:
        self._validate_period(start_date, end_date)
        self._validate_units(units, start_date, end_date)
        request = Request(self._registry.next_request_id(), user, units,
                          start_date, end_date)
        self._registry.add_request(request)
        self._journal.register(user, f"Заявка №{request.id} создана", "request")
        price = self._pricing.calculate(units, user, request.days)
        self._journal.register(
            user, f"Предварительная стоимость аренды: {price.total:.2f} руб. "
                  f"({price.describe()})", "price")
        return request

    ## @brief Одобрить заявку
    #  @param request Заявка
    #  @param employee Сотрудник, принимающий решение
    #  @throw InvalidTransition Если заявка не в статусе «На рассмотрении»
    def approve(self, request: Request, employee: Person) -> None:
        require_staff(employee)
        request.transition(RequestStatus.APPROVED)
        self._journal.register(request.user,
                               f"Заявка №{request.id} одобрена", "request")

    ## @brief Отклонить заявку
    #  @param request Заявка
    #  @param employee Сотрудник, принимающий решение
    #  @param reason Причина отклонения
    def reject(self, request: Request, employee: Person,
               reason: str = "") -> None:
        require_staff(employee)
        request.transition(RequestStatus.REJECTED)
        message = f"Заявка №{request.id} отклонена"
        self._journal.register(request.user,
                               f"{message}: {reason}" if reason else message,
                               "request")

    ## @brief Проверить период аренды
    #  @param start_date Дата начала
    #  @param end_date Дата окончания
    #  @throw ValidationError Если период некорректен
    def _validate_period(self, start_date: date, end_date: date) -> None:
        if end_date <= start_date:
            raise ValidationError("Дата окончания должна быть позже даты начала")
        if (end_date - start_date).days > MAX_RENTAL_DAYS:
            raise ValidationError(
                f"Максимальный срок аренды — {MAX_RENTAL_DAYS} суток")

    ## @brief Проверить единицы техники
    #  @param units Единицы техники
    #  @param start_date Дата начала
    #  @param end_date Дата окончания
    #  @throw ValidationError Если единицы недоступны
    def _validate_units(self, units: Sequence[EquipmentUnit],
                        start_date: date, end_date: date) -> None:
        if not units:
            raise ValidationError(
                "Заявка должна содержать хотя бы одну единицу техники")
        for unit in units:
            self._validate_unit(unit, start_date, end_date)

    ## @brief Проверить одну единицу техники
    #  @param unit Единица техники
    #  @param start_date Дата начала
    #  @param end_date Дата окончания
    #  @throw ValidationError Если единица недоступна
    def _validate_unit(self, unit: EquipmentUnit, start_date: date,
                       end_date: date) -> None:
        if not self._registry.contains_unit(unit):
            raise ValidationError(
                f"Единица {unit.inventory_number} не зарегистрирована")
        if not unit.is_available:
            raise ValidationError(f"Единица {unit.inventory_number} недоступна")
        if self._is_booked(unit, start_date, end_date):
            raise ValidationError(
                f"Единица {unit.inventory_number} занята в выбранный период")

    ## @brief Проверить, свободна ли единица в период
    #  @param unit Единица техники
    #  @param start_date Дата начала
    #  @param end_date Дата окончания
    #  @return True, если единица забронирована другой заявкой
    def _is_booked(self, unit: EquipmentUnit, start_date: date,
                   end_date: date) -> bool:
        for request in self._registry.requests:
            if request.status in (RequestStatus.REJECTED, RequestStatus.CLOSED):
                continue
            if any(item is unit for item in request.units) \
                    and request.overlaps(start_date, end_date):
                return True
        return False
