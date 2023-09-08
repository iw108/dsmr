from enum import StrEnum


class ObisCode(StrEnum):
    """Enum definifing OBIS codes."""

    P1_MESSAGE_TIMESTAMP = "\d-\d:1\.0\.0"

    CURRENT_ELECTRICITY_USAGE = "\d-\d:1\.7\.0"
    ELECTRICITY_USED_TARIFF_1 = "\d-\d:1\.8\.1"
    ELECTRICITY_USED_TARIFF_2 = "\d-\d:1\.8\.2"
    ELECTRICITY_ACTIVE_TARIFF = "\d-\d:96\.14\.0"

    HOURLY_GAS_METER_READING = "\d-\d:24\.2\.1"
