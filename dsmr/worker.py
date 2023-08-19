import asyncio
from contextlib import asynccontextmanager

from dsmr_parser import telegram_specifications
from dsmr_parser.parsers import TelegramParser
from dsmr_parser.obis_references import P1_MESSAGE_TIMESTAMP


async def handler(raw_telegram: str):

    parser = TelegramParser(telegram_specifications.V5)
    telegram = parser.parse(raw_telegram)

    telegram[P1_MESSAGE_TIMESTAMP]

    # telegram[GAS_METER_READING]

    assert True


async def worker(queue: asyncio.Queue):
    
    while True:
        telegram: str = await queue.get()

        print("Processing telegram")

        await handler(telegram)
        queue.task_done()

        print("Processed telegram")


class WorkerManager:

    def __init__(self, queue: asyncio.Queue):
        self._queue = queue
    
    def add(self, telegram: str):
        self._queue.put_nowait(telegram)


@asynccontextmanager
async def managed_worker(
    _queue: asyncio.Queue | None = None,
):
    print("Starting worker")

    queue = _queue or asyncio.Queue()
    worker_task = asyncio.create_task(worker(queue))

    print("Started worker")

    yield WorkerManager(queue)

    print("stopping worker")

    await queue.join()
    worker_task.cancel()

    print("Stopped worker")


