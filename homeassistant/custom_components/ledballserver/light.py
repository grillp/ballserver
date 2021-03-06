import logging

import voluptuous as vol
import requests
import json

# Import the device class from the component that you want to support
from homeassistant.components.light import (ATTR_BRIGHTNESS, ATTR_HS_COLOR, ATTR_EFFECT,
                                            SUPPORT_BRIGHTNESS, SUPPORT_EFFECT, SUPPORT_COLOR,
                                            Light, PLATFORM_SCHEMA)
from homeassistant.const import CONF_HOSTS
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOSTS): vol.All(cv.ensure_list, [cv.string]),
})

SERVICE_EFFECT_COLORLOOP = 'balllight_effect_colorloop'
SERVICE_EFFECT_STOP = 'balllight_effect_stop'

SUPPORT_LEDBALL = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR | SUPPORT_EFFECT)
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
        self._hs_color = color_util.color_RGB_to_hs(0,0,0)
        self._effect = None
        self._last_good_result = "{\"state\":\"OFF\"}"

    @property
    def effect_list(self):
        """Return the list of supported effects for this light."""
        return [
            SERVICE_EFFECT_COLORLOOP,
            SERVICE_EFFECT_STOP,
        ]

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
    def effect(self):
        """Return the Brightness of the Bulb"""
        return self._effect

    @property
    def hs_color(self):
        return self._hs_color

    @property
    def is_on(self):
        """Return true if light is on."""
        _LOGGER.debug("host %s: is_on %s", self._name, self._state)
        return self._state

    def send_command(self, command):
        _LOGGER.debug("host %s; http://%s/%s", self._name, self._host, command)
        try:
            r = requests.get("http://"+self._host+"/"+command)
            self._last_good_result = r.text
            _LOGGER.debug("host %s: RSP: %s", self._name, r.text)
        except OSError as e:
            _LOGGER.error("host %s: Exception: %s", self._name, str(e))

        return self._last_good_result

    def send_brightness_command(self):
        # 3 Bightness Levels. 1-3
        # divided in 3 ranges
        l = (self._brightness / (256 / 3)) + 1
        command = "brightness?l="+str(int(l))
        return self.send_command(command)


    def send_color_command(self):
        r,g,b = [_ for _ in color_util.color_hs_to_RGB(*self._hs_color)]
        command = "color?c=("+str(r)+","+str(g)+","+str(b)+")"
        return self.send_command(command)

    def send_cycle_command(self):
        command = "cycle"
        return self.send_command(command)

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        _LOGGER.debug("turn_on %s", self._name)

        self.send_command("on")

        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("turn_on %s : brightness=%s", self._name, self._brightness)
            self.send_brightness_command();

        if ATTR_HS_COLOR in kwargs:
            self._hs_color=kwargs[ATTR_HS_COLOR]
            _LOGGER.debug("turn_on %s : color=%s", self._name, self._hs_color)
            self._effect = None
            self.send_color_command();

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

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        _LOGGER.debug("turn_off %s", self._name)
        self.send_command("off")

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.debug("update %s", self._name)
        state = json.loads(self.send_command("state"))
        self._state = (state["state"] == "ON")
        if (self._state):
            self._hs_color = color_util.color_RGB_to_hs(*state["color"])
            self._brightness = ((int(state["brightness"])-1) * 83) + 41
