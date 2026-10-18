## @file fine.py
#  @brief Штраф за нарушение условий аренды
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0

from __future__ import annotations
from typing import Optional

from .enums import FineReason
from .issue import Issue


## @brief Штраф за нарушение условий аренды
class Fine:
    ## @brief Конструктор
    #  @param id Идентификатор штрафа
    #  @param reason Причина начисления
    #  @param amount Сумма штрафа
    #  @param issue Выдача, по которой начислен штраф
    def __init__(self, id: int, reason: FineReason, amount: float,
                 issue: Optional[Issue] = None) -> None:
        self._id = id            ##< Идентификатор штрафа
        self._reason = reason    ##< Причина начисления
        self._amount = amount    ##< Сумма штрафа
        self._issue = issue      ##< Связанная выдача
        self._paid = False       ##< Признак оплаты

    ## @brief Идентификатор штрафа
    @property
    def id(self) -> int:
        return self._id

    ## @brief Причина начисления
    @property
    def reason(self) -> FineReason:
        return self._reason

    ## @brief Сумма штрафа
    @property
    def amount(self) -> float:
        return self._amount

    ## @brief Связанная выдача
    @property
    def issue(self) -> Optional[Issue]:
        return self._issue

    ## @brief Оплачен ли штраф
    @property
    def is_paid(self) -> bool:
        return self._paid

    ## @brief Оплатить штраф
    def pay(self) -> None:
        self._paid = True

    ## @brief Получить сумму штрафа (совместимо с версией 1.0)
    #  @return Сумма штрафа
    def get_amount(self) -> float:
        return self._amount
