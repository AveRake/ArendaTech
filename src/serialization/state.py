## @file state.py
#  @brief Состояние сервиса и его преобразование в JSON-структуру
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..domain import EquipmentUnit, Fine, Issue, Notification, Request
from .equipment import unit_from_dict, unit_to_dict
from .rental import (
    fine_from_dict, fine_to_dict, issue_from_dict, issue_to_dict,
    notification_from_dict, notification_to_dict, request_from_dict,
    request_to_dict,
)


## @brief Состояние сервиса аренды
@dataclass
class ServiceState:
    ## @brief Единицы техники
    units: List[EquipmentUnit] = field(default_factory=list)
    ## @brief Заявки
    requests: List[Request] = field(default_factory=list)
    ## @brief Выдачи
    issues: List[Issue] = field(default_factory=list)
    ## @brief Штрафы
    fines: List[Fine] = field(default_factory=list)
    ## @brief Уведомления
    notifications: List[Notification] = field(default_factory=list)


def state_to_dict(state: ServiceState) -> Dict[str, Any]:
    ## @brief Преобразовать состояние сервиса в словарь
    #  @param state Состояние сервиса
    #  @return Словарь для JSON
    unit_index = {unit.inventory_number: unit for unit in state.units}
    return {
        "version": 2,
        "units": [unit_to_dict(unit) for unit in state.units],
        "requests": [request_to_dict(request, unit_index)
                     for request in state.requests],
        "issues": [issue_to_dict(issue) for issue in state.issues],
        "fines": [fine_to_dict(fine) for fine in state.fines],
        "notifications": [notification_to_dict(item)
                          for item in state.notifications],
    }


def state_from_dict(payload: Dict[str, Any]) -> ServiceState:
    ## @brief Восстановить состояние сервиса из словаря
    #  @param payload Словарь из JSON
    #  @return Состояние сервиса
    units = [unit_from_dict(item) for item in payload.get("units", [])]
    unit_index = {unit.inventory_number: unit for unit in units}
    requests = [request_from_dict(item, unit_index)
                for item in payload.get("requests", [])]
    request_index = {request.id: request for request in requests}
    issues = [issue_from_dict(item, request_index)
              for item in payload.get("issues", [])]
    fines = [fine_from_dict(item) for item in payload.get("fines", [])]
    notifications = [notification_from_dict(item)
                     for item in payload.get("notifications", [])]
    return ServiceState(units=units, requests=requests, issues=issues,
                        fines=fines, notifications=notifications)
