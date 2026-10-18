# Сравнение метрик кода

| Показатель | v1.0 (ЛР2) | v2.0 черновик | v2.0 итог |
|---|---|---|---|
| Модулей | 5 | 5 | 29 |
| Классов | 13 | 13 | 46 |
| Методов и функций | 36 | 88 | 194 |
| SLOC | 435 | 740 | 2655 |
| Строк исполняемого кода | 105 | 373 | 679 |
| Суммарная CC | 59 | 185 | 390 |
| Максимальная CC метода | 3 | 16 | 9 |
| Средняя CC метода | 1.14 | 1.9 | 1.62 |
| Методов со CC > 10 | 0 | 3 | 0 |
| Максимальная связанность класса | 4 | 7 | 16 |
| Максимальная глубина наследования | 3 | 3 | 3 |
| Средний MI модулей | 52.2 | 42.1 | 36.8 |
| Минимальный MI модуля | 13.7 | 3.1 | 21.0 |
| Средний MI методов | 74.5 | 74.6 | 73.4 |
| Минимальный MI метода | 52.2 | 35.7 | 43.1 |
| Методов в красной зоне MI | 0 | 0 | 0 |
| Нарушений правил | 1 | 6 | 0 |

## Самые сложные методы

### v1.0 (ЛР2)

| Метод | Файл:строка | CC | MI | Связанность |
|---|---|---|---|---|
| `Person.set_email` | metrics/snapshots/v1_0/src/domain.py:48 | 3 | 69.5 | 0 |
| `RentalService.validate_dates` | metrics/snapshots/v1_0/src/service.py:70 | 3 | 71.9 | 0 |
| `RentalService.return_equipment` | metrics/snapshots/v1_0/src/service.py:58 | 2 | 65.2 | 2 |
| `Person.__init__` | metrics/snapshots/v1_0/src/domain.py:34 | 1 | 68.8 | 0 |
| `Person.get_fio` | metrics/snapshots/v1_0/src/domain.py:42 | 1 | 82.0 | 0 |

### v2.0 черновик

| Метод | Файл:строка | CC | MI | Связанность |
|---|---|---|---|---|
| `RentalService.return_equipment` | metrics/snapshots/v2_0_raw/src/service.py:166 | 16 | 35.7 | 2 |
| `RentalService.create_request` | metrics/snapshots/v2_0_raw/src/service.py:82 | 11 | 46.9 | 3 |
| `RentalService.build_report` | metrics/snapshots/v2_0_raw/src/service.py:223 | 11 | 42.1 | 0 |
| `RentalService.estimate_cost` | metrics/snapshots/v2_0_raw/src/service.py:126 | 8 | 51.8 | 2 |
| `RentalService.load_state` | metrics/snapshots/v2_0_raw/src/service.py:300 | 8 | 46.2 | 4 |

### v2.0 итог

| Метод | Файл:строка | CC | MI | Связанность |
|---|---|---|---|---|
| `RentalReport.statistics` | src/reports.py:60 | 9 | 51.8 | 1 |
| `state_from_dict` | src/serialization/state.py:52 | 8 | 51.9 | 1 |
| `state_to_dict` | src/serialization/state.py:35 | 7 | 53.8 | 1 |
| `RequestDesk._is_booked` | src/requests.py:127 | 6 | 60.4 | 2 |
| `run_demo` | src/demo.py:56 | 5 | 43.1 | 3 |

