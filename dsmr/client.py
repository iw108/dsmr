import asyncio

from .worker import managed_worker
from .streamer import managed_telegram_streamer


async def main():

    async with managed_worker() as worker_manager:
        async with managed_telegram_streamer() as streamer:
            async for raw_telegram in streamer:
                worker_manager.add(raw_telegram)


asyncio.run(main())