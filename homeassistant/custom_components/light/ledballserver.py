import logging

import voluptuous as vol
import http.client
import json

# Import the device class from the component that you want to support
from homeassistant.components.light import (ATTR_BRIGHTNESS, ATTR_RGB_COLOR,
                                            SUPPORT_BRIGHTNESS, SUPPORT_RGB_COLOR,
                                            Light, PLATFORM_SCHEMA)
from homeassistant.const import CONF_HOSTS
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOSTS): vol.All(cv.ensure_list, [cv.string]),
})

SUPPORT_LEDBALL = (SUPPORT_BRIGHTNESS | SUPPORT_RGB_COLOR )
BYTE_MAX = 255

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the LED Ball Server platform."""

    hosts = config.get(CONF_HOSTS)

    _LOGGER.info("Setting up..")

    if hosts:
        # Support retro compatibility with comma separated list of hosts
        # from config
        hosts = hosts[0] if len(hosts) == 1 else hosts
        hosts = hosts.split(',') if isinstance(hosts, str) else hosts
        led_ball_lights = []
        counter = 0
        _LOGGER.info("Found %s hosts", len(hosts))

        for host in hosts:
            _LOGGER.info("Added host %s", host)
            led_ball_lights.append(LedBallLight(host, counter))
            counter = counter + 1

        add_devices(led_ball_lights)

class LedBallLight(Light):
    """Representation of an LED Ball Light."""

    def __init__(self, host, id):
        """Initialize an LED Ball Light."""
        self._host = host
        self._id = id
        self._name = "LED Ball Light " + str(id)
        self._state = False
        self._brightness = None
        red = int(1 * BYTE_MAX)
        green = 0
        blue = 0
        self._rgb = [red, green, blue]

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_LEDBALL

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the Brightness of the Bulb"""
        return self._brightness

    @property
    def rgb_color(self):
        return self._rgb

    @property
    def is_on(self):
        """Return true if light is on."""
        _LOGGER.debug("is_on %s", self._state)
        return self._state

    def send_command(self, command):
        _LOGGER.debug("host %s: CMD: %s", self._name, command)
        conn = http.client.HTTPConnection(self._host)
        conn.request("GET", "/" + command)
        response = conn.getresponse()
        data = response.read()
        _LOGGER.debug("host %s: RSP: %s", self._name, data)
        conn.close()
        return data.decode('utf-8')

# import http.client
# def send_command(command):
#     conn = http.client.HTTPConnection("rasp-3:8080")
#     conn.request("GET", "/" + command)
#     response = conn.getresponse()
#     data = response.read()
#     conn.close()
#     return data.decode('utf-8')

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        _LOGGER.debug("turn_on %s", self._name)

        self.send_command("on")

        if ATTR_BRIGHTNESS in kwargs:
            color_rgb = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("turn_on %s : brightness=%s", self._name, kwargs[ATTR_BRIGHTNESS])
            if abs(color[0] - color[1]) > 100):
                self.send_command("red")
            else:
                self.send_command("yellow")

        if ATTR_RGB_COLOR in kwargs:
            _LOGGER.debug("turn_on %s : color=%s", self._name, kwargs[ATTR_RGB_COLOR])

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        _LOGGER.debug("turn_off %s", self._name)
        self.send_command("off")

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.debug("update %s", self._name)
        state = json.loads(self.send_command("state.json"))
        self._state = (state["state"] == "ON")
        self._rgb = state["color"]
        self._brightness = ((int(state["brightness"])-1) * 83) + 41
