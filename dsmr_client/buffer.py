import re
from typing import Generator

from .telegram import Telegram


class TelegramBuffer:
    _FIND_TELEGRAMS_REGEX = r"\/[^\/]+?\![A-F0-9]{0,4}\0?\r\n"

    def __init__(self, *, _buffer: str | None = None):
        self._buffer = _buffer or ""

        self._regex_pattern = re.compile(self._FIND_TELEGRAMS_REGEX, re.DOTALL)

    def get_all(self) -> Generator[Telegram, None, None]:
        for telegram in self._regex_pattern.findall(self._buffer):
            self._remove(telegram)
            yield Telegram(telegram)

    def append(self, data: str):
        self._buffer += data

    def _remove(self, telegram: str):
        # Remove data leading up to the telegram and the telegram itself.
        index = self._buffer.index(telegram) + len(telegram)

        self._buffer = self._buffer[index:]
