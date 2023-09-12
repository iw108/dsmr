import asyncio
import logging
from typing import Awaitable, Callable

from .streamer import TelegramStreamer
from .telegram import Telegram

LOGGER = logging.getLogger(__name__)


class Consumer:
    worker_task: asyncio.Task

    def __init__(
        self,
        handler: Callable[[Telegram], Awaitable[None]],
        *,
        _queue: asyncio.Queue[Telegram] | None = None,
    ):
        self.handler = handler
        self.queue = _queue or asyncio.Queue[Telegram](maxsize=20)

    async def _worker(self):
        LOGGER.info("Starting worker")

        while True:
            telegram = await self.queue.get()

            LOGGER.info("Processing telegram: %s", telegram.id)

            try:
                await asyncio.wait_for(self.handler(telegram), 10)
            except Exception as exc:
                LOGGER.error("Couldn't process telegram: %s", telegram.id, exc_info=exc)

            self.queue.task_done()

            LOGGER.info("Processed telegram: %s", telegram.id)

    async def consume_stream(self, stream: TelegramStreamer):
        LOGGER.info("Consuming stream")

        telegram_count = 0

        async for telegram in stream:
            if telegram_count == 0:
                try:
                    self.queue.put_nowait(telegram)
                except asyncio.QueueEmpty:
                    LOGGER.info("Queue full")

            telegram_count = (telegram_count + 1) % 10

    async def __aenter__(self):
        self.worker_task = asyncio.create_task(self._worker())
        return self

    async def __aexit__(self, *_):
        await self.queue.join()
        self.worker_task.cancel()
