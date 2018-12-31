# tradfri-mqtt

Whilst the TRÅDFRI gateway allows you to pair Hue bulbs, for some reason it won't
expose them to HomeKit. Additionally control outlets aren't yet available in HomeKit.

This script is a little bridge between the TRÅDFRI gateway and an MQTT broker
that uses topics/payloads compatible with [homekit2mqtt](https://github.com/hobbyquaker/homekit2mqtt)
so your Hue bulbs and control outlets can appear in HomeKit.
