from io import StringIO
from robots.robots_utils import RobotUtils
from utils import Sender

import json
import threading
import time


class RobotCommunicationHandler(object):
    def __init__(self, clientSocket) -> None:
        super().__init__()
        self.clientSocket = clientSocket
        self.robot = None
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
        try:
            parsedMessage = self.parseMessage(message.decode('utf-8'))
        except:
            print('Wrong json format')
        else:
            if parsedMessage['type'] == 'robot_update':
                if self.robot == None:
                    self.robot = parsedMessage['data']['name']
                parsedMessage['data']['timestamp'] = time.time_ns()
                RobotUtils().setRobot(parsedMessage['data'])
            Sender(None, None).sendFromRobotToHandler(parsedMessage)

    def parseMessage(self, message: str) -> dict:
        print(message)
        return json.load(StringIO(message))

    def sendMessage(self, message: dict) -> None:
        if message['data']['name'] == self.robot:
            messageStr = json.dumps(message)
            self.clientSocket.send(bytes(messageStr, 'ascii'))
        else:
            return
