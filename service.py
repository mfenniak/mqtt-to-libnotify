from typing import Literal

class Service(object):
    def __init__(self) -> None:
        pass

    async def status_update(self, state: Literal["ON"] | Literal["OFF"]) -> None:
        pass

    async def start(self) -> None:
        pass
