import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable
from uuid import uuid4

LOGGER = logging.getLogger(__name__)


async def default_handler(_: str):
    pass


async def worker(
    queue: asyncio.Queue,
    handler: Callable[[str], Awaitable[None]],
):
    while True:
        telegram: str = await queue.get()

        telegram_id = uuid4().hex[:6]

        LOGGER.debug("Processing telegram: %s", telegram_id)

        try:
            await handler(telegram)
        except Exception as exc:
            LOGGER.error("Couldn't process telegram", exec_info=exc)

        queue.task_done()

        LOGGER.debug("Processed telegram: %s", telegram_id)


class Consumer:
    def __init__(self, queue: asyncio.Queue):
        self._queue = queue

    def add(self, telegram: str):
        self._queue.put_nowait(telegram)


@asynccontextmanager
async def managed_consumer(
    handler: Callable[[str], Awaitable[None]] = default_handler,
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
