## @file domain.py
#  @brief Классы предметной области «АрендаТех» (версия 2.0)
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#  @copyright ЗАО "АБС"
#
#  @par Содержит классы:
#  - @ref Person, @ref Student, @ref Teacher
#  - @ref Administrator, @ref Technician
#  - @ref EquipmentModel, @ref EquipmentUnit, @ref Category
#  - @ref Request, @ref Issue, @ref Fine, @ref Notification

from __future__ import annotations
from datetime import date
from typing import List, Optional

STATUS_PENDING = "На рассмотрении"
STATUS_APPROVED = "Одобрена"
STATUS_REJECTED = "Отклонена"
STATUS_ISSUED = "Выдана"
STATUS_CLOSED = "Закрыта"

CONDITION_OK = "Хорошее"
CONDITION_DAMAGED = "Повреждено"
CONDITION_LOST = "Утеряно"


class Person:
    def __init__(self, id: int, fio: str, email: str, phone: str):
        self._id = id
        self._fio = fio
        self._email = email
        self._phone = phone

    def get_id(self) -> int:
        return self._id

    def get_fio(self) -> str:
        return self._fio

    def get_email(self) -> str:
        return self._email

    def set_email(self, email: str) -> bool:
        if not email or "@" not in email:
            return False
        self._email = email
        return True

    def get_phone(self) -> str:
        return self._phone

    def get_role(self) -> str:
        return "person"

    def __str__(self) -> str:
        return f"Person({self._fio})"


class Student(Person):
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 student_id: str, group: str, faculty: str):
        super().__init__(id, fio, email, phone)
        self._student_id = student_id
        self._group = group
        self._faculty = faculty

    def get_group(self) -> str:
        return self._group

    def get_student_id(self) -> str:
        return self._student_id

    def get_role(self) -> str:
        return "student"


class Teacher(Person):
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 department: str, position: str):
        super().__init__(id, fio, email, phone)
        self._department = department
        self._position = position

    def get_department(self) -> str:
        return self._department

    def get_role(self) -> str:
        return "teacher"


class Administrator(Person):
    def __init__(self, id: int, fio: str, email: str, phone: str, employee_id: str):
        super().__init__(id, fio, email, phone)
        self._employee_id = employee_id

    def get_employee_id(self) -> str:
        return self._employee_id

    def get_role(self) -> str:
        return "administrator"


class Technician(Administrator):
    def __init__(self, id: int, fio: str, email: str, phone: str, employee_id: str):
        super().__init__(id, fio, email, phone, employee_id)

    def get_role(self) -> str:
        return "technician"


class Category:
    def __init__(self, id: int, name: str, fragile: bool = False):
        self._id = id
        self._name = name
        self._fragile = fragile

    def get_name(self) -> str:
        return self._name

    def is_fragile(self) -> bool:
        return self._fragile


class EquipmentModel:
    def __init__(self, id: int, name: str, category: str,
                 characteristics: str, daily_rate: float):
        self._id = id
        self._name = name
        self._category = category
        self._characteristics = characteristics
        self._daily_rate = daily_rate

    def get_id(self) -> int:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_category(self) -> str:
        return self._category

    def get_characteristics(self) -> str:
        return self._characteristics

    def get_daily_rate(self) -> float:
        return self._daily_rate


class EquipmentUnit:
    def __init__(self, id: int, inventory_number: str, model: EquipmentModel,
                 status: str, available: bool):
        self._id = id
        self._inventory_number = inventory_number
        self._model = model
        self._status = status
        self._available = available

    def get_id(self) -> int:
        return self._id

    def get_model(self) -> EquipmentModel:
        return self._model

    def get_status(self) -> str:
        return self._status

    def set_status(self, status: str) -> None:
        self._status = status

    def is_available(self) -> bool:
        return self._available

    def set_available(self, available: bool) -> None:
        self._available = available

    def get_inventory_number(self) -> str:
        return self._inventory_number


class Request:
    def __init__(self, id: int, user: Person, units: List[EquipmentUnit],
                 start_date: str, end_date: str, status: str = STATUS_PENDING):
        self._id = id
        self._user = user
        self._units = units
        self._start_date = start_date
        self._end_date = end_date
        self._status = status

    def get_id(self) -> int:
        return self._id

    def get_user(self) -> Person:
        return self._user

    def get_units(self) -> List[EquipmentUnit]:
        return self._units

    def get_status(self) -> str:
        return self._status

    def set_status(self, status: str) -> None:
        self._status = status

    def get_start_date(self) -> str:
        return self._start_date

    def get_end_date(self) -> str:
        return self._end_date

    def days(self) -> int:
        first = date.fromisoformat(self._start_date)
        last = date.fromisoformat(self._end_date)
        return (last - first).days

    def period_overlaps(self, start_date: str, end_date: str) -> bool:
        first = date.fromisoformat(start_date)
        last = date.fromisoformat(end_date)
        own_first = date.fromisoformat(self._start_date)
        own_last = date.fromisoformat(self._end_date)
        return own_first <= last and first <= own_last

    def approve(self) -> None:
        self._status = STATUS_APPROVED

    def reject(self) -> None:
        self._status = STATUS_REJECTED


class Issue:
    def __init__(self, id: int, request: Request, issue_date: str, cost: float = 0.0):
        self._id = id
        self._request = request
        self._issue_date = issue_date
        self._return_date = ""
        self._condition = ""
        self._cost = cost

    def get_id(self) -> int:
        return self._id

    def get_request(self) -> Request:
        return self._request

    def get_issue_date(self) -> str:
        return self._issue_date

    def get_return_date(self) -> str:
        return self._return_date

    def get_condition(self) -> str:
        return self._condition

    def get_cost(self) -> float:
        return self._cost

    def is_open(self) -> bool:
        return not self._return_date

    def close(self, return_date: str, condition: str) -> None:
        self._return_date = return_date
        self._condition = condition


class Fine:
    def __init__(self, id: int, reason: str, amount: float, issue: Optional[Issue] = None):
        self._id = id
        self._reason = reason
        self._amount = amount
        self._paid = False
        self._issue = issue

    def get_id(self) -> int:
        return self._id

    def get_reason(self) -> str:
        return self._reason

    def get_amount(self) -> float:
        return self._amount

    def is_paid(self) -> bool:
        return self._paid

    def pay(self) -> None:
        self._paid = True


class Notification:
    def __init__(self, id: int, message: str, date: str, user_id: int = 0,
                 kind: str = "info"):
        self._id = id
        self._message = message
        self._date = date
        self._user_id = user_id
        self._kind = kind

    def get_message(self) -> str:
        return self._message

    def get_date(self) -> str:
        return self._date

    def get_user_id(self) -> int:
        return self._user_id

    def get_kind(self) -> str:
        return self._kind
