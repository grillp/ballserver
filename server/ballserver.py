#!/usr/bin/env python

from twisted.web import server
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints
from subprocess import call
import logging
import logging.handlers
import json
from time import sleep
from ast import literal_eval

MULTI_COMMAND_DELAY=0.4

LOG_FILENAME = "/tmp/myservice.log"
LOG_LEVEL = logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

CMD_ON = 'KEY_F1'
CMD_OFF = 'KEY_F2'
CMD_AUTO = 'KEY_F3'
CMD_PAUSE = 'KEY_F4'
CMD_FLASH = 'KEY_F5'
CMD_BRIGHT = 'KEY_F6'
CMD_TIMER_3H = 'KEY_F7'
CMD_WHITE = 'KEY_F8'
CMD_RED = 'KEY_F9'
CMD_GREEN = 'KEY_F10'
CMD_DARK_BLUE = 'KEY_F11'
CMD_AMBER = 'KEY_F12'
CMD_PURPLE = 'KEY_F13'
CMD_LIGHT_BLUE = 'KEY_F14'

COLOR_WHITE = CMD_WHITE
COLOR_RED = CMD_RED
COLOR_GREEN = CMD_GREEN
COLOR_DARK_BLUE = CMD_DARK_BLUE
COLOR_AMBER = CMD_AMBER
COLOR_PURPLE = CMD_PURPLE
COLOR_LIGHT_BLUE = CMD_LIGHT_BLUE

def colorToCommand(color):
    """ As long as the COLOR_* and CMD_* above are equal this will work"""
    return color

colors_rgb_lookup = {
    COLOR_WHITE: (245, 245, 245),
    COLOR_RED: (139, 0, 0),
    COLOR_GREEN: (0, 100, 0),
    COLOR_DARK_BLUE: (0, 0, 139),
    COLOR_AMBER:  (255, 165, 0),
    COLOR_PURPLE: (128, 0, 128),
    COLOR_LIGHT_BLUE: (173, 216, 230),
}

def colorDistanceInRGB(color1, color2):
    r1, g1, b1 = [_ for _ in color1]
    r2, g2, b2 = [_ for _ in color2]
    return ((r2-r1)*0.30) ** 2 + ((g2-g1)*0.59) ** 2 + ((b2-b1)*0.11) ** 2

MAX_COLOR_DISTANCE = colorDistanceInRGB((0,0,0),(255,255,255))
def closestColorInRGB(color):
    match_name = None
    match_distance = MAX_COLOR_DISTANCE
    for name, rgb in colors_rgb_lookup.items():
        distance = colorDistanceInRGB(color, rgb)
        if distance < match_distance:
            match_name = name
            match_distance = distance
    return match_name

class LEDBall():
    def __init__(self):
        self._on = False
        self._brightness = 0
        self._color = None
        self.color(COLOR_AMBER)
        self.powerOff()

    def send_ir_command(self, command):
        call(["/usr/bin/irsend", "SEND_ONCE", "ledball", command]);
        sleep(MULTI_COMMAND_DELAY)

    def powerOnPlusCommand(self, command):
        self.powerOn()
        self.send_ir_command(command);

    def powerOn(self):
        self.send_ir_command(CMD_ON)
        if not self._on:
            self._brightness = 3
        self._on = True

    def powerOff(self):
        self.send_ir_command(CMD_OFF)
        self._on = False
        self._brightness = 0

    def color(self, color):
        self._color = color
        self.powerOnPlusCommand(colorToCommand(color))

    def brightness(self):
        self._brightness = ((self._brightness) % 3 + 1)
        self.powerOnPlusCommand(CMD_BRIGHT)

    def cycle(self):
        self.powerOnPlusCommand(CMD_AUTO)

    def isOn(self):
        return self._on

    def getBrightness(self):
        return self._brightness;

    def getColor(self):
        return self._color

def rendersStateResponse(request, ledball):
    state = "ON" if ledball.isOn() else "OFF"
    brightness = str(ledball.getBrightness())
    color = colors_rgb_lookup[ledball.getColor()]
    data = json.dumps({'state': state, 'brightness': brightness, 'color': color})
    request.setHeader('Content-Type', 'application/json')
    request.write(data)
    request.finish()
    return server.NOT_DONE_YET

class WebRoot(Resource):
    # isLeaf = True
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        return response()

class BallOn(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, request):
        self._ledball.powerOn()
    	return rendersStateResponse(request, self._ledball)

class BallOff(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, request):
        self._ledball.powerOff()
        return rendersStateResponse(request, self._ledball)

class BallColor(Resource):
    isLeaf = True
    def __init__(self, ledball, color):
        self._ledball = ledball
        self._color = color
    def render_GET(self, request):
        self._ledball.color(self._color)
        return rendersStateResponse(request, self._ledball)

class BallColorSet(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, request):
        color = literal_eval(request.args['c'])
        self._ledball.color(closestColorInRGB(color))
        return rendersStateResponse(request, self._ledball)

class BallBrightness(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, request):
        self._ledball.brightness()
        return rendersStateResponse(request, self._ledball)

class BallColorCycle(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, request):
        self._ledball.cycle()
        return rendersStateResponse(request, self._ledball)

class BallState(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, request):
        return rendersStateResponse(request, self._ledball)

logger.info("Setting up Web Server..")

ledball = LEDBall()
web_root = WebRoot()
web_root.putChild("on", BallOn(ledball))
web_root.putChild("off", BallOff(ledball))
web_root.putChild("red", BallColor(ledball, COLOR_RED))
web_root.putChild("yellow", BallColor(ledball, COLOR_AMBER))
web_root.putChild("white", BallColor(ledball, COLOR_WHITE))
web_root.putChild("blue", BallColor(ledball, COLOR_DARK_BLUE))
web_root.putChild("lightblue", BallColor(ledball, COLOR_LIGHT_BLUE))
web_root.putChild("green", BallColor(ledball, COLOR_GREEN))
web_root.putChild("purple", BallColor(ledball, COLOR_PURPLE))
web_root.putChild("brightness", BallBrightness(ledball))
web_root.putChild("cycle", BallColorCycle(ledball))
web_root.putChild("state", BallState(ledball))
web_root.putChild("color", BallColorSet(ledball))

logger.info("Setting up Site")
site = server.Site(web_root)
logger.info("Setting up endpoint")
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
endpoint.listen(site)
logger.info("runnign reactor")
reactor.run()
logger.info("Terminating")
