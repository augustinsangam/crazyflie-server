import json
import threading
from io import StringIO

from src.drone.drone_utils import DroneUtils, Drone
from src.utils import Sender

from src.dashboard.message import Message


class DashboardCommunicationHandler(object):

    def __init__(self, socket) -> None:
        super().__init__()
        self.socket = socket
        self.sendAllRobotsStatus()
        self.thread = threading.Thread(
            target=self.handleCommunications,
        )
        self.thread.start()

    def handleCommunications(self) -> None:
        while not self.socket.closed:
            message = self.socket.receive()
            self.onReceiveMessage(message)

    def onReceiveMessage(self, message: str) -> None:
        if message == None:
            print('dashboard connexion closed')
            return

        try:
            parsedMessage = self.parseMessage(message)
        except:
            print('Wrong json format')
        else:
            print('Message recieved')
            Sender(None, None).sendToDrones(parsedMessage)

            if parsedMessage['type'] == "take_off":
                self.takeOff(parsedMessage['data']['name'])
            elif parsedMessage['type'] == "land":
                self.land(parsedMessage['data']['name'])
            else:
                raise(Exception('Unrecognized command type'))

    def takeOff(self, droneName: str) -> None:
        print(f'take off command for {droneName}')
        return

    def land(self, droneName: str) -> None:
        print(f'land command for {droneName}')
        return

    def parseMessage(self, message: str) -> dict:
        print(message)
        return json.load(StringIO(message))

    def sendAllRobotsStatus(self) -> None:
        drones: dict[str, Drone] = DroneUtils().getDrones()
        for drone in drones.values():
            self.sendMessage({
                "type": "pulse",
                "data": drone
            })

    def sendMessage(self, message: Message) -> None:
        messageStr = json.dumps(message)
        self.socket.send(messageStr)
