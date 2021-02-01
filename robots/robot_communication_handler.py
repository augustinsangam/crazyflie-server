from io import StringIO
from robots.robots_utils import RobotUtils, Robot
from utils import Sender

import json
import threading
import time


class RobotCommunicationHandler(object):
    def __init__(self, clientSocket) -> None:
        super().__init__()
        self.clientSocket = clientSocket

        self.thread = threading.Thread(
            target=self.handleCommunications,
        )
        self.thread.start()

    def handleCommunications(self):
        while True:
            print('wait for reception')

            message = self.clientSocket.recv(1024)
            print(f'Received {message}')
            self.onReceivedMessage(message)

            self.clientSocket.send(bytes('ACK!', 'ascii'))
            print('ACK sent')

    def onReceivedMessage(self, message):
        if message == None:
            return
        parsedMessage = self.parseMessage(message.decode('utf-8'))

        if parsedMessage['type'] == 'robot_update':
            parsedMessage['data']['lastUpdate'] = time.time_ns()
            RobotUtils().setRobot(parsedMessage['data'])
        Sender(None, None).sendFromRobotToHandler(parsedMessage)

    def parseMessage(self, message: str) -> dict:
        print(message)
        return json.load(StringIO(message))

    def sendMessage(self, message: dict) -> None:
        messageStr = json.dumps(message)
        self.clientSocket.send(bytes(messageStr, 'ascii'))
