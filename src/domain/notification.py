## @file notification.py
#  @brief Уведомление пользователя
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Уведомление не зависит от пользователя-объекта: хранится только
#  идентификатор получателя, поэтому журнал уведомлений (@ref
#  notifications.py) не связан с иерархией пользователей.

from __future__ import annotations
from datetime import date


## @brief Уведомление пользователя
class Notification:
    ## @brief Конструктор
    #  @param id Идентификатор уведомления
    #  @param user_id Идентификатор получателя
    #  @param message Текст уведомления
    #  @param date Дата формирования
    #  @param kind Канал/тип уведомления
    def __init__(self, id: int, user_id: int, message: str, date: date,
                 kind: str = "info") -> None:
        self._id = id            ##< Идентификатор уведомления
        self._user_id = user_id  ##< Получатель
        self._message = message  ##< Текст уведомления
        self._date = date        ##< Дата формирования
        self._kind = kind        ##< Тип уведомления

    ## @brief Идентификатор уведомления
    @property
    def id(self) -> int:
        return self._id

    ## @brief Получатель
    @property
    def user_id(self) -> int:
        return self._user_id

    ## @brief Текст уведомления
    @property
    def message(self) -> str:
        return self._message

    ## @brief Дата формирования
    @property
    def date(self) -> date:
        return self._date

    ## @brief Тип уведомления
    @property
    def kind(self) -> str:
        return self._kind
