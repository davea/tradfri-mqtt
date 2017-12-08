#!/usr/bin/env python
import os
import asyncio
from random import randint

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0

from pytradfri.api.aiocoap_api import APIFactory
from pytradfri import Gateway

GATEWAY_IP = os.environ['GATEWAY_IP']
GATEWAY_ID = os.environ['GATEWAY_ID']
GATEWAY_PSK = os.environ['GATEWAY_PSK']

LIGHT_ID = int(os.environ['LIGHT_ID'])

MQTT_TOPICS = os.environ['MQTT_TOPICS'].split(",")
MQTT_BROKER = os.environ['MQTT_BROKER']

api, light = None, None


async def mqtt_loop():
    topics = [(topic, QOS_0) for topic in MQTT_TOPICS]
    client = MQTTClient()
    await client.connect(MQTT_BROKER)
    await client.subscribe(topics)
    try:
        while True:
            message = await client.deliver_message()
            packet = message.publish_packet
            topic = packet.variable_header.topic_name
            payload = bytes(packet.payload.data)
            await handle_message(topic, payload)
        await client.unsubscribe(topics)
        await client.disconnect()
    except ClientException:
        raise


async def handle_message(topic: str, payload: bytes):
    if topic.endswith("power"):
        await api(light.light_control.set_state(payload == b'1'))
    if topic.endswith("brightness"):
        brightness = max(0, min(254, int(float(payload))))
        # HomeKit ranges from 0–100, so 1% ends up as 2.54 on the MQTT topic
        # Set TRADFRI brightness to 1 in this case.
        if brightness == 2:
            brightness = 1
        await api(light.light_control.set_dimmer(brightness))
    print(payload)


async def setup_tradfri():
    global api, light
    api_factory = APIFactory(host=GATEWAY_IP, psk_id=GATEWAY_ID, psk=GATEWAY_PSK)
    api = api_factory.request
    gateway = Gateway()
    light = await api(gateway.get_device(LIGHT_ID))


async def main_loop():
    await setup_tradfri()
    await mqtt_loop()


def main():
    asyncio.get_event_loop().run_until_complete(main_loop())


if __name__ == '__main__':
    main()
