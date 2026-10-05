## @file main.py
#  @brief Точка входа приложения «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2025-01-01
#  @version 1.0
#
#  @par Использует файлы:
#  - @ref domain.py
#  - @ref service.py

from src.domain import Student, EquipmentModel, EquipmentUnit
from src.service import RentalService


## @brief Точка входа
#  @return Код возврата
def main() -> int:
    student = Student(1, "Иванов И.И.", "ivanov@example.com",
                      "+79990000000", "12345", "ИТ-01", "ФИТ")
    model = EquipmentModel(1, "Ноутбук Lenovo ThinkPad", "Ноутбуки",
                           "16GB/512GB", 500.0)
    unit = EquipmentUnit(1, "INV-001", model, "Доступна", True)

    service = RentalService()
    request = service.create_request(student, [unit], "2025-01-10", "2025-01-15")
    print(f"Студент: {student.get_fio()}, группа: {student.get_group()}")
    print(f"Модель: {model.get_name()}, цена: {model.get_daily_rate()}")
    print(f"Заявка: {request.get_status()}")

    issue = service.issue_equipment(request, "2025-01-10")
    print(f"После выдачи: {request.get_status()}")

    service.return_equipment(issue, "2025-01-15", "Хорошее", 0.0)
    print("Возврат оформлен")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())