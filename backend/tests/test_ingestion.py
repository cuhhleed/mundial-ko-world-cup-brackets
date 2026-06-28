"""Tests for the ingestion module (E5-S2)."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.match import Match


def run_async(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_match(
    match_id="R32-1",
    status="scheduled",
    kickoff_time="2026-06-28T16:00:00Z",
    home_team="ARG",
    away_team="BRA",
    home_score=None,
    away_score=None,
) -> Match:
    return Match(
        match_id=match_id,
        round="R32",
        match_number=1,
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
        status=status,
        kickoff_time=kickoff_time,
    )


# ---------------------------------------------------------------------------
# Cache operations
# ---------------------------------------------------------------------------


class TestCacheOperations:
    def test_set_match_state_writes_correct_key_and_sets_ttl(self):
        mock_redis = AsyncMock()
        import app.db.cache as cache_module

        with patch.object(cache_module, "_client", mock_redis):
            run_async(
                cache_module.set_match_state(
                    "R32-1", {"status": "live", "home_score": "1"}
                )
            )

        mock_redis.hset.assert_called_once_with(
            "match:R32-1", mapping={"status": "live", "home_score": "1"}
        )
        mock_redis.expire.assert_called_once_with("match:R32-1", 86400)

    def test_get_match_state_returns_decoded_hash(self):
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {"status": "live", "home_score": "1"}
        import app.db.cache as cache_module

        with patch.object(cache_module, "_client", mock_redis):
            result = run_async(cache_module.get_match_state("R32-1"))

        mock_redis.hgetall.assert_called_once_with("match:R32-1")
        assert result == {"status": "live", "home_score": "1"}

    def test_get_match_state_returns_none_when_key_missing(self):
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {}
        import app.db.cache as cache_module

        with patch.object(cache_module, "_client", mock_redis):
            result = run_async(cache_module.get_match_state("R32-99"))

        assert result is None

    def test_set_round_matches_deletes_then_rpush_then_expire(self):
        mock_redis = AsyncMock()
        import app.db.cache as cache_module

        with patch.object(cache_module, "_client", mock_redis):
            run_async(cache_module.set_round_matches("R32", ["R32-1", "R32-2"]))

        mock_redis.delete.assert_called_once_with("round:R32:matches")
        mock_redis.rpush.assert_called_once_with("round:R32:matches", "R32-1", "R32-2")
        mock_redis.expire.assert_called_once_with("round:R32:matches", 86400)

    def test_update_leaderboard_calls_zadd(self):
        mock_redis = AsyncMock()
        import app.db.cache as cache_module

        with patch.object(cache_module, "_client", mock_redis):
            run_async(cache_module.update_leaderboard("user-1", 42))

        mock_redis.zadd.assert_called_once_with("leaderboard", {"user-1": 42})


# ---------------------------------------------------------------------------
# _compute_sleep_duration
# ---------------------------------------------------------------------------


class TestComputeSleepDuration:
    def _make_poller(self):
        from app.ingestion.poller import IngestionPoller

        return IngestionPoller()

    def test_returns_poll_interval_when_match_is_live(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.INGESTION_POLL_INTERVAL", 60)
        monkeypatch.setattr("app.config.settings.INGESTION_HEARTBEAT_INTERVAL", 3600)
        monkeypatch.setattr("app.config.settings.INGESTION_PRE_KICKOFF_BUFFER", 300)

        poller = self._make_poller()
        poller._match_states = {"R32-1": "live", "R32-2": "scheduled"}

        with patch("app.ingestion.poller.get_scheduled_matches") as mock_gsm:
            result = poller._compute_sleep_duration()

        mock_gsm.assert_not_called()
        assert result == 60

    def test_returns_heartbeat_when_no_scheduled_matches(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.INGESTION_POLL_INTERVAL", 60)
        monkeypatch.setattr("app.config.settings.INGESTION_HEARTBEAT_INTERVAL", 3600)
        monkeypatch.setattr("app.config.settings.INGESTION_PRE_KICKOFF_BUFFER", 300)

        poller = self._make_poller()
        poller._match_states = {}

        with patch("app.ingestion.poller.get_scheduled_matches", return_value={}):
            result = poller._compute_sleep_duration()

        assert result == 3600

    def test_sleeps_until_kickoff_minus_buffer(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.INGESTION_POLL_INTERVAL", 60)
        monkeypatch.setattr("app.config.settings.INGESTION_HEARTBEAT_INTERVAL", 3600)
        monkeypatch.setattr("app.config.settings.INGESTION_PRE_KICKOFF_BUFFER", 300)

        poller = self._make_poller()
        poller._match_states = {}

        # Kickoff 1000 seconds from now → sleep = 1000 - 300 = 700, clamped to [60, 3600]
        future_kickoff = (
            datetime.now(tz=timezone.utc) + timedelta(seconds=1000)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        match = make_match(status="scheduled", kickoff_time=future_kickoff)

        with patch(
            "app.ingestion.poller.get_scheduled_matches", return_value={"R32-1": match}
        ):
            result = poller._compute_sleep_duration()

        assert 690 <= result <= 710  # 700 ± small timing tolerance

    def test_sleep_clamped_to_poll_interval_minimum(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.INGESTION_POLL_INTERVAL", 60)
        monkeypatch.setattr("app.config.settings.INGESTION_HEARTBEAT_INTERVAL", 3600)
        monkeypatch.setattr("app.config.settings.INGESTION_PRE_KICKOFF_BUFFER", 300)

        poller = self._make_poller()
        poller._match_states = {}

        # Kickoff 100 seconds from now → 100 - 300 = -200, clamped to 60
        near_kickoff = (
            datetime.now(tz=timezone.utc) + timedelta(seconds=100)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        match = make_match(status="scheduled", kickoff_time=near_kickoff)

        with patch(
            "app.ingestion.poller.get_scheduled_matches", return_value={"R32-1": match}
        ):
            result = poller._compute_sleep_duration()

        assert result == 60

    def test_sleep_clamped_to_heartbeat_interval_maximum(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.INGESTION_POLL_INTERVAL", 60)
        monkeypatch.setattr("app.config.settings.INGESTION_HEARTBEAT_INTERVAL", 3600)
        monkeypatch.setattr("app.config.settings.INGESTION_PRE_KICKOFF_BUFFER", 300)

        poller = self._make_poller()
        poller._match_states = {}

        # Kickoff 10000 seconds from now → 10000 - 300 = 9700, clamped to 3600
        far_kickoff = (
            datetime.now(tz=timezone.utc) + timedelta(seconds=10000)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        match = make_match(status="scheduled", kickoff_time=far_kickoff)

        with patch(
            "app.ingestion.poller.get_scheduled_matches", return_value={"R32-1": match}
        ):
            result = poller._compute_sleep_duration()

        assert result == 3600


# ---------------------------------------------------------------------------
# _poll_cycle transition detection
# ---------------------------------------------------------------------------


class TestPollCycleTransitionDetection:
    def test_put_match_called_once_on_live_to_completed_transition(self):
        from app.ingestion.poller import IngestionPoller

        poller = IngestionPoller()
        poller._match_states = {"R32-1": "live"}

        completed_match = make_match(
            match_id="R32-1", status="completed", home_score=2, away_score=1
        )
        canned_result = {"scored": 0, "failed": 0, "errors": [], "updates": []}

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches",
                return_value={"R32-1": completed_match},
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.put_match") as mock_put,
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.rescore_all_brackets", return_value=canned_result
            ),
            patch("app.ingestion.poller.clear_leaderboard", new_callable=AsyncMock),
            patch("app.ingestion.poller.update_leaderboard", new_callable=AsyncMock),
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        mock_put.assert_called_once_with(completed_match)

    def test_put_match_not_called_again_when_already_completed(self):
        from app.ingestion.poller import IngestionPoller

        poller = IngestionPoller()
        poller._match_states = {"R32-1": "completed"}

        completed_match = make_match(
            match_id="R32-1", status="completed", home_score=2, away_score=1
        )

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches",
                return_value={"R32-1": completed_match},
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.put_match") as mock_put,
            patch("app.ingestion.poller.emit_heartbeat"),
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        mock_put.assert_not_called()

    def test_first_poll_of_already_completed_match_triggers_handle_completion(self):
        from app.ingestion.poller import IngestionPoller

        poller = IngestionPoller()
        poller._match_states = {}

        completed_match = make_match(
            match_id="R32-1", status="completed", home_score=1, away_score=0
        )
        canned_result = {"scored": 0, "failed": 0, "errors": [], "updates": []}

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches",
                return_value={"R32-1": completed_match},
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.put_match") as mock_put,
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.rescore_all_brackets", return_value=canned_result
            ),
            patch("app.ingestion.poller.clear_leaderboard", new_callable=AsyncMock),
            patch("app.ingestion.poller.update_leaderboard", new_callable=AsyncMock),
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        mock_put.assert_called_once_with(completed_match)


# ---------------------------------------------------------------------------
# load_initial_schedule
# ---------------------------------------------------------------------------


class TestLoadInitialSchedule:
    def test_writes_only_new_matches(self):
        existing_ids = {f"R32-{i}" for i in range(1, 3)}  # 2 existing matches
        all_espn_ids = {f"R32-{i}" for i in range(1, 17)}  # 16 from ESPN

        existing_matches = {mid: make_match(match_id=mid) for mid in existing_ids}
        espn_matches = {mid: make_match(match_id=mid) for mid in all_espn_ids}

        with (
            patch(
                "app.ingestion.schedule_loader.get_match_schedule",
                return_value=espn_matches,
            ),
            patch(
                "app.ingestion.schedule_loader.get_all_matches",
                return_value=existing_matches,
            ),
            patch("app.ingestion.schedule_loader.put_match") as mock_put,
        ):
            from app.ingestion.schedule_loader import load_initial_schedule

            written, updated = load_initial_schedule("20260628", "20260719")

        assert written == 14
        assert updated == 0
        assert mock_put.call_count == 14
        # Confirm none of the existing IDs were written
        written_ids = {call.args[0].match_id for call in mock_put.call_args_list}
        assert written_ids.isdisjoint(existing_ids)

    def test_updates_scheduled_matches_with_resolved_teams(self):
        # Existing scheduled match with placeholder teams
        existing_match = make_match(
            match_id="R32-1", status="scheduled", home_team="L1", away_team="L2"
        )
        # Existing completed match — should not be touched
        existing_completed = make_match(
            match_id="R32-2",
            status="completed",
            home_team="OLD1",
            away_team="OLD2",
            home_score=1,
            away_score=0,
        )
        existing_matches = {"R32-1": existing_match, "R32-2": existing_completed}

        # ESPN returns resolved team codes for R32-1 and updated teams for R32-2
        espn_r32_1 = make_match(
            match_id="R32-1", status="scheduled", home_team="ARG", away_team="BRA"
        )
        espn_r32_2 = make_match(
            match_id="R32-2",
            status="completed",
            home_team="NEW1",
            away_team="NEW2",
            home_score=1,
            away_score=0,
        )
        espn_matches = {"R32-1": espn_r32_1, "R32-2": espn_r32_2}

        with (
            patch(
                "app.ingestion.schedule_loader.get_match_schedule",
                return_value=espn_matches,
            ),
            patch(
                "app.ingestion.schedule_loader.get_all_matches",
                return_value=existing_matches,
            ),
            patch("app.ingestion.schedule_loader.put_match") as mock_put,
        ):
            from app.ingestion.schedule_loader import load_initial_schedule

            written, updated = load_initial_schedule("20260628", "20260719")

        # Only the scheduled match with changed teams should be updated
        assert written == 0
        assert updated == 1
        mock_put.assert_called_once_with(espn_r32_1)

    def test_does_not_update_when_teams_unchanged(self):
        existing_match = make_match(
            match_id="R32-1", status="scheduled", home_team="ARG", away_team="BRA"
        )
        existing_matches = {"R32-1": existing_match}

        espn_match = make_match(
            match_id="R32-1", status="scheduled", home_team="ARG", away_team="BRA"
        )
        espn_matches = {"R32-1": espn_match}

        with (
            patch(
                "app.ingestion.schedule_loader.get_match_schedule",
                return_value=espn_matches,
            ),
            patch(
                "app.ingestion.schedule_loader.get_all_matches",
                return_value=existing_matches,
            ),
            patch("app.ingestion.schedule_loader.put_match") as mock_put,
        ):
            from app.ingestion.schedule_loader import load_initial_schedule

            written, updated = load_initial_schedule("20260628", "20260719")

        assert written == 0
        assert updated == 0
        mock_put.assert_not_called()


# ---------------------------------------------------------------------------
# KO schedule refresh
# ---------------------------------------------------------------------------


class TestKOScheduleRefresh:
    def _make_poller(self):
        from app.ingestion.poller import IngestionPoller

        return IngestionPoller()

    def _base_patches(self):
        """Return a dict of base patches common to all KO refresh tests."""
        return {
            "fetch_scoreboard": patch(
                "app.ingestion.poller.fetch_scoreboard", return_value=[]
            ),
            "set_match_state": patch(
                "app.ingestion.poller.set_match_state", new_callable=AsyncMock
            ),
            "emit_heartbeat": patch("app.ingestion.poller.emit_heartbeat"),
            "to_thread": patch("asyncio.to_thread", side_effect=_fake_to_thread),
        }

    def test_grp_completion_sets_retry_counter(self):
        poller = self._make_poller()
        poller._match_states = {"GRP-1": "live"}

        grp_match = Match(
            match_id="GRP-1",
            round="GRP",
            match_number=1,
            home_team="ARG",
            away_team="BRA",
            home_score=1,
            away_score=0,
            status="completed",
            kickoff_time="2026-06-26T16:00:00Z",
        )
        canned_result = {"scored": 0, "failed": 0, "errors": [], "updates": []}

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches",
                return_value={"GRP-1": grp_match},
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.put_match"),
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.rescore_all_brackets", return_value=canned_result
            ),
            patch("app.ingestion.poller.clear_leaderboard", new_callable=AsyncMock),
            patch("app.ingestion.poller.update_leaderboard", new_callable=AsyncMock),
            patch(
                "app.ingestion.poller.load_initial_schedule", return_value=(0, 0)
            ) as mock_load,
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        # Counter should have been set to 5 then decremented to 4 (no updates found)
        assert poller._ko_refresh_retries == 4
        mock_load.assert_called_once_with("20260628", "20260719")

    def test_non_grp_completion_does_not_trigger_refresh(self):
        poller = self._make_poller()
        poller._match_states = {"R32-1": "live"}
        poller._ko_refresh_retries = 0

        r32_match = make_match(
            match_id="R32-1", status="completed", home_score=2, away_score=1
        )
        canned_result = {"scored": 0, "failed": 0, "errors": [], "updates": []}

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches",
                return_value={"R32-1": r32_match},
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.put_match"),
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.rescore_all_brackets", return_value=canned_result
            ),
            patch("app.ingestion.poller.clear_leaderboard", new_callable=AsyncMock),
            patch("app.ingestion.poller.update_leaderboard", new_callable=AsyncMock),
            patch(
                "app.ingestion.poller.load_initial_schedule", return_value=(0, 0)
            ) as mock_load,
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        assert poller._ko_refresh_retries == 0
        mock_load.assert_not_called()

    def test_retries_decrement_when_no_update(self):
        poller = self._make_poller()
        poller._match_states = {}
        poller._ko_refresh_retries = 3

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches", return_value={}
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.load_initial_schedule", return_value=(0, 0)
            ) as mock_load,
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        assert poller._ko_refresh_retries == 2
        mock_load.assert_called_once_with("20260628", "20260719")

    def test_retries_clear_on_successful_update(self):
        poller = self._make_poller()
        poller._match_states = {}
        poller._ko_refresh_retries = 3

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches", return_value={}
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.load_initial_schedule", return_value=(0, 2)
            ) as mock_load,
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        assert poller._ko_refresh_retries == 0
        mock_load.assert_called_once_with("20260628", "20260719")

    def test_multiple_grp_completions_trigger_single_refresh(self):
        poller = self._make_poller()
        poller._match_states = {"GRP-1": "live", "GRP-2": "live"}

        grp_match_1 = Match(
            match_id="GRP-1",
            round="GRP",
            match_number=1,
            home_team="ARG",
            away_team="BRA",
            home_score=1,
            away_score=0,
            status="completed",
            kickoff_time="2026-06-26T16:00:00Z",
        )
        grp_match_2 = Match(
            match_id="GRP-2",
            round="GRP",
            match_number=2,
            home_team="FRA",
            away_team="GER",
            home_score=2,
            away_score=1,
            status="completed",
            kickoff_time="2026-06-26T16:00:00Z",
        )
        canned_result = {"scored": 0, "failed": 0, "errors": [], "updates": []}

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches",
                return_value={"GRP-1": grp_match_1, "GRP-2": grp_match_2},
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.put_match"),
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.rescore_all_brackets", return_value=canned_result
            ),
            patch("app.ingestion.poller.clear_leaderboard", new_callable=AsyncMock),
            patch("app.ingestion.poller.update_leaderboard", new_callable=AsyncMock),
            patch(
                "app.ingestion.poller.load_initial_schedule", return_value=(0, 0)
            ) as mock_load,
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        # Despite two GRP completions, load_initial_schedule called only once
        mock_load.assert_called_once_with("20260628", "20260719")


# ---------------------------------------------------------------------------
# emit_heartbeat
# ---------------------------------------------------------------------------


class TestEmitHeartbeat:
    def test_puts_correct_metric_data(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.CLOUDWATCH_NAMESPACE", "MundialKO")
        monkeypatch.setattr("app.config.settings.ENVIRONMENT", "test")

        mock_cw = MagicMock()

        with patch("app.ingestion.heartbeat._cloudwatch", mock_cw):
            from app.ingestion.heartbeat import emit_heartbeat

            emit_heartbeat()

        mock_cw.put_metric_data.assert_called_once()
        call_kwargs = mock_cw.put_metric_data.call_args

        assert call_kwargs.kwargs["Namespace"] == "MundialKO"
        metric = call_kwargs.kwargs["MetricData"][0]
        assert metric["MetricName"] == "IngestionHeartbeat"
        assert metric["Value"] == 1
        assert metric["Dimensions"][0] == {"Name": "Environment", "Value": "test"}


# ---------------------------------------------------------------------------
# rescore_all_brackets
# ---------------------------------------------------------------------------


class TestRescoreAllBrackets:
    def _make_bracket(self, bracket_id, user_id, predictions=None, locked_slots=None):
        from app.models.bracket import Bracket, SlotPrediction

        if predictions is None:
            predictions = {
                "R32-1": SlotPrediction(teams=["ARG", "BRA"], winner="ARG"),
            }
        return Bracket(
            bracket_id=bracket_id,
            user_id=user_id,
            predictions=predictions,
            locked_slots=locked_slots or [],
            total_points=0,
            status="submitted",
            created_at="2026-06-24T00:00:00+00:00",
        )

    def test_rescore_updates_dynamo_for_each_bracket(self):

        bracket_a = self._make_bracket("b-1", "user-1")
        bracket_b = self._make_bracket("b-2", "user-2")
        completed = {}

        mock_table = MagicMock()

        with (
            patch(
                "app.services.brackets.get_all_brackets",
                return_value=[bracket_a, bracket_b],
            ),
            patch(
                "app.services.brackets.get_completed_matches", return_value=completed
            ),
            patch("app.services.brackets.get_table", return_value=mock_table),
        ):
            from app.services.brackets import rescore_all_brackets

            result = rescore_all_brackets()

        assert result["scored"] == 2
        assert result["failed"] == 0
        assert mock_table.update_item.call_count == 2

        call_keys = [
            c.kwargs["Key"]["bracket_id"] for c in mock_table.update_item.call_args_list
        ]
        assert "b-1" in call_keys
        assert "b-2" in call_keys

    def test_rescore_continues_on_bracket_failure(self):
        bracket_a = self._make_bracket("b-1", "user-1")
        bracket_b = self._make_bracket("b-2", "user-2")
        completed = {}

        mock_table = MagicMock()
        mock_table.update_item.side_effect = [Exception("DynamoDB error"), None]

        with (
            patch(
                "app.services.brackets.get_all_brackets",
                return_value=[bracket_a, bracket_b],
            ),
            patch(
                "app.services.brackets.get_completed_matches", return_value=completed
            ),
            patch("app.services.brackets.get_table", return_value=mock_table),
        ):
            from app.services.brackets import rescore_all_brackets

            result = rescore_all_brackets()

        assert result["failed"] == 1
        assert result["scored"] == 1
        assert len(result["errors"]) == 1


# ---------------------------------------------------------------------------
# _trigger_scoring
# ---------------------------------------------------------------------------


class TestTriggerScoring:
    def test_trigger_scoring_calls_rescore_and_updates_leaderboard(self):
        from app.ingestion.poller import IngestionPoller

        poller = IngestionPoller()
        match = make_match(
            match_id="R32-1", status="completed", home_score=1, away_score=0
        )

        canned_result = {
            "scored": 2,
            "failed": 0,
            "errors": [],
            "updates": [("b-1", "user-1", 10), ("b-2", "user-2", 5)],
        }

        mock_update_leaderboard = AsyncMock()

        with (
            patch(
                "app.ingestion.poller.rescore_all_brackets", return_value=canned_result
            ),
            patch("app.ingestion.poller.clear_leaderboard", new_callable=AsyncMock),
            patch("app.ingestion.poller.update_leaderboard", mock_update_leaderboard),
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._trigger_scoring(match))

        assert mock_update_leaderboard.call_count == 2
        mock_update_leaderboard.assert_any_call("user-1", 10)
        mock_update_leaderboard.assert_any_call("user-2", 5)

    def test_match_completion_triggers_full_rescore(self):
        from app.ingestion.poller import IngestionPoller

        poller = IngestionPoller()
        poller._match_states = {"R32-1": "live"}

        completed_match = make_match(
            match_id="R32-1", status="completed", home_score=2, away_score=1
        )

        canned_result = {
            "scored": 1,
            "failed": 0,
            "errors": [],
            "updates": [("b-1", "user-1", 7)],
        }

        mock_update_leaderboard = AsyncMock()

        with (
            patch("app.ingestion.poller.fetch_scoreboard", return_value=[]),
            patch(
                "app.ingestion.poller.espn_events_to_matches",
                return_value={"R32-1": completed_match},
            ),
            patch("app.ingestion.poller.set_match_state", new_callable=AsyncMock),
            patch("app.ingestion.poller.put_match"),
            patch("app.ingestion.poller.emit_heartbeat"),
            patch(
                "app.ingestion.poller.rescore_all_brackets", return_value=canned_result
            ),
            patch("app.ingestion.poller.clear_leaderboard", new_callable=AsyncMock),
            patch("app.ingestion.poller.update_leaderboard", mock_update_leaderboard),
            patch("asyncio.to_thread", side_effect=_fake_to_thread),
        ):
            run_async(poller._poll_cycle())

        mock_update_leaderboard.assert_called_once_with("user-1", 7)


# ---------------------------------------------------------------------------
# Helpers for asyncio.to_thread mocking
# ---------------------------------------------------------------------------


async def _fake_to_thread(func, *args, **kwargs):
    """Run sync functions inline so tests don't need a thread pool."""
    return func(*args, **kwargs)
