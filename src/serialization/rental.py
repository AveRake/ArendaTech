## @file rental.py
#  @brief Сериализация заявок, выдач, штрафов и уведомлений
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Заявка хранит ссылки на единицы техники по инвентарным номерам,
#  выдача — идентификатор заявки. При загрузке ссылки восстанавливаются
#  через индексы, поэтому ссылочная целостность сохраняется.

from __future__ import annotations
from datetime import date
from typing import Any, Dict

from ..domain import (
    EquipmentUnit, Fine, FineReason, Issue, Notification, Request, RequestStatus,
    ReturnCondition,
)
from .persons import person_from_dict, person_to_dict


def request_to_dict(request: Request,
                    unit_index: Dict[str, EquipmentUnit]) -> Dict[str, Any]:
    ## @brief Преобразовать заявку в словарь
    #  @param request Заявка
    #  @param unit_index Индекс единиц техники по инвентарному номеру
    #  @return Словарь с полями заявки
    return {
        "id": request.id,
        "user": person_to_dict(request.user),
        "units": [unit.inventory_number for unit in request.units
                  if unit.inventory_number in unit_index],
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "status": request.status.value,
    }


def request_from_dict(data: Dict[str, Any],
                      unit_index: Dict[str, EquipmentUnit]) -> Request:
    ## @brief Восстановить заявку
    #  @param data Словарь полей
    #  @param unit_index Индекс единиц техники по инвентарному номеру
    #  @return Заявка
    units = [unit_index[number] for number in data["units"] if number in unit_index]
    return Request(
        data["id"], person_from_dict(data["user"]), units,
        date.fromisoformat(data["start_date"]), date.fromisoformat(data["end_date"]),
        RequestStatus(data.get("status", RequestStatus.PENDING.value)),
    )


def issue_to_dict(issue: Issue) -> Dict[str, Any]:
    ## @brief Преобразовать выдачу в словарь
    #  @param issue Выдача
    #  @return Словарь с полями выдачи
    return {
        "id": issue.id,
        "request_id": issue.request.id,
        "issue_date": issue.issue_date.isoformat(),
        "cost": issue.cost,
        "return_date": issue.return_date.isoformat() if issue.return_date else None,
        "condition": issue.condition.value if issue.condition else None,
    }


def issue_from_dict(data: Dict[str, Any], request_index: Dict[int, Request]) -> Issue:
    ## @brief Восстановить выдачу
    #  @param data Словарь полей
    #  @param request_index Индекс заявок по идентификатору
    #  @return Выдача
    issue = Issue(data["id"], request_index[data["request_id"]],
                  date.fromisoformat(data["issue_date"]), data.get("cost", 0.0))
    if data.get("return_date"):
        issue.close(date.fromisoformat(data["return_date"]),
                    ReturnCondition(data["condition"]))
    return issue


def fine_to_dict(fine: Fine) -> Dict[str, Any]:
    ## @brief Преобразовать штраф в словарь
    #  @param fine Штраф
    #  @return Словарь с полями штрафа
    return {
        "id": fine.id,
        "reason": fine.reason.value,
        "amount": fine.amount,
        "paid": fine.is_paid,
    }


def fine_from_dict(data: Dict[str, Any]) -> Fine:
    ## @brief Восстановить штраф
    #  @param data Словарь полей
    #  @return Штраф
    fine = Fine(data["id"], FineReason(data["reason"]), data["amount"])
    if data.get("paid"):
        fine.pay()
    return fine


def notification_to_dict(item: Notification) -> Dict[str, Any]:
    ## @brief Преобразовать уведомление в словарь
    #  @param item Уведомление
    #  @return Словарь с полями уведомления
    return {
        "id": item.id,
        "user_id": item.user_id,
        "message": item.message,
        "date": item.date.isoformat(),
        "kind": item.kind,
    }


def notification_from_dict(data: Dict[str, Any]) -> Notification:
    ## @brief Восстановить уведомление
    #  @param data Словарь полей
    #  @return Уведомление
    return Notification(data["id"], data["user_id"], data["message"],
                        date.fromisoformat(data["date"]), data.get("kind", "info"))
