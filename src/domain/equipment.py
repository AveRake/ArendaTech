## @file equipment.py
#  @brief Модели и единицы техники «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @par Содержит классы:
#  - @c Category
#  - @c EquipmentModel
#  - @c EquipmentUnit
#
#  @details Категория теперь содержит коэффициент ущерба при повреждении,
#  а модель — стоимость возмещения при утере. Благодаря этому правила
#  начисления штрафов (см. @ref fines.py) стали табличными и не содержат
#  зашитых в код названий категорий.

from __future__ import annotations

from .enums import UnitStatus
from .errors import ValidationError


## @brief Категория техники
class Category:
    ## @brief Конструктор
    #  @param id Идентификатор категории
    #  @param name Название категории
    #  @param damage_coefficient Доля суточной ставки, взыскиваемая при повреждении
    def __init__(self, id: int, name: str, damage_coefficient: float = 0.10) -> None:
        self._id = id                              ##< Идентификатор категории
        self._name = name                          ##< Название категории
        self._damage_coefficient = damage_coefficient  ##< Коэффициент ущерба

    ## @brief Название категории
    @property
    def name(self) -> str:
        return self._name

    ## @brief Коэффициент ущерба при повреждении
    @property
    def damage_coefficient(self) -> float:
        return self._damage_coefficient

    ## @brief Получить название категории (совместимо с версией 1.0)
    #  @return Название категории
    def get_name(self) -> str:
        return self._name


## @brief Модель техники
class EquipmentModel:
    ## @brief Конструктор
    #  @param id Идентификатор модели
    #  @param name Название модели
    #  @param category Категория техники
    #  @param characteristics Характеристики
    #  @param daily_rate Стоимость аренды в сутки
    #  @param replacement_cost Стоимость возмещения при утере
    #  @throw ValidationError Если суточная ставка отрицательна
    def __init__(self, id: int, name: str, category: Category,
                 characteristics: str, daily_rate: float,
                 replacement_cost: float = 0.0) -> None:
        if daily_rate < 0:
            raise ValidationError("Стоимость аренды не может быть отрицательной")
        self._id = id                          ##< Идентификатор модели
        self._name = name                      ##< Название модели
        self._category = category              ##< Категория
        self._characteristics = characteristics  ##< Характеристики
        self._daily_rate = daily_rate          ##< Стоимость аренды в сутки
        self._replacement_cost = replacement_cost or daily_rate * 10  ##< Возмещение при утере

    ## @brief Идентификатор модели
    @property
    def id(self) -> int:
        return self._id

    ## @brief Название модели
    @property
    def name(self) -> str:
        return self._name

    ## @brief Категория техники
    @property
    def category(self) -> Category:
        return self._category

    ## @brief Характеристики модели
    @property
    def characteristics(self) -> str:
        return self._characteristics

    ## @brief Стоимость аренды в сутки
    @property
    def daily_rate(self) -> float:
        return self._daily_rate

    ## @brief Стоимость возмещения при утере
    @property
    def replacement_cost(self) -> float:
        return self._replacement_cost

    ## @brief Получить стоимость аренды (совместимо с версией 1.0)
    #  @return Стоимость в сутки
    def get_daily_rate(self) -> float:
        return self._daily_rate

    ## @brief Получить название модели (совместимо с версией 1.0)
    #  @return Название модели
    def get_name(self) -> str:
        return self._name


## @brief Единица техники (конкретный инвентарный объект)
class EquipmentUnit:
    ## @brief Конструктор
    #  @param id Идентификатор единицы
    #  @param inventory_number Инвентарный номер
    #  @param model Модель техники
    #  @param status Состояние единицы
    def __init__(self, id: int, inventory_number: str, model: EquipmentModel,
                 status: UnitStatus = UnitStatus.AVAILABLE) -> None:
        self._id = id                            ##< Идентификатор единицы
        self._inventory_number = inventory_number  ##< Инвентарный номер
        self._model = model                      ##< Модель техники
        self._status = status                    ##< Состояние единицы

    ## @brief Идентификатор единицы
    @property
    def id(self) -> int:
        return self._id

    ## @brief Модель техники
    @property
    def model(self) -> EquipmentModel:
        return self._model

    ## @brief Инвентарный номер
    @property
    def inventory_number(self) -> str:
        return self._inventory_number

    ## @brief Состояние единицы
    @property
    def status(self) -> UnitStatus:
        return self._status

    ## @brief Изменить состояние единицы
    #  @param status Новое состояние
    def set_status(self, status: UnitStatus) -> None:
        self._status = status

    ## @brief Доступна ли единица для выдачи
    #  @return True, если единица свободна
    @property
    def is_available(self) -> bool:
        return self._status is UnitStatus.AVAILABLE

    ## @brief Получить инвентарный номер (совместимо с версией 1.0)
    #  @return Инвентарный номер
    def get_inventory_number(self) -> str:
        return self._inventory_number

    ## @brief Получить модель (совместимо с версией 1.0)
    #  @return Модель техники
    def get_model(self) -> EquipmentModel:
        return self._model
