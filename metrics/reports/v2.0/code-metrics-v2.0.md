# Метрики кода проекта «ArendaTech»

## Сводка

| Показатель | Значение |
|---|---|
| Модулей | 29 |
| Классов | 46 |
| Методов классов | 163 |
| Функций модулей | 31 |
| Строк исходного кода (SLOC) | 2655 |
| Строк исполняемого кода | 679 |
| Суммарная цикломатическая сложность | 390 |
| Средний индекс сопровождаемости | 36.8 |
| Нарушений правил | 0 |

## Метрики по модулям

| Модуль | SLOC | EL | CC | Coupling | DIT | MI | Зона |
|---|---|---|---|---|---|---|---|
| `src/__init__.py` | 0 | 0 | 1 | 0 | 1 | 99.9 | green |
| `src/cli.py` | 105 | 40 | 8 | 3 | 1 | 30.3 | green |
| `src/demo.py` | 111 | 50 | 11 | 8 | 1 | 28.9 | green |
| `src/description.py` | 88 | 0 | 1 | 0 | 1 | 57.4 | green |
| `src/domain/__init__.py` | 58 | 9 | 1 | 0 | 1 | 41.4 | green |
| `src/domain/enums.py` | 70 | 20 | 6 | 1 | 2 | 40.0 | green |
| `src/domain/equipment.py` | 166 | 37 | 28 | 2 | 1 | 23.7 | green |
| `src/domain/errors.py` | 33 | 0 | 6 | 1 | 3 | 51.1 | green |
| `src/domain/fine.py` | 61 | 16 | 10 | 2 | 1 | 38.9 | green |
| `src/domain/issue.py` | 86 | 25 | 13 | 3 | 1 | 33.6 | green |
| `src/domain/notification.py` | 54 | 12 | 8 | 0 | 1 | 41.2 | green |
| `src/domain/people.py` | 195 | 42 | 31 | 3 | 2 | 21.0 | green |
| `src/domain/request.py` | 109 | 30 | 17 | 5 | 1 | 29.5 | green |
| `src/fines.py` | 140 | 34 | 24 | 8 | 2 | 25.6 | green |
| `src/issues.py` | 121 | 45 | 15 | 15 | 1 | 27.9 | green |
| `src/main.py` | 34 | 8 | 4 | 0 | 1 | 47.7 | green |
| `src/notifications.py` | 63 | 16 | 14 | 2 | 1 | 36.6 | green |
| `src/permissions.py` | 25 | 6 | 4 | 2 | 1 | 52.6 | green |
| `src/pricing.py` | 161 | 44 | 27 | 8 | 2 | 23.3 | green |
| `src/registry.py` | 107 | 27 | 20 | 6 | 1 | 29.0 | green |
| `src/reports.py` | 122 | 40 | 23 | 5 | 1 | 26.6 | green |
| `src/repository.py` | 84 | 18 | 16 | 3 | 2 | 33.5 | green |
| `src/requests.py` | 135 | 46 | 23 | 8 | 1 | 25.6 | green |
| `src/serialization/__init__.py` | 44 | 5 | 1 | 0 | 1 | 45.2 | green |
| `src/serialization/equipment.py` | 46 | 9 | 3 | 4 | 1 | 41.4 | green |
| `src/serialization/persons.py` | 99 | 25 | 16 | 4 | 1 | 29.9 | green |
| `src/serialization/rental.py` | 120 | 20 | 17 | 3 | 1 | 27.1 | green |
| `src/serialization/state.py` | 67 | 21 | 17 | 5 | 1 | 34.0 | green |
| `src/service.py` | 151 | 34 | 25 | 16 | 1 | 23.8 | green |

## Наиболее сложные методы (топ-10 по CC)

| Сущность | Файл:строка | CC | MI | Coupling |
|---|---|---|---|---|
| `RentalReport.statistics` | src/reports.py:60 | 9 | 51.7 | 1 |
| `state_from_dict` | src/serialization/state.py:52 | 8 | 51.9 | 1 |
| `state_to_dict` | src/serialization/state.py:35 | 7 | 53.8 | 1 |
| `RequestDesk._is_booked` | src/requests.py:127 | 6 | 60.4 | 2 |
| `run_demo` | src/demo.py:56 | 5 | 43.1 | 3 |
| `NotificationJournal.for_user` | src/notifications.py:45 | 5 | 72.1 | 1 |
| `person_to_dict` | src/serialization/persons.py:19 | 5 | 50.5 | 4 |
| `RentalService.__init__` | src/service.py:43 | 5 | 57.4 | 6 |
| `RentalService.notifications` | src/service.py:129 | 5 | 64.6 | 1 |
| `RequestDesk._validate_unit` | src/requests.py:111 | 4 | 60.3 | 2 |

## Нарушения пороговых правил

Нарушений не обнаружено.
