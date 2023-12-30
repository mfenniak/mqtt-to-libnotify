from aiomqtt import Client, Message
from dataclasses import dataclass
from enum import Enum, auto
from mqtt import MqttMessageReceiver
from typing import Literal
import datetime
import json
import pytz

class DoorStatus(Enum):
    UNKNOWN = auto()
    OPEN = auto()
    CLOSED = auto()

@dataclass
class DoorInformation:
    status: DoorStatus
    status_since: datetime.datetime

class DoorDataResolver(MqttMessageReceiver):
    def __init__(self, topic: str) -> None:
        self.data = DoorInformation(
            status=DoorStatus.UNKNOWN,
            status_since=datetime.datetime.now(pytz.utc)
        )
        self.topic = topic

    async def subscribe_to_topics(self, client: Client) -> None:
        await client.subscribe(self.topic)

    async def handle_message(self, message: Message) -> bool:
        if str(message.topic) != self.topic:
            return False
        if not isinstance(message.payload, bytes):
            return False

        assert self.data is not None

        payload = json.loads(message.payload)
        timestamp = datetime.datetime.strptime(payload.get("timestamp"), '%Y-%m-%d %H:%M:%S.%f%z')
        state: Literal["closed"] | Literal["open"] = payload.get("state")

        match state:
            case "closed":
                door_status = DoorStatus.CLOSED
            case "open":
                door_status = DoorStatus.OPEN
            case _:
                door_status = DoorStatus.UNKNOWN
        
        self.data = DoorInformation(status=door_status, status_since=timestamp)

        # If the status wasn't updated recently, then it's probably a persistent message received after a restart
        # so we should ignore it
        if self.data.status_since < datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=1):
            print("Ignoring message because it's too old")
            return True

        # FIXME: Send the notification here        
        print("Door status updated to", self.data.status, "at", self.data.status_since)

        return True
