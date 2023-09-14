import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, AsyncIterator

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
        _buffer: TelegramBuffer | None = None,
    ):
        self.reader = reader
        self.options = streamer_options or StreamerOptions()
        self.buffer = _buffer or TelegramBuffer()

        self._is_streaming: bool = True

    async def _read(self) -> str:
        try:
            data = await asyncio.wait_for(
                self.reader.read(self.options.buffer_size),
                self.options.read_timeout,
            )
        except asyncio.TimeoutError as exc:
            LOGGER.info("Read timeout")
            raise ReadTimeout() from exc
        return data.decode()

    async def __aiter__(self) -> AsyncIterator[Telegram]:
        while self._is_streaming:
            data = await self._read()
            self.buffer.append(data)

            for telegram in self.buffer.get_all():
                LOGGER.debug("Received telegram")
                yield telegram

    def stop(self):
        self._is_streaming = False


@asynccontextmanager
async def managed_telegram_streamer(
    host: str,
    port: int,
) -> AsyncGenerator[TelegramStreamer, None]:
    LOGGER.debug("Opening connection")

    reader, writer = await asyncio.open_connection(host, port)

    LOGGER.info("Opened connection")

    try:
        yield TelegramStreamer(reader)
    finally:
        LOGGER.info("Closing streamer")

        writer.close()
        await writer.wait_closed()

        LOGGER.info("Closed streamer")
