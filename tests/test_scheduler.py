from datetime import date

from league_scheduler import generate_schedule


def test_avoid_sunday_when_possible() -> None:
    payload = {
        "series": [
            {
                "name": "Serie A",
                "teams": [
                    {"name": "Mapuches", "rules": {"no_play_weekdays": [6]}},
                    {"name": "Halcones"},
                ],
            }
        ]
    }

    schedule = generate_schedule(
        payload,
        start_date=date(2026, 4, 19),  # domingo
        round_interval_days=7,
        max_shift_days=3,
    )

    assert len(schedule) == 1
    match = schedule[0]
    assert match.date != "2026-04-19"
    assert match.forced_restriction is False


def test_force_when_all_days_blocked() -> None:
    payload = {
        "series": [
            {
                "name": "Serie A",
                "teams": [
                    {"name": "Mapuches", "rules": {"no_play_weekdays": [0, 1, 2, 3, 4, 5, 6]}},
                    {"name": "Halcones"},
                ],
            }
        ]
    }

    schedule = generate_schedule(
        payload,
        start_date=date(2026, 4, 19),
        round_interval_days=7,
        max_shift_days=3,
    )

    assert len(schedule) == 1
    match = schedule[0]
    assert match.date == "2026-04-19"
    assert match.forced_restriction is True
    assert any("Mapuches" in note for note in match.notes)
