from io import StringIO
from src.drone.drone_utils import DroneUtils
from src.utils import Sender

import json
import threading
import time


class DroneCommunicationHandler(object):
    def __init__(self, socket) -> None:
        super().__init__()
        self.socket = socket
        self.drone = None
        self.active = True

        self.thread = threading.Thread(
            target=self.handleCommunications,
        )
        self.thread.start()

    def handleCommunications(self):
        while self.active == True:
            print('wait for reception')

            message = self.socket.recv(1024)
            print(f'Recieved {message}')
            self.onReceivedMessage(message)

    def onReceivedMessage(self, message):
        if message == b'':
            self.socket.close()
            Sender(None, None).removeDroneCommunicationHandler(self)
            self.active = False
            print('Drone communication handler closed')
            return
        try:
            parsedMessage = self.parseMessage(message.decode('utf-8'))
        except:
            print('Wrong json format')
        else:
            if parsedMessage['type'] == 'pulse':
                if self.drone == None:
                    self.drone = parsedMessage['data']['name']
                parsedMessage['data']['timestamp'] = time.time_ns()
                DroneUtils().setDrone(parsedMessage['data'])
            Sender(None, None).sendToDashboards(parsedMessage)

    def parseMessage(self, message: str) -> dict:
        print(message)
        return json.load(StringIO(message))

    def sendMessage(self, message: dict) -> None:
        if message['data']['name'] == self.drone or message['data']['name'] == '*':
            messageStr = json.dumps(message)
            self.socket.send(bytes(messageStr, 'ascii'))
        else:
            return
