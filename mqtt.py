from aiomqtt import Client, Message
from dataclasses import dataclass
from service import Service
import asyncio
import backoff
import logging

logging.getLogger('backoff').addHandler(logging.StreamHandler())

@dataclass
class MqttConfig:
    hostname: str | None # None - mqtt disabled
    port: int
    username: str | None
    password: str | None

    discovery_prefix: str | None  # None - discovery disabled
    discovery_node_id: str | None
    discovery_object_id: str | None

class MqttMessageReceiver:
    async def subscribe_to_topics(self, client: Client) -> None:
        pass
    async def handle_message(self, message: Message) -> bool:
        return False

def on_runtime_error(e: Exception) -> bool:
    # give up when we have a RuntimeError because that can include the asyncio event loop shutting down
    return isinstance(e, RuntimeError)

class MqttServer(Service):
    def __init__(self, config: MqttConfig, shutdown_event: asyncio.Event, other_receivers: list[MqttMessageReceiver]):
        self.config = config
        self.shutdown_event = shutdown_event
        self.status_update_queue: asyncio.Queue[str] = asyncio.Queue()
        self.other_receivers = other_receivers

    async def start(self) -> None:
        print("MqttServer.start", repr(self.config))
        if self.config.hostname is None:
            return
        asyncio.create_task(self.serve_forever())

    async def serve_forever(self) -> None:
        print("MqqServer.serve_forever")
        while not self.shutdown_event.is_set():
            try:
                await self.connect_and_listen_mqtt()
            except Exception as e:
                print("Exception starting up connect_and_listen_mqtt", e)

    @backoff.on_exception(backoff.expo, Exception, giveup=on_runtime_error, raise_on_giveup=False, max_time=300)  # Catch all exceptions
    async def connect_and_listen_mqtt(self) -> None:
        assert self.config.hostname is not None
        client = Client(
            hostname=self.config.hostname,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password
        )
        async with client:
            await self.process_messages_forever(client)

    async def process_messages_forever(self, client: Client) -> None:
        # Subscribe to the topic where we'll receive data from MQTT
        for other_receiver in self.other_receivers:
            await other_receiver.subscribe_to_topics(client)

        # this is correct, but create_task types are wrong? https://github.com/python/typeshed/issues/10185
        messages_next = asyncio.create_task(anext(client.messages)) # type: ignore
        # status_update = asyncio.create_task(self.status_update_queue.get())
        shutdown_wait = asyncio.create_task(self.shutdown_event.wait())

        while not self.shutdown_event.is_set():
            aws = [ messages_next, shutdown_wait ]
            await asyncio.wait(aws, return_when=asyncio.FIRST_COMPLETED)

            if messages_next.done():
                message = messages_next.result()
                for other_receiver in self.other_receivers:
                    try:
                        # if an exception occurrs in handle_message, it will propagate up to here all the way
                        # to the backoff decorator which will reconnect to mqtt -- that's not the right reaction
                        # since it's not an mqtt problem, but rather a software problem.  Should catch and log.
                        if await other_receiver.handle_message(message):
                            break
                    except Exception as e:
                        print("Exception in handle_message", e)
                else:
                    print("Unknown message", message.topic, message.payload)
                # this is correct, but create_task types are wrong? https://github.com/python/typeshed/issues/10185
                messages_next = asyncio.create_task(anext(client.messages)) # type: ignore
