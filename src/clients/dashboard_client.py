import json
import logging
import threading
from io import StringIO
from typing import Dict

from models.client import Client
from models.drone import Drone
from models.message import Message
from services.communications import CommunicationService
from services.drones import DronesService


class DashboardClient(Client):

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
            return

        try:
            parsedMessage = self.parseMessage(message)
        except:
            logging.error('Wrong json format')
        else:
            logging.info(f'Message received : {message}')
            CommunicationService.sendToArgosClients(parsedMessage)

            if parsedMessage['type'] == "take_off":
                self.takeOff(parsedMessage['data']['name'])
            elif parsedMessage['type'] == "land":
                self.land(parsedMessage['data']['name'])
            else:
                raise(Exception('Unrecognized command type'))

    def takeOff(self, droneName: str) -> None:
        logging.info(f'take off command for {droneName}')
        return

    def land(self, droneName: str) -> None:
        logging.info(f'land command for {droneName}')
        return

    def parseMessage(self, message: str) -> dict:
        return json.load(StringIO(message))

    def sendAllRobotsStatus(self) -> None:
        drones: Dict[str, Drone] = DronesService.getDrones()
        for drone in drones.values():
            self.sendMessage({
                "type": "pulse",
                "data": drone
            })

    def sendMessage(self, message: Message) -> None:
        messageStr = json.dumps(message)
        self.socket.send(messageStr)
