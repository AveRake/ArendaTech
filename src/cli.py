## @file cli.py
#  @brief Интерфейс командной строки приложения «АрендаТех»
#  @author Арсланов В.Д.
#  @date 2026-02-10
#  @version 2.0
#
#  @details Команды:
#  - @c demo   — демонстрационный сценарий полного цикла аренды;
#  - @c report — отчёт по сохранённому состоянию (JSON);
#  - @c metrics— запуск анализатора метрик кода (metrics/code_metrics.py).
#
#  @code
#  python -m src.main demo
#  python -m src.main report --state data/state.json
#  python -m src.main metrics
#  @endcode

from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional, Sequence

from .demo import run_demo
from .reports import RentalReport
from .serialization import state_from_dict

#: Корень проекта (каталог с пакетом src).
PROJECT_ROOT = Path(__file__).resolve().parent.parent


## @brief Построить парсер аргументов командной строки
#  @return Настроенный парсер
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="src.main",
        description="Сервис аренды техники для учебных учреждений «АрендаТех».",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="демонстрационный сценарий")
    demo_parser.add_argument("--state", default=None,
                             help="сохранить состояние сервиса в JSON-файл")
    demo_parser.set_defaults(handler=run_demo_command)

    report_parser = subparsers.add_parser(
        "report", help="отчёт по сохранённому состоянию")
    report_parser.add_argument("--state", required=True,
                               help="путь к JSON-файлу состояния")
    report_parser.set_defaults(handler=run_report_command)

    metrics_parser = subparsers.add_parser(
        "metrics", help="рассчитать метрики кода проекта")
    metrics_parser.add_argument("--out-dir", default="metrics/reports/current",
                                help="каталог для отчётов о метриках")
    metrics_parser.add_argument("--label", default="code-metrics",
                                help="префикс имён файлов отчётов")
    metrics_parser.set_defaults(handler=run_metrics_command)
    return parser


## @brief Команда demo
#  @param args Аргументы командной строки
#  @return Код возврата
def run_demo_command(args: argparse.Namespace) -> int:
    return run_demo(args.state)


## @brief Команда report
#  @param args Аргументы командной строки
#  @return Код возврата
def run_report_command(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.state).read_text(encoding="utf-8"))
    state = state_from_dict(payload)
    print(RentalReport(state.units, state.requests, state.issues,
                       state.fines).build())
    return 0


## @brief Команда metrics
#  @param args Аргументы командной строки
#  @return Код возврата
def run_metrics_command(args: argparse.Namespace) -> int:
    script = PROJECT_ROOT / "metrics" / "code_metrics.py"
    command = [sys.executable, str(script), "src", "--root", ".",
               "--out-dir", args.out_dir, "--label", args.label]
    return subprocess.call(command, cwd=str(PROJECT_ROOT))


## @brief Точка входа CLI
#  @param argv Аргументы командной строки (по умолчанию sys.argv[1:])
#  @return Код возврата
def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler: Callable[[argparse.Namespace], int] = args.handler
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
