## @file service.py
#  @brief Сервисный слой приложения «АрендаТех» (версия 2.0)
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#  @copyright ЗАО "АБС"
#
#  @details @c RentalService — фасад сервиса. Бизнес-правила разделены по
#  сценариям использования: работа с заявками (@ref requests.py), выдача и
#  возврат (@ref issues.py), расчёт стоимости (@ref pricing.py), штрафы
#  (@ref fines.py), уведомления (@ref notifications.py), хранение
#  (@ref repository.py).
#
#  В версии 1.0 весь функционал находился в одном классе: связанность 16,
#  индекс сопровождаемости 3.1, три метода нарушали правило CA1502.
#  В версии 2.0 фасад содержит только делегирование и агрегацию результатов.

from __future__ import annotations
from datetime import date
from typing import List, Optional, Sequence

from .domain import (
    EquipmentUnit, Fine, Issue, Notification, Person, Request, ReturnCondition,
)
from .fines import FineCalculator, FineItem
from .issues import IssueDesk
from .notifications import NotificationJournal
from .pricing import PriceCalculator
from .registry import RentalRegistry
from .reports import RentalReport
from .requests import RequestDesk
from .serialization import ServiceState


## @brief Сервис аренды техники
#  @details Предоставляет приложению единый интерфейс к сценариям аренды.
class RentalService:
    ## @brief Конструктор
    #  @param pricing Калькулятор стоимости аренды
    #  @param fines Калькулятор штрафов
    #  @param journal Журнал уведомлений
    #  @param registry Реестр объектов сервиса
    def __init__(self, pricing: Optional[PriceCalculator] = None,
                 fines: Optional[FineCalculator] = None,
                 journal: Optional[NotificationJournal] = None,
                 registry: Optional[RentalRegistry] = None) -> None:
        self._pricing = pricing or PriceCalculator()
        self._journal = journal or NotificationJournal()
        self._registry = registry or RentalRegistry()
        self._request_desk = RequestDesk(self._registry, self._pricing,
                                         self._journal)
        self._issue_desk = IssueDesk(self._registry, self._pricing,
                                     fines or FineCalculator(), self._journal)

    ## @brief Единицы техники сервиса
    @property
    def units(self) -> List[EquipmentUnit]:
        return self._registry.units

    ## @brief Заявки сервиса
    @property
    def requests(self) -> List[Request]:
        return self._registry.requests

    ## @brief Выдачи сервиса
    @property
    def issues(self) -> List[Issue]:
        return self._registry.issues

    ## @brief Начисленные штрафы
    @property
    def fines(self) -> List[Fine]:
        return self._registry.fines

    ## @brief Зарегистрировать единицу техники
    #  @param unit Единица техники
    def add_unit(self, unit: EquipmentUnit) -> None:
        self._registry.add_unit(unit)

    ## @brief Создать заявку на аренду
    #  @param user Пользователь-заявитель
    #  @param units Единицы техники
    #  @param start_date Дата начала аренды
    #  @param end_date Дата окончания аренды
    #  @return Созданная заявка
    def create_request(self, user: Person, units: Sequence[EquipmentUnit],
                       start_date: date, end_date: date) -> Request:
        return self._request_desk.create(user, units, start_date, end_date)

    ## @brief Одобрить заявку
    #  @param request Заявка
    #  @param employee Сотрудник, принимающий решение
    def approve_request(self, request: Request, employee: Person) -> None:
        self._request_desk.approve(request, employee)

    ## @brief Отклонить заявку
    #  @param request Заявка
    #  @param employee Сотрудник, принимающий решение
    #  @param reason Причина отклонения
    def reject_request(self, request: Request, employee: Person,
                       reason: str = "") -> None:
        self._request_desk.reject(request, employee, reason)

    ## @brief Выдать технику по одобренной заявке
    #  @param request Заявка
    #  @param employee Сотрудник, выдающий технику
    #  @param issue_date Дата выдачи
    #  @return Оформленная выдача
    def issue_equipment(self, request: Request, employee: Person,
                        issue_date: date) -> Issue:
        return self._issue_desk.issue(request, employee, issue_date)

    ## @brief Оформить возврат техники
    #  @param issue Выдача
    #  @param employee Сотрудник, принимающий технику
    #  @param return_date Дата возврата
    #  @param condition Состояние техники
    #  @return Список начисленных штрафов
    def return_equipment(self, issue: Issue, employee: Person,
                         return_date: date,
                         condition: ReturnCondition) -> List[FineItem]:
        return self._issue_desk.return_equipment(issue, employee,
                                                 return_date, condition)

    ## @brief Уведомления пользователя или все уведомления
    #  @param user_id Идентификатор получателя (None — все пользователи)
    #  @param kind Тип уведомления (None — все типы)
    #  @return Список уведомлений
    def notifications(self, user_id: Optional[int] = None,
                      kind: Optional[str] = None) -> List[Notification]:
        if user_id is None:
            return [item for item in self._journal.all()
                    if kind is None or item.kind == kind]
        return self._journal.for_user(user_id, kind)

    ## @brief Текстовый отчёт по работе сервиса
    #  @return Многострочный отчёт
    def report(self) -> str:
        return RentalReport(self.units, self.requests,
                            self.issues, self.fines).build()

    ## @brief Текущее состояние сервиса
    #  @return Снимок состояния
    def state(self) -> ServiceState:
        return self._registry.snapshot(self._journal.all())

    ## @brief Восстановить состояние сервиса
    #  @param state Снимок состояния
    def restore(self, state: ServiceState) -> None:
        self._registry.load(state)
        self._journal.restore(list(state.notifications))
