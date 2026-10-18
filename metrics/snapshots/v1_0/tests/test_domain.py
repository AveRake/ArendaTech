ё## @file test_domain.py
#  @brief Unit-тесты для модуля domain
#  @author Колганов Иван
#  @date 2025-10-02
#  @version 1.0

import pytest
from src.domain import Person, Student, EquipmentModel, Category


## @brief Тест создания объекта Person
def test_person_creation():
    p = Person(1, "Иванов И.И.", "test@test.ru", "+79990000000")
    assert p.get_fio() == "Иванов И.И."


## @brief Тест метода set_email с корректным email
def test_set_email_valid():
    p = Person(1, "Test", "old@test.ru", "+70000000000")
    assert p.set_email("new@test.ru") is True
    assert p.get_email() == "new@test.ru"


## @brief Тест метода set_email с пустой строкой
def test_set_email_empty():
    p = Person(1, "Test", "old@test.ru", "+70000000000")
    assert p.set_email("") is False


## @brief Тест создания студента
def test_student_group():
    s = Student(2, "Петров П.П.", "s@test.ru", "+79991111111",
                "12345", "ИТ-01", "ФИТ")
    assert s.get_group() == "ИТ-01"


## @brief Тест стоимости модели техники
def test_equipment_model_rate():
    m = EquipmentModel(1, "Ноутбук Lenovo", "Ноутбуки", "16GB/512GB", 500.0)
    assert m.get_daily_rate() == 500.0


## @brief Тест категории
def test_category_name():
    c = Category(1, "Ноутбуки")
    assert c.get_name() == "Ноутбуки"