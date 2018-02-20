#!/usr/bin/env python
import os

from mqttwrapper.hbmqtt_backend import run_script

from pytradfri.api.aiocoap_api import APIFactory
from pytradfri import Gateway


GATEWAY_IP = os.environ['GATEWAY_IP']
GATEWAY_ID = os.environ['GATEWAY_ID']
GATEWAY_PSK = os.environ['GATEWAY_PSK']
LIGHT_ID = int(os.environ['LIGHT_ID'])


async def handle_message(topic: str, payload: bytes, api, light):
    if topic.endswith("power"):
        await api(light.light_control.set_state(payload == b'1'))
    if topic.endswith("brightness"):
        brightness = max(0, min(254, int(float(payload))))
        # HomeKit ranges from 0–100, so 1% ends up as 2.54 on the MQTT topic
        # Set TRADFRI brightness to 1 in this case.
        if brightness == 2:
            brightness = 1
        await api(light.light_control.set_dimmer(brightness))


async def setup_tradfri():
    api_factory = APIFactory(host=GATEWAY_IP, psk_id=GATEWAY_ID, psk=GATEWAY_PSK)
    api = api_factory.request
    gateway = Gateway()
    light = await api(gateway.get_device(LIGHT_ID))
    return {
        'api': api,
        'light': light,
    }


def main():
    run_script(handle_message, context_callback=setup_tradfri)


if __name__ == '__main__':
    main()
