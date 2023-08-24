import asyncio
import logging
import logging.config
from pathlib import Path

from .influxdb import managed_influxdb_consumer
from .settings import Settings
from .streamer import managed_telegram_streamer

logging.config.fileConfig(
    Path(__file__).parent / "logging.conf",
    disable_existing_loggers=False,
)


async def main(*, _settings: Settings | None = None):
    settings = _settings or Settings()

    telegram_count = 0

    _managed_telegram_streamer = managed_telegram_streamer(
        settings.TCP_HOST, settings.TCP_PORT
    )

    async with (
        _managed_telegram_streamer as telegram_streamer,
        managed_influxdb_consumer(settings) as telegram_consumer,
    ):
        async for raw_telegram in telegram_streamer:
            if telegram_count % 10 == 0:
                telegram_consumer.add(raw_telegram)

            telegram_count += 1


if __name__ == "__main__":
    asyncio.run(main())
