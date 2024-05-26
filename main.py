#!/usr/bin/env python

from config import Config, NotifySendConfig, MqttConfig
from di import Container
from mainservice import MainService
import os

def main(main_service: MainService) -> None:
    main_service.process()

# Main function
if __name__ == "__main__":
    config = Config(
        notifysend=NotifySendConfig(
            path=os.environ["NOTIFY_SEND_CMD"]
        ),
        icon_path=os.environ.get("ICON_PATH", "./icons/"),
        mqtt=MqttConfig(
            hostname=os.environ["MQTT_HOST"],
            port=int(os.environ.get("MQTT_PORT", 1883)),
            username=os.environ["MQTT_USERNAME"],
            password=os.environ["MQTT_PASSWORD"],
        ),
    )
    main_service = Container(config=config).main_service
    main(main_service)
