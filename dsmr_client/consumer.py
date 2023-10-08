import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

from .streamer import TelegramStreamer
from .telegram import Telegram

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ConsumerOptions:
    queue_size: int = 20
    handler_timeout: float = 10.0


class Consumer:
    worker_task: asyncio.Task

    def __init__(
        self,
        handler: Callable[[Telegram], Awaitable[None]],
        *,
        consumer_options: ConsumerOptions | None = None,
        _queue: asyncio.Queue[Telegram] | None = None,
    ):
        self.handler = handler
        self.options = consumer_options or ConsumerOptions()

        self.queue = _queue or asyncio.Queue[Telegram](maxsize=self.options.queue_size)

    async def _worker(self, event: asyncio.Event):
        LOGGER.info("Starting worker")

        event.set()

        while True:
            telegram = await self.queue.get()

            LOGGER.debug("Processing telegram: %s", telegram.id)

            try:
                await asyncio.wait_for(
                    self.handler(telegram),
                    self.options.handler_timeout,
                )
            except Exception as exc:
                LOGGER.error("Couldn't process telegram: %s", telegram.id, exc_info=exc)

            self.queue.task_done()

            LOGGER.debug("Processed telegram: %s", telegram.id)

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
        LOGGER.info("Entering consumer")

        worker_ready = asyncio.Event()
        self.worker_task = asyncio.create_task(self._worker(worker_ready))

        await worker_ready.wait()

        return self

    async def __aexit__(self, *_):
        LOGGER.info("Exiting consumer")
        await self.queue.join()
        self.worker_task.cancel()
