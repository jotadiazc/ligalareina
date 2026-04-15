from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from league_scheduler import build_output, generate_schedule


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera fixtures automáticos para una liga de fútbol con restricciones por equipo."
    )
    parser.add_argument("--input", required=True, help="Archivo JSON con la estructura de liga.")
    parser.add_argument(
        "--start-date",
        required=True,
        help="Fecha inicial en formato YYYY-MM-DD para la primera ronda.",
    )
    parser.add_argument(
        "--round-interval-days",
        type=int,
        default=7,
        help="Separación de días entre rondas (default 7).",
    )
    parser.add_argument(
        "--max-shift-days",
        type=int,
        default=3,
        help="Máximo corrimiento de días para evitar restricciones (default 3).",
    )
    parser.add_argument(
        "--output",
        default="fixture_output.json",
        help="Archivo JSON de salida (default fixture_output.json).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    start = date.fromisoformat(args.start_date)

    schedule = generate_schedule(
        payload,
        start_date=start,
        round_interval_days=args.round_interval_days,
        max_shift_days=args.max_shift_days,
    )
    output = build_output(schedule)

    Path(args.output).write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Fixture generado en: {args.output}")


if __name__ == "__main__":
    main()
