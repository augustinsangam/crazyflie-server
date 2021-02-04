import json
import threading
from io import StringIO

from robots.robot import Robot
from robots.robots_utils import RobotUtils
from utils import Sender

from dashboard.message import Message


class DashboardHandler(object):

    def __init__(self, ws) -> None:
        super().__init__()
        self.ws = ws
        self.sendAllRobotsStatus()
        self.thread = threading.Thread(
            target=self.handleCommunications,
        )
        self.thread.start()

    def handleCommunications(self) -> None:
        while not self.ws.closed:
            message = self.ws.receive()
            self.onReceiveMessage(message)

    def onReceiveMessage(self, message: str) -> None:
        if message == None:
            return

        try:
            parsedMessage = self.parseMessage(message)
        except:
            print('Wrong json format')
        else:
            print('Message recieved')
            Sender(None, None).sendFromDashboardToRobots(parsedMessage)

            if parsedMessage['type'] == "take_off":
                self.takeOff(parsedMessage['data']['name'])
            elif parsedMessage['type'] == "land":
                self.land(parsedMessage['data']['name'])
            else:
                raise(Exception('Unrecognized command type'))

    def takeOff(self, robotName: str) -> None:
        print(f'take off command for {robotName}')
        return

    def land(self, robotName: str) -> None:
        print(f'land command for {robotName}')
        return

    def parseMessage(self, message: str) -> dict:
        print(message)
        return json.load(StringIO(message))

    def sendAllRobotsStatus(self) -> None:
        robots: dict[str, Robot] = RobotUtils().getRobots()
        for robot in robots.values():
            self.sendMessage({
                "type": "robot_update",
                "data": robot
            })

    def sendMessage(self, message: Message) -> None:
        messageStr = json.dumps(message)
        self.ws.send(messageStr)
