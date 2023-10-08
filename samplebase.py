cpuinfo = open("/proc/cpuinfo").read()
if "Raspberry Pi" in cpuinfo:
    EMULATED = False
else:
    EMULATED = True
    print("Emulating RGB matrix...")

import argparse
import asyncio
import importlib
import mqtt
import pytz
import sys
import types
from typing import Literal, Any

config_obj: object | types.ModuleType = object()
try:
    # use import_module to avoid mypy from finding this file only when running local dev
    config_obj = importlib.import_module("config")
except ModuleNotFoundError:
    pass

if EMULATED:
    from RGBMatrixEmulator import RGBMatrix # type: ignore
else:
    from rgbmatrix import RGBMatrix # type: ignore
from rgbmatrix import RGBMatrixOptions
from dependency_injector.providers import Provider


class SampleBase(object):
    def __init__(self, rgbmatrix_provider: Provider[RGBMatrix]) -> None:
        self.rgbmatrix_provider = rgbmatrix_provider

        self.state: Literal["ON"] | Literal["OFF"] = "ON"
        self.turn_on_event: asyncio.Event | None = None
        self.shutdown_event = asyncio.Event()
        self.matrix: RGBMatrix | None = None

    async def run(self) -> None:
        raise NotImplemented

    async def turn_on(self) -> None:
        if self.state == "ON":
            return
        assert self.turn_on_event is not None
        self.state = "ON"
        self.turn_on_event.set()
        # await self.mqtt.status_update(self.state)

    async def turn_off(self) -> None:
        if self.state == "OFF":
            return
        assert self.turn_on_event is None
        self.turn_on_event = asyncio.Event()
        self.state = "OFF"
        # await self.mqtt.status_update(self.state)

    def process(self) -> None:
        # mqtt_config = mqtt.get_config(self.args)
        # self.mqtt = mqtt.MqttServer(mqtt_config, self, self.shutdown_event)

        self.matrix = None
        try:
            # Start loop
            print("Press CTRL-C to stop sample")
            asyncio.run(self.async_run())
        except KeyboardInterrupt:
            self.shutdown_event.set()
            print("Exiting\n")
            sys.exit(0)

    def pre_run(self) -> None:
        raise NotImplemented

    async def update_data(self) -> None:
        raise NotImplemented

    async def create_canvas(self, matrix: RGBMatrix) -> None:
        raise NotImplemented

    async def draw_frame(self, matrix: RGBMatrix) -> None:
        raise NotImplemented

    async def async_run(self) -> None:
        # self.mqtt.start()
        self.pre_run()
        await self.main_loop()

    async def main_loop(self) -> None:
        while True:
            await self.update_data()

            if self.state == "OFF":
                if self.matrix is not None:
                    self.matrix.Clear()
                    del self.matrix
                    self.matrix = None

                # Wake when we're turned on...
                assert self.turn_on_event is not None
                turn_on_event_task = asyncio.create_task(self.turn_on_event.wait())
                # Wake after a bit just to do an update_data call...
                sleep_task = asyncio.create_task(asyncio.sleep(120))
                # Wait until either wake condition; doesn't matter which.
                await asyncio.wait([ turn_on_event_task, sleep_task ], return_when=asyncio.FIRST_COMPLETED)

            elif self.state == "ON":
                if self.matrix is None:
                    # self.matrix = RGBMatrix(options = self.rgbmatrixoptions)
                    # print("rgbmatrixoptions", repr(self.rgbmatrixoptions))
                    self.matrix = self.rgbmatrix_provider()
                    await self.create_canvas(self.matrix)

                await self.draw_frame(self.matrix)
                await asyncio.sleep(0.1)
