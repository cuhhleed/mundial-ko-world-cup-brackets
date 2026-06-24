"""Tests for the ESPN API client and adapter (E5-S1)."""

from unittest.mock import MagicMock

import httpx

import app.espn.client as espn_client_module
from app.espn.adapter import (
    _map_status,
    _normalize_team_code,
    espn_event_to_match,
    espn_events_to_matches,
)
from app.espn.client import fetch_live_scores, fetch_scoreboard

# ---------------------------------------------------------------------------
# Factory fixture
# ---------------------------------------------------------------------------


def make_espn_event(
    event_id="401234567",
    home_abbr="ARG",
    away_abbr="BRA",
    home_score="0",
    away_score="0",
    state="pre",
    stage="round-of-32",
    date="2026-06-28T16:00:00Z",
    home_shootout=None,
    away_shootout=None,
    home_winner=False,
    away_winner=False,
) -> dict:
    """Build a well-formed ESPN event dict with sensible defaults."""
    home_competitor: dict = {
        "homeAway": "home",
        "team": {"abbreviation": home_abbr},
        "score": home_score,
        "winner": home_winner,
    }
    away_competitor: dict = {
        "homeAway": "away",
        "team": {"abbreviation": away_abbr},
        "score": away_score,
        "winner": away_winner,
    }

    if home_shootout is not None:
        home_competitor["shootoutScore"] = home_shootout
    if away_shootout is not None:
        away_competitor["shootoutScore"] = away_shootout

    return {
        "id": event_id,
        "date": date,
        "competitions": [
            {
                "stage": stage,
                "status": {
                    "type": {
                        "state": state,
                        "name": "STATUS_SCHEDULED" if state == "pre" else "STATUS_IN_PROGRESS",
                        "completed": state == "post",
                    }
                },
                "competitors": [home_competitor, away_competitor],
            }
        ],
    }


# ---------------------------------------------------------------------------
# TestTeamCodeNormalization
# ---------------------------------------------------------------------------


class TestTeamCodeNormalization:
    def test_placeholder_1a(self):
        assert _normalize_team_code("1A") == "A1"

    def test_placeholder_2b(self):
        assert _normalize_team_code("2B") == "B2"

    def test_fifa_code_passes_through(self):
        assert _normalize_team_code("ARG") == "ARG"

    def test_placeholder_last_group(self):
        # Edge: last group (P)
        assert _normalize_team_code("1P") == "P1"


# ---------------------------------------------------------------------------
# TestStatusMapping
# ---------------------------------------------------------------------------


class TestStatusMapping:
    def test_pre_maps_to_scheduled(self):
        assert _map_status("pre") == "scheduled"

    def test_in_maps_to_live(self):
        assert _map_status("in") == "live"

    def test_post_maps_to_completed(self):
        assert _map_status("post") == "completed"

    def test_unknown_state_defaults_to_scheduled(self):
        assert _map_status("unknown_state") == "scheduled"


# ---------------------------------------------------------------------------
# TestScoreExtraction
# ---------------------------------------------------------------------------


class TestScoreExtraction:
    def test_scheduled_match_scores_are_none(self):
        event = make_espn_event(state="pre", home_score="0", away_score="0")
        # ESPN returns "0" for scheduled matches, but with state "pre" scores
        # may still be "0" — let's use empty string to test the None path
        event["competitions"][0]["competitors"][0]["score"] = ""
        event["competitions"][0]["competitors"][1]["score"] = ""
        match = espn_event_to_match(event, "R32-1")
        assert match.home_score is None
        assert match.away_score is None

    def test_completed_match_scores_parsed(self):
        event = make_espn_event(
            state="post", home_score="2", away_score="1", home_winner=True
        )
        match = espn_event_to_match(event, "R32-1")
        assert match.home_score == 2
        assert match.away_score == 1

    def test_pk_match_scores_and_winner(self):
        # Regulation draw 1-1, home wins on pens 4-3
        event = make_espn_event(
            state="post",
            home_score="1",
            away_score="1",
            home_shootout=4,
            away_shootout=3,
            home_winner=True,
        )
        match = espn_event_to_match(event, "R32-1")
        assert match.home_score == 1
        assert match.away_score == 1
        assert match.pk_home_score == 4
        assert match.pk_away_score == 3
        assert match.pk_winner == "ARG"  # home team


# ---------------------------------------------------------------------------
# TestHomeAwayAssignment
# ---------------------------------------------------------------------------


class TestHomeAwayAssignment:
    def test_away_competitor_first_in_array(self):
        """Adapter must use homeAway field, not array position."""
        event = make_espn_event(home_abbr="ESP", away_abbr="FRA", state="post",
                                home_score="3", away_score="1", home_winner=True)
        # Swap the competitors so away is first in the list
        competitors = event["competitions"][0]["competitors"]
        competitors[0], competitors[1] = competitors[1], competitors[0]

        match = espn_event_to_match(event, "R32-5")
        assert match.home_team == "ESP"
        assert match.away_team == "FRA"
        assert match.home_score == 3
        assert match.away_score == 1


# ---------------------------------------------------------------------------
# TestEventToMatch
# ---------------------------------------------------------------------------


class TestEventToMatch:
    def test_full_round_trip(self):
        date = "2026-06-28T18:00:00Z"
        event = make_espn_event(
            event_id="401999001",
            home_abbr="ARG",
            away_abbr="BRA",
            home_score="2",
            away_score="1",
            state="post",
            stage="round-of-32",
            date=date,
            home_winner=True,
        )
        slot_id = "R32-3"
        match = espn_event_to_match(event, slot_id)

        assert match.match_id == slot_id
        assert match.round == "R32"
        assert match.match_number == 3
        assert match.home_team == "ARG"
        assert match.away_team == "BRA"
        assert match.home_score == 2
        assert match.away_score == 1
        assert match.status == "completed"
        assert match.kickoff_time == date


# ---------------------------------------------------------------------------
# TestSlotAssignment
# ---------------------------------------------------------------------------


class TestSlotAssignment:
    def test_r32_events_assigned_chronologically(self):
        events = [
            make_espn_event(
                event_id=f"40100000{i}",
                date=f"2026-06-2{i}T16:00:00Z",
                stage="round-of-32",
            )
            for i in range(8, 12)  # dates: 28, 29, 20, 21 → sorted chronologically
        ]
        # Sort expected dates for reference
        sorted_dates = sorted(e["date"] for e in events)
        result = espn_events_to_matches(events)

        assert "R32-1" in result
        assert "R32-4" in result
        # Verify chronological order: R32-1 should have the earliest date
        assert result["R32-1"].kickoff_time == sorted_dates[0]
        assert result["R32-4"].kickoff_time == sorted_dates[3]

    def test_final_event_gets_final_slot(self):
        event = make_espn_event(
            event_id="401999100",
            stage="final",
            date="2026-07-19T20:00:00Z",
        )
        result = espn_events_to_matches([event])
        assert "FINAL" in result
        assert result["FINAL"].match_id == "FINAL"
        assert result["FINAL"].match_number == 1

    def test_tp_event_gets_tp_slot(self):
        event = make_espn_event(
            event_id="401999099",
            stage="third-place",
            date="2026-07-18T20:00:00Z",
        )
        result = espn_events_to_matches([event])
        assert "TP" in result
        assert result["TP"].match_id == "TP"


# ---------------------------------------------------------------------------
# TestFetchScoreboard (mock HTTP)
# ---------------------------------------------------------------------------


class TestFetchScoreboard:
    def _make_response(self, status_code: int, json_data: dict | None = None) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        if json_data is not None:
            resp.json.return_value = json_data
        return resp

    def test_successful_fetch_returns_events(self, monkeypatch):
        event = make_espn_event()
        mock_response = self._make_response(200, {"events": [event]})

        mock_get = MagicMock(return_value=mock_response)
        monkeypatch.setattr(espn_client_module, "_client", MagicMock(get=mock_get))

        events = fetch_scoreboard()
        assert len(events) == 1

    def test_500_response_retries_and_returns_empty(self, monkeypatch):
        mock_response = self._make_response(500)
        mock_get = MagicMock(return_value=mock_response)

        # Override sleep to avoid actual delays in tests
        monkeypatch.setattr(espn_client_module.time, "sleep", lambda _: None)
        monkeypatch.setattr(espn_client_module, "_client", MagicMock(get=mock_get))

        events = fetch_scoreboard()
        assert events == []
        assert mock_get.call_count == 3  # max_retries=3

    def test_transport_error_retries_and_returns_empty(self, monkeypatch):
        mock_get = MagicMock(side_effect=httpx.TransportError("connection failed"))

        monkeypatch.setattr(espn_client_module.time, "sleep", lambda _: None)
        monkeypatch.setattr(espn_client_module, "_client", MagicMock(get=mock_get))

        events = fetch_scoreboard()
        assert events == []
        assert mock_get.call_count == 3

    def test_404_returns_empty_immediately_no_retry(self, monkeypatch):
        mock_response = self._make_response(404)
        mock_get = MagicMock(return_value=mock_response)

        monkeypatch.setattr(espn_client_module.time, "sleep", lambda _: None)
        monkeypatch.setattr(espn_client_module, "_client", MagicMock(get=mock_get))

        events = fetch_scoreboard()
        assert events == []
        assert mock_get.call_count == 1  # no retry on 4xx


# ---------------------------------------------------------------------------
# TestFetchLiveScores
# ---------------------------------------------------------------------------


class TestFetchLiveScores:
    def _make_response(self, status_code: int, json_data: dict) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        return resp

    def test_filters_to_in_progress_only(self, monkeypatch):
        pre_event = make_espn_event(event_id="1", state="pre")
        in_event = make_espn_event(event_id="2", state="in")
        post_event = make_espn_event(event_id="3", state="post")

        mock_response = self._make_response(200, {"events": [pre_event, in_event, post_event]})
        mock_get = MagicMock(return_value=mock_response)

        monkeypatch.setattr(espn_client_module, "_client", MagicMock(get=mock_get))

        live_events = fetch_live_scores()
        assert len(live_events) == 1
        assert live_events[0]["id"] == "2"
