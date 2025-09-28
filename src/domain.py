## @file domain.py
#  @brief Классы предметной области «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2025-01-01
#  @version 1.0
#  @copyright ЗАО "АБС"
#
#  @par Содержит классы:
#  - @ref Person
#  - @ref Student
#  - @ref Teacher
#  - @ref Administrator
#  - @ref Technician
#  - @ref EquipmentModel
#  - @ref EquipmentUnit
#  - @ref Request
#  - @ref Issue
#  - @ref Fine
#  - @ref Notification

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


## @brief Базовый класс пользователя
#  @details Содержит общие поля и методы для всех пользователей системы.
class Person:
    ## @brief Конструктор
    #  @param id Уникальный идентификатор
    #  @param fio ФИО
    #  @param email Электронная почта
    #  @param phone Телефон
    def __init__(self, id: int, fio: str, email: str, phone: str):
        self._id = id            ##< Уникальный идентификатор
        self._fio = fio          ##< ФИО
        self._email = email      ##< Email
        self._phone = phone      ##< Телефон

    ## @brief Получить ФИО
    #  @return ФИО пользователя
    def get_fio(self) -> str:
        return self._fio

    ## @brief Изменить email
    #  @param email Новый email
    #  @return True, если успешно, иначе False
    def set_email(self, email: str) -> bool:
        if not email:
            return False
        self._email = email
        return True

    def get_email(self) -> str:
        return self._email

    ## @brief Строковое представление
    #  @return Строка с ФИО
    def __str__(self) -> str:
        return f"Person({self._fio})"


## @brief Класс студента
#  @details Наследник Person, содержит данные студента.
class Student(Person):
    ## @brief Конструктор
    #  @param id Идентификатор
    #  @param fio ФИО
    #  @param email Email
    #  @param phone Телефон
    #  @param student_id Номер студенческого билета
    #  @param group Учебная группа
    #  @param faculty Факультет
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 student_id: str, group: str, faculty: str):
        super().__init__(id, fio, email, phone)
        self._student_id = student_id  ##< Номер студенческого
        self._group = group            ##< Группа
        self._faculty = faculty        ##< Факультет

    ## @brief Получить группу
    #  @return Название группы
    def get_group(self) -> str:
        return self._group


## @brief Класс преподавателя
class Teacher(Person):
    ## @brief Конструктор
    #  @param id Идентификатор
    #  @param fio ФИО
    #  @param email Email
    #  @param phone Телефон
    #  @param department Кафедра
    #  @param position Должность
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 department: str, position: str):
        super().__init__(id, fio, email, phone)
        self._department = department  ##< Кафедра
        self._position = position      ##< Должность

    ## @brief Получить кафедру
    #  @return Название кафедры
    def get_department(self) -> str:
        return self._department


## @brief Класс администратора
class Administrator(Person):
    ## @brief Конструктор
    #  @param id Идентификатор
    #  @param fio ФИО
    #  @param email Email
    #  @param phone Телефон
    #  @param employee_id Табельный номер
    def __init__(self, id: int, fio: str, email: str, phone: str, employee_id: str):
        super().__init__(id, fio, email, phone)
        self._employee_id = employee_id  ##< Табельный номер


## @brief Класс техника
#  @details Наследник Administrator.
class Technician(Administrator):
    ## @brief Конструктор
    #  @param id Идентификатор
    #  @param fio ФИО
    #  @param email Email
    #  @param phone Телефон
    #  @param employee_id Табельный номер
    def __init__(self, id: int, fio: str, email: str, phone: str, employee_id: str):
        super().__init__(id, fio, email, phone, employee_id)


## @brief Класс модели техники
class EquipmentModel:
    ## @brief Конструктор
    #  @param id Идентификатор модели
    #  @param name Название модели
    #  @param category Категория
    #  @param characteristics Характеристики
    #  @param daily_rate Стоимость аренды в сутки
    def __init__(self, id: int, name: str, category: str,
                 characteristics: str, daily_rate: float):
        self._id = id                            ##< ID модели
        self._name = name                        ##< Название
        self._category = category                ##< Категория
        self._characteristics = characteristics  ##< Характеристики
        self._daily_rate = daily_rate            ##< Стоимость аренды в сутки

    ## @brief Получить стоимость аренды
    #  @return Стоимость в сутки
    def get_daily_rate(self) -> float:
        return self._daily_rate

    ## @brief Получить название
    #  @return Название модели
    def get_name(self) -> str:
        return self._name


## @brief Класс единицы техники
class EquipmentUnit:
    ## @brief Конструктор
    #  @param id ID единицы
    #  @param inventory_number Инвентарный номер
    #  @param model Модель техники
    #  @param status Статус
    #  @param available Доступность
    def __init__(self, id: int, inventory_number: str, model: EquipmentModel,
                 status: str, available: bool):
        self._id = id                            ##< ID единицы
        self._inventory_number = inventory_number  ##< Инвентарный номер
        self._model = model                      ##< Модель
        self._status = status                    ##< Статус
        self._available = available              ##< Доступность

    ## @brief Доступна ли единица
    #  @return True, если доступна
    def is_available(self) -> bool:
        return self._available

    ## @brief Получить инвентарный номер
    #  @return Инвентарный номер
    def get_inventory_number(self) -> str:
        return self._inventory_number


## @brief Класс заявки на аренду
class Request:
    ## @brief Конструктор
    #  @param id ID заявки
    #  @param user Пользователь-заявитель
    #  @param units Список единиц техники
    #  @param start_date Дата начала аренды
    #  @param end_date Дата окончания аренды
    #  @param status Статус заявки
    def __init__(self, id: int, user: Person, units: List[EquipmentUnit],
                 start_date: str, end_date: str, status: str):
        self._id = id                ##< ID заявки
        self._user = user            ##< Пользователь
        self._units = units          ##< Единицы техники
        self._start_date = start_date  ##< Дата начала
        self._end_date = end_date      ##< Дата окончания
        self._status = status          ##< Статус

    ## @brief Получить статус
    #  @return Статус заявки
    def get_status(self) -> str:
        return self._status

    ## @brief Одобрить заявку
    def approve(self) -> None:
        self._status = "Одобрена"

    ## @brief Отклонить заявку
    def reject(self) -> None:
        self._status = "Отклонена"


## @brief Класс выдачи техники
class Issue:
    ## @brief Конструктор
    #  @param id ID выдачи
    #  @param request Заявка
    #  @param issue_date Дата выдачи
    def __init__(self, id: int, request: Request, issue_date: str):
        self._id = id                ##< ID выдачи
        self._request = request      ##< Заявка
        self._issue_date = issue_date  ##< Дата выдачи
        self._return_date = ""       ##< Дата возврата
        self._condition = ""         ##< Состояние при возврате

    ## @brief Закрыть выдачу (возврат)
    #  @param return_date Дата возврата
    #  @param condition Состояние техники
    def close(self, return_date: str, condition: str) -> None:
        self._return_date = return_date
        self._condition = condition


## @brief Класс штрафа
class Fine:
    ## @brief Конструктор
    #  @param id ID штрафа
    #  @param reason Причина штрафа
    #  @param amount Сумма штрафа
    def __init__(self, id: int, reason: str, amount: float):
        self._id = id            ##< ID штрафа
        self._reason = reason    ##< Причина
        self._amount = amount    ##< Сумма
        self._paid = False       ##< Оплачен

    ## @brief Оплатить штраф
    def pay(self) -> None:
        self._paid = True

    ## @brief Получить сумму штрафа
    #  @return Сумма
    def get_amount(self) -> float:
        return self._amount


## @brief Класс уведомления
class Notification:
    ## @brief Конструктор
    #  @param id ID уведомления
    #  @param message Текст уведомления
    #  @param date Дата
    def __init__(self, id: int, message: str, date: str):
        self._id = id            ##< ID уведомления
        self._message = message  ##< Текст
        self._date = date        ##< Дата

    ## @brief Получить текст уведомления
    #  @return Текст
    def get_message(self) -> str:
        return self._message


## @brief Класс категории техники
#  @details Используется для группировки моделей оборудования по типам.
class Category:
    ## @brief Конструктор
    #  @param id Идентификатор категории
    #  @param name Название категории
    def __init__(self, id: int, name: str):
        self._id = id      ##< ID категории
        self._name = name  ##< Название категории

    ## @brief Получить название категории
    #  @return Название категории
    def get_name(self) -> str:
        return self._name