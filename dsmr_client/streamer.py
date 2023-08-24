import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator

from dsmr_parser.clients.telegram_buffer import TelegramBuffer

LOGGER = logging.getLogger(__name__)


class TelegramStreamer:
    BUFFER_SIZE = 256

    def __init__(
        self,
        reader: asyncio.StreamReader,
        *,
        event: asyncio.Event | None = None,
        _buffer: TelegramBuffer | None = None
    ):
        self.reader = reader
        self.event = event or asyncio.Event()
        self.buffer = _buffer or TelegramBuffer()

    async def _waiter(self) -> None:
        await self.event.wait()

    async def _read(self) -> str:
        data = await self.reader.read(self.BUFFER_SIZE)
        return data.decode()

    async def __aiter__(self) -> AsyncIterator[str]:
        while not self.event.is_set():
            read_task = asyncio.create_task(self._read())
            waiter_task = asyncio.create_task(self._waiter())

            done, _ = await asyncio.wait(
                (read_task, waiter_task),
                return_when=asyncio.FIRST_COMPLETED,
            )

            if read_task in done:
                self.buffer.append(read_task.result())
                for raw_telegram in self.buffer.get_all():
                    LOGGER.debug("Received telegram")
                    yield raw_telegram


def get_cancellation_event() -> asyncio.Event:
    event = asyncio.Event()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, event.set)

    return event


@asynccontextmanager
async def managed_telegram_streamer(
    host: str,
    port: int,
    _cancellation_event: asyncio.Event | None = None,
) -> AsyncGenerator[TelegramStreamer, None]:
    LOGGER.debug("Opening connection")

    reader, writer = await asyncio.open_connection(host, port)

    LOGGER.debug("Opened connection")

    cancellation_event = _cancellation_event or get_cancellation_event()

    yield TelegramStreamer(reader, event=cancellation_event)

    LOGGER.debug("Closing streamer")

    writer.close()
    await writer.wait_closed()

    LOGGER.debug("Closing streamer")
