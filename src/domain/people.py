## @file people.py
#  @brief Пользователи системы «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#  @copyright ЗАО "АБС"
#
#  @par Содержит классы:
#  - @c Person
#  - @c Student
#  - @c Teacher
#  - @c Employee
#
#  @details В версии 1.0 иерархия имела вид Person → Administrator →
#  Technician (глубина наследования 3) и нарушала правило CA1501.
#  В версии 2.0 иерархия уплощена: административные и технические роли
#  вынесены в перечисление @c UserRole, а сотрудники описываются единым
#  классом @c Employee (глубина наследования не превышает 2).

from __future__ import annotations
from typing import Optional

from .enums import UserRole
from .errors import ValidationError


## @brief Базовый класс пользователя
#  @details Содержит общие поля и поведение всех пользователей системы.
class Person:
    ## @brief Конструктор
    #  @param id Уникальный идентификатор
    #  @param fio ФИО
    #  @param email Электронная почта
    #  @param phone Телефон
    #  @param role Роль пользователя (по умолчанию не задана)
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 role: Optional[UserRole] = None) -> None:
        self._id = id                ##< Уникальный идентификатор
        self._fio = fio              ##< ФИО
        self._email = email          ##< Электронная почта
        self._phone = phone          ##< Телефон
        self._role = role            ##< Роль пользователя

    ## @brief Идентификатор пользователя
    @property
    def id(self) -> int:
        return self._id

    ## @brief ФИО пользователя
    @property
    def fio(self) -> str:
        return self._fio

    ## @brief Электронная почта
    @property
    def email(self) -> str:
        return self._email

    ## @brief Телефон
    @property
    def phone(self) -> str:
        return self._phone

    ## @brief Роль пользователя
    @property
    def role(self) -> Optional[UserRole]:
        return self._role

    ## @brief Может ли пользователь управлять заявками и выдачами
    @property
    def can_manage(self) -> bool:
        return False

    ## @brief Получить ФИО (совместимо с версией 1.0)
    #  @return ФИО пользователя
    def get_fio(self) -> str:
        return self._fio

    ## @brief Получить email (совместимо с версией 1.0)
    #  @return Электронная почта
    def get_email(self) -> str:
        return self._email

    ## @brief Изменить email
    #  @param email Новый адрес электронной почты
    #  @return True, если адрес корректен и сохранён
    def set_email(self, email: str) -> bool:
        if not email or "@" not in email:
            return False
        self._email = email
        return True

    ## @brief Строковое представление
    #  @return Строка с ФИО
    def __str__(self) -> str:
        return f"{type(self).__name__}({self._fio})"


## @brief Студент учебного заведения
class Student(Person):
    ## @brief Конструктор
    #  @param id Идентификатор
    #  @param fio ФИО
    #  @param email Электронная почта
    #  @param phone Телефон
    #  @param student_id Номер студенческого билета
    #  @param group Учебная группа
    #  @param faculty Факультет
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 student_id: str, group: str, faculty: str) -> None:
        super().__init__(id, fio, email, phone, UserRole.STUDENT)
        self._student_id = student_id  ##< Номер студенческого билета
        self._group = group            ##< Учебная группа
        self._faculty = faculty        ##< Факультет

    ## @brief Учебная группа
    @property
    def group(self) -> str:
        return self._group

    ## @brief Номер студенческого билета
    @property
    def student_id(self) -> str:
        return self._student_id

    ## @brief Факультет
    @property
    def faculty(self) -> str:
        return self._faculty

    ## @brief Получить группу (совместимо с версией 1.0)
    #  @return Название группы
    def get_group(self) -> str:
        return self._group


## @brief Преподаватель
class Teacher(Person):
    ## @brief Конструктор
    #  @param id Идентификатор
    #  @param fio ФИО
    #  @param email Электронная почта
    #  @param phone Телефон
    #  @param department Кафедра
    #  @param position Должность
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 department: str, position: str) -> None:
        super().__init__(id, fio, email, phone, UserRole.TEACHER)
        self._department = department  ##< Кафедра
        self._position = position      ##< Должность

    ## @brief Кафедра
    @property
    def department(self) -> str:
        return self._department

    ## @brief Должность
    @property
    def position(self) -> str:
        return self._position

    ## @brief Получить кафедру
    #  @return Название кафедры
    def get_department(self) -> str:
        return self._department


## @brief Сотрудник сервиса (администратор или техник)
#  @details Роль задаётся перечислением @c UserRole, поэтому отдельные
#  классы Administrator и Technician не требуются.
class Employee(Person):
    ## @brief Конструктор
    #  @param id Идентификатор
    #  @param fio ФИО
    #  @param email Электронная почта
    #  @param phone Телефон
    #  @param employee_id Табельный номер
    #  @param role Роль сотрудника: ADMINISTRATOR или TECHNICIAN
    #  @throw ValidationError Если роль не является ролью сотрудника
    def __init__(self, id: int, fio: str, email: str, phone: str,
                 employee_id: str, role: UserRole = UserRole.ADMINISTRATOR) -> None:
        if role not in (UserRole.ADMINISTRATOR, UserRole.TECHNICIAN):
            raise ValidationError(f"Роль «{role}» не является ролью сотрудника")
        super().__init__(id, fio, email, phone, role)
        self._employee_id = employee_id  ##< Табельный номер

    ## @brief Может ли сотрудник управлять заявками и выдачами
    @property
    def can_manage(self) -> bool:
        return True

    ## @brief Получить табельный номер
    #  @return Табельный номер
    def get_employee_id(self) -> str:
        return self._employee_id
