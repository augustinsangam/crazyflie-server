import json
import logging
from io import StringIO
from threading import Thread
from typing import List, Set

from clients.dashboard_client import DashboardClient
from flask import Flask
from flask_threaded_sockets import Sockets, ThreadedWebsocketServer
from metaclasses.singleton import Singleton
from models.connection import HandlerType
from models.drone import Drone
from models.message import Message
from services.communications import CommunicationService


class DashboardController(metaclass=Singleton):

    app = Flask(__name__)
    sockets = Sockets(app)
    HOST = '0.0.0.0'
    SERVER_PORT = 5000
    webSocketServer = None
    clients: Set[DashboardClient] = set()

    @sockets.route('/dashboard')
    def handleClient(webSocket):
        client = DashboardClient()
        DashboardController.clients.add(client)
        client.connection.addCallback(
            HandlerType.connection, DashboardController.onClientConnect, client=client)
        client.connection.addCallback(
            HandlerType.disconnection, DashboardController.onClientDisconnect, client=client)
        client.connection.addCallback(
            HandlerType.message, DashboardController.onClientReceivedMessage, client=client)
        client.connection.addCallback(
            HandlerType.error, DashboardController.onClientRaisedError, client=client)
        client.connect(webSocket)
        client.thread.join()

    @app.route('/')
    def hello():
        return 'Dashboard Controller'

    def launchServer(self):
        webSocketServer = ThreadedWebsocketServer(
            DashboardController.HOST,
            DashboardController.SERVER_PORT,
            DashboardController.app
        )
        DashboardController.webSocketServer = webSocketServer
        webSocketServer.serve_forever()

    def launch(self) -> Thread:
        thread = Thread(target=self.launchServer)
        thread.start()
        return thread

    def stopServer():
        for client in DashboardController.clients:
            client.closeClient()
        DashboardController.webSocketServer.shutdown()

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
        logging.info(message)
        if message == None:
            return
        try:
            parsedMessage = DashboardController.parseMessage(message)
        except:
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
            'Sending all robots statuts to new Dashboard client')
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

    @staticmethod
    def parseMessage(message: str) -> dict:
        return json.load(StringIO(message))
