## @file service.py
#  @brief Сервисный слой приложения «АрендаТех» (версия 2.0)
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @par Использует файл:
#  - @ref domain.py
#
#  @par Содержит классы:
#  - @ref RentalService

from __future__ import annotations
import json
from datetime import date
from typing import Dict, List, Optional

from .domain import (
    Administrator, Category, EquipmentModel, EquipmentUnit, Fine, Issue,
    Notification, Person, Request, Student, Teacher, Technician,
    STATUS_APPROVED, STATUS_CLOSED, STATUS_ISSUED, STATUS_PENDING,
    STATUS_REJECTED, CONDITION_DAMAGED, CONDITION_LOST, CONDITION_OK,
)

MAX_RENTAL_DAYS = 30


class RentalService:
    def __init__(self) -> None:
        self._requests: List[Request] = []
        self._issues: List[Issue] = []
        self._fines: List[Fine] = []
        self._notifications: List[Notification] = []
        self._units: List[EquipmentUnit] = []
        self._notification_seq = 0

    def add_unit(self, unit: EquipmentUnit) -> None:
        self._units.append(unit)

    def get_units(self) -> List[EquipmentUnit]:
        return list(self._units)

    def get_requests(self) -> List[Request]:
        return list(self._requests)

    def get_issues(self) -> List[Issue]:
        return list(self._issues)

    def get_fines(self) -> List[Fine]:
        return list(self._fines)

    def get_notifications(self, user_id: Optional[int] = None,
                          kind: Optional[str] = None) -> List[Notification]:
        result = []
        for notification in self._notifications:
            if user_id is not None and notification.get_user_id() != user_id:
                continue
            if kind is not None and notification.get_kind() != kind:
                continue
            result.append(notification)
        return result

    def _notify(self, user: Person, message: str, kind: str = "info") -> Notification:
        self._notification_seq += 1
        notification = Notification(self._notification_seq, message,
                                    date.today().isoformat(), user.get_id(), kind)
        self._notifications.append(notification)
        return notification

    def validate_dates(self, start_date: str, end_date: str) -> bool:
        if not start_date or not end_date:
            return False
        try:
            first = date.fromisoformat(start_date)
            last = date.fromisoformat(end_date)
        except ValueError:
            return False
        if last <= first:
            return False
        return (last - first).days <= MAX_RENTAL_DAYS

    def create_request(self, user: Person, units: List[EquipmentUnit],
                       start_date: str, end_date: str) -> Request:
        if not units:
            raise ValueError("Заявка должна содержать хотя бы одну единицу техники")
        if not self.validate_dates(start_date, end_date):
            raise ValueError("Некорректный период аренды (1..30 суток)")
        for unit in units:
            if unit not in self._units:
                raise ValueError(f"Единица {unit.get_inventory_number()} не зарегистрирована")
            if not unit.is_available():
                raise ValueError(f"Единица {unit.get_inventory_number()} недоступна")
            for request in self._requests:
                if request.get_status() in (STATUS_REJECTED, STATUS_CLOSED):
                    continue
                for busy in request.get_units():
                    if busy is unit and request.period_overlaps(start_date, end_date):
                        raise ValueError(
                            f"Единица {unit.get_inventory_number()} занята в выбранный период")
        request = Request(len(self._requests) + 1, user, units, start_date, end_date)
        self._requests.append(request)
        self._notify(user, f"Заявка №{request.get_id()} создана", "request")
        cost = self.estimate_cost(user, units, request.days())
        self._notify(user, f"Предварительная стоимость аренды: {cost:.2f} руб.", "price")
        return request

    def approve_request(self, request: Request, employee: Person) -> None:
        if not isinstance(employee, Administrator):
            raise PermissionError("Заявку может одобрить только сотрудник (администратор или техник)")
        if request.get_status() != STATUS_PENDING:
            raise ValueError(f"Нельзя одобрить заявку в статусе «{request.get_status()}»")
        request.set_status(STATUS_APPROVED)
        self._notify(request.get_user(), f"Заявка №{request.get_id()} одобрена", "request")

    def reject_request(self, request: Request, employee: Person, reason: str = "") -> None:
        if not isinstance(employee, Administrator):
            raise PermissionError("Заявку может отклонить только сотрудник")
        if request.get_status() != STATUS_PENDING:
            raise ValueError(f"Нельзя отклонить заявку в статусе «{request.get_status()}»")
        request.reject()
        text = f"Заявка №{request.get_id()} отклонена"
        if reason:
            text = text + f": {reason}"
        self._notify(request.get_user(), text, "request")

    def estimate_cost(self, user: Person, units: List[EquipmentUnit], days: int) -> float:
        base = 0.0
        for unit in units:
            base += unit.get_model().get_daily_rate() * days
        role = user.get_role()
        if role == "student":
            base = base * 0.90
        elif role == "teacher":
            base = base * 0.95
        if days > 14:
            base = base * 0.90
        elif days > 7:
            base = base * 0.95
        if len(units) >= 3:
            base = base * 0.97
        if base < 0:
            base = 0.0
        return round(base, 2)

    def issue_equipment(self, request: Request, employee: Person,
                        issue_date: str) -> Issue:
        if not isinstance(employee, Administrator):
            raise PermissionError("Технику может выдать только сотрудник")
        if request.get_status() != STATUS_APPROVED:
            raise ValueError(f"Выдача возможна только для одобренной заявки, а не «{request.get_status()}»")
        for unit in request.get_units():
            if not unit.is_available():
                raise ValueError(f"Единица {unit.get_inventory_number()} недоступна")
        cost = self.estimate_cost(request.get_user(), request.get_units(), request.days())
        issue = Issue(len(self._issues) + 1, request, issue_date, cost)
        self._issues.append(issue)
        request.set_status(STATUS_ISSUED)
        for unit in request.get_units():
            unit.set_available(False)
            unit.set_status("Выдана")
        self._notify(request.get_user(),
                     f"Техника выдана по заявке №{request.get_id()}, стоимость {cost:.2f} руб.",
                     "issue")
        return issue

    def return_equipment(self, issue: Issue, return_date: str, condition: str) -> None:
        if not issue.is_open():
            raise ValueError("Эта выдача уже закрыта")
        request = issue.get_request()
        try:
            planned = date.fromisoformat(request.get_end_date())
            actual = date.fromisoformat(return_date)
        except ValueError as error:
            raise ValueError(f"Некорректная дата возврата: {error}") from error
        if actual < date.fromisoformat(issue.get_issue_date()):
            raise ValueError("Дата возврата раньше даты выдачи")
        fine_total = 0.0
        reasons: List[str] = []
        if actual > planned:
            overdue_days = (actual - planned).days
            penalty = 0.0
            for unit in request.get_units():
                penalty += unit.get_model().get_daily_rate() * 0.5 * overdue_days
            fine_total += penalty
            reasons.append(f"Просрочка {overdue_days} сут.")
        if condition == CONDITION_DAMAGED:
            damage = 0.0
            for unit in request.get_units():
                category = unit.get_model().get_category()
                if category in ("Проекторы", "Фототехника"):
                    damage += unit.get_model().get_daily_rate() * 0.20
                else:
                    damage += unit.get_model().get_daily_rate() * 0.10
            fine_total += damage
            reasons.append("Повреждение")
        elif condition == CONDITION_LOST:
            loss = 0.0
            for unit in request.get_units():
                loss += unit.get_model().get_daily_rate() * 10
            fine_total += loss
            reasons.append("Утеря")
        elif condition != CONDITION_OK:
            raise ValueError(f"Неизвестное состояние техники: «{condition}»")
        issue.close(return_date, condition)
        request.set_status(STATUS_CLOSED)
        for unit in request.get_units():
            unit.set_available(True)
            if condition == CONDITION_LOST:
                unit.set_status("Списана")
            elif condition == CONDITION_DAMAGED:
                unit.set_status("На ремонте")
            else:
                unit.set_status("Доступна")
        if fine_total > 0:
            fine = Fine(len(self._fines) + 1, ", ".join(reasons), round(fine_total, 2), issue)
            self._fines.append(fine)
            self._notify(request.get_user(),
                         f"Начислен штраф {fine.get_amount():.2f} руб. за: {fine.get_reason()}",
                         "fine")
        self._notify(request.get_user(),
                     f"Возврат по заявке №{request.get_id()} оформлен ({condition})", "return")

    def build_report(self) -> str:
        active = [issue for issue in self._issues if issue.is_open()]
        income = 0.0
        for issue in self._issues:
            income += issue.get_cost()
        fines_total = 0.0
        unpaid = 0.0
        for fine in self._fines:
            fines_total += fine.get_amount()
            if not fine.is_paid():
                unpaid += fine.get_amount()
        busy = 0
        free = 0
        by_category: Dict[str, int] = {}
        for unit in self._units:
            if unit.is_available():
                free += 1
            else:
                busy += 1
            category = unit.get_model().get_category()
            by_category[category] = by_category.get(category, 0) + 1
        lines = [
            "ОТЧЁТ СЕРВИСА «АРЕНДАТЕХ»",
            f"Единиц техники: {len(self._units)} (свободно {free}, занято {busy})",
            f"Заявок: {len(self._requests)}",
            f"Выдач: {len(self._issues)} (активных {len(active)})",
            f"Начисленный доход: {income:.2f} руб.",
            f"Штрафы: {fines_total:.2f} руб. (не оплачено {unpaid:.2f} руб.)",
        ]
        for category in sorted(by_category):
            lines.append(f"  {category}: {by_category[category]} ед.")
        if active:
            lines.append("Активные выдачи:")
            for issue in active:
                request = issue.get_request()
                lines.append(
                    f"  выдача №{issue.get_id()}, заявка №{request.get_id()}, "
                    f"{request.get_user().get_fio()}, до {request.get_end_date()}")
        return "\n".join(lines)

    def save_state(self, path: str) -> None:
        payload = {
            "requests": [
                {
                    "id": request.get_id(),
                    "user_id": request.get_user().get_id(),
                    "units": [unit.get_inventory_number() for unit in request.get_units()],
                    "start_date": request.get_start_date(),
                    "end_date": request.get_end_date(),
                    "status": request.get_status(),
                }
                for request in self._requests
            ],
            "issues": [
                {
                    "id": issue.get_id(),
                    "request_id": issue.get_request().get_id(),
                    "issue_date": issue.get_issue_date(),
                    "return_date": issue.get_return_date(),
                    "condition": issue.get_condition(),
                    "cost": issue.get_cost(),
                }
                for issue in self._issues
            ],
            "fines": [
                {
                    "id": fine.get_id(),
                    "reason": fine.get_reason(),
                    "amount": fine.get_amount(),
                    "paid": fine.is_paid(),
                }
                for fine in self._fines
            ],
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def load_state(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self._requests = []
        self._issues = []
        self._fines = []
        for record in payload.get("requests", []):
            user = Person(record["user_id"], "Пользователь", "user@example.com", "")
            units = [unit for unit in self._units
                     if unit.get_inventory_number() in record.get("units", [])]
            request = Request(record["id"], user, units, record["start_date"],
                              record["end_date"], record["status"])
            self._requests.append(request)
        for record in payload.get("issues", []):
            issue = Issue(record["id"], self._requests[0], record["issue_date"],
                          record.get("cost", 0.0))
            if record.get("return_date"):
                issue.close(record["return_date"], record.get("condition", ""))
            self._issues.append(issue)
        for record in payload.get("fines", []):
            fine = Fine(record["id"], record["reason"], record["amount"])
            if record.get("paid"):
                fine.pay()
            self._fines.append(fine)
