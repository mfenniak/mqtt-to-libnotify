from aiomqtt import Client
from dataclasses import dataclass
from typing import Any, Literal, TYPE_CHECKING
import argparse
import asyncio
import backoff
import importlib
import json
import logging
import os
import socket
import traceback
import types

if TYPE_CHECKING:
    from samplebase import SampleBase

config_obj: object | types.ModuleType = object()
try:
    # use import_module to avoid mypy from finding this file only when running local dev
    config_obj = importlib.import_module("config")
except ModuleNotFoundError:
    pass

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


def get_discovery_topic(config: MqttConfig) -> str:
    return f"{config.discovery_prefix}/switch/{config.discovery_node_id}/{config.discovery_object_id}/config"

def get_state_topic(config: MqttConfig) -> str:
    return f"{config.discovery_prefix}/{config.discovery_node_id}/{config.discovery_object_id}/state"

def get_cmd_topic(config: MqttConfig) -> str:
    return f"{config.discovery_prefix}/{config.discovery_node_id}/{config.discovery_object_id}/cmd"

def get_availability_topic(config: MqttConfig) -> str:
    return f"{config.discovery_prefix}/{config.discovery_node_id}/{config.discovery_object_id}/available"

def get_discovery_payload(config: MqttConfig) -> dict[str, Any]:
    return {
        "name": config.discovery_object_id,
        "unique_id": f"pixelperfectpi_{config.discovery_object_id}",
        "state_topic": get_state_topic(config),
        "command_topic": get_cmd_topic(config),
        "availability_topic": get_availability_topic(config),
        "device": {
            "identifiers": [config.discovery_object_id],
            "name": "pixelperfectpi"
        }
    }

def on_runtime_error(e: Exception) -> bool:
    # give up when we have a RuntimeError because that can include the asyncio event loop shutting down
    return isinstance(e, RuntimeError)

class MqttServer(object):
    def __init__(self, config: MqttConfig, clock: "SampleBase", shutdown_event: asyncio.Event):
        self.config = config
        self.clock = clock
        self.shutdown_event = shutdown_event
        self.status_update_queue: asyncio.Queue[str] = asyncio.Queue()

    def start(self) -> None:
        if self.config.hostname is None:
            return
        asyncio.create_task(self.serve_forever())

    async def serve_forever(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                await self.connect_and_listen_mqtt()
            except Exception as e:
                print("Exception starting up connect_and_listen_mqtt", e)

    @backoff.on_exception(backoff.expo, Exception, giveup=on_runtime_error, raise_on_giveup=False)  # Catch all exceptions
    async def connect_and_listen_mqtt(self) -> None:
        assert self.config.hostname is not None
        client = Client(
            hostname=self.config.hostname,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password
        )
        async with client:
            await self.status_update(self.clock.state)

            try:
                await self.publish_discovery(client)
                await self.publish_availability(client, "online")
                await self.process_messages_forever(client)
            finally:
                try:
                    await self.publish_availability(client, "offline")
                except:
                    # Best effort -- ignore any errors
                    pass

    async def publish_discovery(self, client: Client) -> None:
        if self.config.discovery_prefix is None:
            return
        await client.publish(
            get_discovery_topic(self.config),
            json.dumps(get_discovery_payload(self.config)),
            qos=1, retain=True)

    async def publish_availability(self, client: Client, availability: Literal["online"] | Literal["offline"]) -> None:
        await client.publish(
            get_availability_topic(self.config),
            availability,
            qos=1, retain=True)

    async def process_messages_forever(self, client: Client) -> None:
        async with client.messages() as messages:
            # Subscribe to the topic where we'll receive commands for the switch
            await client.subscribe(get_cmd_topic(self.config))

            # this is correct, but create_task types are wrong? https://github.com/python/typeshed/issues/10185
            messages_next = asyncio.create_task(anext(messages)) # type: ignore
            status_update = asyncio.create_task(self.status_update_queue.get())
            shutdown_wait = asyncio.create_task(self.shutdown_event.wait())

            while not self.shutdown_event.is_set():
                aws = [ messages_next, status_update, shutdown_wait ]
                await asyncio.wait(aws, return_when=asyncio.FIRST_COMPLETED)

                if messages_next.done():
                    cmd = messages_next.result().payload.decode().upper()
                    if cmd == "ON":
                        await self.clock.turn_on()
                    elif cmd == "OFF":
                        await self.clock.turn_off()
                    # this is correct, but create_task types are wrong? https://github.com/python/typeshed/issues/10185
                    messages_next = asyncio.create_task(anext(messages)) # type: ignore

                if status_update.done():
                    status = status_update.result()
                    await client.publish(get_state_topic(self.config), status, qos=1, retain=True)
                    status_update = asyncio.create_task(self.status_update_queue.get())
    
    async def status_update(self, state: Literal["ON"] | Literal["OFF"]) -> None:
        await self.status_update_queue.put(state)


def config_arg_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mqtt-host",
        help="MQTT hostname",
        default=os.environ.get("MQTT_HOST", getattr(config_obj, "MQTT_HOST", None)),
        type=str)
    parser.add_argument("--mqtt-port",
        help="MQTT port",
        default=os.environ.get("MQTT_PORT", getattr(config_obj, "MQTT_PORT", 1883)),
        type=int)
    parser.add_argument("--mqtt-username",
        help="MQTT username",
        default=os.environ.get("MQTT_USERNAME", getattr(config_obj, "MQTT_USERNAME", None)),
        type=str)
    parser.add_argument("--mqtt-password",
        help="MQTT password",
        default=os.environ.get("MQTT_PASSWORD", getattr(config_obj, "MQTT_PASSWORD", None)),
        type=str)
    parser.add_argument(
        "--mqtt-discovery-prefix",
        help="MQTT discovery prefix",
        default=os.environ.get("MQTT_DISCOVERY_PREFIX", getattr(config_obj, "MQTT_DISCOVERY_PREFIX", "homeassistant")),
        type=str)
    parser.add_argument(
        "--mqtt-discovery-node-id",
        help="MQTT discovery node id",
        default=os.environ.get("MQTT_DISCOVERY_NODE_ID", getattr(config_obj, "MQTT_DISCOVERY_NODE_ID", "pixelperfectpi")),
        type=str)
    parser.add_argument(
        "--mqtt-discovery-object-id",
        help="MQTT discovery object id",
        default=os.environ.get("MQTT_DISCOVERY_OBJECT_ID", getattr(config_obj, "MQTT_DISCOVERY_OBJECT_ID", socket.gethostname())),
        type=str)


def get_config(args: argparse.Namespace) -> MqttConfig:
    return MqttConfig(
        hostname=args.mqtt_host,
        port=args.mqtt_port,
        username=args.mqtt_username,
        password=args.mqtt_password,
        discovery_prefix=args.mqtt_discovery_prefix,
        discovery_node_id=args.mqtt_discovery_node_id,
        discovery_object_id=args.mqtt_discovery_object_id,
    )