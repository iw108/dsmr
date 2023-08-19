import asyncio
from contextlib import asynccontextmanager
import signal
from typing import AsyncGenerator, AsyncIterator

from dsmr_parser.clients.telegram_buffer import TelegramBuffer


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
                    yield raw_telegram


def get_cancellation_event() -> asyncio.Event:

    event = asyncio.Event()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, event.set)

    return event


@asynccontextmanager
async def managed_telegram_streamer(
    cancellation_event: asyncio.Event | None = None,
) -> AsyncGenerator[TelegramStreamer, None]:
    
    print("Connecting...")
    reader, writer = await asyncio.open_connection("localhost", 8888)
    _cancellation_event = cancellation_event or get_cancellation_event()

    yield TelegramStreamer(reader, event=_cancellation_event)

    print("Closing connection...")

    writer.close()
    await writer.wait_closed()

    print("connection closed")

