import json
from io import StringIO
from robots.robot import Robot
from robots.robots_handler import RobotHandler


class DashboadHandler(object):

  def __init__(self, ws) -> None:
    super().__init__()
    self.ws = ws
    self.sendAllRobotsStatus()
    self.handleCommunications()

  def handleCommunications(self) -> None:
    while not self.ws.closed:
      message = self.ws.receive()
      self.onRecieveMessage(message)

  def onRecieveMessage(self, message: str) -> None:
    print(message)
    parsedMessage = self.parseMessage(message)
    print('Message recieved')
    if parsedMessage['type'] == "take_off":
      self.takeOff(parsedMessage['data']['robotName'])
    elif parsedMessage['type'] == "land":
      self.land(parsedMessage['data']['robotName'])
    else:
      raise(Exception('Unrecognized command type'))

  def takeOff(self, robotName: str) -> None:
    print(f'take off command for {robotName}')
    return

  def land(self, robotName: str) -> None:
    print(f'land command for {robotName}')
    return

  def parseMessage(self, message:str) -> dict:
    return json.load(StringIO(message))

  def sendAllRobotsStatus(self) -> None:
    robots: dict[str, Robot] = RobotHandler().getRobots()
    for robot in robots.values():
      self.sendMessage(robot)

  def sendMessage(self, message: dict) -> None:
    messageStr = json.dumps(message)
    self.ws.send(messageStr)
