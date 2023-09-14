import asyncio
import logging
import logging.config
import os
import signal
from pathlib import Path

from tenacity import retry, retry_if_exception_type, wait_fixed

from .influxdb import managed_influxdb_consumer
from .settings import Settings
from .streamer import ReadTimeout, managed_telegram_streamer


def configure_logging(log_level: str):
    logging.config.fileConfig(
        Path(__file__).parent / "logging.conf",
        disable_existing_loggers=False,
        defaults={"log_level": log_level},
    )


@retry(
    retry=retry_if_exception_type(ReadTimeout),
    wait=wait_fixed(60),
)
async def main(
    *,
    _settings: Settings | None = None,
    _loop: asyncio.AbstractEventLoop | None = None,
):
    settings = _settings or Settings()
    loop = _loop or asyncio.get_running_loop()

    _managed_telegram_streamer = managed_telegram_streamer(
        settings.TCP_HOST, settings.TCP_PORT
    )

    async with (
        managed_influxdb_consumer(settings) as telegram_consumer,
        _managed_telegram_streamer as telegram_streamer,
    ):
        loop.add_signal_handler(signal.SIGINT, telegram_streamer.stop)

        await telegram_consumer.consume_stream(telegram_streamer)


if __name__ == "__main__":
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    asyncio.run(main())
