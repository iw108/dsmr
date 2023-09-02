import re
from dataclasses import dataclass
from typing import Generator, Type

from .dto import CosemDatetime, DataPoint, DataT, MbusDataPoint
from .obis import ObisCode


@dataclass(frozen=True)
class _RawDataPoint:
    value: str
    unit: str | None


@dataclass(frozen=True, kw_only=True)
class _TelegramEntry:
    id: str
    data: str

    def get_raw_data_points(self) -> Generator[_RawDataPoint, None, None]:
        for item in map(str, re.findall(r"\((.+?)\)", self.data)):
            try:
                value, unit = item.split("*")
            except ValueError:
                value, unit = item, None

            yield _RawDataPoint(value, unit)


class Telegram:
    def __init__(self, data: str):
        self._data = data

    def _get_entry(
        self,
        obis_code: ObisCode,
    ) -> _TelegramEntry:
        obis_regex = rf"^(?P<id>{obis_code})(?P<data>.+?)\r$"

        if res := re.search(obis_regex, self._data, re.MULTILINE):
            return _TelegramEntry(**res.groupdict())

        raise ValueError("Not present")

    def get_data_point(
        self,
        obis_code: ObisCode,
        target_cls: Type[DataPoint[DataT]],
    ) -> DataPoint[DataT]:
        entry = self._get_entry(obis_code)

        raw_data_point = next(entry.get_raw_data_points())

        return target_cls(**raw_data_point.__dict__)

    def get_mbus_data_point(
        self,
        obis_code: ObisCode,
        target_cls: Type[MbusDataPoint[DataT]],
    ) -> Generator[MbusDataPoint[DataT], None, None]:
        entry = self._get_entry(obis_code)

        raw_data_points = list(entry.get_raw_data_points())
        for index in range(0, len(raw_data_points), 2):
            raw_timestamp, raw_data_point = raw_data_points[index : index + 2]

            timepstamp = DataPoint[CosemDatetime](**raw_timestamp.__dict__)

            yield target_cls(
                timestamp=timepstamp.value,
                **raw_data_point.__dict__,
            )
