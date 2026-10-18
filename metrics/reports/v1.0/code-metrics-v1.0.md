# Метрики кода проекта «ArendaTech»

## Сводка

| Показатель | Значение |
|---|---|
| Модулей | 5 |
| Классов | 13 |
| Методов классов | 35 |
| Функций модулей | 1 |
| Строк исходного кода (SLOC) | 435 |
| Строк исполняемого кода | 105 |
| Суммарная цикломатическая сложность | 59 |
| Средний индекс сопровождаемости | 52.2 |
| Нарушений правил | 1 |

## Метрики по модулям

| Модуль | SLOC | EL | CC | Coupling | DIT | MI | Зона |
|---|---|---|---|---|---|---|---|
| `metrics/snapshots/v1_0/src/__init__.py` | 0 | 0 | 1 | 0 | 1 | 99.9 | green |
| `metrics/snapshots/v1_0/src/description.py` | 30 | 0 | 1 | 0 | 1 | 67.6 | green |
| `metrics/snapshots/v1_0/src/domain.py` | 293 | 69 | 45 | 2 | 3 | 13.6 | yellow |
| `metrics/snapshots/v1_0/src/main.py` | 39 | 17 | 2 | 4 | 1 | 44.5 | green |
| `metrics/snapshots/v1_0/src/service.py` | 73 | 19 | 10 | 4 | 1 | 35.5 | green |

## Наиболее сложные методы (топ-10 по CC)

| Сущность | Файл:строка | CC | MI | Coupling |
|---|---|---|---|---|
| `Person.set_email` | metrics/snapshots/v1_0/src/domain.py:48 | 3 | 69.5 | 0 |
| `RentalService.validate_dates` | metrics/snapshots/v1_0/src/service.py:70 | 3 | 71.9 | 0 |
| `RentalService.return_equipment` | metrics/snapshots/v1_0/src/service.py:58 | 2 | 65.2 | 2 |
| `Person.__init__` | metrics/snapshots/v1_0/src/domain.py:34 | 1 | 68.9 | 0 |
| `Person.get_fio` | metrics/snapshots/v1_0/src/domain.py:42 | 1 | 82.0 | 0 |
| `Person.get_email` | metrics/snapshots/v1_0/src/domain.py:54 | 1 | 82.0 | 0 |
| `Person.__str__` | metrics/snapshots/v1_0/src/domain.py:59 | 1 | 82.6 | 0 |
| `Student.__init__` | metrics/snapshots/v1_0/src/domain.py:74 | 1 | 65.7 | 0 |
| `Student.get_group` | metrics/snapshots/v1_0/src/domain.py:83 | 1 | 82.0 | 0 |
| `Teacher.__init__` | metrics/snapshots/v1_0/src/domain.py:96 | 1 | 68.0 | 0 |

## Нарушения пороговых правил

| Правило | Уровень | Сущность | Значение | Порог |
|---|---|---|---|---|
| CA1505 (Код трудно сопровождать) | warning | `src.domain` metrics/snapshots/v1_0/src/domain.py:1 | 13.65 | 20 |
