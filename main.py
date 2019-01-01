#!/usr/bin/env python
import os
import logging
import asyncio

from mqttwrapper import run_script

from pytradfri.api.aiocoap_api import APIFactory
from pytradfri import Gateway


GATEWAY_IP = os.environ['GATEWAY_IP']
GATEWAY_ID = os.environ['GATEWAY_ID']
GATEWAY_PSK = os.environ['GATEWAY_PSK']

LIGHT_IDS = os.environ['LIGHT_IDS']
OUTLET_IDS = os.environ['OUTLET_IDS']


def handle_message(topic: str, payload: bytes, lights, outlets):
    device_type, device, attribute = topic.split("/")[1:]
    device_id = lights[device] if device_type == "lighting" else outlets[device]

    if attribute == "power":
        value = payload == b'1'
    elif attribute == "brightness":
        value = max(0, min(254, int(float(payload))))

    if device_type == "switch":
        asyncio.run(tradfri_set_outlet_state(device_id, value))
    elif device_type == "lighting" and attribute == "power":
        asyncio.run(tradfri_set_light_state(device_id, value))
    elif device_type == "lighting" and attribute == "brightness":
        asyncio.run(tradfri_set_light_dimmer(device_id, value))


async def tradfri_get_api_device(device_id):
    api_factory = APIFactory(host=GATEWAY_IP, psk_id=GATEWAY_ID, psk=GATEWAY_PSK)
    api = api_factory.request
    gateway = Gateway()
    device = await api(gateway.get_device(device_id))
    return api, device


async def tradfri_set_outlet_state(device_id, value):
    api, device = await tradfri_get_api_device(device_id)
    await api(device.socket_control.set_state(value))


async def tradfri_set_light_state(device_id, value):
    api, device = await tradfri_get_api_device(device_id)
    await api(device.light_control.set_state(value))


async def tradfri_set_light_dimmer(device_id, value):
    api, device = await tradfri_get_api_device(device_id)
    await api(device.light_control.set_dimmer(value))


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

    lights = {name: device_id for device_id, name in (i.split(":") for i in LIGHT_IDS.split(","))}
    outlets = {name: device_id for device_id, name in (i.split(":") for i in OUTLET_IDS.split(","))}

    run_script(handle_message, topics=get_topics(), lights=lights, outlets=outlets)


if __name__ == '__main__':
    main()
