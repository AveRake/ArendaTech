## @file notifications.py
#  @brief Журнал уведомлений пользователей «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details В версии 1.0 уведомления формировались внутри сервиса
#  (счётчик @c _notification_seq и список @c _notifications увеличивали
#  связанность @c RentalService). В версии 2.0 уведомления вынесены в
#  самостоятельный журнал, который можно заменить другой реализацией
#  (например, отправкой писем) без изменения бизнес-логики.

from __future__ import annotations
from datetime import date
from typing import List, Optional

from .domain import Notification, Person


## @brief Журнал уведомлений в памяти
class NotificationJournal:
    ## @brief Конструктор
    def __init__(self) -> None:
        self._items: List[Notification] = []
        self._sequence = 0

    ## @brief Зарегистрировать уведомление
    #  @param user Получатель
    #  @param message Текст уведомления
    #  @param kind Тип уведомления (request, price, issue, fine, return)
    #  @param day Дата формирования (по умолчанию — сегодня)
    #  @return Созданное уведомление
    def register(self, user: Person, message: str, kind: str = "info",
                 day: Optional[date] = None) -> Notification:
        self._sequence += 1
        notification = Notification(self._sequence, user.id, message,
                                    day or date.today(), kind)
        self._items.append(notification)
        return notification

    ## @brief Уведомления пользователя
    #  @param user_id Идентификатор получателя
    #  @param kind Тип уведомления (None — все типы)
    #  @return Список уведомлений
    def for_user(self, user_id: int, kind: Optional[str] = None) -> List[Notification]:
        return [item for item in self._items
                if item.user_id == user_id and (kind is None or item.kind == kind)]

    ## @brief Все уведомления журнала
    #  @return Список уведомлений
    def all(self) -> List[Notification]:
        return list(self._items)

    ## @brief Восстановить журнал из сохранённого состояния
    #  @param items Ранее сохранённые уведомления
    def restore(self, items: List[Notification]) -> None:
        self._items = list(items)
        self._sequence = max((item.id for item in self._items), default=0)

    ## @brief Очистить журнал
    def clear(self) -> None:
        self._items = []
        self._sequence = 0
