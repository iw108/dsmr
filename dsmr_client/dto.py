from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

DataT = TypeVar("DataT")


class DataPoint(BaseModel, Generic[DataT]):
    value: DataT
    unit: str | None = None


class MbusDataPoint(DataPoint[DataT]):
    timestamp: datetime


def parse_datetime(data: str):
    return datetime.strptime(data[:-1], "%y%m%d%H%M%S")


CosemDatetime = Annotated[datetime, BeforeValidator(parse_datetime)]
