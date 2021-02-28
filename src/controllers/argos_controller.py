import json
import logging
import socket
from io import StringIO
from threading import Thread
from typing import Any, Set, Union

from src.clients.argos_client import ArgosClient
from src.metaclasses.singleton import Singleton
from src.models.connection import HandlerType
from src.models.drone import Drone
from src.models.message import Message
from src.services.communications import CommunicationService
from src.services.drones_set import DronesSet


class ArgosController(metaclass=Singleton):
    TCP_HOST = '0.0.0.0'
    TCP_PORT = 3995
    BUFFER_SIZE = 20
    N_MAX_DRONES = 10
    TCPServer = None
    running = True
    dronesSet = DronesSet()
    clients: Set[ArgosClient] = set()

    @staticmethod
    def launch() -> Thread:
        thread = Thread(target=ArgosController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def launchServer():
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
            except:
                pass

    @staticmethod
    def stopServer():
        for client in ArgosController.clients:
            client.closeClient()
        ArgosController.running = False
        ArgosController.TCPServer.close()

    @staticmethod
    def handleClient(clientSocket, addr):
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
                client=client
            )
        client.connect(clientSocket)

    @staticmethod
    def onClientConnect(client: ArgosClient) -> None:
        logging.info(f'New ARGoS client connected on socket {client.socket}')

    @staticmethod
    def onClientDisconnect(client: ArgosClient) -> None:
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
    def onClientReceivedMessage(message: bytes, client: ArgosClient) -> None:
        droneIdentifier = ArgosController.getDroneIdentifier(client.socket)
        try:
            messageStr = message.decode('utf-8')
            parsedMessage: Message = json.load(StringIO(messageStr))
        except ValueError:
            logging.error(
                f'ARGoS client {droneIdentifier} receive a wrong json format : {message}')
        else:
            logging.info(
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
    def onClientRaisedError(error: Exception, client: ArgosClient) -> None:
        droneIdentifier = ArgosController.getDroneIdentifier(client.socket)
        logging.info(
            f'ARGoS client {droneIdentifier} raised an error:\n{error}')

    @staticmethod
    def sendMessage(message: Message) -> None:
        targetedDroneName = message['data']['name']
        if targetedDroneName == '*':
            for client in ArgosController.clients:
                ArgosController.sendMessageToSocket(client.socket, message)
            return

        droneSearchReturn = ArgosController.dronesSet.findDroneByName(
            targetedDroneName)
        if not droneSearchReturn:
            return
        webSocket = droneSearchReturn['key']
        ArgosController.sendMessageToSocket(webSocket, message)

    @staticmethod
    def sendMessageToSocket(webSocket, message: Message):
        messageStr = json.dumps(message)
        webSocket.send(bytes(messageStr, 'ascii'))

    @staticmethod
    def getDroneIdentifier(webSocket) -> Union[Drone, Any]:
        drone: Drone = ArgosController.dronesSet.getDrone(webSocket)
        return drone['name'] if drone else webSocket
