## @file test_reports.py
#  @brief Unit-тесты построения отчёта
#  @author Колганов Иван
#  @date 2026-02-10
#  @version 2.0

from datetime import date

from src.domain import (
    Category, Employee, EquipmentModel, EquipmentUnit, Student, UserRole,
)
from src.reports import RentalReport
from src.service import RentalService


def build_filled_service() -> RentalService:
    service = RentalService()
    laptops = Category(1, "Ноутбуки", damage_coefficient=0.10)
    projectors = Category(2, "Проекторы", damage_coefficient=0.20)
    laptop = EquipmentModel(1, "Ноутбук", laptops, "16GB", 500.0)
    projector = EquipmentModel(2, "Проектор", projectors, "4200 лм", 700.0)
    service.add_unit(EquipmentUnit(1, "INV-001", laptop))
    service.add_unit(EquipmentUnit(2, "INV-002", laptop))
    service.add_unit(EquipmentUnit(3, "INV-003", projector))
    return service


## @brief Тест статистики по единицам техники
def test_statistics_units_and_categories():
    service = build_filled_service()
    stats = RentalReport(service.units, service.requests, service.issues,
                         service.fines).statistics()
    assert stats.units_total == 3
    assert stats.units_free == 3
    assert stats.by_category == {"Ноутбуки": 2, "Проекторы": 1}


## @brief Тест статистики по деньгам и активным выдачам
def test_statistics_money_and_active():
    service = build_filled_service()
    student = Student(1, "Иванов И.И.", "i@test.ru", "+79990000000",
                      "123", "ИТ-01", "ФИТ")
    admin = Employee(2, "Сидорова А.А.", "a@test.ru", "+79992222222",
                     "EMP-1", UserRole.ADMINISTRATOR)
    request = service.create_request(student, service.units[:1],
                                     date(2026, 2, 10), date(2026, 2, 20))
    service.approve_request(request, admin)
    issue = service.issue_equipment(request, admin, date(2026, 2, 10))
    report = RentalReport(service.units, service.requests, service.issues,
                          service.fines)
    stats = report.statistics()
    assert stats.issues_total == 1
    assert stats.issues_active == 1
    assert stats.income == issue.cost
    assert stats.units_free == 2
    assert len(report.active_issues()) == 1


## @brief Тест текста отчёта
def test_report_text():
    service = build_filled_service()
    text = RentalReport(service.units, service.requests, service.issues,
                        service.fines).build()
    assert "ОТЧЁТ СЕРВИСА «АРЕНДАТЕХ»" in text
    assert "Единиц техники: 3" in text
    assert "Ноутбуки: 2 ед." in text
