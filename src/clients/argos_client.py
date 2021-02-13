import json
import logging
import threading
import time
from io import StringIO

from services.communications import CommunicationService
from services.drones import DronesService


class ArgosClient:
    def __init__(self, socket) -> None:
        self.socket = socket
        self.drone = None
        self.active = True
        self.thread = threading.Thread(
            target=self.handleCommunications,
        )
        self.thread.start()

    def handleCommunications(self):
        while self.active:
            message = self.socket.recv(1024)
            if message == b'':
                # TODO : CommunicationService.removeDroneCommunicationHandler(self)
                self.socket.close()
                logging.info('Drone communication handler closed')
                break
            logging.info(f'Recieved {message}')
            self.onReceivedMessage(message)

    def onReceivedMessage(self, message):
        try:
            parsedMessage = self.parseMessage(message.decode('utf-8'))
        except:
            logging.info('Wrong json format')
        else:
            if parsedMessage['type'] == 'pulse':
                if self.drone == None:
                    self.drone = parsedMessage['data']['name']
                parsedMessage['data']['timestamp'] = int(time.time())
                DronesService().setDrone(parsedMessage['data'])
            CommunicationService.sendToDashboardClients(parsedMessage)

    def parseMessage(self, message: str) -> dict:
        return json.load(StringIO(message))

    def sendMessage(self, message: dict) -> None:
        if message['data']['name'] == self.drone or message['data']['name'] == '*':
            messageStr = json.dumps(message)
            self.socket.send(bytes(messageStr, 'ascii'))
