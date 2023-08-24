from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from dsmr_parser import telegram_specifications
from dsmr_parser.obis_references import CURRENT_ELECTRICITY_USAGE, P1_MESSAGE_TIMESTAMP
from dsmr_parser.objects import CosemObject
from dsmr_parser.parsers import Telegram, TelegramParser
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api_async import WriteApiAsync

from .consumer import Consumer, managed_consumer
from .settings import Settings


class InfluxHandler:
    def __init__(
        self,
        write_api: WriteApiAsync,
        bucket: str,
    ):
        self.write_api = write_api
        self.bucket = bucket

    async def __call__(self, telegram: str) -> None:
        parser = TelegramParser(telegram_specifications.V5)
        telegram = parser.parse(telegram)

        output = self._map_telegram(telegram)

        await self.write_api.write(self.bucket, record=output)

    @staticmethod
    def _map_telegram(telegram: Telegram) -> dict:
        data = {"measurement": "dsmr"}

        timestamp = telegram[P1_MESSAGE_TIMESTAMP]
        if isinstance(timestamp, CosemObject) and isinstance(timestamp.value, datetime):
            data["time"] = timestamp.value.isoformat()

        electricity_usage = telegram[CURRENT_ELECTRICITY_USAGE]
        if isinstance(electricity_usage, CosemObject):
            data["fields"] = {
                "electricity_usage": float(electricity_usage.value),
            }

        return data


@asynccontextmanager
async def managed_influxdb_consumer(
    settings: Settings,
) -> AsyncGenerator[Consumer, None]:
    influxdb_client = InfluxDBClientAsync(
        url=str(settings.INFLUXDB_URL),
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG,
    )

    async with influxdb_client:
        handler = InfluxHandler(
            influxdb_client.write_api(),
            settings.INFLUXDB_BUCKET,
        )

        async with managed_consumer(handler) as worker_manager:
            yield worker_manager
