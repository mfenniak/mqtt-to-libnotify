from typing import Any, TypeVar, Generic

T = TypeVar("T")

class NotificationSink(Generic[T]):
    async def notify(self, arg: T) -> None:
        raise NotImplementedError
