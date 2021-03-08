import json
import logging
import pathlib
import socket
import time
from io import StringIO
from threading import Thread
from typing import Any, List, Set, Union

from src.clients.argos_client import ArgosClient
from src.metaclasses.singleton import Singleton
from src.models.connection import HandlerType
from src.models.drone import Drone
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
    TCPServer = None
    running = True
    dronesSet = DronesSet()
    clients: Set[ArgosClient] = set()
    missionHandler: MissionHandler = None

    @staticmethod
    def launch() -> Thread:
        """Launches a thread in witch the TCP server will start, and return that thread.

        """
        thread = Thread(target=ArgosController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def launchServer():
        """Start the TCP server in non-blocking mode. Tries to accept new connection as long as the server is running.

        """
        TCPServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPServer.setblocking(False)
        TCPServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPServer.bind((ArgosController.TCP_HOST, ArgosController.TCP_PORT))
        TCPServer.listen(ArgosController.N_MAX_DRONES)
        ArgosController.TCPServer = TCPServer

        while ArgosController.running:
            try:
                clientSocket, addr = TCPServer.accept()
                ArgosController.handleClient(clientSocket, addr)
                time.sleep(1)
            except:
                pass

    @staticmethod
    def stopServer():
        """Closes all the clients connections, then closes the server.

        """
        for client in ArgosController.clients:
            client.closeClient()
        ArgosController.running = False
        ArgosController.TCPServer.close()

    @staticmethod
    def handleClient(clientSocket, addr):
        """Creates a client witch will listen to the new connection. Callbacks handlers are set for every event.

          @param clientSocket: the socket of the new connection.
        """
        client = ArgosClient()
        ArgosController.clients.add(client)
        handlers = [
            [HandlerType.connection, ArgosController.onClientConnect],
            [HandlerType.disconnection, ArgosController.onClientDisconnect],
            [HandlerType.message, ArgosController.onClientReceivedMessage],
            [HandlerType.error, ArgosController.onClientRaisedError],
        ]
        for handlerType, handlerFunc in handlers:
            client.connection.addCallback(
                handlerType,
                handlerFunc,
                client
            )
        client.connect(clientSocket)

    @staticmethod
    def onClientConnect(client: ArgosClient) -> None:
        """Called by a client when it connects to its socket.

          @param client: the client witch called the function.
        """
        logging.info(f'New ARGoS client connected on socket {client.socket}')

    @staticmethod
    def onClientDisconnect(client: ArgosClient) -> None:
        """Called by a client when it disconnects from its socket. It send a message to the \
            dashboards to inform the disconnection only if the server is running.

          @param client: the client witch called the function.
        """
        logging.info(f'ARGoS client disconnected from socket {client.socket}')
        ArgosController.clients.remove(client)
        if ArgosController.running:
            drone = ArgosController.dronesSet.getDrone(client.socket)
            CommunicationService().sendToDashboardController(
                Message(
                    type="disconnect",
                    data={"name": drone['name']}
                )
            )
            ArgosController.dronesSet.removeDrone(client.socket)

    @staticmethod
    def onClientReceivedMessage(client: ArgosClient, message: bytes) -> None:
        """Called by a client when it receives a message. The message is first decoded from byte to ascii,
        then parsed as json. It updates the drone stored status, then sends the message to the dashboards.

          @param client: the client witch called the function.
          @param message: the message in bytes received by the client.
        """
        droneIdentifier = ArgosController.getDroneIdentifier(client.socket)
        try:
            messageStr = message.decode('utf-8')
            parsedMessage: Message = json.load(StringIO(messageStr))
        except ValueError:
            logging.error(
                f'ARGoS client {droneIdentifier} receive a wrong json format : {message}')
        else:
            logging.debug(
                f'ARGoS client {droneIdentifier} received message : {messageStr}')
            if parsedMessage['type'] != 'pulse':
                return
            droneData: dict = parsedMessage['data']
            droneData: dict = {**droneData, "real": False}
            # Force ARGoS drone not to be real
            drone = Drone(**droneData)
            ArgosController.dronesSet.setDrone(client.socket, drone)
            CommunicationService().sendToDashboardController(parsedMessage)

    @staticmethod
    def onClientRaisedError(client: ArgosClient, error: Exception) -> None:
        """Called when a client raises an error while it waits for messages.

          @param client: the client witch called the function.
          @param error: the exception  raised by the client.
        """
        droneIdentifier = ArgosController.getDroneIdentifier(client.socket)
        logging.info(
            f'ARGoS client {droneIdentifier} raised an error:\n{error}')

    @staticmethod
    def sendMessage(message: Message) -> None:
        """Sends the specified message to the correct drone. doesn't sends anything if the requested drone doesn't
        exist.

          @param message: the message to send.
        """
        if message['type'] == 'startMission':
            missionRequestData: dict = message['data']
            if missionRequestData['type'] == 'fake':
                ArgosController.startFakeMission()
            elif missionRequestData['type'] == 'argos':
                ArgosController.startMission()
            return

        targetedDroneName = message['data']['name']
        if targetedDroneName == '*':
            for client in ArgosController.clients:
                ArgosController.sendMessageToSocket(client.socket, message)
            return

        droneSearchReturn = ArgosController.dronesSet.findDroneByName(
            targetedDroneName)
        if not droneSearchReturn:
            return
        clientSocket = droneSearchReturn['key']
        ArgosController.sendMessageToSocket(clientSocket, message)

    @staticmethod
    def sendMessageToSocket(clientSocket, message: Message):
        """Sends the specified message to the specified socket after converting it from json to string.

          @param clientSocket: the socket to send the message.
          @param message: the message to send.
        """
        messageStr = json.dumps(message)
        clientSocket.send(bytes(messageStr, 'ascii'))

    @staticmethod
    def getDroneIdentifier(clientSocket) -> Union[Drone, Any]:
        """Find the drone associated with the specified socket. If the drone name isn't yet registered, the socket is
        returned.

          @param clientSocket: the socket of the searched drone.
        """
        drone: Drone = ArgosController.dronesSet.getDrone(clientSocket)
        return drone['name'] if drone else clientSocket

    @staticmethod
    def startFakeMission():
        fakeDronesSet = DronesSet()
        fakeDronesSet.setDrone('Drone # 1',
                               Drone(name='Drone#1', speed=0, battery=0, position=[0, 0, 0], timestamp=0,
                                     flying=True, ledOn=True, real=False, multiRange=[0, 0, 0, 0, 0]))
        fakeDronesSet.setDrone('Drone # 2',
                               Drone(name='Drone#2', speed=0, battery=0, position=[0, 0, 0], timestamp=0,
                                     flying=True, ledOn=True, real=False, multiRange=[0, 0, 0, 0, 0]))
        ArgosController.missionHandler = MissionHandler(
            dronesSet=fakeDronesSet,
            missionType='fake',
            sendMessageCallable=lambda m: CommunicationService().sendToDashboardController(m)
        )
        Thread(target=ArgosController.simulateFakeMission).start()

    @staticmethod
    def startMission():
        ArgosController.sendMessage(
            Message(
                type='takeOff',
                data={"name": "*"}
            )
        )
        if ArgosController.missionHandler is not None:
            ArgosController.missionHandler.endMission()

        ArgosController.missionHandler = MissionHandler(
            dronesSet=ArgosController.dronesSet,
            missionType='argos',
            sendMessageCallable=lambda m: CommunicationService().sendToDashboardController(m)
        )

    @staticmethod
    def simulateFakeMission():
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
                time.sleep(i % 2)
                ArgosController.missionHandler.onReceivedPositionAndBorders(
                    droneName, position, points)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=-1.8, y=0.4), Vec2(x=-0.8, y=0.4), Vec2(x=-0.8, y=0.6), Vec2(x=-1.8, y=0.6),
                 Vec2(x=-1.8, y=0.4)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=-0.8, y=-1.8), Vec2(x=-0.8, y=-0.8), Vec2(x=-0.6, y=-0.8), Vec2(x=-0.6, y=-1.8),
                 Vec2(x=-0.8, y=-1.8)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=0.2, y=1.8), Vec2(x=0.2, y=0.6), Vec2(x=0.6, y=0.6), Vec2(x=0.6, y=1.8), Vec2(x=0.2, y=1.8)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=0.2, y=-1), Vec2(x=0.2, y=-1.2), Vec2(x=0.8, y=-1.2), Vec2(x=0.8, y=-1)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=0.8, y=2), Vec2(x=2, y=2), Vec2(x=2, y=-2), Vec2(x=-0.4, y=-2)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=-2, y=-1.8), Vec2(x=-2, y=0.2)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=-1, y=-2), Vec2(x=-1.8, y=-2)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=-2, y=0.8), Vec2(x=-2, y=1.8)])
            time.sleep(1)

            ArgosController.missionHandler.onFindShape(
                [Vec2(x=-1.8, y=2), Vec2(x=0, y=2)])
            time.sleep(1)

            ArgosController.missionHandler.endMission()
