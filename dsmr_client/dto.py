from datetime import datetime
from typing import Annotated, Generic, TypeVar
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

DataT = TypeVar("DataT")


class DataPoint(BaseModel, Generic[DataT]):
    value: DataT
    unit: str | None = None


class MbusDataPoint(DataPoint[DataT]):
    timestamp: datetime


def parse_datetime(data: str):
    timezone = ZoneInfo("Europe/Amsterdam")

    naive = datetime.strptime(data[:-1], "%y%m%d%H%M%S")
    aware = naive.replace(tzinfo=timezone)

    return aware


CosemDatetime = Annotated[datetime, BeforeValidator(parse_datetime)]
