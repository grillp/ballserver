#!/usr/bin/env python

from twisted.web import server
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints
from subprocess import call
import logging
import logging.handlers
import json
from time import sleep

MULTI_COMMAND_DELAY=0.4


LOG_FILENAME = "/tmp/myservice.log"
LOG_LEVEL = logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

colors = {
    'yellow': (255, 255, 0),
    'red': (255, 0, 0),
}

class LEDBall():
    def __init__(self):
        self._on = False
        self._brightness = 0
        self._color = None
        self.yellow()
        self.powerOff()

    def send_ir_command(self, command):
        call(["/usr/bin/irsend", "SEND_ONCE", "ledball", command]);

    def powerOnPlusCommand(self, command):
        self.powerOn()
        sleep(MULTI_COMMAND_DELAY)
        self.send_ir_command(command);

    def powerOn(self):
        self.send_ir_command("KEY_POWER")
        if not self._on:
            self._brightness = 3
        self._on = True

    def powerOff(self):
        self.send_ir_command("KEY_OFF")
        self._on = False
        self._brightness = 0

    def red(self):
        self._color = 'red'
        self.powerOnPlusCommand("KEY_RED")

    def yellow(self):
        self._color = 'yellow'
        self.powerOnPlusCommand("KEY_YELLOW")

    def brightness(self):
        self._brightness = ((self._brightness) % 3 + 1)
        self.powerOnPlusCommand("KEY_BRIGHTNESS_CYCLE")

    def cycle(self):
        self.powerOnPlusCommand("KEY_CYCLEWINDOWS")

    def isOn(self):
        return self._on

    def getBrightness(self):
        return self._brightness;

    def getColor(self):
        return self._color

def response(message=""):
    if message != "":
        message = message + "</br>"
    return "<html>" + message + "<a href='/on'>ON</a><br/><a href='/off'>OFF</a><br/><a href='/red'>RED</a><br/><a href='/yellow'>YELLOW</a><br/><a href='/brightness'>BRIGHTNESS</a><br/><a href='/colours'>COLOURS</a></html>"

def rendersStateResponse(request, ledball):
    state = "ON" if ledball.isOn() else "OFF"
    brightness = str(ledball.getBrightness())
    color = colors[ledball.getColor()]
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
    def render_GET(self, Request):
        self._ledball.powerOn()
    	return rendersStateResponse(request, self._ledball)

class BallOff(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.powerOff()
        return rendersStateResponse(request, self._ledball)

class BallRed(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.red()
        return rendersStateResponse(request, self._ledball)

class BallYellow(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.yellow()
        return rendersStateResponse(request, self._ledball)

class BallBrightness(Resource):
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.brightness()
        return rendersStateResponse(request, self._ledball)

class BallColourCycle(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.cycle()
        return rendersStateResponse(request, self._ledball)

class BallState(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, request):
        return "ON" if self._ledball.isOn() else "OFF"

class BallStateJson(Resource):
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
web_root.putChild("red", BallRed(ledball))
web_root.putChild("yellow", BallYellow(ledball))
web_root.putChild("brightness", BallBrightness(ledball))
web_root.putChild("colours", BallColourCycle(ledball))
web_root.putChild("state", BallState(ledball))
web_root.putChild("state.json", BallStateJson(ledball))

logger.info("Setting up Site")
site = server.Site(web_root)
logger.info("Setting up endpoint")
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
endpoint.listen(site)
logger.info("runnign reactor")
reactor.run()
logger.info("Terminating")
