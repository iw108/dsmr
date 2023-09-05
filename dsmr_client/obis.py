from enum import StrEnum


class ObisCode(StrEnum):
    P1_MESSAGE_TIMESTAMP = "\d-\d:1\.0\.0"
    CURRENT_ELECTRICITY_USAGE = "\d-\d:1\.7\.0"
    HOURLY_GAS_METER_READING = "\d-\d:24\.2\.1"
    ELECTRICITY_USED_TARIFF_1 = "\d-\d:1\.8\.1"
    ELECTRICITY_USED_TARIFF_2 = "\d-\d:1\.8\.2"
