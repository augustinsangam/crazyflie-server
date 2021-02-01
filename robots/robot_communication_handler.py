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
        self.active = True

        self.thread = threading.Thread(
            target=self.handleCommunications,
        )
        self.thread.start()

    def handleCommunications(self):
        while self.active == True:
            print('wait for reception')

            message = self.clientSocket.recv(1024)
            print(f'Recieved {message}')
            self.onReceivedMessage(message)

    def onReceivedMessage(self, message):
        if message == b'':
            self.clientSocket.close()
            Sender(None, None).dropRobotHandler(self)
            self.active = False
            return
        parsedMessage = self.parseMessage(message.decode('utf-8'))

        if parsedMessage['type'] == 'robot_update':
            parsedMessage['data']['timestamp'] = time.time_ns()
            RobotUtils().setRobot(parsedMessage['data'])
        Sender(None, None).sendFromRobotToHandler(parsedMessage)

    def parseMessage(self, message: str) -> dict:
        print(message)
        return json.load(StringIO(message))

    def sendMessage(self, message: dict) -> None:
        messageStr = json.dumps(message)
        self.clientSocket.send(bytes(messageStr, 'ascii'))
