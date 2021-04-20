import json
import logging
import math
import pathlib
import socket
import time
from io import StringIO
from threading import Thread
from typing import Any, List, Set, Union

from src.clients.argos_client import ArgosClient
from src.metaclasses.singleton import Singleton
from src.models.connection import HandlerType
from src.models.drone import Drone, droneDiff
from src.models.message import Message
from src.models.mission import Vec2
from src.services.communications import CommunicationService
from src.services.drones_set import DronesSet
from src.services.mission_handler import MissionHandler


class ArgosController(metaclass=Singleton):
    TCP_HOST = '0.0.0.0'
    TCP_PORT = 3995
    BUFFER_SIZE = 20
    N_MAX_DRONES = 10
    TCPServer: socket = None
    running = True
    dronesSet = DronesSet()
    clients: Set[ArgosClient] = set()
    missionHandler: MissionHandler = None
    client: ArgosClient = None

    @staticmethod
    def launch() -> Thread:
        """Launches a thread in witch the TCP server will start, and return
        that thread.

        """
        thread = Thread(target=ArgosController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def launchServer():
        """Start the TCP server in non-blocking mode. Tries to accept new
        connection as long as the server is running.

        """
        TCPServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPServer.setblocking(False)
        TCPServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPServer.bind((ArgosController.TCP_HOST, ArgosController.TCP_PORT))
        TCPServer.listen(ArgosController.N_MAX_DRONES)
        ArgosController.TCPServer = TCPServer

        while ArgosController.running:
            try:
                if ArgosController.client is None:
                    clientSocket, addr = TCPServer.accept()
                    ArgosController.handleClient(clientSocket, addr)
            except:
                pass
            time.sleep(1)

    @staticmethod
    def stopServer():
        """Closes all the clients connections, then closes the server.

        """
        # for client in ArgosController.clients:
        #     client.closeClient()
        if ArgosController.client is not None:
            ArgosController.client.closeClient()
        ArgosController.running = False
        ArgosController.TCPServer.close()

    @staticmethod
    def handleClient(clientSocket, addr):
        """Creates a client witch will listen to the new connection.
        Callbacks handlers are set for every event.

          @param clientSocket: the socket of the new connection.
        """
        ArgosController.client = ArgosClient()
        ArgosController.dronesSet = DronesSet()
        handlers = [
            [HandlerType.connection, ArgosController.onClientConnect],
            [HandlerType.disconnection, ArgosController.onClientDisconnect],
            [HandlerType.message, ArgosController.onClientReceivedMessage],
            [HandlerType.error, ArgosController.onClientRaisedError],
        ]
        for handlerType, handlerFunc in handlers:
            ArgosController.client.connection.addCallback(
                handlerType,
                handlerFunc,
                ArgosController.client
            )
        ArgosController.client.connect(clientSocket)

    @staticmethod
    def onClientConnect(client: ArgosClient) -> None:
        """Called by a client when it connects to its socket.

          @param client: the client witch called the function.
        """
        logging.info(f'New ARGoS client connected on socket {client.socket}')

    @staticmethod
    def onClientDisconnect(client: ArgosClient) -> None:
        """Called by a client when it disconnects from its socket. It send a
        message to the dashboards to inform the disconnection only if the
        server is running.

          @param client: the client witch called the function.
        """
        logging.info(f'ARGoS client disconnected from socket {client.socket}')
        if ArgosController.running:
            drones = ArgosController.dronesSet.getDrones()
            for drone in drones:
                CommunicationService().sendToDashboardController(
                    Message(
                        type="disconnect",
                        data={"name": drone}
                    )
                )
        ArgosController.client = None
        ArgosController.dronesSet = DronesSet()
        if ArgosController.missionHandler is not None:
            ArgosController.missionHandler.stopMission()
            ArgosController.missionHandler = None

    @staticmethod
    def onClientReceivedMessage(client: ArgosClient, message: bytes) -> None:
        """Called by a client when it receives a message. The message is
        first decoded from byte to ascii, then parsed as json. It updates the
        drone stored status, then sends the message to the dashboards.

          @param client: the client witch called the function.
          @param message: the message in bytes received by the client.
        """
        try:
            messageStr = message.decode('utf-8')
            messages = list(filter(lambda x: x, messageStr.split('\n')))
            parsedMessages: List = list(map(lambda x: json.load(StringIO(x)), messages))
        except ValueError as e:
            logging.error(e)
            logging.error(
                f'ARGoS client received a wrong json format : {message}')
        else:
            for parsedMessage in parsedMessages:
                if parsedMessage['type'] != 'pulse':
                    return

                pulseData: dict = parsedMessage['data']
                oldDrone = ArgosController.dronesSet.getDrone(pulseData['name'])
                if not oldDrone:
                    oldDrone = {}
                pulseData: dict = {**oldDrone, **pulseData, "real": False}

                drone = Drone(**pulseData)
                ArgosController.dronesSet.setDrone(drone['name'], drone)
                CommunicationService().sendToDashboardController(
                    Message(
                        type="pulse",
                        data=droneDiff(oldDrone, drone)
                    )
                )

                if ArgosController.missionHandler is not None:
                    ArgosController.missionHandler.onReceivedPositionAndRange(
                        drone['name'],
                        Vec2(x=drone['position'][0], y=drone['position'][1]),
                        drone['yaw'], drone['ranges'])
                    if ArgosController.missionHandler.checkMissionEnd():
                        ArgosController.missionHandler = None

    @staticmethod
    def onClientRaisedError(client: ArgosClient, error: Exception) -> None:
        """Called when a client raises an error while it waits for messages.

          @param client: the client witch called the function.
          @param error: the exception  raised by the client.
        """
        logging.info(
            f'ARGoS client raised an error:\n{error}')

    @staticmethod
    def onControllerReceivedMessage(message: Message):
        """Decide what to do with the given message. It can start a mission
        or send the message as is to the clients. @param message: the message
        received.
        """
        if message['type'] == 'startMission':
            missionRequestData: dict = message['data']
            if missionRequestData['type'] == 'fake':
                ArgosController.startFakeMission()
            elif missionRequestData['type'] == 'argos':
                initialDronesPos = {}
                offsetDronePos = {}
                for drone in ArgosController.dronesSet.getDrones().values():
                    initialDronesPos[drone['name']] = Vec2(x=drone['position'][0], y=drone['position'][1])
                    offsetDronePos[drone['name']] = Vec2(x=0, y=0)
                ArgosController.startMission(initialDronesPos, offsetDronePos)
                if ArgosController.missionHandler.mission['status'] == 'inProgress':
                    for drone in ArgosController.dronesSet.getDrones().values():
                        ArgosController.sendMessage(Message(type='startMission', data={'name': drone['name']}))
            return
        elif message['type'] == 'returnToBase':
            for drone in ArgosController.dronesSet.getDrones().values():
                ArgosController.sendMessage(Message(type='returnToBase', data={'name': drone['name']}))
        elif message['type'] == 'stopMission':
            if ArgosController.missionHandler is not None:
                ArgosController.missionHandler.stopMission()
                for drone in ArgosController.dronesSet.getDrones().values():
                    ArgosController.sendMessage(Message(type='stopMission', data={'name': drone['name']}))
                ArgosController.missionHandler = None

    @staticmethod
    def sendMessage(message: Message) -> None:
        """Sends the specified message to the client. Start a mission if the
        message type is 'startMission'.

          @param message: the message to send.
        """
        ArgosController.sendMessageToSocket(
            ArgosController.client.socket, message)

    @staticmethod
    def sendMessageToSocket(clientSocket, message: Message):
        """Sends the specified message to the specified socket after
        converting it from json to string.

          @param clientSocket: the socket to send the message.
          @param message: the message to send.
        """

        messageStr = json.dumps(message)
        clientSocket.send(bytes(messageStr + '\n', 'ascii'))

    @staticmethod
    def getDroneIdentifier(webSocket) -> Union[Drone, Any]:
        """Find the drone associated with the specified socket. If the drone
        name isn't yet registered, the socket is returned. NOT USED ANYMORE

          @param webSocket: the socket of the searched drone.
        """
        drone: Drone = ArgosController.dronesSet.getDrone(webSocket)
        return drone['name'] if drone else webSocket

    @staticmethod
    def startFakeMission():
        """Start a fake mission in a separated thread. For demo purposes only.

        """
        fakeDronesSet = DronesSet()
        fakeDronesSet.setDrone('Drone # 1',
                               Drone(name='Drone#1', speed=0, battery=0,
                                     position=[0, 0, 0], timestamp=0,
                                     state="exploring", ledOn=True, real=False,
                                     ranges=[0, 0, 0, 0], yaw=0))
        fakeDronesSet.setDrone('Drone # 2',
                               Drone(name='Drone#2', speed=0, battery=0,
                                     position=[0, 0, 0], timestamp=0,
                                     state="exploring", ledOn=True, real=False,
                                     ranges=[0, 0, 0, 0], yaw=0))
        ArgosController.missionHandler = MissionHandler(
            dronesSet=fakeDronesSet,
            missionType='fake',
            sendMessageCallable=lambda m: CommunicationService().sendToDashboardController(m)
        )
        Thread(target=ArgosController.simulateFakeMission).start()

    @staticmethod
    def startMission(initialDronePos: dict, offsetDronePos: dict):
        """Start a mission. Order drones to takeoff and initialize a mission
        handler.

        """
        logging.info("\n START MISSION \n")
        for drone in ArgosController.dronesSet.getDrones():
            ArgosController.sendMessage(
                Message(
                    type='startMission',
                    data={"name": drone}
                )
            )

        ArgosController.missionHandler = MissionHandler(
            dronesSet=ArgosController.dronesSet,
            missionType='argos',
            initialDronePos=initialDronePos,
            offsetDronePos=offsetDronePos,
            sendMessageCallable=lambda m: CommunicationService().sendToDashboardController(m)
        )

    @staticmethod
    def simulateFakeMission():
        """Start a fake mission using the droneFeed file to simulate flying
        drones. For demo purposes only.
        """
        with open('data/droneFeed.json', 'r') as f:
            jsonDronesFeed = json.load(f)
            droneName: str
            position: Vec2
            points: List[Vec2]

            frames = []

            for feed in jsonDronesFeed['frames']:
                frame = [
                    feed[0],
                    Vec2(x=feed[1][0], y=feed[1][1]),
                    [Vec2(x=feed[2][0][0], y=feed[2][0][1]),
                     Vec2(x=feed[2][1][0], y=feed[2][1][1]),
                     Vec2(x=feed[2][2][0], y=feed[2][2][1]),
                     Vec2(x=feed[2][3][0], y=feed[2][3][1])]
                ]
                frames.append(frame)

            i = 0
            for droneName, position, points in frames:
                i += 1
                time.sleep((i % 2) / 5)
                ArgosController.missionHandler.handlePositionAndBorders(
                    droneName, position, points)

            ArgosController.missionHandler.endMission()
