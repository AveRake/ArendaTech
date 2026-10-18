## @file repository.py
#  @brief Хранилище состояния сервиса «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details В версии 1.0 методы @c save_state и @c load_state находились в
#  классе @c RentalService и работали с файловой системой напрямую
#  (связанность сервиса росла, восстановление связей между объектами было
#  реализовано с ошибкой: все выдачи ссылались на первую заявку).
#  В версии 2.0 хранилище вынесено в отдельный слой с интерфейсом
#  @c RentalRepository; сервис зависит только от интерфейса.

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Protocol

from .serialization import ServiceState, state_from_dict, state_to_dict


## @brief Интерфейс хранилища состояния
class RentalRepository(Protocol):
    ## @brief Сохранить состояние
    #  @param state Состояние сервиса
    def save(self, state: ServiceState) -> None:
        ...

    ## @brief Загрузить состояние
    #  @return Ранее сохранённое состояние
    def load(self) -> ServiceState:
        ...


## @brief Хранилище в оперативной памяти
class InMemoryRepository:
    ## @brief Конструктор
    def __init__(self) -> None:
        self._state: Optional[ServiceState] = None

    ## @brief Сохранить состояние
    #  @param state Состояние сервиса
    def save(self, state: ServiceState) -> None:
        self._state = state

    ## @brief Загрузить состояние
    #  @return Сохранённое состояние (пустое, если ничего не сохранено)
    def load(self) -> ServiceState:
        return self._state if self._state is not None else ServiceState()


## @brief Хранилище в JSON-файле
class JsonRepository:
    ## @brief Конструктор
    #  @param path Путь к файлу состояния
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    ## @brief Путь к файлу состояния
    @property
    def path(self) -> Path:
        return self._path

    ## @brief Сохранить состояние в файл
    #  @param state Состояние сервиса
    def save(self, state: ServiceState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = state_to_dict(state)
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    ## @brief Загрузить состояние из файла
    #  @return Состояние сервиса
    #  @throw FileNotFoundError Если файл состояния отсутствует
    def load(self) -> ServiceState:
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return state_from_dict(payload)


## @brief Создать хранилище по пути к файлу
#  @param path Путь к файлу состояния или None для хранилища в памяти
#  @return Хранилище состояния
def create_repository(path: Optional[str] = None) -> RentalRepository:
    return JsonRepository(path) if path else InMemoryRepository()
