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

def response(message=""):
  if message != "":
    message = message + "</br>"
  return "<html>" + message + "<a href='/on'>ON</a><br/><a href='/off'>OFF</a><br/><a href='/red'>RED</a><br/><a href='/yellow'>YELLOW</a><br/><a href='/brightness'>BRIGHTNESS</a><br/><a href='/colours'>COLOURS</a></html>"

isBallOn = False
def setBallOnState(state):
    isBallOn = state
    logger.info("setBallOnState = " + isBallOn)

def getBallOnState():
    logger.info("getBallOnState = " + isBallOn)
    return isBallOn

def send_ir_command(command):
    call(["/usr/bin/irsend", "SEND_ONCE", "ledball", command]);

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
    setBallOnState(True)
    def render_GET(self, Request):
        send_ir_command("KEY_POWER");
    	return response("Ball On - OK")

class BallOff(Resource):
    isLeaf = True
    setBallOnState(False)
    def render_GET(self, Request):
        send_ir_command("KEY_OFF");
        return response("Ball Off - OK")

class BallRed(Resource):
    isLeaf = True
    def render_GET(self, Request):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_RED");
        return response("Ball Red - OK")

class BallYellow(Resource):
    isLeaf = True
    def render_GET(self, Request):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_YELLOW");
        return response("Ball Yellow - OK")

class BallBrightness(Resource):
    isLeaf = True
    def render_GET(self, Request):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_BRIGHTNESS_CYCLE");
        return response("Brightness - OK")

class BallColourCycle(Resource):
    isLeaf = True
    def render_GET(self, Request):
        send_ir_command("KEY_POWER");
        sleep(COMMAND_DELAY)
        send_ir_command("KEY_CYCLEWINDOWS");
        return response("Colour Cycle - OK")

class BallState(Resource):
    isLeaf = True
    def render_GET(self, Request):
        return "ON" if getBallOnState() else "OFF"

logger.info("Setting up Web Server..")

web_root = WebRoot()
web_root.putChild("on", BallOn())
web_root.putChild("off", BallOff())
web_root.putChild("red", BallRed())
web_root.putChild("yellow", BallYellow())
web_root.putChild("brightness", BallBrightness())
web_root.putChild("colours", BallColourCycle())
web_root.putChild("state", BallState())

# turn ball off
isBallOn = False
send_ir_command("KEY_OFF");

logger.info("Setting up Site")
site = server.Site(web_root)
logger.info("Setting up endpoint")
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
endpoint.listen(site)
logger.info("runnign reactor")
reactor.run()
logger.info("Terminating")
