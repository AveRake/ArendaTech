## @file issues.py
#  @brief Сценарий выдачи и возврата техники
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Сценарий оформляет выдачу по одобренной заявке, рассчитывает
#  стоимость аренды и штрафы при возврате. В версии 1.0 эта логика
#  находилась в методах @c issue_equipment и @c return_equipment сервиса,
#  второй из которых имел цикломатическую сложность 16.

from __future__ import annotations
from datetime import date
from typing import List, Sequence

from .domain import (
    EquipmentUnit, Fine, InvalidTransition, Issue, Person, Request,
    RequestStatus, ReturnCondition, UnitStatus, ValidationError,
)
from .fines import FineCalculator, FineItem, RETURN_UNIT_STATUS
from .notifications import NotificationJournal
from .permissions import require_staff
from .pricing import PriceCalculator
from .registry import RentalRegistry


## @brief Сценарий выдачи и возврата техники
class IssueDesk:
    ## @brief Конструктор
    #  @param registry Реестр объектов сервиса
    #  @param pricing Калькулятор стоимости аренды
    #  @param fines Калькулятор штрафов
    #  @param journal Журнал уведомлений
    def __init__(self, registry: RentalRegistry, pricing: PriceCalculator,
                 fines: FineCalculator, journal: NotificationJournal) -> None:
        self._registry = registry
        self._pricing = pricing
        self._fines = fines
        self._journal = journal

    ## @brief Выдать технику по одобренной заявке
    #  @param request Заявка
    #  @param employee Сотрудник, выдающий технику
    #  @param issue_date Дата выдачи
    #  @return Оформленная выдача
    #  @throw InvalidTransition Если заявка не одобрена
    #  @throw ValidationError Если техника недоступна
    def issue(self, request: Request, employee: Person,
              issue_date: date) -> Issue:
        require_staff(employee)
        self._ensure_approved(request)
        self._ensure_units_free(request.units)
        price = self._pricing.calculate(request.units, request.user, request.days)
        issue = Issue(self._registry.next_issue_id(), request, issue_date,
                      price.total)
        self._registry.add_issue(issue)
        request.transition(RequestStatus.ISSUED)
        for unit in request.units:
            unit.set_status(UnitStatus.ISSUED)
        self._journal.register(
            request.user,
            f"Техника выдана по заявке №{request.id}, "
            f"стоимость {price.total:.2f} руб.", "issue")
        return issue

    ## @brief Оформить возврат техники
    #  @param issue Выдача
    #  @param employee Сотрудник, принимающий технику
    #  @param return_date Дата возврата
    #  @param condition Состояние техники
    #  @return Список начисленных штрафов
    #  @throw ValidationError Если выдача уже закрыта
    def return_equipment(self, issue: Issue, employee: Person,
                         return_date: date,
                         condition: ReturnCondition) -> List[FineItem]:
        require_staff(employee)
        if not issue.is_open:
            raise ValidationError(f"Выдача №{issue.id} уже закрыта")
        issue.close(return_date, condition)
        request = issue.request
        request.transition(RequestStatus.CLOSED)
        for unit in request.units:
            unit.set_status(RETURN_UNIT_STATUS[condition])
        items = self._fines.calculate(issue, condition, return_date)
        self._register_fines(issue, items)
        self._journal.register(
            request.user,
            f"Возврат по заявке №{request.id} оформлен ({condition.value})",
            "return")
        return items

    ## @brief Проверить, что заявка одобрена
    #  @param request Заявка
    #  @throw InvalidTransition Если статус заявки не «Одобрена»
    def _ensure_approved(self, request: Request) -> None:
        if request.status is not RequestStatus.APPROVED:
            raise InvalidTransition(
                f"Выдача возможна только для одобренной заявки, "
                f"текущий статус — «{request.status.value}»")

    ## @brief Проверить, что единицы свободны
    #  @param units Единицы техники
    #  @throw ValidationError Если единица уже выдана
    def _ensure_units_free(self, units: Sequence[EquipmentUnit]) -> None:
        for unit in units:
            if not unit.is_available:
                raise ValidationError(
                    f"Единица {unit.inventory_number} недоступна")

    ## @brief Зарегистрировать штрафы по возврату
    #  @param issue Выдача
    #  @param items Начисления
    def _register_fines(self, issue: Issue, items: List[FineItem]) -> None:
        for item in items:
            fine = Fine(self._registry.next_fine_id(), item.reason, item.amount,
                        issue)
            self._registry.add_fine(fine)
            self._journal.register(
                issue.request.user,
                f"Начислен штраф {fine.amount:.2f} руб. "
                f"({fine.reason.value})", "fine")
