#!/usr/bin/env python

from dependency_injector.wiring import Provide, inject
from di import Container
from mainservice import MainService

@inject
def main(main_service: MainService = Provide[Container.main_service]) -> None:
    main_service.process()

# Main function
if __name__ == "__main__":
    container = Container()

    container.config.notifysend.path.from_env("NOTIFY_SEND_CMD", as_=str)
    container.config.icon_path.from_env("ICON_PATH", as_=str, default="./icons/")
    container.config.mqtt.hostname.from_env("MQTT_HOST")
    container.config.mqtt.port.from_env("MQTT_PORT", as_=int, default=1883)
    container.config.mqtt.username.from_env("MQTT_USERNAME", as_=str)
    container.config.mqtt.password.from_env("MQTT_PASSWORD", as_=str)

    container.wire(modules=[__name__])
    main()
    container.shutdown_resources()
