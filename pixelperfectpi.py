#!/usr/bin/env python

from samplebase import EMULATED, SampleBase

if EMULATED:
    from RGBMatrixEmulator import RGBMatrix, graphics # type: ignore
else:
    from rgbmatrix import RGBMatrix, graphics # type: ignore
from PIL import Image, ImageColor
import time
import asyncio
import datetime
import pytz
from typing import Set, TypeVar, Any, List
from data.purpleair import PurpleAirDataResolver
from data.envcanada import EnvironmentCanadaDataResolver
from data.calendar import CalendarDataResolver
from data import DataResolver
from draw import Box
from draw.drawpanel import DrawPanel
from draw.multipanelpanel import MultiPanelPanel

from component.time import TimeComponent

T = TypeVar('T')






# TODO List:
# - Add icons - like a lightning bolt for power, or, sun^ sunv for high and low?
# - Animations - don't know where, when, but let's use all the pixels sometimes
# - Add capability for panels to have subpanels, since drawing ops are full panel size
# - Add something with an icon/image -- maybe the weather forecast
# New data:
# - Power: Usage, Solar Generation
# - Home Assistant: Back door / Garage door / etc. Open
# - Google Location: Distance to Mathieu?
# - Home Assistant: Presence
# - Countdown - France Flag & # days to France
# - Errors from any of the other data collectors / displayers
# - anxi - Any errors on Prometheus?


class Clock(SampleBase):
    def __init__(self, data_resolvers: List[DataResolver[T]], time_component: TimeComponent, current_component: MultiPanelPanel, lower_panels: MultiPanelPanel) -> None:
        super().__init__()
        self.data_resolvers = data_resolvers
        self.time_component = time_component
        self.current_component = current_component
        self.lower_panels = lower_panels

    def pre_run(self) -> None:
        self.background_tasks: Set[asyncio.Task[Any]] = set()

    async def create_canvas(self, matrix: RGBMatrix) -> None:
        self.offscreen_canvas = matrix.CreateFrameCanvas()
        self.buffer = Image.new("RGB", (self.offscreen_canvas.width, self.offscreen_canvas.height))

    async def update_data(self) -> None:
        now = time.time()
        for data_resolver in self.data_resolvers:
            task = asyncio.create_task(data_resolver.maybe_refresh(now))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

    async def draw_frame(self, matrix: RGBMatrix) -> None:
        now = time.time()
        self.time_component.draw(self.buffer, now=now, frame=0, data=None) # FIXME: find a way to remove frame/data params
        self.current_component.draw(self.buffer, now=now, frame=0, data=None)
        self.lower_panels.draw(self.buffer, now=now, frame=0, data=None)
        self.offscreen_canvas.SetImage(self.buffer, 0, 0)

        self.offscreen_canvas = matrix.SwapOnVSync(self.offscreen_canvas)
