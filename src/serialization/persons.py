## @file persons.py
#  @brief Сериализация пользователей «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Пользователь сохраняется вместе с признаком вида (@c kind),
#  чтобы при загрузке восстановить нужный подкласс (@c Student,
#  @c Teacher или @c Employee).

from __future__ import annotations
from typing import Any, Callable, Dict

from ..domain import (
    Employee, Person, Student, Teacher, UserRole,
)


def person_to_dict(person: Person) -> Dict[str, Any]:
    ## @brief Преобразовать пользователя в словарь
    #  @param person Пользователь
    #  @return Словарь с полями пользователя
    data: Dict[str, Any] = {
        "id": person.id,
        "fio": person.fio,
        "email": person.email,
        "phone": person.phone,
        "role": person.role.value if person.role else None,
        "kind": person_kind(person),
    }
    if isinstance(person, Student):
        data.update(student_id=person.student_id, group=person.group,
                    faculty=person.faculty)
    elif isinstance(person, Teacher):
        data.update(department=person.department, position=person.position)
    elif isinstance(person, Employee):
        data.update(employee_id=person.get_employee_id())
    return data


def person_kind(person: Person) -> str:
    ## @brief Определить вид пользователя для сериализации
    #  @param person Пользователь
    #  @return Строковый признак вида
    if isinstance(person, Student):
        return "student"
    if isinstance(person, Teacher):
        return "teacher"
    if isinstance(person, Employee):
        return "employee"
    return "person"


def _person_from_dict(data: Dict[str, Any]) -> Person:
    ## @brief Восстановить базового пользователя
    #  @param data Словарь полей
    #  @return Пользователь
    role = UserRole(data["role"]) if data.get("role") else None
    return Person(data["id"], data["fio"], data["email"], data["phone"], role)


def _student_from_dict(data: Dict[str, Any]) -> Person:
    ## @brief Восстановить студента
    #  @param data Словарь полей
    #  @return Студент
    return Student(data["id"], data["fio"], data["email"], data["phone"],
                   data["student_id"], data["group"], data["faculty"])


def _teacher_from_dict(data: Dict[str, Any]) -> Person:
    ## @brief Восстановить преподавателя
    #  @param data Словарь полей
    #  @return Преподаватель
    return Teacher(data["id"], data["fio"], data["email"], data["phone"],
                   data["department"], data["position"])


def _employee_from_dict(data: Dict[str, Any]) -> Person:
    ## @brief Восстановить сотрудника
    #  @param data Словарь полей
    #  @return Сотрудник
    return Employee(data["id"], data["fio"], data["email"], data["phone"],
                    data["employee_id"], UserRole(data["role"]))


#: Фабрики пользователей по признаку вида.
PERSON_FACTORIES: Dict[str, Callable[[Dict[str, Any]], Person]] = {
    "person": _person_from_dict,
    "student": _student_from_dict,
    "teacher": _teacher_from_dict,
    "employee": _employee_from_dict,
}


def person_from_dict(data: Dict[str, Any]) -> Person:
    ## @brief Восстановить пользователя
    #  @param data Словарь полей
    #  @return Пользователь нужного вида
    return PERSON_FACTORIES.get(data.get("kind", "person"), _person_from_dict)(data)
