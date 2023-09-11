import asyncio
import logging
import logging.config
import os
from pathlib import Path

from .influxdb import managed_influxdb_consumer
from .settings import Settings
from .streamer import managed_telegram_streamer


def configure_logging(log_level: str):
    logging.config.fileConfig(
        Path(__file__).parent / "logging.conf",
        disable_existing_loggers=False,
        defaults={"log_level": log_level},
    )


async def main(*, _settings: Settings | None = None):
    settings = _settings or Settings()

    _managed_telegram_streamer = managed_telegram_streamer(
        settings.TCP_HOST, settings.TCP_PORT
    )

    async with (
        _managed_telegram_streamer as telegram_streamer,
        managed_influxdb_consumer(settings) as telegram_consumer,
    ):
        await telegram_consumer.consume_stream(telegram_streamer)


if __name__ == "__main__":
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    asyncio.run(main())
