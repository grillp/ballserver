#!/usr/bin/env python

from twisted.web import server
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints
from subprocess import call
import logging
import logging.handlers
from time import sleep

COMMAND_DELAY=0.4


LOG_FILENAME = "/tmp/myservice.log"
LOG_LEVEL = logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class LEDBall():
    def __init__(self):
        self._on = False
        self.powerOff()

    def send_ir_command(command):
        call(["/usr/bin/irsend", "SEND_ONCE", "ledball", command]);

    def powerOn(self):
        send_ir_command("KEY_POWER");
        self._on = True

    def powerOff(self):
        send_ir_command("KEY_OFF");
        self._on = False

    def isOn(self):
        return self._on

    def red(self):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_RED");

    def yellow(self):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_YELLOW");

    def brightness(self):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_BRIGHTNESS_CYCLE");

    def cycle(self):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_CYCLEWINDOWS");

def response(message=""):
  if message != "":
    message = message + "</br>"
  return "<html>" + message + "<a href='/on'>ON</a><br/><a href='/off'>OFF</a><br/><a href='/red'>RED</a><br/><a href='/yellow'>YELLOW</a><br/><a href='/brightness'>BRIGHTNESS</a><br/><a href='/colours'>COLOURS</a></html>"

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
    	return response("Ball On - OK")

class BallOff(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.powerOff()
        return response("Ball Off - OK")

class BallRed(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.red()
        return response("Ball Red - OK")

class BallYellow(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.yellow()
        return response("Ball Yellow - OK")

class BallColourCycle(Resource):
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.brightness()
        return response("Brightness - OK")

class BallBrightness(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        self._ledball.cycle()
        return response("Colour Cycle - OK")

class BallState(Resource):
    isLeaf = True
    def __init__(self, ledball):
        self._ledball = ledball
    def render_GET(self, Request):
        return "ON" if self._ledball.isOn() else "OFF"

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

logger.info("Setting up Site")
site = server.Site(web_root)
logger.info("Setting up endpoint")
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
endpoint.listen(site)
logger.info("runnign reactor")
reactor.run()
logger.info("Terminating")
