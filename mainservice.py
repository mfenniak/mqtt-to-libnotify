from typing import List
import asyncio
from service import Service

class MainService(object):
    def __init__(self, shutdown_event: asyncio.Event, services: List[Service]) -> None:
        self.services = services
        self.shutdown_event = shutdown_event

    def process(self) -> None:
        try:
            # Start loop
            print("Press CTRL-C to terminate")
            asyncio.run(self.async_run())
        except KeyboardInterrupt:
            self.shutdown_event.set()
            return

    async def async_run(self) -> None:
        for service in self.services:
            await service.start()
        await self.main_loop()

    async def main_loop(self) -> None:
        while self.shutdown_event.is_set() is False:
            # FIXME: Not really sure what to do as a "main loop"; should this even exist?
            await asyncio.sleep(3600)
