## @file service.py
#  @brief Сервисный слой приложения «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2025-01-01
#  @version 1.0
#
#  @par Использует файл:
#  - @ref domain.py
#
#  @par Содержит классы:
#  - @ref RentalService

from typing import List
from .domain import (
    Student, Teacher, EquipmentModel, EquipmentUnit,
    Request, Issue, Fine, Notification
)


## @brief Сервис аренды техники
#  @details Содержит бизнес-логику: создание заявок, выдачу, возврат,
#  начисление штрафов и уведомления.
class RentalService:
    ## @brief Конструктор
    def __init__(self):
        self._requests: List[Request] = []  ##< Список заявок
        self._issues: List[Issue] = []      ##< Список выдач
        self._fines: List[Fine] = []        ##< Список штрафов

    ## @brief Создать заявку на аренду
    #  @param user Пользователь
    #  @param units Единицы техники
    #  @param start_date Дата начала
    #  @param end_date Дата окончания
    #  @return Созданная заявка
    def create_request(self, user, units: List[EquipmentUnit],
                       start_date: str, end_date: str) -> Request:
        req = Request(len(self._requests) + 1, user, units,
                      start_date, end_date, "На рассмотрении")
        self._requests.append(req)
        return req

    ## @brief Одобрить заявку и выдать технику
    #  @param request Заявка
    #  @param issue_date Дата выдачи
    #  @return Созданная запись выдачи
    def issue_equipment(self, request: Request, issue_date: str) -> Issue:
        request.approve()
        issue = Issue(len(self._issues) + 1, request, issue_date)
        self._issues.append(issue)
        return issue

    ## @brief Вернуть технику
    #  @param issue Запись выдачи
    #  @param return_date Дата возврата
    #  @param condition Состояние
    #  @param fine_amount Сумма штрафа (0, если нет)
    def return_equipment(self, issue: Issue, return_date: str,
                         condition: str, fine_amount: float = 0.0) -> None:
        issue.close(return_date, condition)
        if fine_amount > 0:
            fine = Fine(len(self._fines) + 1, "Повреждение", fine_amount)
            self._fines.append(fine)

    ## @brief Проверить корректность дат на аренды
    #  @details Дата начала должна быть строго раньше даты окончания.
    #  @param start_date Дата начала аренды
    #  @param end_date Дата окончания аренды
    #  @return True, если даты корректны, иначе False
    def validate_dates(self, start_date: str, end_date: str) -> bool:
        if not start_date or not end_date:
            return False
        return start_date < end_date