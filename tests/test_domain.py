## @file test_domain.py
#  @brief Unit-тесты предметной области «АрендаТех»
#  @author Колганов Иван
#  @date 2026-02-10
#  @version 2.0
#
#  @details В версии 1.0 файл не запускался: в начале стоял посторонний
#  символ «ё», из-за чего pytest падал с NameError. Ошибка исправлена,
#  тесты переписаны и дополнены проверками статусов, дат и ролей.

from datetime import date

import pytest

from src.domain import (
    Category, Employee, EquipmentModel, EquipmentUnit, InvalidTransition,
    Issue, Person, Request, RequestStatus, ReturnCondition, Student, Teacher,
    UnitStatus, UserRole, ValidationError,
)


def make_model() -> EquipmentModel:
    return EquipmentModel(1, "Ноутбук Lenovo", Category(1, "Ноутбуки"),
                          "16GB/512GB", 500.0)


def make_unit(number: str = "INV-001") -> EquipmentUnit:
    return EquipmentUnit(1, number, make_model())


## @brief Тест создания объекта Person
def test_person_creation():
    person = Person(1, "Иванов И.И.", "test@test.ru", "+79990000000")
    assert person.fio == "Иванов И.И."
    assert person.role is None
    assert person.can_manage is False


## @brief Тест метода set_email с корректным email
def test_set_email_valid():
    person = Person(1, "Test", "old@test.ru", "+70000000000")
    assert person.set_email("new@test.ru") is True
    assert person.email == "new@test.ru"


## @brief Тест метода set_email с пустой строкой
def test_set_email_empty():
    person = Person(1, "Test", "old@test.ru", "+70000000000")
    assert person.set_email("") is False


## @brief Тест создания студента и его роли
def test_student_group_and_role():
    student = Student(2, "Петров П.П.", "s@test.ru", "+79991111111",
                      "12345", "ИТ-01", "ФИТ")
    assert student.group == "ИТ-01"
    assert student.role is UserRole.STUDENT
    assert student.can_manage is False


## @brief Тест преподавателя
def test_teacher_department():
    teacher = Teacher(3, "Петров П.П.", "t@test.ru", "+79991111111",
                      "Кафедра ИТ", "Доцент")
    assert teacher.get_department() == "Кафедра ИТ"
    assert teacher.role is UserRole.TEACHER


## @brief Тест сотрудника: роль сотрудника даёт право управления
def test_employee_can_manage():
    employee = Employee(4, "Сидоров С.С.", "e@test.ru", "+79992222222",
                        "EMP-1", UserRole.TECHNICIAN)
    assert employee.can_manage is True
    assert employee.get_employee_id() == "EMP-1"


## @brief Тест запрета роли, не являющейся ролью сотрудника
def test_employee_rejects_student_role():
    with pytest.raises(ValidationError):
        Employee(5, "Сидоров С.С.", "e@test.ru", "+79992222222",
                 "EMP-2", UserRole.STUDENT)


## @brief Тест стоимости модели техники
def test_equipment_model_rate():
    model = make_model()
    assert model.daily_rate == 500.0
    assert model.replacement_cost == 5000.0


## @brief Тест категории и коэффициента ущерба
def test_category_names_and_coefficient():
    category = Category(1, "Проекторы", damage_coefficient=0.2)
    assert category.get_name() == "Проекторы"
    assert category.damage_coefficient == 0.2


## @brief Тест доступности единицы техники
def test_equipment_unit_availability():
    unit = make_unit()
    assert unit.is_available is True
    unit.set_status(UnitStatus.ISSUED)
    assert unit.is_available is False


## @brief Тест расчёта суток аренды
def test_request_days():
    request = Request(1, Person(1, "A", "a@a.ru", ""), [make_unit()],
                      date(2026, 2, 10), date(2026, 2, 20))
    assert request.days == 10
    assert request.status is RequestStatus.PENDING


## @brief Тест проверки пересечения периодов
def test_request_overlaps():
    request = Request(1, Person(1, "A", "a@a.ru", ""), [make_unit()],
                      date(2026, 2, 10), date(2026, 2, 20))
    assert request.overlaps(date(2026, 2, 15), date(2026, 2, 18)) is True
    assert request.overlaps(date(2026, 2, 21), date(2026, 2, 25)) is False


## @brief Тест некорректного периода аренды
def test_request_rejects_empty_units_and_period():
    user = Person(1, "A", "a@a.ru", "")
    with pytest.raises(ValidationError):
        Request(1, user, [], date(2026, 2, 10), date(2026, 2, 20))
    with pytest.raises(ValidationError):
        Request(1, user, [make_unit()], date(2026, 2, 20), date(2026, 2, 10))


## @brief Тест допустимых и недопустимых переходов статуса
def test_request_transitions():
    request = Request(1, Person(1, "A", "a@a.ru", ""), [make_unit()],
                      date(2026, 2, 10), date(2026, 2, 20))
    request.transition(RequestStatus.APPROVED)
    assert request.status is RequestStatus.APPROVED
    with pytest.raises(InvalidTransition):
        request.transition(RequestStatus.CLOSED)


## @brief Тест просрочки и закрытия выдачи
def test_issue_overdue_and_close():
    request = Request(1, Person(1, "A", "a@a.ru", ""), [make_unit()],
                      date(2026, 2, 10), date(2026, 2, 20))
    issue = Issue(1, request, date(2026, 2, 10), 5000.0)
    assert issue.is_open is True
    assert issue.overdue_days(date(2026, 2, 24)) == 4
    assert issue.overdue_days(date(2026, 2, 18)) == 0
    issue.close(date(2026, 2, 24), ReturnCondition.DAMAGED)
    assert issue.is_open is False
    assert issue.condition is ReturnCondition.DAMAGED
    assert issue.cost == 5000.0
