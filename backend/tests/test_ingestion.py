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
            run_async(cache_module.set_match_state("R32-1", {"status": "live", "home_score": "1"}))

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
        future_kickoff = (datetime.now(tz=timezone.utc) + timedelta(seconds=1000)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        match = make_match(status="scheduled", kickoff_time=future_kickoff)

        with patch("app.ingestion.poller.get_scheduled_matches", return_value={"R32-1": match}):
            result = poller._compute_sleep_duration()

        assert 690 <= result <= 710  # 700 ± small timing tolerance

    def test_sleep_clamped_to_poll_interval_minimum(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.INGESTION_POLL_INTERVAL", 60)
        monkeypatch.setattr("app.config.settings.INGESTION_HEARTBEAT_INTERVAL", 3600)
        monkeypatch.setattr("app.config.settings.INGESTION_PRE_KICKOFF_BUFFER", 300)

        poller = self._make_poller()
        poller._match_states = {}

        # Kickoff 100 seconds from now → 100 - 300 = -200, clamped to 60
        near_kickoff = (datetime.now(tz=timezone.utc) + timedelta(seconds=100)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        match = make_match(status="scheduled", kickoff_time=near_kickoff)

        with patch("app.ingestion.poller.get_scheduled_matches", return_value={"R32-1": match}):
            result = poller._compute_sleep_duration()

        assert result == 60

    def test_sleep_clamped_to_heartbeat_interval_maximum(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.INGESTION_POLL_INTERVAL", 60)
        monkeypatch.setattr("app.config.settings.INGESTION_HEARTBEAT_INTERVAL", 3600)
        monkeypatch.setattr("app.config.settings.INGESTION_PRE_KICKOFF_BUFFER", 300)

        poller = self._make_poller()
        poller._match_states = {}

        # Kickoff 10000 seconds from now → 10000 - 300 = 9700, clamped to 3600
        far_kickoff = (datetime.now(tz=timezone.utc) + timedelta(seconds=10000)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        match = make_match(status="scheduled", kickoff_time=far_kickoff)

        with patch("app.ingestion.poller.get_scheduled_matches", return_value={"R32-1": match}):
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

        completed_match = make_match(match_id="R32-1", status="completed", home_score=2, away_score=1)

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

        mock_put.assert_called_once_with(completed_match)

    def test_put_match_not_called_again_when_already_completed(self):
        from app.ingestion.poller import IngestionPoller

        poller = IngestionPoller()
        poller._match_states = {"R32-1": "completed"}

        completed_match = make_match(match_id="R32-1", status="completed", home_score=2, away_score=1)

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

        completed_match = make_match(match_id="R32-1", status="completed", home_score=1, away_score=0)

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

            written = load_initial_schedule("20260628", "20260719")

        assert written == 14
        assert mock_put.call_count == 14
        # Confirm none of the existing IDs were written
        written_ids = {call.args[0].match_id for call in mock_put.call_args_list}
        assert written_ids.isdisjoint(existing_ids)


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
# Helpers for asyncio.to_thread mocking
# ---------------------------------------------------------------------------


async def _fake_to_thread(func, *args, **kwargs):
    """Run sync functions inline so tests don't need a thread pool."""
    return func(*args, **kwargs)
