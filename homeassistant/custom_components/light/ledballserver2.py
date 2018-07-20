"""

"""
import logging

import voluptuous as vol
import http.client
import json

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_EFFECT, ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS, SUPPORT_EFFECT, SUPPORT_COLOR,
    Light, PLATFORM_SCHEMA)

from homeassistant.const import CONF_HOSTS
import homeassistant.util.color as color_util
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOSTS): vol.All(cv.ensure_list, [cv.string]),
})

SERVICE_EFFECT_COLORLOOP = 'balllight_effect_colorloop'
SERVICE_EFFECT_STOP = 'balllight_effect_stop'

SUPPORT_LEDBALL = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR | SUPPORT_EFFECT)
BYTE_MAX = 255

def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Set up the demo light platform."""
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
            led_ball_lights.append(LedBallLight2(host, counter))
            counter = counter + 1

        add_devices_callback(led_ball_lights)

class LedBallLight2(Light):
    """Representation of an LED Ball Light."""

    def __init__(self, host, id):
        """Initialize an LED Ball Light."""
        self._host = host
        self._id = id
        self._name = "LED Ball Light " + str(id)
        self._state = False
        self._brightness = None
        self._hs_color = color_util.color_RGB_to_hs([0,0,0])
        self._effect = None

    @property
    def should_poll(self) -> bool:
        """No polling needed for a demo light."""
        return False

    @property
    def name(self) -> str:
        """Return the name of the light if any."""
        return self._name

    @property
    def unique_id(self):
        """Return unique ID for light."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return availability."""
        # This demo light is always available, but well-behaving components
        # should implement this to inform Home Assistant accordingly.
        # return self._available
        return True

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def hs_color(self) -> tuple:
        """Return the hs color value."""
        return self._hs_color

    @property
    def effect_list(self) -> list:
        """Return the list of supported effects."""
        return self._effect_list

    @property
    def effect(self) -> str:
        """Return the current effect."""
        return [
            SERVICE_EFFECT_COLORLOOP,
            SERVICE_EFFECT_STOP,
        ]

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_LEDBALL

    def send_command(self, command):
        _LOGGER.debug("host %s: CMD: %s", self._name, command)
        conn = http.client.HTTPConnection(self._host)
        conn.request("GET", "/" + command)
        response = conn.getresponse()
        data = response.read()
        _LOGGER.debug("host %s: RSP: %s", self._name, data)
        conn.close()
        return data.decode('utf-8')

    def send_brightness_command(self):
        # 3 Bightness Levels. 1-3
        # divided in 3 ranges
        l = (self._brightness / (256 / 3)) + 1
        command = "brightness?l="+str(int(l))
        return self.send_command(command)


    def send_color_command(self):
        r,g,b = [_ for _ in color_util.color_hs_to_RGB(seld._hs_color)]
        command = "color?c=("+str(r)+","+str(g)+","+str(b)+")"
        return self.send_command(command)

    def send_cycle_command(self):
        command = "cycle"
        return self.send_command(command)

    def turn_on(self, **kwargs) -> None:
        """Turn the light on."""
        self._state = True

        if ATTR_HS_COLOR in kwargs:
            self._hs_color = kwargs[ATTR_HS_COLOR]
            _LOGGER.debug("turn_on %s : color=%s", self._name, self._hs_color)
            self._effect = None
            self.send_color_command();

        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("turn_on %s : brightness=%s", self._name, self._brightness)
            self.send_brightness_command();

        if ATTR_EFFECT in kwargs:
            effect = kwargs.get(ATTR_EFFECT)
            self._effect = effect
            _LOGGER.debug("turn_on %s : effect=%s", self._name, effect)
            if effect == SERVICE_EFFECT_COLORLOOP:
                self.send_cycle_command();
            else:
                _LOGGER.debug("turn_on %s : resetting color=%s", self._name,self._hs_color)
                self._effect = None
                self.send_color_command()

        # As we have disabled polling, we need to inform
        # Home Assistant about updates in our state ourselves.
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        self._state = False
        _LOGGER.debug("turn_off %s", self._name)
        self.send_command("off")

        # As we have disabled polling, we need to inform
        # Home Assistant about updates in our state ourselves.
        self.schedule_update_ha_state()
