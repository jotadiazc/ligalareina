from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

WEEKDAYS_ES = {
    0: "lunes",
    1: "martes",
    2: "miércoles",
    3: "jueves",
    4: "viernes",
    5: "sábado",
    6: "domingo",
}


@dataclass(frozen=True)
class TeamRule:
    no_play_weekdays: set[int] = field(default_factory=set)

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "TeamRule":
        if not payload:
            return cls()

        weekdays = set(payload.get("no_play_weekdays", []))
        invalid = [w for w in weekdays if w < 0 or w > 6]
        if invalid:
            raise ValueError(
                f"Días inválidos en no_play_weekdays: {invalid}. Deben estar entre 0 (lunes) y 6 (domingo)."
            )
        return cls(no_play_weekdays=weekdays)


@dataclass(frozen=True)
class Team:
    name: str
    rule: TeamRule = field(default_factory=TeamRule)


@dataclass(frozen=True)
class Match:
    home: Team
    away: Team


@dataclass(frozen=True)
class ScheduledMatch:
    serie: str
    round_number: int
    match_number: int
    home: str
    away: str
    date: str
    forced_restriction: bool
    notes: list[str]


def _rotate_round_robin(teams: list[Team]) -> list[list[Match]]:
    if len(teams) < 2:
        raise ValueError("Cada serie debe tener al menos 2 equipos.")

    internal = teams[:]
    if len(internal) % 2 == 1:
        internal.append(Team(name="__BYE__"))

    rounds: list[list[Match]] = []
    for _ in range(len(internal) - 1):
        pairings: list[Match] = []
        for i in range(len(internal) // 2):
            a = internal[i]
            b = internal[-1 - i]
            if a.name == "__BYE__" or b.name == "__BYE__":
                continue
            if i % 2 == 0:
                pairings.append(Match(home=a, away=b))
            else:
                pairings.append(Match(home=b, away=a))
        rounds.append(pairings)
        internal = [internal[0], internal[-1], *internal[1:-1]]

    return rounds


def _violations_for_date(match: Match, d: date) -> list[str]:
    violations: list[str] = []
    weekday = d.weekday()

    if weekday in match.home.rule.no_play_weekdays:
        violations.append(
            f"{match.home.name} evita jugar los {WEEKDAYS_ES[weekday]}"
        )
    if weekday in match.away.rule.no_play_weekdays:
        violations.append(
            f"{match.away.name} evita jugar los {WEEKDAYS_ES[weekday]}"
        )
    return violations


def _pick_best_date(match: Match, anchor: date, max_shift_days: int = 3) -> tuple[date, bool, list[str]]:
    offsets = sorted(range(-max_shift_days, max_shift_days + 1), key=lambda x: (abs(x), x))

    for offset in offsets:
        candidate = anchor + timedelta(days=offset)
        violations = _violations_for_date(match, candidate)
        if not violations:
            return candidate, False, []

    forced_violations = _violations_for_date(match, anchor)
    return anchor, True, forced_violations


def generate_schedule(
    league_payload: dict[str, Any],
    start_date: date,
    round_interval_days: int = 7,
    max_shift_days: int = 3,
) -> list[ScheduledMatch]:
    series = league_payload.get("series", [])
    if not series:
        raise ValueError("La liga debe incluir al menos una serie.")

    calendar: list[ScheduledMatch] = []

    for serie in series:
        serie_name = serie.get("name")
        team_payloads = serie.get("teams", [])
        if not serie_name:
            raise ValueError("Cada serie debe tener un nombre.")

        teams = [
            Team(
                name=team_data["name"],
                rule=TeamRule.from_payload(team_data.get("rules")),
            )
            for team_data in team_payloads
        ]

        if len(teams) < 2:
            raise ValueError(f"La serie '{serie_name}' necesita al menos 2 equipos.")

        rounds = _rotate_round_robin(teams)
        for r_idx, round_matches in enumerate(rounds, start=1):
            round_anchor = start_date + timedelta(days=(r_idx - 1) * round_interval_days)
            for m_idx, match in enumerate(round_matches, start=1):
                picked_date, forced, notes = _pick_best_date(match, round_anchor, max_shift_days)
                calendar.append(
                    ScheduledMatch(
                        serie=serie_name,
                        round_number=r_idx,
                        match_number=m_idx,
                        home=match.home.name,
                        away=match.away.name,
                        date=picked_date.isoformat(),
                        forced_restriction=forced,
                        notes=notes,
                    )
                )

    return sorted(calendar, key=lambda m: (m.date, m.serie, m.round_number, m.match_number))


def build_output(schedule: list[ScheduledMatch]) -> dict[str, Any]:
    return {
        "matches": [
            {
                "serie": m.serie,
                "round": m.round_number,
                "match": m.match_number,
                "home": m.home,
                "away": m.away,
                "date": m.date,
                "forced_restriction": m.forced_restriction,
                "notes": m.notes,
            }
            for m in schedule
        ]
    }
