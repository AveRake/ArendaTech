## @file registry.py
#  @brief Реестр объектов сервиса «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Реестр хранит единицы техники, заявки, выдачи и штрафы и
#  выдаёт идентификаторы новым объектам. Реестр не содержит бизнес-правил:
#  их реализуют сценарии @ref requests.py и @ref issues.py.

from __future__ import annotations
from typing import List, Sequence

from .domain import EquipmentUnit, Fine, Issue, Request, ValidationError
from .serialization import ServiceState


## @brief Реестр объектов сервиса аренды
class RentalRegistry:
    ## @brief Конструктор
    def __init__(self) -> None:
        self._units: List[EquipmentUnit] = []
        self._requests: List[Request] = []
        self._issues: List[Issue] = []
        self._fines: List[Fine] = []

    ## @brief Единицы техники
    @property
    def units(self) -> List[EquipmentUnit]:
        return list(self._units)

    ## @brief Заявки
    @property
    def requests(self) -> List[Request]:
        return list(self._requests)

    ## @brief Выдачи
    @property
    def issues(self) -> List[Issue]:
        return list(self._issues)

    ## @brief Штрафы
    @property
    def fines(self) -> List[Fine]:
        return list(self._fines)

    ## @brief Зарегистрировать единицу техники
    #  @param unit Единица техники
    #  @throw ValidationError Если инвентарный номер уже зарегистрирован
    def add_unit(self, unit: EquipmentUnit) -> None:
        if any(item.inventory_number == unit.inventory_number
               for item in self._units):
            raise ValidationError(
                f"Единица с номером {unit.inventory_number} уже зарегистрирована")
        self._units.append(unit)

    ## @brief Зарегистрировать заявку
    #  @param request Заявка
    def add_request(self, request: Request) -> None:
        self._requests.append(request)

    ## @brief Зарегистрировать выдачу
    #  @param issue Выдача
    def add_issue(self, issue: Issue) -> None:
        self._issues.append(issue)

    ## @brief Зарегистрировать штраф
    #  @param fine Штраф
    def add_fine(self, fine: Fine) -> None:
        self._fines.append(fine)

    ## @brief Идентификатор для новой заявки
    #  @return Следующий свободный идентификатор
    def next_request_id(self) -> int:
        return len(self._requests) + 1

    ## @brief Идентификатор для новой выдачи
    #  @return Следующий свободный идентификатор
    def next_issue_id(self) -> int:
        return len(self._issues) + 1

    ## @brief Идентификатор для нового штрафа
    #  @return Следующий свободный идентификатор
    def next_fine_id(self) -> int:
        return len(self._fines) + 1

    ## @brief Зарегистрирована ли единица техники
    #  @param unit Единица техники
    #  @return True, если единица есть в реестре
    def contains_unit(self, unit: EquipmentUnit) -> bool:
        return any(item is unit for item in self._units)

    ## @brief Загрузить данные из снимка состояния
    #  @param state Снимок состояния
    def load(self, state: ServiceState) -> None:
        self._units = list(state.units)
        self._requests = list(state.requests)
        self._issues = list(state.issues)
        self._fines = list(state.fines)

    ## @brief Получить снимок состояния
    #  @param notifications Уведомления журнала
    #  @return Снимок состояния
    def snapshot(self, notifications: Sequence) -> ServiceState:
        return ServiceState(units=self._units, requests=self._requests,
                            issues=self._issues, fines=self._fines,
                            notifications=list(notifications))
