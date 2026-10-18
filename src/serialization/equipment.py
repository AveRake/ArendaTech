## @file equipment.py
#  @brief Сериализация единиц техники «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0

from __future__ import annotations
from typing import Any, Dict

from ..domain import Category, EquipmentModel, EquipmentUnit, UnitStatus


def unit_to_dict(unit: EquipmentUnit) -> Dict[str, Any]:
    ## @brief Преобразовать единицу техники в словарь
    #  @param unit Единица техники
    #  @return Словарь с полями единицы
    model = unit.model
    return {
        "id": unit.id,
        "inventory_number": unit.inventory_number,
        "status": unit.status.value,
        "model": {
            "id": model.id,
            "name": model.name,
            "category": model.category.name,
            "damage_coefficient": model.category.damage_coefficient,
            "characteristics": model.characteristics,
            "daily_rate": model.daily_rate,
            "replacement_cost": model.replacement_cost,
        },
    }


def unit_from_dict(data: Dict[str, Any]) -> EquipmentUnit:
    ## @brief Восстановить единицу техники
    #  @param data Словарь полей
    #  @return Единица техники
    model_data = data["model"]
    category = Category(0, model_data["category"],
                        model_data.get("damage_coefficient", 0.1))
    model = EquipmentModel(model_data.get("id", 0), model_data["name"], category,
                           model_data.get("characteristics", ""),
                           model_data["daily_rate"],
                           model_data.get("replacement_cost", 0.0))
    return EquipmentUnit(data["id"], data["inventory_number"], model,
                         UnitStatus(data.get("status", UnitStatus.AVAILABLE.value)))
