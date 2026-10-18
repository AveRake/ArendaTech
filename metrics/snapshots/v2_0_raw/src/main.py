## @file main.py
#  @brief Точка входа приложения «АрендаТех» (демонстрационный сценарий)
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @par Использует файлы:
#  - @ref domain.py
#  - @ref service.py

from src.domain import (
    Administrator, Category, EquipmentModel, EquipmentUnit, Student, Teacher,
    Technician, CONDITION_DAMAGED,
)
from src.service import RentalService


## @brief Демонстрационный сценарий работы сервиса
#  @return Код возврата
def main() -> int:
    service = RentalService()

    student = Student(1, "Иванов И.И.", "ivanov@example.com",
                      "+79990000000", "12345", "ИТ-01", "ФИТ")
    teacher = Teacher(2, "Петров П.П.", "petrov@example.com",
                      "+79991111111", "Кафедра ИТ", "Доцент")
    admin = Administrator(3, "Сидорова А.А.", "admin@example.com",
                          "+79992222222", "EMP-001")
    technician = Technician(4, "Кузнецов К.К.", "tech@example.com",
                            "+79993333333", "EMP-002")

    laptops = Category(1, "Ноутбуки")
    projectors = Category(2, "Проекторы", fragile=True)
    laptop_model = EquipmentModel(1, "Ноутбук Lenovo ThinkPad", laptops.get_name(),
                                  "16GB/512GB", 500.0)
    projector_model = EquipmentModel(2, "Проектор Epson EB-970", projectors.get_name(),
                                     "4200 лм", 700.0)

    laptop_1 = EquipmentUnit(1, "INV-001", laptop_model, "Доступна", True)
    laptop_2 = EquipmentUnit(2, "INV-002", laptop_model, "Доступна", True)
    projector = EquipmentUnit(3, "INV-003", projector_model, "Доступна", True)
    for unit in (laptop_1, laptop_2, projector):
        service.add_unit(unit)

    print("=== АрендаТех, версия 2.0 ===")
    request = service.create_request(student, [laptop_1, laptop_2],
                                     "2026-02-10", "2026-02-20")
    print(f"Заявка №{request.get_id()}: {request.get_status()}, "
          f"суток — {request.days()}")

    service.approve_request(request, admin)
    print(f"После одобрения: {request.get_status()}")

    issue = service.issue_equipment(request, technician, "2026-02-10")
    print(f"Выдача №{issue.get_id()}, стоимость {issue.get_cost():.2f} руб.")

    try:
        service.create_request(teacher, [laptop_1], "2026-02-15", "2026-02-18")
    except ValueError as error:
        print(f"Ожидаемый отказ: {error}")

    service.return_equipment(issue, "2026-02-24", CONDITION_DAMAGED)
    print("Возврат оформлен, штрафы:")
    for fine in service.get_fines():
        print(f"  №{fine.get_id()}: {fine.get_reason()} — {fine.get_amount():.2f} руб.")

    print()
    print(service.build_report())
    print()
    print("Уведомления студента:")
    for notification in service.get_notifications(user_id=student.get_id()):
        print(f"  [{notification.get_kind()}] {notification.get_message()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
