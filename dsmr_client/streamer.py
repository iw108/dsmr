import asyncio
import logging
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from .buffer import TelegramBuffer
from .exceptions import ReadTimeout
from .telegram import Telegram

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class StreamerOptions:
    """Configurable options for `TelegramStreamer`."""

    buffer_size: int = 256
    read_timeout: int = 10


class TelegramStreamer:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        *,
        streamer_options: StreamerOptions | None = None,
        stop_event: asyncio.Event | None = None,
        _buffer: TelegramBuffer | None = None,
    ):
        self.reader = reader

        self.options = streamer_options or StreamerOptions()
        self.stop_event = stop_event or asyncio.Event()
        self.buffer = _buffer or TelegramBuffer()

    async def _read(self) -> str:
        try:
            data = await asyncio.wait_for(
                self.reader.read(self.options.buffer_size),
                self.options.read_timeout,
            )
        except TimeoutError as exc:
            LOGGER.info("Read timeout")
            raise ReadTimeout() from exc
        return data.decode()

    async def __aiter__(self) -> AsyncIterator[Telegram]:
        while not self.stop_event.is_set():
            data = await self._read()
            self.buffer.append(data)

            for telegram in self.buffer.drain():
                LOGGER.info("Received telegram")
                yield telegram


@asynccontextmanager
async def managed_telegram_streamer(
    host: str, port: int, stop_event: asyncio.Event | None = None
) -> AsyncGenerator[TelegramStreamer, None]:
    LOGGER.info("Opening connection")

    reader, writer = await asyncio.open_connection(host, port)

    LOGGER.info("Opened connection")

    try:
        yield TelegramStreamer(reader, stop_event=stop_event)
    finally:
        LOGGER.info("Closing streamer")

        writer.close()
        await writer.wait_closed()

        LOGGER.info("Closed streamer")
