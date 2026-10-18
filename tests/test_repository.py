## @file test_repository.py
#  @brief Unit-тесты сохранения и загрузки состояния
#  @author Колганов Иван
#  @date 2026-02-10
#  @version 2.0

import json
from datetime import date

from src.domain import (
    Category, Employee, EquipmentModel, EquipmentUnit, RequestStatus,
    ReturnCondition, Student, UserRole,
)
from src.repository import InMemoryRepository, JsonRepository, create_repository
from src.serialization import ServiceState, state_from_dict, state_to_dict
from src.service import RentalService


def build_service() -> RentalService:
    service = RentalService()
    category = Category(1, "Ноутбуки", damage_coefficient=0.10)
    model = EquipmentModel(1, "Ноутбук", category, "16GB", 500.0)
    unit = EquipmentUnit(1, "INV-001", model)
    service.add_unit(unit)
    student = Student(1, "Иванов И.И.", "i@test.ru", "+79990000000",
                      "123", "ИТ-01", "ФИТ")
    admin = Employee(2, "Сидорова А.А.", "a@test.ru", "+79992222222",
                     "EMP-1", UserRole.ADMINISTRATOR)
    request = service.create_request(student, [unit], date(2026, 2, 10),
                                     date(2026, 2, 20))
    service.approve_request(request, admin)
    issue = service.issue_equipment(request, admin, date(2026, 2, 10))
    service.return_equipment(issue, admin, date(2026, 2, 20),
                             ReturnCondition.GOOD)
    return service


## @brief Тест сохранения состояния в JSON и загрузки обратно
def test_json_round_trip(tmp_path):
    service = build_service()
    path = tmp_path / "state.json"
    repository = JsonRepository(str(path))
    repository.save(service.state())
    assert path.exists()

    restored = RentalService()
    restored.restore(repository.load())
    assert len(restored.requests) == 1
    assert restored.requests[0].user.fio == "Иванов И.И."
    assert restored.requests[0].status is RequestStatus.CLOSED
    assert restored.issues[0].request.id == restored.requests[0].id
    assert restored.issues[0].condition is ReturnCondition.GOOD
    assert restored.units[0].inventory_number == "INV-001"


## @brief Тест ссылочной целостности после загрузки
def test_issue_refers_to_loaded_request(tmp_path):
    service = build_service()
    repository = JsonRepository(str(tmp_path / "state.json"))
    repository.save(service.state())
    restored = RentalService()
    restored.restore(repository.load())
    assert restored.issues[0].request is restored.requests[0]


## @brief Тест сериализации состояния в словарь
def test_state_to_dict_contains_sections():
    payload = state_to_dict(build_service().state())
    assert set(payload) >= {"units", "requests", "issues", "fines", "notifications"}
    assert payload["requests"][0]["user"]["kind"] == "student"


## @brief Тест восстановления состояния из словаря
def test_state_from_dict():
    original = build_service().state()
    restored = state_from_dict(json.loads(json.dumps(state_to_dict(original),
                                                     ensure_ascii=False)))
    assert isinstance(restored, ServiceState)
    assert len(restored.units) == 1
    assert len(restored.issues) == 1


## @brief Тест хранилища в памяти
def test_in_memory_repository():
    repository = InMemoryRepository()
    state = build_service().state()
    repository.save(state)
    assert repository.load().requests[0].id == state.requests[0].id


## @brief Тест фабрики хранилищ
def test_create_repository(tmp_path):
    assert isinstance(create_repository(), InMemoryRepository)
    repository = create_repository(str(tmp_path / "state.json"))
    assert isinstance(repository, JsonRepository)
