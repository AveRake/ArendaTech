## @file __init__.py
#  @brief Пакет предметной области «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Пакет объединяет модули @ref enums.py, @ref errors.py,
#  @ref people.py, @ref equipment.py, @ref request.py, @ref issue.py,
#  @ref fine.py и @ref notification.py. Реэкспорт имён сохраняет
#  совместимость с версией 1.0: @c "from src.domain import Person"
#  продолжает работать.
#
#  @par Состав пакета:
#  - @ref enums.py — перечисления ролей, статусов и состояний
#  - @ref errors.py — иерархия исключений предметной области
#  - @ref people.py — пользователи системы
#  - @ref equipment.py — категории, модели и единицы техники
#  - @ref request.py — заявка на аренду и переходы статусов
#  - @ref issue.py — выдача техники и возврат
#  - @ref fine.py — штраф
#  - @ref notification.py — уведомление пользователя

from .enums import FineReason, RequestStatus, ReturnCondition, UnitStatus, UserRole
from .equipment import Category, EquipmentModel, EquipmentUnit
from .errors import (
    DomainError, InvalidTransition, NotFoundError, PermissionDenied,
    ValidationError,
)
from .fine import Fine
from .issue import Issue
from .notification import Notification
from .people import Employee, Person, Student, Teacher
from .request import ALLOWED_TRANSITIONS, Request

__all__ = [
    "ALLOWED_TRANSITIONS",
    "Category",
    "DomainError",
    "Employee",
    "EquipmentModel",
    "EquipmentUnit",
    "Fine",
    "FineReason",
    "InvalidTransition",
    "Issue",
    "NotFoundError",
    "Notification",
    "PermissionDenied",
    "Person",
    "Request",
    "RequestStatus",
    "ReturnCondition",
    "Student",
    "Teacher",
    "UnitStatus",
    "UserRole",
    "ValidationError",
]
