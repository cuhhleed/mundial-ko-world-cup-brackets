import asyncio
import contextlib
import time
from datetime import datetime, timezone

from app.config import settings
from app.db.cache import clear_leaderboard, set_match_state, update_leaderboard
from app.espn.adapter import espn_events_to_matches
from app.espn.client import fetch_scoreboard
from app.ingestion.heartbeat import emit_heartbeat
from app.ingestion.schedule_loader import load_initial_schedule
from app.logging import get_logger
from app.models.match import Match
from app.services.brackets import rescore_all_brackets
from app.services.matches import get_scheduled_matches, put_match

logger = get_logger("poller")


class IngestionPoller:
    def __init__(self) -> None:
        self._match_states: dict[str, str] = {}

    async def run(self, shutdown: asyncio.Event) -> None:
        logger.info("poller_starting")

        if await self._run_or_shutdown(
            asyncio.to_thread(load_initial_schedule, "20260611", "20260627"),
            shutdown,
        ):
            return

        if await self._run_or_shutdown(
            asyncio.to_thread(load_initial_schedule, "20260628", "20260719"),
            shutdown,
        ):
            return

        while not shutdown.is_set():
            sleep_duration = await asyncio.to_thread(self._compute_sleep_duration)
            logger.info("poller_sleeping", seconds=sleep_duration)

            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(shutdown.wait(), timeout=sleep_duration)

            if shutdown.is_set():
                break

            if await self._run_or_shutdown(self._poll_cycle(), shutdown):
                break

        logger.info("poller_stopped")

    async def _run_or_shutdown(
        self, task_coro: asyncio.coroutines, shutdown: asyncio.Event
    ) -> bool:
        """Run *task_coro* but return True immediately if *shutdown* fires first."""
        task = asyncio.ensure_future(task_coro)
        waiter = asyncio.ensure_future(shutdown.wait())

        done, pending = await asyncio.wait(
            {task, waiter}, return_when=asyncio.FIRST_COMPLETED
        )

        for p in pending:
            p.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await p

        if task in done and task.exception():
            raise task.exception()

        return shutdown.is_set()

    def _compute_sleep_duration(self) -> float:
        poll_interval = float(settings.INGESTION_POLL_INTERVAL)
        heartbeat_interval = float(settings.INGESTION_HEARTBEAT_INTERVAL)
        buffer = float(settings.INGESTION_PRE_KICKOFF_BUFFER)

        # If any tracked match is live, poll at the fast interval
        if any(status == "live" for status in self._match_states.values()):
            return poll_interval

        # Find the nearest future kickoff from DynamoDB scheduled matches
        scheduled = get_scheduled_matches()
        if not scheduled:
            return heartbeat_interval

        now = datetime.now(tz=timezone.utc)
        nearest_seconds: float | None = None

        for match in scheduled.values():
            try:
                kickoff = datetime.fromisoformat(
                    match.kickoff_time.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                continue

            seconds_until = (kickoff - now).total_seconds()
            if seconds_until > 0:
                if nearest_seconds is None or seconds_until < nearest_seconds:
                    nearest_seconds = seconds_until

        if nearest_seconds is None:
            return heartbeat_interval

        sleep = nearest_seconds - buffer
        return max(poll_interval, min(sleep, heartbeat_interval))

    async def _poll_cycle(self) -> None:
        logger.info("poll_cycle_start")

        events = await asyncio.to_thread(fetch_scoreboard)
        matches = espn_events_to_matches(events)

        for match_id, match in matches.items():
            string_data = {
                k: str(v) for k, v in match.model_dump(exclude_none=True).items()
            }
            await set_match_state(match_id, string_data)

            previous_status = self._match_states.get(match_id)
            current_status = match.status

            if previous_status != "completed" and current_status == "completed":
                await self._handle_completion(match)

            self._match_states[match_id] = current_status

        await asyncio.to_thread(emit_heartbeat)
        logger.info("poll_cycle_done", match_count=len(matches))

    async def _handle_completion(self, match: Match) -> None:
        logger.info("match_completed", match_id=match.match_id)
        await asyncio.to_thread(put_match, match)
        await self._trigger_scoring(match)

    async def _trigger_scoring(self, match: Match) -> None:
        logger.info("scoring_trigger_start", match_id=match.match_id)
        start = time.monotonic()

        result = await asyncio.to_thread(rescore_all_brackets)

        await clear_leaderboard()
        for _bracket_id, user_id, total_points in result["updates"]:
            await update_leaderboard(user_id, total_points)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "scoring_trigger_done",
            match_id=match.match_id,
            scored=result["scored"],
            failed=result["failed"],
            elapsed_ms=elapsed_ms,
        )

        if result["errors"]:
            logger.error(
                "scoring_trigger_errors",
                match_id=match.match_id,
                errors=result["errors"],
            )
