from app.models.team import TeamRecord
from app.services.matches import get_completed_matches


def compute_team_records() -> dict[str, TeamRecord]:
    """Compute W/L/D and goals for all teams from completed matches (group + KO)."""
    completed = get_completed_matches()

    records: dict[str, TeamRecord] = {}

    def _get_or_create(team: str) -> TeamRecord:
        if team not in records:
            records[team] = TeamRecord(
                team=team,
                wins=0,
                draws=0,
                losses=0,
                goals_for=0,
                goals_against=0,
            )
        return records[team]

    for match in completed.values():
        home = match.home_team
        away = match.away_team
        home_score = match.home_score or 0
        away_score = match.away_score or 0

        home_record = _get_or_create(home)
        away_record = _get_or_create(away)

        # Accumulate regulation goals
        home_record.goals_for += home_score
        home_record.goals_against += away_score
        away_record.goals_for += away_score
        away_record.goals_against += home_score

        if home_score > away_score:
            home_record.wins += 1
            away_record.losses += 1
        elif away_score > home_score:
            away_record.wins += 1
            home_record.losses += 1
        else:
            # Scores are level — check for PK winner (KO matches)
            if match.pk_winner:
                if match.pk_winner == home:
                    home_record.wins += 1
                    away_record.losses += 1
                else:
                    away_record.wins += 1
                    home_record.losses += 1
            else:
                # No PK winner → group stage draw
                home_record.draws += 1
                away_record.draws += 1

    return records
