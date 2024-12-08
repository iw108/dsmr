import asyncio
import logging
import logging.config
import os
import signal
from pathlib import Path

from tenacity import retry, retry_if_exception_type

from .influxdb import managed_influxdb_handler
from .settings import Settings
from .streamer import ReadTimeout, managed_telegram_streamer


def configure_logging(log_level: str):
    logging.config.fileConfig(
        Path(__file__).parent / "logging.conf",
        disable_existing_loggers=False,
        defaults={"log_level": log_level},
    )


@retry(retry=retry_if_exception_type(ReadTimeout))
async def main(
    *,
    _settings: Settings | None = None,
    _loop: asyncio.AbstractEventLoop | None = None,
):
    settings = _settings or Settings()
    stop_event = asyncio.Event()

    loop = _loop or asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_event.set)

    _managed_telegram_streamer = managed_telegram_streamer(
        settings.TCP_HOST,
        settings.TCP_PORT,
        stop_event=stop_event,
    )

    async with (
        _managed_telegram_streamer as stream,
        managed_influxdb_handler(settings) as handler,
    ):
        async for telegram in stream:
            await handler(telegram)


if __name__ == "__main__":
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    asyncio.run(main())
