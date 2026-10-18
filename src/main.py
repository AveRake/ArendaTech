## @file main.py
#  @brief Точка входа приложения «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @par Использует файлы:
#  - @ref cli.py
#
#  @details Запуск без аргументов выполняет демонстрационный сценарий,
#  запуск с аргументами — команду интерфейса командной строки:
#  @code
#  python -m src.main
#  python -m src.main demo
#  python -m src.main report --state data/state.json
#  @endcode

from __future__ import annotations
import sys
from typing import Optional, Sequence

from .cli import main as cli_main


## @brief Точка входа
#  @param argv Аргументы командной строки
#  @return Код возврата
def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    return cli_main(arguments if arguments else ["demo"])


if __name__ == "__main__":
    raise SystemExit(main())
