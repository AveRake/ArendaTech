## @file test_service.py
#  @brief Unit-тесты сервиса аренды
#  @author Колганов Иван
#  @date 2026-02-10
#  @version 2.0

from datetime import date

import pytest

from src.domain import (
    Category, Employee, EquipmentModel, EquipmentUnit, InvalidTransition,
    PermissionDenied, RequestStatus, ReturnCondition, Student, Teacher,
    UnitStatus, UserRole, ValidationError,
)
from src.service import RentalService


def make_service():
    service = RentalService()
    category = Category(1, "Ноутбуки", damage_coefficient=0.10)
    model = EquipmentModel(1, "Ноутбук", category, "16GB", 500.0)
    units = [EquipmentUnit(1, "INV-001", model), EquipmentUnit(2, "INV-002", model)]
    for unit in units:
        service.add_unit(unit)
    return service, units


def make_student():
    return Student(1, "Иванов И.И.", "i@test.ru", "+79990000000",
                   "123", "ИТ-01", "ФИТ")


def make_admin():
    return Employee(3, "Сидорова А.А.", "a@test.ru", "+79992222222",
                    "EMP-1", UserRole.ADMINISTRATOR)


## @brief Тест полного цикла: заявка → выдача → возврат
def test_full_cycle():
    service, units = make_service()
    student = make_student()
    request = service.create_request(student, units, date(2026, 2, 10),
                                    date(2026, 2, 20))
    assert request.status is RequestStatus.PENDING

    service.approve_request(request, make_admin())
    assert request.status is RequestStatus.APPROVED

    issue = service.issue_equipment(request, make_admin(), date(2026, 2, 10))
    assert request.status is RequestStatus.ISSUED
    assert issue.cost == 8550.0  # 10000 * 0.9 * 0.95
    assert all(unit.status is UnitStatus.ISSUED for unit in units)

    fine_items = service.return_equipment(issue, make_admin(), date(2026, 2, 24),
                                         ReturnCondition.DAMAGED)
    assert request.status is RequestStatus.CLOSED
    assert {item.reason.value for item in fine_items} == {"Просрочка", "Повреждение"}
    assert all(unit.status is UnitStatus.IN_REPAIR for unit in units)
    assert len(service.fines) == 2
    assert sum(fine.amount for fine in service.fines) == 2100.0


## @brief Тест отказа в доступе для студента
def test_student_cannot_approve():
    service, units = make_service()
    request = service.create_request(make_student(), units,
                                    date(2026, 2, 10), date(2026, 2, 20))
    with pytest.raises(PermissionDenied):
        service.approve_request(request, make_student())


## @brief Тест запрета выдачи неодобренной заявки
def test_issue_requires_approval():
    service, units = make_service()
    request = service.create_request(make_student(), units,
                                    date(2026, 2, 10), date(2026, 2, 20))
    with pytest.raises(InvalidTransition):
        service.issue_equipment(request, make_admin(), date(2026, 2, 10))


## @brief Тест отказа при бронировании занятой единицы
def test_booking_conflict():
    service, units = make_service()
    student = make_student()
    service.create_request(student, [units[0]], date(2026, 2, 10),
                           date(2026, 2, 20))
    teacher = Teacher(2, "Петров П.П.", "p@test.ru", "+79991111111",
                      "Кафедра", "Доцент")
    with pytest.raises(ValidationError):
        service.create_request(teacher, [units[0]], date(2026, 2, 15),
                               date(2026, 2, 18))


## @brief Тест разрешения бронирования в непересекающийся период
def test_booking_in_free_period():
    service, units = make_service()
    student = make_student()
    service.create_request(student, [units[0]], date(2026, 2, 10),
                           date(2026, 2, 20))
    teacher = Teacher(2, "Петров П.П.", "p@test.ru", "+79991111111",
                      "Кафедра", "Доцент")
    request = service.create_request(teacher, [units[0]], date(2026, 2, 21),
                                     date(2026, 2, 25))
    assert request.status is RequestStatus.PENDING


## @brief Тест отклонения заявки и уведомления
def test_reject_request_notifies_user():
    service, units = make_service()
    student = make_student()
    request = service.create_request(student, units, date(2026, 2, 10),
                                     date(2026, 2, 20))
    service.reject_request(request, make_admin(), "нет свободных единиц")
    assert request.status is RequestStatus.REJECTED
    messages = [item.message for item in service.notifications(user_id=student.id)]
    assert any("отклонена" in message for message in messages)


## @brief Тест запрета повторного возврата
def test_return_twice_fails():
    service, units = make_service()
    student = make_student()
    admin = make_admin()
    request = service.create_request(student, units, date(2026, 2, 10),
                                     date(2026, 2, 20))
    service.approve_request(request, admin)
    issue = service.issue_equipment(request, admin, date(2026, 2, 10))
    service.return_equipment(issue, admin, date(2026, 2, 20),
                             ReturnCondition.GOOD)
    with pytest.raises(ValidationError):
        service.return_equipment(issue, admin, date(2026, 2, 21),
                                 ReturnCondition.GOOD)


## @brief Тест запрета аренды более 30 суток
def test_period_limit():
    service, units = make_service()
    with pytest.raises(ValidationError):
        service.create_request(make_student(), units, date(2026, 2, 1),
                               date(2026, 3, 15))


## @brief Тест запрета повторной регистрации единицы
def test_duplicate_unit_registration():
    service, units = make_service()
    with pytest.raises(ValidationError):
        service.add_unit(EquipmentUnit(3, "INV-001", units[0].model))


## @brief Тест отчёта сервиса
def test_report_contains_key_blocks():
    service, units = make_service()
    student = make_student()
    admin = make_admin()
    request = service.create_request(student, units, date(2026, 2, 10),
                                     date(2026, 2, 20))
    service.approve_request(request, admin)
    service.issue_equipment(request, admin, date(2026, 2, 10))
    report = service.report()
    assert "ОТЧЁТ СЕРВИСА «АРЕНДАТЕХ»" in report
    assert "Начисленный доход" in report
    assert "Активные выдачи" in report
