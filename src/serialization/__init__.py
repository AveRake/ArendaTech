## @file __init__.py
#  @brief Пакет сериализации состояния «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details В версии 1.0 преобразование объектов в JSON выполнялось внутри
#  сервиса и не покрывалось тестами. В версии 2.0 сериализация вынесена в
#  отдельный пакет с парными функциями «объект → словарь» и «словарь → объект».
#
#  @par Состав пакета:
#  - @ref persons.py — пользователи
#  - @ref equipment.py — единицы техники
#  - @ref rental.py — заявки, выдачи, штрафы, уведомления
#  - @ref state.py — состояние сервиса целиком

from .equipment import unit_from_dict, unit_to_dict
from .persons import PERSON_FACTORIES, person_from_dict, person_kind, person_to_dict
from .rental import (
    fine_from_dict, fine_to_dict, issue_from_dict, issue_to_dict,
    notification_from_dict, notification_to_dict, request_from_dict,
    request_to_dict,
)
from .state import ServiceState, state_from_dict, state_to_dict

__all__ = [
    "PERSON_FACTORIES",
    "ServiceState",
    "fine_from_dict",
    "fine_to_dict",
    "issue_from_dict",
    "issue_to_dict",
    "notification_from_dict",
    "notification_to_dict",
    "person_from_dict",
    "person_kind",
    "person_to_dict",
    "request_from_dict",
    "request_to_dict",
    "state_from_dict",
    "state_to_dict",
    "unit_from_dict",
    "unit_to_dict",
]
