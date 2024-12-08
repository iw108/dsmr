import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

TELEGRAM = (
    "/ISK5\\2M550T-1012\r\n"
    "\r\n"
    "1-3:0.2.8(50)\r\n"
    "0-0:1.0.0({timestamp})\r\n"
    "0-0:96.1.1(4530303434303037303638383233393138)\r\n"
    "1-0:1.8.1(005692.236*kWh)\r\n"
    "1-0:1.8.2(006067.531*kWh)\r\n"
    "1-0:2.8.1(000000.000*kWh)\r\n"
    "1-0:2.8.2(000000.000*kWh)\r\n"
    "0-0:96.14.0(0002)\r\n"
    "1-0:1.7.0(00.213*kW)\r\n"
    "1-0:2.7.0(00.000*kW)\r\n"
    "0-0:96.7.21(00007)\r\n"
    "0-0:96.7.9(00018)\r\n"
    "1-0:32.32.0(01517)\r\n"
    "1-0:52.32.0(00004)\r\n"
    "1-0:72.32.0(00106)\r\n"
    "1-0:32.36.0(00001)\r\n"
    "1-0:52.36.0(00002)\r\n"
    "1-0:72.36.0(00146)\r\n"
    "0-0:96.13.0()\r\n"
    "1-0:32.7.0(236.3*V)\r\n"
    "1-0:52.7.0(235.1*V)\r\n"
    "1-0:72.7.0(236.1*V)\r\n"
    "1-0:31.7.0(000*A)\r\n"
    "1-0:51.7.0(000*A)\r\n"
    "1-0:71.7.0(000*A)\r\n"
    "1-0:21.7.0(00.000*kW)\r\n"
    "1-0:41.7.0(00.116*kW)\r\n"
    "1-0:61.7.0(00.096*kW)\r\n"
    "1-0:22.7.0(00.000*kW)\r\n"
    "1-0:42.7.0(00.000*kW)\r\n"
    "1-0:62.7.0(00.000*kW)\r\n"
    "0-1:24.1.0(003)\r\n"
    "0-1:96.1.0(4730303333353935393032313731363138)\r\n"
    "0-1:24.2.1({timestamp})(05663.731*m3)\r\n"
    "!E652\r\n"
)


class TelegramGenerator:
    def __init__(self, zone_info: ZoneInfo):
        self.zone_info = zone_info

    def __call__(self) -> bytes:
        now = datetime.now(tz=self.zone_info)

        return TELEGRAM.format(timestamp=now.strftime("%y%m%d%H%M%SS")).encode()


async def connection_callback(
    _: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
):
    print("Connection made...")

    telegram_generator = TelegramGenerator(zone_info=ZoneInfo("Europe/Amsterdam"))

    try:
        while True:
            telegram = telegram_generator()
            for index in range(0, len(telegram), 256):
                writer.write(telegram[index : index + 256])
                await writer.drain()
            await asyncio.sleep(1)
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        connection_callback,
        port=8888,
    )

    async with server:
        print("Server started.")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
