## @file request.py
#  @brief Заявка на аренду техники
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Заявка хранит даты как @c datetime.date и проверяет допустимость
#  переходов статуса (правило @c Request.transition). В версии 1.0 статус
#  был строкой, а переходы не проверялись.

from __future__ import annotations
from datetime import date
from typing import Dict, List, Sequence, Tuple

from .enums import RequestStatus
from .equipment import EquipmentUnit
from .errors import InvalidTransition, ValidationError
from .people import Person

#: Допустимые переходы статусов заявки.
ALLOWED_TRANSITIONS: Dict[RequestStatus, Tuple[RequestStatus, ...]] = {
    RequestStatus.PENDING: (RequestStatus.APPROVED, RequestStatus.REJECTED),
    RequestStatus.APPROVED: (RequestStatus.ISSUED,),
    RequestStatus.ISSUED: (RequestStatus.CLOSED,),
    RequestStatus.REJECTED: (),
    RequestStatus.CLOSED: (),
}


## @brief Заявка на аренду техники
class Request:
    ## @brief Конструктор
    #  @param id Идентификатор заявки
    #  @param user Пользователь-заявитель
    #  @param units Единицы техники
    #  @param start_date Дата начала аренды
    #  @param end_date Дата окончания аренды
    #  @param status Начальный статус заявки
    #  @throw ValidationError Если период аренды некорректен
    def __init__(self, id: int, user: Person, units: Sequence[EquipmentUnit],
                 start_date: date, end_date: date,
                 status: RequestStatus = RequestStatus.PENDING) -> None:
        if not units:
            raise ValidationError("Заявка должна содержать хотя бы одну единицу техники")
        if end_date <= start_date:
            raise ValidationError("Дата окончания должна быть позже даты начала")
        self._id = id                ##< Идентификатор заявки
        self._user = user            ##< Заявитель
        self._units = list(units)    ##< Единицы техники
        self._start_date = start_date  ##< Дата начала аренды
        self._end_date = end_date      ##< Дата окончания аренды
        self._status = status          ##< Статус заявки

    ## @brief Идентификатор заявки
    @property
    def id(self) -> int:
        return self._id

    ## @brief Заявитель
    @property
    def user(self) -> Person:
        return self._user

    ## @brief Единицы техники
    @property
    def units(self) -> List[EquipmentUnit]:
        return list(self._units)

    ## @brief Дата начала аренды
    @property
    def start_date(self) -> date:
        return self._start_date

    ## @brief Дата окончания аренды
    @property
    def end_date(self) -> date:
        return self._end_date

    ## @brief Статус заявки
    @property
    def status(self) -> RequestStatus:
        return self._status

    ## @brief Количество суток аренды
    @property
    def days(self) -> int:
        return (self._end_date - self._start_date).days

    ## @brief Пересекается ли период заявки с заданным
    #  @param start_date Начало проверяемого периода
    #  @param end_date Окончание проверяемого периода
    #  @return True, если периоды пересекаются
    def overlaps(self, start_date: date, end_date: date) -> bool:
        return self._start_date <= end_date and start_date <= self._end_date

    ## @brief Перевести заявку в новый статус
    #  @param target Целевой статус
    #  @throw InvalidTransition Если переход недопустим
    def transition(self, target: RequestStatus) -> None:
        if target not in ALLOWED_TRANSITIONS[self._status]:
            raise InvalidTransition(
                f"Недопустимый переход заявки №{self._id}: "
                f"«{self._status.value}» → «{target.value}»")
        self._status = target

    ## @brief Получить статус (совместимо с версией 1.0)
    #  @return Текст статуса
    def get_status(self) -> str:
        return self._status.value
