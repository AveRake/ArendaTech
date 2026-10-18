## @file issue.py
#  @brief Выдача техники и связанные с ней операции
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Выдача ссылается на заявку и хранит стоимость аренды, а также
#  результат возврата. Метод @c Issue.overdue_days используется правилом
#  начисления штрафа за просрочку (см. @ref fines.py).

from __future__ import annotations
from datetime import date
from typing import Optional

from .enums import ReturnCondition
from .errors import ValidationError
from .request import Request


## @brief Выдача техники по заявке
class Issue:
    ## @brief Конструктор
    #  @param id Идентификатор выдачи
    #  @param request Заявка
    #  @param issue_date Дата выдачи
    #  @param cost Стоимость аренды
    def __init__(self, id: int, request: Request, issue_date: date,
                 cost: float = 0.0) -> None:
        self._id = id                ##< Идентификатор выдачи
        self._request = request      ##< Заявка
        self._issue_date = issue_date  ##< Дата выдачи
        self._cost = cost            ##< Стоимость аренды
        self._return_date: Optional[date] = None  ##< Дата возврата
        self._condition: Optional[ReturnCondition] = None  ##< Состояние при возврате

    ## @brief Идентификатор выдачи
    @property
    def id(self) -> int:
        return self._id

    ## @brief Заявка
    @property
    def request(self) -> Request:
        return self._request

    ## @brief Дата выдачи
    @property
    def issue_date(self) -> date:
        return self._issue_date

    ## @brief Стоимость аренды
    @property
    def cost(self) -> float:
        return self._cost

    ## @brief Дата возврата
    @property
    def return_date(self) -> Optional[date]:
        return self._return_date

    ## @brief Состояние техники при возврате
    @property
    def condition(self) -> Optional[ReturnCondition]:
        return self._condition

    ## @brief Открыта ли выдача
    @property
    def is_open(self) -> bool:
        return self._return_date is None

    ## @brief Закрыть выдачу (оформить возврат)
    #  @param return_date Дата возврата
    #  @param condition Состояние техники
    #  @throw ValidationError Если возврат раньше выдачи
    def close(self, return_date: date, condition: ReturnCondition) -> None:
        if return_date < self._issue_date:
            raise ValidationError("Дата возврата не может быть раньше даты выдачи")
        self._return_date = return_date
        self._condition = condition

    ## @brief Количество суток просрочки на дату возврата
    #  @param return_date Фактическая дата возврата
    #  @return Число суток просрочки (0, если просрочки нет)
    def overdue_days(self, return_date: date) -> int:
        late = (return_date - self._request.end_date).days
        return max(0, late)
