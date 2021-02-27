import json
import logging
import socket
from io import StringIO
from threading import Thread
from typing import Any, Set, Union

from clients.argos_client import ArgosClient
from metaclasses.singleton import Singleton
from models.connection import HandlerType
from models.drone import Drone
from models.message import Message
from services.communications import CommunicationService
from services.drones_set import DronesSet


class ArgosController(metaclass=Singleton):
    TCP_IP = '0.0.0.0'
    TCP_PORT = 3995
    BUFFER_SIZE = 20
    N_MAX_DRONES = 10
    TCPServer = None
    running = True
    dronesSet = DronesSet()
    clients: Set[ArgosClient] = set()

    def launch(self) -> Thread:
        thread = Thread(target=self.launchServer)
        thread.start()
        return thread

    def launchServer(self):
        TCPServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPServer.setblocking(False)
        TCPServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPServer.bind((ArgosController.TCP_IP, ArgosController.TCP_PORT))
        TCPServer.listen(ArgosController.N_MAX_DRONES)
        ArgosController.TCPServer = TCPServer

        while ArgosController.running:
            try:
                clientSocket, addr = TCPServer.accept()
                self.handleClient(clientSocket, addr)
            except:
                pass

    def stopServer():
        for client in ArgosController.clients:
            client.closeClient()
        ArgosController.running = False
        ArgosController.TCPServer.close()

    def handleClient(self, clientSocket, addr):
        client = ArgosClient()
        ArgosController.clients.add(client)
        client.connection.addCallback(
            HandlerType.connection, ArgosController.onClientConnect, client=client)
        client.connection.addCallback(
            HandlerType.disconnection, ArgosController.onClientDisconnect, client=client)
        client.connection.addCallback(
            HandlerType.message, ArgosController.onClientReceivedMessage, client=client)
        client.connection.addCallback(
            HandlerType.error, ArgosController.onClientRaisedError, client=client)
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
            CommunicationService().sendToDashboardController({
                "type": "disconnect",
                "data": {
                    "name": drone['name']
                }
            })
        ArgosController.dronesSet.removeDrone(client.socket)

    @staticmethod
    def onClientReceivedMessage(message: bytes, client: ArgosClient) -> None:
        droneIdentifier = ArgosController.getDroneIdentifier(client.socket)
        try:
            messageStr = message.decode('utf-8')
            parsedMessage: Message = json.load(StringIO(messageStr))
        except:
            logging.error(
                f'ARGoS client {droneIdentifier} receive a wrong json format : {messageStr}')
        else:
            logging.info(
                f'ARGoS client {droneIdentifier} received message : {messageStr}')
            if parsedMessage['type'] != 'pulse':
                return
            drone: Drone = parsedMessage['data']
            # Force ARGoS drone not to be real
            drone = {**drone, "real": False}
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
        socket = droneSearchReturn['key']
        ArgosController.sendMessageToSocket(socket, message)

    @staticmethod
    def sendMessageToSocket(socket, message: Message):
        messageStr = json.dumps(message)
        socket.send(bytes(messageStr, 'ascii'))

    @staticmethod
    def getDroneIdentifier(socket) -> Union[Drone, Any]:
        drone: Drone = ArgosController.dronesSet.getDrone(socket)
        return drone['name'] if drone else socket
