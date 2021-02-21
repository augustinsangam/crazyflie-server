import json
import logging
from io import StringIO
from threading import Thread
from typing import Dict

from models.drone import Drone
from models.message import Message
from services.communications import CommunicationService
from services.drones import DronesService


class DashboardClient:

    def __init__(self, socket) -> None:
        super().__init__()
        self.socket = socket
        self.sendAllRobotsStatus()
        self.thread = Thread(
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
            CommunicationService.sendToAllCrazyradioClients(parsedMessage)

            # if parsedMessage['type'] == "takeOff":
            #     self.takeOff(parsedMessage['data']['name'])
            # elif parsedMessage['type'] == "land":
            #     self.land(parsedMessage['data']['name'])
            # elif parsedMessage['type'] == "lighten":
            #     self.lighten(parsedMessage['data']['name'])
            # elif parsedMessage['type'] == "darken":
            #     self.darken(parsedMessage['data']['name'])
            # else:
            #     raise(Exception('Unrecognized command type'))

    def takeOff(self, droneName: str) -> None:
        logging.info(f'take off command for {droneName}')
        return

    def land(self, droneName: str) -> None:
        logging.info(f'land command for {droneName}')
        return

    def parseMessage(self, message: str) -> dict:
        return json.load(StringIO(message))

    def sendAllRobotsStatus(self) -> None:
        logging.info(
            'Sending all robots statuts to new Dashboard client')
        drones: Dict[str, Drone] = DronesService.getDrones()
        for drone in drones.values():
            self.sendMessage({
                "type": "pulse",
                "data": drone
            })

    def sendMessage(self, message: Message) -> None:
        messageStr = json.dumps(message)
        self.socket.send(messageStr)

    def closeClient(self):
        self.socket.__del__()
