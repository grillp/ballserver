import logging

import voluptuous as vol
import http.client

# Import the device class from the component that you want to support
from homeassistant.components.light import ATTR_BRIGHTNESS, Light, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOSTS
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOSTS): vol.All(cv.ensure_list, [cv.string]),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the LED Ball Server platform."""

    hosts = config.get(CONF_HOSTS)

    if hosts:
        # Support retro compatibility with comma separated list of hosts
        # from config
        hosts = hosts[0] if len(hosts) == 1 else hosts
        hosts = hosts.s plit(',') if isinstance(hosts, str) else hosts
        led_ball_lights = []
        counter = 0
        for host in hosts:
            led_ball_lights.append(LedBallLight(host, counter))
            counter = counter + 1
        add_devices(led_ball_lights)

class LedBallLight(Light):
    """Representation of an LED Ball Light."""

    def __init__(self, host, id):
        """Initialize an LED Ball Light."""
        self._host = host
        self._id = id
        self._name = "LED Ball Light " + id
        self._state = None
        self._brightness = None

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the Brightness of the Bulb"""
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    def send_command(self, command):
        conn = http.client.HTTPConnection(self._host)
        conn.request("GET", "/" + command)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return data

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        self.send_command("on")

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self.send_command("off")

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = (self.send_command("state") == "ON")
