## @file permissions.py
#  @brief Проверка прав пользователя «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Проверка вынесена из сервиса в отдельную функцию, чтобы
#  сценарии работы с заявками (@ref requests.py) и с выдачами
#  (@ref issues.py) не дублировали код и не зависели друг от друга.

from __future__ import annotations

from .domain import PermissionDenied, Person


## @brief Проверить, что пользователь является сотрудником сервиса
#  @param user Проверяемый пользователь
#  @throw PermissionDenied Если пользователь не имеет прав сотрудника
def require_staff(user: Person) -> None:
    if user.can_manage:
        return
    role = user.role.value if user.role else "гость"
    raise PermissionDenied(
        f"Операция доступна только сотруднику сервиса, "
        f"а «{user.fio}» — {role}")
