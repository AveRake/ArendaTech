## @file demo.py
#  @brief Демонстрационный сценарий работы сервиса «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Сценарий используется в точке входа @ref main.py и в отчёте по
#  лабораторной работе: он проходит полный цикл «заявка → согласование →
#  выдача → возврат с штрафом → отчёт → сохранение состояния».

from __future__ import annotations
from datetime import date
from typing import List, Optional

from .domain import (
    Category, Employee, EquipmentModel, EquipmentUnit, ReturnCondition,
    Student, Teacher, UserRole,
)
from .repository import JsonRepository
from .service import RentalService


## @brief Создать справочники и единицы техники
#  @param service Сервис аренды
#  @return Кортеж (студент, преподаватель, администратор, техник, единицы)
def build_fixtures(service: RentalService):
    student = Student(1, "Иванов И.И.", "ivanov@example.com",
                      "+79990000000", "12345", "ИТ-01", "ФИТ")
    teacher = Teacher(2, "Петров П.П.", "petrov@example.com",
                      "+79991111111", "Кафедра ИТ", "Доцент")
    admin = Employee(3, "Сидорова А.А.", "admin@example.com",
                     "+79992222222", "EMP-001", UserRole.ADMINISTRATOR)
    technician = Employee(4, "Кузнецов К.К.", "tech@example.com",
                          "+79993333333", "EMP-002", UserRole.TECHNICIAN)

    laptops = Category(1, "Ноутбуки", damage_coefficient=0.10)
    projectors = Category(2, "Проекторы", damage_coefficient=0.20)
    laptop_model = EquipmentModel(1, "Ноутбук Lenovo ThinkPad", laptops,
                                  "16GB/512GB", 500.0)
    projector_model = EquipmentModel(2, "Проектор Epson EB-970", projectors,
                                     "4200 лм", 700.0)

    units: List[EquipmentUnit] = [
        EquipmentUnit(1, "INV-001", laptop_model),
        EquipmentUnit(2, "INV-002", laptop_model),
        EquipmentUnit(3, "INV-003", projector_model),
    ]
    for unit in units:
        service.add_unit(unit)
    return student, teacher, admin, technician, units


## @brief Выполнить демонстрационный сценарий
#  @param state_path Путь для сохранения состояния (None — не сохранять)
#  @return Код возврата
def run_demo(state_path: Optional[str] = None) -> int:
    service = RentalService()
    student, teacher, admin, technician, units = build_fixtures(service)
    laptop_1, laptop_2, projector = units

    print("=== АрендаТех, версия 2.0: демонстрационный сценарий ===")
    request = service.create_request(student, [laptop_1, laptop_2],
                                     date(2026, 2, 10), date(2026, 2, 20))
    print(f"Создана заявка №{request.id}: статус «{request.status.value}», "
          f"суток — {request.days}")

    service.approve_request(request, admin)
    print(f"После согласования: «{request.status.value}»")

    issue = service.issue_equipment(request, technician, date(2026, 2, 10))
    print(f"Оформлена выдача №{issue.id}, стоимость {issue.cost:.2f} руб.")

    rejection = _try_overlap_booking(service, teacher, laptop_1)
    if rejection:
        print(f"Ожидаемый отказ: {rejection}")

    fines = service.return_equipment(issue, technician, date(2026, 2, 24),
                                     ReturnCondition.DAMAGED)
    print("Возврат оформлен, начисления:")
    for item in fines:
        print(f"  {item.reason.value}: {item.amount:.2f} руб.")

    print()
    print(service.report())
    print()
    print("Уведомления студента:")
    for notification in service.notifications(user_id=student.id):
        print(f"  [{notification.kind}] {notification.message}")
    if state_path:
        JsonRepository(state_path).save(service.state())
        print(f"\nСостояние сервиса сохранено в {state_path}")
    return 0


## @brief Попытаться забронировать занятую единицу
#  @param service Сервис аренды
#  @param user Пользователь
#  @param unit Занятая единица техники
#  @return Текст ошибки или пустая строка
def _try_overlap_booking(service: RentalService, user, unit: EquipmentUnit) -> str:
    try:
        service.create_request(user, [unit], date(2026, 2, 15), date(2026, 2, 18))
    except Exception as error:  # noqa: BLE001 - демонстрация обработки ошибок
        return str(error)
    return ""


## @brief Точка входа демонстрационного сценария
#  @return Код возврата
def main() -> int:
    return run_demo()
