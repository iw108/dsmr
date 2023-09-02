import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable
from uuid import uuid4

from .telegram import Telegram

LOGGER = logging.getLogger(__name__)


HandlerT = Callable[[Telegram], Awaitable[None]]


async def default_handler(_: Telegram):
    pass


async def worker(
    queue: asyncio.Queue,
    handler: HandlerT,
):
    while True:
        telegram: Telegram = await queue.get()

        telegram_id = uuid4().hex[:6]

        LOGGER.debug("Processing telegram: %s", telegram_id)

        try:
            await handler(telegram)
        except Exception as exc:
            LOGGER.error("Couldn't process telegram", exc_info=exc)

        queue.task_done()

        LOGGER.debug("Processed telegram: %s", telegram_id)


class Consumer:
    def __init__(self, queue: asyncio.Queue):
        self._queue = queue

    def add(self, telegram: Telegram):
        self._queue.put_nowait(telegram)


@asynccontextmanager
async def managed_consumer(
    handler: HandlerT = default_handler,
    *,
    _queue: asyncio.Queue | None = None,
) -> AsyncGenerator[Consumer, None]:
    LOGGER.debug("Starting consumer")

    queue = _queue or asyncio.Queue()
    worker_task = asyncio.create_task(worker(queue, handler))

    LOGGER.debug("Started consumer")

    yield Consumer(queue)

    LOGGER.debug("Stopping consumer.")

    await queue.join()
    worker_task.cancel()

    LOGGER.debug("Stopped consumer.")
