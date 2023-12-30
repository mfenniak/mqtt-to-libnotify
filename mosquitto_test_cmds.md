# Subscribe & Observe all MQTT Traffic

```
mosquitto_sub -h $MQTT_HOST -u $MQTT_USERNAME -P $MQTT_PASSWORD -t "#" -v
```

# Send test door state

```
mosquitto_pub -h $MQTT_HOST -u $MQTT_USERNAME -P $MQTT_PASSWORD \
    -t "homeassistant/output/door/garage_door" \
    --retain \
    -m "{ \"timestamp\": \"$(date +"%Y-%m-%d %H:%M:%S.%6N%:z")\", \"state\": \"open\" }"
```

```
mosquitto_pub -h $MQTT_HOST -u $MQTT_USERNAME -P $MQTT_PASSWORD \
    -t "homeassistant/output/door/garage_door" \
    --retain \
    -m "{ \"timestamp\": \"$(date +"%Y-%m-%d %H:%M:%S.%6N%:z")\", \"state\": \"closed\" }"
```

## Left open a long time

```
mosquitto_pub -h $MQTT_HOST -u $MQTT_USERNAME -P $MQTT_PASSWORD \
    -t "homeassistant/output/door/garage_door" \
    --retain \
    -m "{ \"timestamp\": \"2020-01-01 01:01:01.000-00:00\", \"state\": \"open\" }"
```
