#!/usr/bin/env python
import os
import logging

from mqttwrapper.hbmqtt_backend import run_script

from pytradfri.api.aiocoap_api import APIFactory
from pytradfri import Gateway


GATEWAY_IP = os.environ['GATEWAY_IP']
GATEWAY_ID = os.environ['GATEWAY_ID']
GATEWAY_PSK = os.environ['GATEWAY_PSK']

LIGHT_IDS = os.environ['LIGHT_IDS']
OUTLET_IDS = os.environ['OUTLET_IDS']


async def handle_message(topic: str, payload: bytes, api, lights, outlets):
    device_type, device, attribute = topic.split("/")[1:]
    if device_type == "lighting":
        light = lights[device]
        if topic.endswith("power"):
            await api(light.light_control.set_state(payload == b'1'))
        if topic.endswith("brightness"):
            brightness = max(0, min(254, int(float(payload))))
            # HomeKit ranges from 0–100, so 1% ends up as 2.54 on the MQTT topic
            # Set TRADFRI brightness to 1 in this case.
            if brightness == 2:
                brightness = 1
            await api(light.light_control.set_dimmer(brightness))
    elif device_type == "switch":
        outlet = outlets[device]
        if topic.endswith("power"):
            await api(outlet.socket_control.set_state(payload == b'1'))

async def get_devices(api, gateway, device_ids):
    devices = {}
    for device_id, topic in (x.split(":") for x in device_ids.split(",")):
        devices[topic] = await api(gateway.get_device(device_id))
    return devices

async def setup_tradfri():
    api_factory = APIFactory(host=GATEWAY_IP, psk_id=GATEWAY_ID, psk=GATEWAY_PSK)
    api = api_factory.request
    gateway = Gateway()
    return {
        'api': api,
        'lights': await get_devices(api, gateway, LIGHT_IDS),
        'outlets': await get_devices(api, gateway, OUTLET_IDS),
    }

def get_topics():
    lights = []
    for light in (x.split(":")[1] for x in LIGHT_IDS.split(",")):
        lights.append("control/lighting/{}/power".format(light))
        lights.append("control/lighting/{}/brightness".format(light))
    outlets = []
    for outlet in (x.split(":")[1] for x in OUTLET_IDS.split(",")):
        outlets.append("control/switch/{}/power".format(outlet))
    return lights + outlets

def main():
    formatter = "[%(asctime)s] %(name)s %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)

    run_script(handle_message, topics=get_topics(), context_callback=setup_tradfri)

if __name__ == '__main__':
    main()
