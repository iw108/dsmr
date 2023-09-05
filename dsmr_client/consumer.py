import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

from .telegram import Telegram

LOGGER = logging.getLogger(__name__)


HandlerT = Callable[[Telegram], Awaitable[None]]


async def default_handler(_: Telegram):
    pass


async def worker(
    queue: asyncio.Queue[Telegram],
    handler: HandlerT,
):
    while True:
        telegram = await queue.get()

        LOGGER.debug("Processing telegram: %s", telegram.id)

        try:
            await handler(telegram)
        except Exception as exc:
            LOGGER.error("Couldn't process telegram", exc_info=exc)

        queue.task_done()

        LOGGER.debug("Processed telegram: %s", telegram.id)


class ConsumerQueue:
    def __init__(self, queue: asyncio.Queue[Telegram]):
        self._queue = queue

    def add(self, telegram: Telegram):
        self._queue.put_nowait(telegram)


@asynccontextmanager
async def managed_consumer(
    handler: HandlerT = default_handler,
    *,
    _queue: asyncio.Queue[Telegram] | None = None,
) -> AsyncGenerator[ConsumerQueue, None]:
    LOGGER.debug("Starting consumer")

    queue = _queue or asyncio.Queue[Telegram]()
    worker_task = asyncio.create_task(worker(queue, handler))

    LOGGER.debug("Started consumer")

    yield ConsumerQueue(queue)

    LOGGER.debug("Stopping consumer.")

    await queue.join()
    worker_task.cancel()

    LOGGER.debug("Stopped consumer.")
