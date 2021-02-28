import json
import logging
from io import StringIO
from threading import Thread
from typing import List, Set

from flask_threaded_sockets.websocket import WebSocket

from src.clients.dashboard_client import DashboardClient
from flask import Flask
from flask_threaded_sockets import Sockets, ThreadedWebsocketServer
from src.metaclasses.singleton import Singleton
from src.models.connection import HandlerType
from src.models.drone import Drone
from src.models.message import Message
from src.services.communications import CommunicationService


class DashboardController(metaclass=Singleton):

    app = Flask(__name__)
    sockets = Sockets(app)
    HOST = '0.0.0.0'
    SERVER_PORT = 5000
    webSocketServer = None
    clients: Set[DashboardClient] = set()

    @staticmethod
    def launchServer():
        webSocketServer = ThreadedWebsocketServer(
            DashboardController.HOST,
            DashboardController.SERVER_PORT,
            DashboardController.app
        )
        DashboardController.webSocketServer = webSocketServer
        webSocketServer.serve_forever()

    @staticmethod
    def launch() -> Thread:
        thread = Thread(target=DashboardController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def stopServer():
        for client in DashboardController.clients:
            client.closeClient()
        DashboardController.webSocketServer.shutdown()

    @staticmethod
    def handleClient(webSocket: WebSocket):
        client = DashboardClient()
        DashboardController.clients.add(client)
        handlers = [
            [HandlerType.connection, DashboardController.onClientConnect],
            [HandlerType.disconnection, DashboardController.onClientDisconnect],
            [HandlerType.message, DashboardController.onClientReceivedMessage],
            [HandlerType.error, DashboardController.onClientRaisedError],
        ]
        for handlerType, handlerFunc in handlers:
            client.connection.addCallback(
                handlerType,
                handlerFunc,
                client=client
            )
        client.connect(webSocket)
        client.thread.join()

    @staticmethod
    def onClientConnect(client: DashboardClient) -> None:
        logging.info(
            f'New Dashboard client connected on socket {client.socket}')
        DashboardController.sendAllRobotsStatus(client.socket)

    @staticmethod
    def onClientDisconnect(client: DashboardClient) -> None:
        logging.info(
            f'Dashboard client disconnected from socket {client.socket}')
        DashboardController.clients.remove(client)

    @staticmethod
    def onClientReceivedMessage(message: str, client: DashboardClient) -> None:
        if message is None:
            return
        try:
            parsedMessage = json.load(StringIO(message))
        except ValueError:
            logging.error(
                f'Dashboard client {client.socket} receive a wrong json format : {message}')
        else:
            logging.info(
                f'Dashboard client {client.socket} received message : {message}')
            CommunicationService().sendToArgosController(parsedMessage)
            CommunicationService().sendToCrazyradioController(parsedMessage)

    @staticmethod
    def onClientRaisedError(error: Exception, client: DashboardClient) -> None:
        logging.info(
            f'Dashboard client {client.socket} raised an error:\n{error}')

    @staticmethod
    def sendAllRobotsStatus(socket) -> None:
        logging.info(
            'Sending all robots status to new Dashboard client')
        drones: List[Drone] = CommunicationService().getAllDrones()
        for drone in drones:
            DashboardController.sendMessageToSocket(socket, {
                "type": "pulse",
                "data": drone
            })

    @staticmethod
    def sendMessage(message: Message) -> None:
        for client in DashboardController.clients:
            DashboardController.sendMessageToSocket(client.socket, message)

    @staticmethod
    def sendMessageToSocket(socket, message: Message) -> None:
        messageStr = json.dumps(message)
        socket.send(messageStr)
        pass


@DashboardController.sockets.route('/dashboard')
def handleNewSocketConnection(webSocket: WebSocket):
    DashboardController.handleClient(webSocket)


@DashboardController.app.route('/')
def handleNewHttpConnection():
    return 'Dashboard Controller'
