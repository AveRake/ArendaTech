# Метрики кода проекта «ArendaTech»

## Сводка

| Показатель | Значение |
|---|---|
| Модулей | 5 |
| Классов | 13 |
| Методов классов | 87 |
| Функций модулей | 1 |
| Строк исходного кода (SLOC) | 740 |
| Строк исполняемого кода | 373 |
| Суммарная цикломатическая сложность | 185 |
| Средний индекс сопровождаемости | 42.1 |
| Нарушений правил | 6 |

## Метрики по модулям

| Модуль | SLOC | EL | CC | Coupling | DIT | MI | Зона |
|---|---|---|---|---|---|---|---|
| `metrics/snapshots/v2_0_raw/src/__init__.py` | 0 | 0 | 1 | 0 | 1 | 99.9 | green |
| `metrics/snapshots/v2_0_raw/src/description.py` | 30 | 0 | 1 | 0 | 1 | 67.6 | green |
| `metrics/snapshots/v2_0_raw/src/domain.py` | 310 | 127 | 85 | 2 | 3 | 5.8 | red |
| `metrics/snapshots/v2_0_raw/src/main.py` | 77 | 39 | 6 | 8 | 1 | 34.1 | green |
| `metrics/snapshots/v2_0_raw/src/service.py` | 323 | 207 | 92 | 7 | 1 | 3.1 | red |

## Наиболее сложные методы (топ-10 по CC)

| Сущность | Файл:строка | CC | MI | Coupling |
|---|---|---|---|---|
| `RentalService.return_equipment` | metrics/snapshots/v2_0_raw/src/service.py:166 | 16 | 35.7 | 2 |
| `RentalService.create_request` | metrics/snapshots/v2_0_raw/src/service.py:82 | 11 | 46.9 | 3 |
| `RentalService.build_report` | metrics/snapshots/v2_0_raw/src/service.py:223 | 11 | 42.1 | 0 |
| `RentalService.estimate_cost` | metrics/snapshots/v2_0_raw/src/service.py:126 | 8 | 51.7 | 2 |
| `RentalService.load_state` | metrics/snapshots/v2_0_raw/src/service.py:300 | 8 | 46.3 | 4 |
| `RentalService.get_notifications` | metrics/snapshots/v2_0_raw/src/service.py:52 | 6 | 59.2 | 1 |
| `RentalService.issue_equipment` | metrics/snapshots/v2_0_raw/src/service.py:145 | 6 | 50.0 | 4 |
| `main` | metrics/snapshots/v2_0_raw/src/main.py:20 | 5 | 38.0 | 8 |
| `RentalService.validate_dates` | metrics/snapshots/v2_0_raw/src/service.py:70 | 5 | 59.1 | 0 |
| `RentalService.save_state` | metrics/snapshots/v2_0_raw/src/service.py:263 | 5 | 43.3 | 0 |

## Нарушения пороговых правил

| Правило | Уровень | Сущность | Значение | Порог |
|---|---|---|---|---|
| CA1505 (Код трудно сопровождать) | warning | `src.domain` metrics/snapshots/v2_0_raw/src/domain.py:1 | 5.82 | 20 |
| CA1505 (Код трудно сопровождать) | warning | `src.service` metrics/snapshots/v2_0_raw/src/service.py:1 | 3.12 | 20 |
| CA1505 (Код трудно сопровождать) | warning | `RentalService` metrics/snapshots/v2_0_raw/src/service.py:28 | 4.20 | 20 |
| CA1502 (Избыточная сложность) | error | `RentalService.create_request` metrics/snapshots/v2_0_raw/src/service.py:82 | 11.00 | 10 |
| CA1502 (Избыточная сложность) | error | `RentalService.return_equipment` metrics/snapshots/v2_0_raw/src/service.py:166 | 16.00 | 10 |
| CA1502 (Избыточная сложность) | error | `RentalService.build_report` metrics/snapshots/v2_0_raw/src/service.py:223 | 11.00 | 10 |
