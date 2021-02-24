import json
import logging
import socket
from io import StringIO
from threading import Thread

from models.drone import Drone
from services.communications import CommunicationService
from services.drones import DronesService
from utils.timestamp import getTimestamp


class ArgosClient:
    def __init__(self, socket) -> None:
        self.socket = socket
        drone: Drone = {
            "name": '',
            "speed": 0.0,
            "battery": 0.0,
            "position": [0.0, 0.0, 0.0],
            "timestamp": getTimestamp(),
            "flying": False,
            "ledOn": True,
            "real": False
        }
        self.drone = drone
        self.thread = Thread(
            target=self.handleCommunications,
        )
        self.thread.start()

    def handleCommunications(self):
        try:
            while True:
                message = self.socket.recv(1024)
                if message == b'':
                    self.socket.close()
                    logging.info('ARGoS client connection closed')
                    break
                self.onReceivedMessage(message)
        except:
            self.socket.close()
            logging.info('ARGoS client connection closed')

    def onReceivedMessage(self, message):
        try:
            messageStr = message.decode('utf-8')
            parsedMessage = self.parseMessage(messageStr)
        except:
            droneName: str = self.drone['name']
            logging.debug(
                f'ARGoS client {droneName} receive a wrong json format : {messageStr}')
        else:
            if parsedMessage['type'] == 'pulse':
                self.drone = parsedMessage['data']
                DronesService.setDrone(parsedMessage['data'])
                CommunicationService.sendToDashboardClients(parsedMessage)

    def parseMessage(self, message: str) -> dict:
        return json.load(StringIO(message))

    def sendMessage(self, message: dict) -> None:
        if message['data']['name'] == self.drone['name'] or message['data']['name'] == '*':
            messageStr = json.dumps(message)
            self.socket.send(bytes(messageStr, 'ascii'))

    def closeClient(self):
        self.socket.shutdown(socket.SHUT_RDWR)
