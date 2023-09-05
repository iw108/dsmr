from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Protocol, Type

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api_async import WriteApiAsync
from pydantic import AnyHttpUrl

from .consumer import ConsumerQueue, managed_consumer
from .dto import CosemDatetime, DataPoint
from .obis import ObisCode
from .telegram import Telegram


class InfluxDBConfig(Protocol):
    INFLUXDB_URL: AnyHttpUrl
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str


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


class InfluxDBHandler(AbstractHandler):
    async def __call__(self, telegram: Telegram) -> None:
        
        timestamp = telegram.get_data_point(
            ObisCode.P1_MESSAGE_TIMESTAMP,
            DataPoint[CosemDatetime],
        )

        energy_usage = telegram.get_data_point(
            ObisCode.CURRENT_ELECTRICITY_USAGE,
            DataPoint[float],
        )

        data = {
            "measurement": "dsmr",
            "tags": {"unit": energy_usage.unit},
            "fields": {"current_energy_usage": energy_usage.value},
            "time": timestamp.value.isoformat(),
        }

        self.write_api.wri

        await self.write_api.write(self.bucket, record=data)


@asynccontextmanager
async def managed_influxdb_consumer(
    config: InfluxDBConfig,
    *,
    _handler_cls: Type[AbstractHandler] = InfluxDBHandler,
) -> AsyncGenerator[ConsumerQueue, None]:
    influxdb_client = InfluxDBClientAsync(
        url=str(config.INFLUXDB_URL),
        token=config.INFLUXDB_TOKEN,
        org=config.INFLUXDB_ORG,
    )

    async with influxdb_client:
        handler = _handler_cls(
            influxdb_client.write_api(),
            config.INFLUXDB_BUCKET,
        )

        async with managed_consumer(handler) as worker_manager:
            yield worker_manager
