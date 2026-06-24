import asyncio
import signal

from app.db import cache
from app.ingestion.poller import IngestionPoller
from app.logging import configure_logging, get_logger

logger = get_logger("ingestion-service")


async def main() -> None:
    configure_logging()
    logger.info("ingestion_service_starting")

    await cache.connect()

    shutdown_event = asyncio.Event()

    loop = asyncio.get_running_loop()

    def _handle_signal(sig):
        logger.info("signal_received", signal=sig.name)
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal, sig)

    poller = IngestionPoller()

    try:
        await poller.run(shutdown_event)
    finally:
        await cache.disconnect()
        logger.info("ingestion_service_stopped")


if __name__ == "__main__":
    asyncio.run(main())
