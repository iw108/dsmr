from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Type

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api_async import WriteApiAsync

from .consumer import Consumer, managed_consumer
from .dto import CosemDatetime, DataPoint, MbusDataPoint
from .obis import ObisCode
from .settings import Settings
from .telegram import Telegram


class AbstractHandler(ABC):
    def __init__(
        self,
        write_api: WriteApiAsync,
        bucket: str,
    ):
        self.write_api = write_api
        self.bucket = bucket

    @abstractmethod
    async def __call__(self, telegram: Telegram) -> None:
        """Handle call."""


class InfluxHandler(AbstractHandler):
    async def __call__(self, telegram: Telegram) -> None:
        _ = telegram.get_data_point(
            ObisCode.P1_MESSAGE_TIMESTAMP,
            DataPoint[CosemDatetime],
        )

        energy_usage = next(
            telegram.get_mbus_data_point(
                ObisCode.CURRENT_ELECTRICITY_USAGE,
                MbusDataPoint[float],
            )
        )

        # print(energy_usage)


@asynccontextmanager
async def managed_influxdb_consumer(
    settings: Settings,
    *,
    _handler_cls: Type[AbstractHandler] = InfluxHandler,
) -> AsyncGenerator[Consumer, None]:
    influxdb_client = InfluxDBClientAsync(
        url=str(settings.INFLUXDB_URL),
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG,
    )

    async with influxdb_client:
        handler = _handler_cls(
            influxdb_client.write_api(),
            settings.INFLUXDB_BUCKET,
        )

        async with managed_consumer(handler) as worker_manager:
            yield worker_manager
